from __future__ import annotations

import copy
import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

QUALITY_WEIGHT = {
    "good": 1.0,
    "degraded": 0.5,
    "artifact": 0.0,
    "dropout": 0.0,
    "missing": 0.0,
    "unknown": 0.0,
}

PARAMETERS = {
    "light_intensity": {"min": 0.20, "max": 1.00, "baseline": 0.60, "max_step": 0.10},
    "motion_intensity": {"min": 0.00, "max": 0.60, "baseline": 0.15, "max_step": 0.10},
    "audio_intensity": {"min": 0.00, "max": 0.70, "baseline": 0.25, "max_step": 0.10},
    "scene_density": {"min": 0.10, "max": 0.80, "baseline": 0.40, "max_step": 0.10},
}

MIN_STATE_CONFIDENCE = 0.55


class ContractError(ValueError):
    pass


@dataclass(frozen=True)
class AffectState:
    state: str
    valence: float | None
    arousal: float | None
    confidence: float
    uncertainty: float
    evidence_quality: str
    model_id: str
    reason_codes: tuple[str, ...]


def _bounded(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _canonical(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def validate_bundle(bundle: dict[str, Any]) -> None:
    if bundle.get("schema_version") != "1.0.0":
        raise ContractError("unsupported schema_version")
    session = bundle.get("session") or {}
    if session.get("synthetic") is not True or session.get("data_class") != "synthetic_only":
        raise ContractError("Phase 1 accepts synthetic_only sessions")
    if not str(session.get("participant_id", "")).startswith("synthetic-"):
        raise ContractError("Phase 1 participant_id must be synthetic")
    session_id = session.get("session_id")
    if not session_id:
        raise ContractError("missing session_id")

    samples = bundle.get("samples")
    if not isinstance(samples, list) or not samples:
        raise ContractError("samples must be a non-empty list")

    last_seq = -1
    last_time = -1
    for sample in samples:
        if sample.get("session_id") != session_id:
            raise ContractError("sample session_id mismatch")
        seq = sample.get("seq")
        mono = sample.get("monotonic_ns")
        if not isinstance(seq, int) or seq <= last_seq:
            raise ContractError("seq must strictly increase")
        if not isinstance(mono, int) or mono < last_time:
            raise ContractError("monotonic_ns must be nondecreasing")
        last_seq, last_time = seq, mono

        quality = sample.get("quality")
        if quality not in QUALITY_WEIGHT:
            raise ContractError(f"unsupported quality: {quality}")
        confidence = sample.get("confidence")
        value = sample.get("value")
        sync_uncertainty = sample.get("sync_uncertainty_ms")
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            raise ContractError("confidence outside [0,1]")
        if not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ContractError("synthetic sensor value outside [0,1]")
        if not isinstance(sync_uncertainty, (int, float)) or sync_uncertainty < 0:
            raise ContractError("invalid sync uncertainty")

    scene = bundle.get("initial_scene") or {}
    for name, spec in PARAMETERS.items():
        value = scene.get(name)
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ContractError(f"invalid scene value: {name}")
        if not spec["min"] <= value <= spec["max"]:
            raise ContractError(f"initial scene outside registry: {name}")

    policy = bundle.get("policy") or {}
    if policy.get("policy_id") != "synthetic-reference-v1":
        raise ContractError("unsupported policy_id")
    if not isinstance(policy.get("seed"), int) or policy["seed"] < 0:
        raise ContractError("seed must be a nonnegative integer")


def _weighted_feature(samples: list[dict[str, Any]], sensor_types: set[str]) -> tuple[float | None, float, int]:
    weighted_sum = 0.0
    total_weight = 0.0
    usable = 0
    for sample in samples:
        if sample["sensor_type"] not in sensor_types:
            continue
        quality_weight = QUALITY_WEIGHT[sample["quality"]]
        weight = quality_weight * float(sample["confidence"])
        if weight <= 0:
            continue
        usable += 1
        weighted_sum += float(sample["value"]) * weight
        total_weight += weight
    if total_weight == 0:
        return None, 0.0, usable
    return weighted_sum / total_weight, min(1.0, total_weight / max(1, usable)), usable


def extract_features(samples: list[dict[str, Any]]) -> dict[str, Any]:
    activation, activation_conf, activation_n = _weighted_feature(samples, {"heart", "eda", "respiration"})
    engagement, engagement_conf, engagement_n = _weighted_feature(
        samples, {"gaze", "pupil", "face_motion", "head_motion", "body_motion"}
    )
    usable_total = activation_n + engagement_n
    confidence_parts = [x for x in (activation_conf, engagement_conf) if x > 0]
    aggregate_confidence = sum(confidence_parts) / len(confidence_parts) if confidence_parts else 0.0
    return {
        "feature_schema": "feature-vector-v1",
        "activation_proxy": activation,
        "engagement_proxy": engagement,
        "usable_sample_count": usable_total,
        "aggregate_confidence": round(aggregate_confidence, 6),
        "missing_features": [
            name
            for name, value in (("activation_proxy", activation), ("engagement_proxy", engagement))
            if value is None
        ],
        "reason_codes": ["synthetic_reference_features_only"],
    }


def estimate_state(features: dict[str, Any]) -> AffectState:
    confidence = float(features["aggregate_confidence"])
    if features["usable_sample_count"] < 3 or features["missing_features"] or confidence < MIN_STATE_CONFIDENCE:
        return AffectState(
            state="unknown",
            valence=None,
            arousal=None,
            confidence=round(confidence, 6),
            uncertainty=round(1.0 - confidence, 6),
            evidence_quality="insufficient",
            model_id="synthetic-estimator-v1",
            reason_codes=("insufficient_or_low_confidence_evidence", "synthetic_reference_only"),
        )

    activation = float(features["activation_proxy"])
    engagement = float(features["engagement_proxy"])
    return AffectState(
        state="known",
        valence=round(_bounded(2.0 * engagement - 1.0, -1.0, 1.0), 6),
        arousal=round(_bounded(activation, 0.0, 1.0), 6),
        confidence=round(confidence, 6),
        uncertainty=round(1.0 - confidence, 6),
        evidence_quality="synthetic_usable",
        model_id="synthetic-estimator-v1",
        reason_codes=("synthetic_reference_only",),
    )


def propose_command(state: AffectState, scene: dict[str, float], seed: int) -> dict[str, Any]:
    if state.state != "known":
        return {
            "parameter": "light_intensity",
            "requested_value": scene["light_intensity"],
            "previous_value": scene["light_intensity"],
            "reason": "unknown_state_noop",
            "policy_id": "synthetic-reference-v1",
            "seed": seed,
        }

    delta = 0.08 if (state.valence or 0.0) >= 0 else -0.05
    requested = round(scene["light_intensity"] + delta, 6)
    return {
        "parameter": "light_intensity",
        "requested_value": requested,
        "previous_value": scene["light_intensity"],
        "reason": "synthetic_positive_direction" if delta > 0 else "synthetic_reduce_direction",
        "policy_id": "synthetic-reference-v1",
        "seed": seed,
    }


def safety_decision(candidate: dict[str, Any], state: AffectState, stop_requested: bool = False) -> dict[str, Any]:
    name = candidate.get("parameter")
    if name not in PARAMETERS:
        return {
            "approved": False,
            "applied_value": None,
            "clamped": False,
            "decision_codes": ["unregistered_parameter"],
        }

    spec = PARAMETERS[name]
    previous = candidate.get("previous_value")
    requested = candidate.get("requested_value")

    if stop_requested:
        return {
            "approved": False,
            "applied_value": spec["baseline"],
            "clamped": False,
            "decision_codes": ["human_stop", "safe_baseline"],
        }

    if state.state != "known" or state.confidence < MIN_STATE_CONFIDENCE:
        return {
            "approved": False,
            "applied_value": previous,
            "clamped": False,
            "decision_codes": ["low_confidence_or_unknown_state", "noop"],
        }

    if (
        not isinstance(previous, (int, float))
        or not isinstance(requested, (int, float))
        or not math.isfinite(previous)
        or not math.isfinite(requested)
    ):
        return {
            "approved": False,
            "applied_value": None,
            "clamped": False,
            "decision_codes": ["non_finite_or_invalid_value"],
        }

    bounded = _bounded(float(requested), spec["min"], spec["max"])
    step_low = float(previous) - spec["max_step"]
    step_high = float(previous) + spec["max_step"]
    stepped = _bounded(bounded, step_low, step_high)
    final = round(_bounded(stepped, spec["min"], spec["max"]), 6)
    clamped = not math.isclose(final, float(requested), abs_tol=1e-12)
    codes = ["approved"]
    if clamped:
        codes.append("clamped_to_safety_envelope")
    return {"approved": True, "applied_value": final, "clamped": clamped, "decision_codes": codes}


def _event(
    session_id: str,
    seq: int,
    event_type: str,
    payload: dict[str, Any],
    parent_ids: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "telemetry-v1",
        "event_id": f"t{seq}",
        "session_id": session_id,
        "seq": seq,
        "event_type": event_type,
        "component_version": "phase1-reference-v1",
        "parent_event_ids": parent_ids or [],
        "payload": payload,
    }


def run_session(bundle: dict[str, Any]) -> dict[str, Any]:
    validate_bundle(bundle)
    data = copy.deepcopy(bundle)
    session = data["session"]
    session_id = session["session_id"]

    features = extract_features(data["samples"])
    state = estimate_state(features)
    state_payload = {
        "state": state.state,
        "valence": state.valence,
        "arousal": state.arousal,
        "confidence": state.confidence,
        "uncertainty": state.uncertainty,
        "evidence_quality": state.evidence_quality,
        "model_id": state.model_id,
        "reason_codes": list(state.reason_codes),
    }

    scene = copy.deepcopy(data["initial_scene"])
    candidate = propose_command(state, scene, data["policy"]["seed"])
    decision = safety_decision(candidate, state, bool(session["stop_requested"]))
    if decision["applied_value"] is not None:
        scene[candidate["parameter"]] = decision["applied_value"]

    telemetry = [
        _event(session_id, 1, "features", features),
        _event(session_id, 2, "affect_state_estimate", state_payload, ["t1"]),
        _event(session_id, 3, "candidate_environment_command", candidate, ["t2"]),
        _event(session_id, 4, "safety_decision", decision, ["t3"]),
        _event(session_id, 5, "scene_applied", {"scene_state": scene}, ["t4"]),
    ]

    result = {
        "pipeline_version": "phase1-reference-v1",
        "policy_seed": data["policy"]["seed"],
        "session_id": session_id,
        "features": features,
        "state": state_payload,
        "candidate": candidate,
        "safety": decision,
        "final_scene": scene,
        "telemetry": telemetry,
    }
    result["replay_digest"] = replay_digest(result)
    return result


def replay_digest(result: dict[str, Any]) -> str:
    normalized = {k: v for k, v in result.items() if k != "replay_digest"}
    return hashlib.sha256(_canonical(normalized).encode("utf-8")).hexdigest()
