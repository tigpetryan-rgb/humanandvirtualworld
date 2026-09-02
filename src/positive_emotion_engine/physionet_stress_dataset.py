from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

DATASET_NAME = "Wearable Device Dataset from Induced Stress and Structured Exercise Sessions"
DATASET_VERSION = "1.0.1"
DATASET_DOI = "10.13026/he0v-tf17"

PROTOCOL_STAGES: dict[str, tuple[str, ...]] = {
    "v1": (
        "Baseline",
        "Stroop",
        "First Rest",
        "TMCT",
        "Second Rest",
        "Real Opinion",
        "Opposite Opinion",
        "Subtract",
    ),
    "v2": (
        "Baseline",
        "TMCT",
        "First Rest",
        "Real Opinion",
        "Opposite Opinion",
        "Second Rest",
        "Subtract",
    ),
}

STRESS_SESSION_CAVEATS: dict[str, str] = {
    "S02": "duplicated_data",
    "f07": "wristband_protection_cover_not_removed_signals_not_all_valid",
    "f14": "recording_split_into_two_parts",
}


class DatasetContractError(ValueError):
    pass


@dataclass(frozen=True)
class StressLabel:
    participant_id: str
    protocol_version: str
    stage: str
    self_reported_stress: float


@dataclass(frozen=True)
class RegularEmpaticaStream:
    session_start_utc: str
    sample_rate_hz: float
    values: tuple[float, ...]
    unit: str

    @property
    def duration_seconds(self) -> float:
        return len(self.values) / self.sample_rate_hz


@dataclass(frozen=True)
class ParticipantDataPolicy:
    participant_id: str
    protocol_version: str
    use_for_model_validation: bool
    reason: str | None


def protocol_version_for_participant(participant_id: str) -> str:
    if participant_id.startswith("S") and participant_id[1:].isdigit():
        return "v1"
    if participant_id.startswith("f") and participant_id[1:].isdigit():
        return "v2"
    raise DatasetContractError(f"unrecognized stress participant id: {participant_id}")


def participant_data_policy(participant_id: str) -> ParticipantDataPolicy:
    version = protocol_version_for_participant(participant_id)
    caveat = STRESS_SESSION_CAVEATS.get(participant_id)
    return ParticipantDataPolicy(
        participant_id=participant_id,
        protocol_version=version,
        use_for_model_validation=caveat is None,
        reason=caveat,
    )


def parse_stress_level_csv(text: str, protocol_version: str) -> list[StressLabel]:
    if protocol_version not in PROTOCOL_STAGES:
        raise DatasetContractError(f"unsupported protocol version: {protocol_version}")
    rows = list(csv.reader(io.StringIO(text)))
    if len(rows) < 2:
        raise DatasetContractError("stress-level CSV must include header and data rows")

    header = [cell.strip() for cell in rows[0]]
    if not header:
        raise DatasetContractError("missing stress-level header")
    actual_stages = tuple(header[1:])
    expected_stages = PROTOCOL_STAGES[protocol_version]
    if actual_stages != expected_stages:
        raise DatasetContractError(
            f"stage header mismatch for {protocol_version}: {actual_stages!r} != {expected_stages!r}"
        )

    labels: list[StressLabel] = []
    seen: set[str] = set()
    for row_number, row in enumerate(rows[1:], start=2):
        if not row or all(not cell.strip() for cell in row):
            continue
        if len(row) != len(header):
            raise DatasetContractError(f"row {row_number} has {len(row)} columns; expected {len(header)}")
        participant_id = row[0].strip()
        if participant_id in seen:
            raise DatasetContractError(f"duplicate participant in label CSV: {participant_id}")
        seen.add(participant_id)
        if protocol_version_for_participant(participant_id) != protocol_version:
            raise DatasetContractError(f"participant {participant_id} does not belong to {protocol_version}")

        for stage, raw in zip(expected_stages, row[1:]):
            try:
                value = float(raw)
            except ValueError as exc:
                raise DatasetContractError(
                    f"non-numeric self-report for {participant_id}/{stage}: {raw!r}"
                ) from exc
            # The published files contain 0.0 values despite the prose describing a 1..10 verbal scale.
            # Preserve the file values rather than silently rewriting them.
            if not 0.0 <= value <= 10.0:
                raise DatasetContractError(
                    f"self-report outside file-supported 0..10 range for {participant_id}/{stage}: {value}"
                )
            labels.append(
                StressLabel(
                    participant_id=participant_id,
                    protocol_version=protocol_version,
                    stage=stage,
                    self_reported_stress=value,
                )
            )
    return labels


def parse_event_tags(text: str) -> tuple[datetime, ...]:
    tags: list[datetime] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        value = line.strip()
        if not value:
            continue
        try:
            tag = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError as exc:
            raise DatasetContractError(f"invalid tag timestamp at line {line_number}: {value!r}") from exc
        if tags and tag <= tags[-1]:
            raise DatasetContractError("event tags must be strictly increasing")
        tags.append(tag)
    if len(tags) < 2:
        raise DatasetContractError("at least two event tags are required")
    return tuple(tags)


