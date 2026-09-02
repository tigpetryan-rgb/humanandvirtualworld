from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

QUALITY_RANK = {
    "good": 1.0,
    "degraded": 0.5,
    "artifact": 0.0,
    "missing": 0.0,
    "dropout": 0.0,
}

CHANNEL_SPECS = {
    "heart_ibi_ms": {"unit": "ms", "min": 300.0, "max": 2000.0, "max_step": 500.0},
    "eda_us": {"unit": "uS", "min": 0.0, "max": 100.0, "max_step": 20.0},
    "respiration_norm": {"unit": "normalized", "min": -1.5, "max": 1.5, "max_step": 1.5},
}

MAX_ABS_OFFSET_MS = 100.0
MAX_ABS_DRIFT_PPM = 200.0
GAP_FACTOR = 1.75


class AcquisitionContractError(ValueError):
    pass


@dataclass(frozen=True)
class NormalizedSample:
    channel: str
    seq: int
    source_time_ms: float
    session_time_ms: float
    value: float | None
    quality: str
    confidence: float
    reason_codes: tuple[str, ...]


def _canonical(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def replay_digest(obj: Any) -> str:
    return hashlib.sha256(_canonical(obj).encode("utf-8")).hexdigest()


def validate_recording(recording: dict[str, Any]) -> None:
    if recording.get("schema_version") != "2.0.0":
        raise AcquisitionContractError("unsupported schema_version")
    if recording.get("data_class") not in {"synthetic_recorded", "deidentified_recorded"}:
        raise AcquisitionContractError("unsupported data_class")
    if not recording.get("session_id"):
        raise AcquisitionContractError("missing session_id")
    channels = recording.get("channels")
    if not isinstance(channels, list) or not channels:
        raise AcquisitionContractError("channels must be non-empty")

    names: set[str] = set()
    for channel in channels:
        name = channel.get("name")
        if name in names:
            raise AcquisitionContractError("duplicate channel")
        names.add(name)
        if name not in CHANNEL_SPECS:
            raise AcquisitionContractError(f"unsupported channel: {name}")
        if channel.get("unit") != CHANNEL_SPECS[name]["unit"]:
            raise AcquisitionContractError(f"unit mismatch: {name}")

        sampling_mode = channel.get("sampling_mode", "regular")
        if sampling_mode not in {"regular", "event"}:
            raise AcquisitionContractError(f"invalid sampling_mode: {name}")
        hz = channel.get("nominal_hz")
        if sampling_mode == "regular":
            if not isinstance(hz, (int, float)) or not math.isfinite(hz) or hz <= 0:
                raise AcquisitionContractError(f"invalid nominal_hz: {name}")
        elif hz is not None and (not isinstance(hz, (int, float)) or not math.isfinite(hz) or hz <= 0):
            raise AcquisitionContractError(f"invalid event nominal_hz: {name}")

        clock = channel.get("clock") or {}
        for key in ("offset_ms", "drift_ppm"):
            value = clock.get(key)
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise AcquisitionContractError(f"invalid clock {key}: {name}")
        samples = channel.get("samples")
        if not isinstance(samples, list) or not samples:
            raise AcquisitionContractError(f"samples must be non-empty: {name}")
        last_seq = -1
        last_source = -math.inf
        for sample in samples:
            seq = sample.get("seq")
            source_time = sample.get("source_time_ms")
            value = sample.get("value")
            if not isinstance(seq, int) or seq <= last_seq:
                raise AcquisitionContractError(f"nonmonotonic seq: {name}")
            if not isinstance(source_time, (int, float)) or not math.isfinite(source_time) or source_time <= last_source:
                raise AcquisitionContractError(f"nonmonotonic source_time_ms: {name}")
            if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value)):
                raise AcquisitionContractError(f"invalid value: {name}")
            last_seq = seq
            last_source = float(source_time)


def normalize_source_time(source_time_ms: float, offset_ms: float, drift_ppm: float) -> float:
    scale = 1.0 + float(drift_ppm) / 1_000_000.0
    if scale <= 0:
        raise AcquisitionContractError("clock scale must be positive")
    return (float(source_time_ms) - float(offset_ms)) / scale