def parse_regular_empatica_stream(
    text: str,
    *,
    unit: str,
    expected_sample_rate_hz: float | None = None,
) -> RegularEmpaticaStream:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 3:
        raise DatasetContractError("regular Empatica stream must contain start, sample rate and values")

    session_start = lines[0]
    try:
        datetime.strptime(session_start, "%Y-%m-%d %H:%M:%S")
    except ValueError as exc:
        raise DatasetContractError(f"invalid UTC session start: {session_start!r}") from exc
    try:
        sample_rate = float(lines[1])
    except ValueError as exc:
        raise DatasetContractError(f"invalid sample rate: {lines[1]!r}") from exc
    if sample_rate <= 0:
        raise DatasetContractError("sample rate must be positive")
    if expected_sample_rate_hz is not None and abs(sample_rate - expected_sample_rate_hz) > 1e-9:
        raise DatasetContractError(
            f"unexpected sample rate {sample_rate}; expected {expected_sample_rate_hz}"
        )

    values: list[float] = []
    for line_number, raw in enumerate(lines[2:], start=3):
        if "," in raw:
            raise DatasetContractError(
                f"expected one-column regular stream at line {line_number}, got {raw!r}"
            )
        try:
            values.append(float(raw))
        except ValueError as exc:
            raise DatasetContractError(f"invalid measurement at line {line_number}: {raw!r}") from exc
    if not values:
        raise DatasetContractError("stream contains no measurements")
    return RegularEmpaticaStream(
        session_start_utc=session_start,
        sample_rate_hz=sample_rate,
        values=tuple(values),
        unit=unit,
    )


def stream_start_offset_seconds(reference: RegularEmpaticaStream, other: RegularEmpaticaStream) -> float:
    reference_start = datetime.strptime(reference.session_start_utc, "%Y-%m-%d %H:%M:%S")
    other_start = datetime.strptime(other.session_start_utc, "%Y-%m-%d %H:%M:%S")
    return (other_start - reference_start).total_seconds()


def validate_public_recorded_bundle(dataset_root: str | Path) -> dict[str, Any]:
    root = Path(dataset_root)
    v1 = parse_stress_level_csv((root / "Stress_Level_v1.csv").read_text(), "v1")
    v2 = parse_stress_level_csv((root / "Stress_Level_v2.csv").read_text(), "v2")

    v1_ids = sorted({label.participant_id for label in v1})
    v2_ids = sorted({label.participant_id for label in v2})
    if len(v1_ids) != 18 or len(v2_ids) != 18:
        raise DatasetContractError(
            f"expected 18 participants per protocol version; got v1={len(v1_ids)} v2={len(v2_ids)}"
        )

    subject = root / "Wearable_Dataset" / "STRESS" / "f10"
    tags = parse_event_tags((subject / "tags.csv").read_text())
    eda = parse_regular_empatica_stream(
        (subject / "EDA.csv").read_text(), unit="uS", expected_sample_rate_hz=4.0
    )
    hr = parse_regular_empatica_stream(
        (subject / "HR.csv").read_text(), unit="bpm", expected_sample_rate_hz=1.0
    )

    f10_labels = [label for label in v2 if label.participant_id == "f10"]
    if len(f10_labels) != len(PROTOCOL_STAGES["v2"]):
        raise DatasetContractError("f10 does not have the expected V2 stage self-reports")

    policies = [participant_data_policy(pid) for pid in [*v1_ids, *v2_ids]]
    excluded = [policy for policy in policies if not policy.use_for_model_validation]

    return {
        "dataset": {
            "name": DATASET_NAME,
            "version": DATASET_VERSION,
            "doi": DATASET_DOI,
        },
        "labels": {
            "v1_participants": len(v1_ids),
            "v1_stage_labels": len(v1),
            "v2_participants": len(v2_ids),
            "v2_stage_labels": len(v2),
            "value_range_observed": [
                min(label.self_reported_stress for label in [*v1, *v2]),
                max(label.self_reported_stress for label in [*v1, *v2]),
            ],
        },
        "recorded_format_probe": {
            "participant_id": "f10",
            "protocol_version": "v2",
            "event_tag_count": len(tags),
            "eda": {
                "start_utc": eda.session_start_utc,
                "sample_rate_hz": eda.sample_rate_hz,
                "samples": len(eda.values),
                "duration_seconds": eda.duration_seconds,
            },
            "hr": {
                "start_utc": hr.session_start_utc,
                "start_offset_from_eda_seconds": stream_start_offset_seconds(eda, hr),
                "sample_rate_hz": hr.sample_rate_hz,
                "samples": len(hr.values),
                "duration_seconds": hr.duration_seconds,
            },
            "alignment_policy": (
                "preserve each published stream start timestamp; align by timestamps during window extraction "
                "rather than requiring equal stream starts"
            ),
        },
        "exclusion_policy": [asdict(policy) for policy in excluded],
        "stage_alignment": {
            "status": "blocked_pending_notebook_verified_tag_mapping",
            "reason": (
                "labels and raw streams are validated, but tag-index-to-stage mapping is not inferred "
                "from timing alone; V1/V2 mappings must be verified against the provided protocol notebook"
            ),
        },
        "phase3_done": False,
    }


def validation_report_json(dataset_root: str | Path) -> str:
    return json.dumps(validate_public_recorded_bundle(dataset_root), indent=2, sort_keys=True)