def clock_diagnostics(channel: dict[str, Any]) -> dict[str, Any]:
    clock = channel["clock"]
    offset = float(clock["offset_ms"])
    drift = float(clock["drift_ppm"])
    flags: list[str] = []
    if abs(offset) > MAX_ABS_OFFSET_MS:
        flags.append("clock_offset_large")
    if abs(drift) > MAX_ABS_DRIFT_PPM:
        flags.append("clock_drift_large")
    return {
        "offset_ms": offset,
        "drift_ppm": drift,
        "quality": "degraded" if flags else "good",
        "reason_codes": flags,
    }


def _classify_sample(channel_name: str, value: float | None, previous_value: float | None) -> tuple[str, float, list[str]]:
    spec = CHANNEL_SPECS[channel_name]
    if value is None:
        return "missing", 0.0, ["explicit_missing_value"]
    v = float(value)
    if not (spec["min"] <= v <= spec["max"]):
        return "artifact", 0.0, ["outside_channel_range"]
    if previous_value is not None and abs(v - previous_value) > spec["max_step"]:
        return "artifact", 0.0, ["large_step_artifact"]
    return "good", 1.0, []


def ingest_recording(recording: dict[str, Any]) -> dict[str, Any]:
    validate_recording(recording)
    normalized: list[NormalizedSample] = []
    channel_summaries: dict[str, Any] = {}
    dropout_intervals: list[dict[str, Any]] = []

    for channel in recording["channels"]:
        name = channel["name"]
        sampling_mode = channel.get("sampling_mode", "regular")
        hz = channel.get("nominal_hz")
        expected_period = 1000.0 / float(hz) if sampling_mode == "regular" else None
        diag = clock_diagnostics(channel)
        previous_source: float | None = None
        previous_value: float | None = None
        quality_counts = {k: 0 for k in QUALITY_RANK}

        for sample in channel["samples"]:
            source_time = float(sample["source_time_ms"])
            if previous_source is not None and expected_period is not None:
                gap = source_time - previous_source
                if gap > expected_period * GAP_FACTOR:
                    missing_estimate = max(1, round(gap / expected_period) - 1)
                    dropout_intervals.append({
                        "channel": name,
                        "start_source_time_ms": round(previous_source + expected_period, 6),
                        "end_source_time_ms": round(source_time - expected_period, 6),
                        "estimated_missing_samples": missing_estimate,
                        "reason_codes": ["sampling_gap"],
                    })
                    quality_counts["dropout"] += missing_estimate

            value = sample.get("value")
            quality, confidence, reasons = _classify_sample(name, value, previous_value)
            if diag["quality"] == "degraded" and quality == "good":
                quality = "degraded"
                confidence = min(confidence, 0.5)
                reasons = [*reasons, *diag["reason_codes"]]
            quality_counts[quality] += 1

            normalized.append(NormalizedSample(
                channel=name,
                seq=int(sample["seq"]),
                source_time_ms=source_time,
                session_time_ms=round(normalize_source_time(source_time, float(channel["clock"]["offset_ms"]), float(channel["clock"]["drift_ppm"])), 6),
                value=float(value) if value is not None else None,
                quality=quality,
                confidence=confidence,
                reason_codes=tuple(reasons),
            ))
            previous_source = source_time
            if value is not None and quality not in {"artifact", "missing"}:
                previous_value = float(value)

        observed = len(channel["samples"])
        usable = quality_counts["good"] + quality_counts["degraded"]
        denom = observed + quality_counts["dropout"]
        channel_summaries[name] = {
            "sampling_mode": sampling_mode,
            "nominal_hz": float(hz) if hz is not None else None,
            "clock": diag,
            "quality_counts": quality_counts,
            "observed_samples": observed,
            "estimated_missing_samples": quality_counts["dropout"] + quality_counts["missing"],
            "usable_fraction": round(usable / denom if denom else 0.0, 6),
        }

    normalized.sort(key=lambda s: (s.session_time_ms, s.channel, s.seq))
    payload = {
        "schema_version": "2.0.0",
        "session_id": recording["session_id"],
        "data_class": recording["data_class"],
        "channel_summaries": channel_summaries,
        "dropout_intervals": dropout_intervals,
        "samples": [{
            "channel": s.channel,
            "seq": s.seq,
            "source_time_ms": s.source_time_ms,
            "session_time_ms": s.session_time_ms,
            "value": s.value,
            "quality": s.quality,
            "confidence": s.confidence,
            "reason_codes": list(s.reason_codes),
        } for s in normalized],
    }
    payload["replay_digest"] = replay_digest(payload)
    return payload


def synchronized_feature_windows(ingested: dict[str, Any], *, window_ms: float = 1000.0) -> list[dict[str, Any]]:
    if window_ms <= 0:
        raise AcquisitionContractError("window_ms must be positive")
    samples = ingested["samples"]
    if not samples:
        return []
    start = math.floor(min(s["session_time_ms"] for s in samples) / window_ms) * window_ms
    end = max(s["session_time_ms"] for s in samples)
    windows: list[dict[str, Any]] = []
    cursor = start

    while cursor <= end:
        upper = cursor + window_ms
        in_window = [s for s in samples if cursor <= s["session_time_ms"] < upper]
        features: dict[str, Any] = {}
        channel_quality: dict[str, Any] = {}

        for name in CHANNEL_SPECS:
            channel_samples = [s for s in in_window if s["channel"] == name]
            usable = [s for s in channel_samples if s["quality"] in {"good", "degraded"} and s["value"] is not None]
            weights = [QUALITY_RANK[s["quality"]] * float(s["confidence"]) for s in usable]
            total_weight = sum(weights)
            mean_value = (sum(float(s["value"]) * w for s, w in zip(usable, weights)) / total_weight) if total_weight > 0 else None
            quality_score = (sum(QUALITY_RANK[s["quality"]] for s in channel_samples) / len(channel_samples)) if channel_samples else 0.0
            channel_quality[name] = {
                "observed": len(channel_samples),
                "usable": len(usable),
                "quality_score": round(quality_score, 6),
                "missing": len(channel_samples) == 0,
            }

            if name == "heart_ibi_ms":
                features["mean_ibi_ms"] = round(mean_value, 6) if mean_value is not None else None
                features["heart_rate_bpm"] = round(60000.0 / mean_value, 6) if mean_value is not None and mean_value > 0 else None
            elif name == "eda_us":
                features["mean_eda_us"] = round(mean_value, 6) if mean_value is not None else None
            elif name == "respiration_norm":
                features["mean_respiration_norm"] = round(mean_value, 6) if mean_value is not None else None
                if usable:
                    values = [float(s["value"]) for s in usable]
                    features["respiration_range"] = round(max(values) - min(values), 6)
                else:
                    features["respiration_range"] = None

        windows.append({
            "window_start_ms": round(cursor, 6),
            "window_end_ms": round(upper, 6),
            "features": features,
            "channel_quality": channel_quality,
            "reason_codes": ["physiological_measurement_only_not_emotion_label"],
        })
        cursor = upper

    return windows


def run_phase2_recording(recording: dict[str, Any], *, window_ms: float = 1000.0) -> dict[str, Any]:
    ingested = ingest_recording(recording)
    windows = synchronized_feature_windows(ingested, window_ms=window_ms)
    result = {
        "schema_version": "2.0.0",
        "session_id": recording["session_id"],
        "recording_digest": ingested["replay_digest"],
        "channel_summaries": ingested["channel_summaries"],
        "dropout_intervals": ingested["dropout_intervals"],
        "normalized_samples": ingested["samples"],
        "windows": windows,
        "scientific_boundary": {
            "signal_quality_is_not_affect_confidence": True,
            "features_are_measurements_not_emotion_labels": True,
        },
    }
    result["replay_digest"] = replay_digest(result)
    return result
