from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from positive_emotion_engine.physionet_stress_dataset import (
    DatasetContractError,
    PROTOCOL_STAGES,
    RegularEmpaticaStream,
    StressLabel,
)
from positive_emotion_engine.state_inference import TrainingExample


@dataclass(frozen=True)
class StageTagMapping:
    """Explicit mapping from one protocol stage to two cleaned tag boundaries.

    The dataset-specific tag indices must come from a verified protocol source.
    This module intentionally has no inferred/default mapping from elapsed time.
    """

    stage: str
    start_tag_index: int
    end_tag_index: int


@dataclass(frozen=True)
class StreamWindowSummary:
    mean: float | None
    expected_samples: int
    observed_samples: int
    usable_samples: int
    coverage: float
    usable_fraction: float


def _parse_utc(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError as exc:
        raise DatasetContractError(f"invalid stream UTC timestamp: {value!r}") from exc


def validate_stage_tag_mapping(
    protocol_version: str,
    mappings: Sequence[StageTagMapping],
    *,
    tag_count: int,
) -> None:
    if protocol_version not in PROTOCOL_STAGES:
        raise DatasetContractError(f"unsupported protocol version: {protocol_version}")
    expected_stages = PROTOCOL_STAGES[protocol_version]
    actual_stages = tuple(mapping.stage for mapping in mappings)
    if actual_stages != expected_stages:
        raise DatasetContractError(
            "stage-tag mapping must preserve exact protocol stage order; "
            f"got {actual_stages!r}, expected {expected_stages!r}"
        )
    if tag_count < 2:
        raise DatasetContractError("at least two cleaned tags are required")

    previous_start = -1
    previous_end = -1
    for mapping in mappings:
        if not isinstance(mapping.start_tag_index, int) or not isinstance(mapping.end_tag_index, int):
            raise DatasetContractError("tag indices must be integers")
        if not (0 <= mapping.start_tag_index < tag_count):
            raise DatasetContractError(f"start tag index out of range for {mapping.stage}")
        if not (0 <= mapping.end_tag_index < tag_count):
            raise DatasetContractError(f"end tag index out of range for {mapping.stage}")
        if mapping.start_tag_index >= mapping.end_tag_index:
            raise DatasetContractError(f"non-positive tag interval for {mapping.stage}")
        if mapping.start_tag_index < previous_start or mapping.end_tag_index < previous_end:
            raise DatasetContractError("stage-tag mappings must be monotonic")
        previous_start = mapping.start_tag_index
        previous_end = mapping.end_tag_index


def _window_summary(
    stream: RegularEmpaticaStream,
    *,
    start: datetime,
    end: datetime,
    valid_min: float,
    valid_max: float,
) -> StreamWindowSummary:
    if end <= start:
        raise DatasetContractError("stage window must have positive duration")

    stream_start = _parse_utc(stream.session_start_utc)
    rate = float(stream.sample_rate_hz)
    start_offset = (start - stream_start).total_seconds()
    end_offset = (end - stream_start).total_seconds()
    duration = (end - start).total_seconds()
    expected = max(1, int(round(duration * rate)))

    # Convert the absolute UTC interval to this stream's own sample index space.
    # Each published stream keeps its independent start timestamp.
    first = max(0, int(math.ceil(start_offset * rate - 1e-9)))
    last_exclusive = min(len(stream.values), int(math.ceil(end_offset * rate - 1e-9)))
    if end_offset <= 0 or first >= len(stream.values) or last_exclusive <= first:
        return StreamWindowSummary(
            mean=None,
            expected_samples=expected,
            observed_samples=0,
            usable_samples=0,
            coverage=0.0,
            usable_fraction=0.0,
        )

    observed_values = stream.values[first:last_exclusive]
    usable = [
        float(value)
        for value in observed_values
        if math.isfinite(float(value)) and valid_min <= float(value) <= valid_max
    ]
    observed = len(observed_values)
    coverage = min(1.0, observed / expected)
    usable_fraction = len(usable) / observed if observed else 0.0
    mean = sum(usable) / len(usable) if usable else None
    return StreamWindowSummary(
        mean=mean,
        expected_samples=expected,
        observed_samples=observed,
        usable_samples=len(usable),
        coverage=coverage,
        usable_fraction=usable_fraction,
    )


def build_stage_training_examples(
    *,
    participant_id: str,
    protocol_version: str,
    labels: Sequence[StressLabel],
    tags: Sequence[datetime],
    eda: RegularEmpaticaStream,
    hr: RegularEmpaticaStream,
    mappings: Sequence[StageTagMapping],
) -> list[TrainingExample]:
    """Build leakage-safe stage examples using only an explicit verified tag mapping.

    No stage is inferred from duration, task difficulty, signal shape, stress value,
    or neighboring participants. Labels are joined by exact participant/stage identity.
    """

    validate_stage_tag_mapping(protocol_version, mappings, tag_count=len(tags))
    if any(tags[index] >= tags[index + 1] for index in range(len(tags) - 1)):
        raise DatasetContractError("cleaned tags must be strictly increasing")

    expected_stages = PROTOCOL_STAGES[protocol_version]
    label_by_stage: dict[str, StressLabel] = {}
    for label in labels:
        if label.participant_id != participant_id:
            continue
        if label.protocol_version != protocol_version:
            raise DatasetContractError(
                f"label protocol mismatch for {participant_id}/{label.stage}: {label.protocol_version}"
            )
        if label.stage in label_by_stage:
            raise DatasetContractError(f"duplicate stage label for {participant_id}/{label.stage}")
        label_by_stage[label.stage] = label
    if tuple(label_by_stage.keys()) != expected_stages:
        raise DatasetContractError(
            "participant labels must contain each protocol stage exactly once and in canonical order"
        )

    examples: list[TrainingExample] = []
    for mapping in mappings:
        start = tags[mapping.start_tag_index]
        end = tags[mapping.end_tag_index]
        if end <= start:
            raise DatasetContractError(f"non-positive timestamp interval for {mapping.stage}")

        eda_summary = _window_summary(
            eda,
            start=start,
            end=end,
            valid_min=0.0,
            valid_max=100.0,
        )
        hr_summary = _window_summary(
            hr,
            start=start,
            end=end,
            valid_min=30.0,
            valid_max=200.0,
        )

        modality_summaries = {
            "eda": eda_summary,
            "hr": hr_summary,
        }
        observed_quality = [
            summary.coverage * summary.usable_fraction
            for summary in modality_summaries.values()
            if summary.observed_samples > 0
        ]
        signal_quality = sum(observed_quality) / len(observed_quality) if observed_quality else 0.0
        observed_modalities = sum(summary.mean is not None for summary in modality_summaries.values())

        label = label_by_stage[mapping.stage]
        examples.append(
            TrainingExample(
                participant_id=participant_id,
                features={
                    "mean_eda_us": round(eda_summary.mean, 6) if eda_summary.mean is not None else None,
                    "heart_rate_bpm": round(hr_summary.mean, 6) if hr_summary.mean is not None else None,
                },
                self_reported_stress=float(label.self_reported_stress),
                quality_score=round(signal_quality, 6),
                provenance={
                    "source": "physionet_wearable_device_dataset",
                    "data_class": "deidentified_recorded",
                    "participant_id": participant_id,
                    "protocol_version": protocol_version,
                    "stage": mapping.stage,
                    "stage_semantics": "context_only_not_emotion_ground_truth",
                    "ground_truth_semantics": "participant_self_reported_stress",
                    "tag_mapping_source_required": "verified_protocol_notebook_or_equivalent_primary_source",
                    "start_tag_index": mapping.start_tag_index,
                    "end_tag_index": mapping.end_tag_index,
                    "window_start_utc": start.strftime("%Y-%m-%d %H:%M:%S"),
                    "window_end_utc": end.strftime("%Y-%m-%d %H:%M:%S"),
                    "eda": {
                        "stream_start_utc": eda.session_start_utc,
                        "expected_samples": eda_summary.expected_samples,
                        "observed_samples": eda_summary.observed_samples,
                        "usable_samples": eda_summary.usable_samples,
                        "coverage": round(eda_summary.coverage, 6),
                        "usable_fraction": round(eda_summary.usable_fraction, 6),
                    },
                    "hr": {
                        "stream_start_utc": hr.session_start_utc,
                        "expected_samples": hr_summary.expected_samples,
                        "observed_samples": hr_summary.observed_samples,
                        "usable_samples": hr_summary.usable_samples,
                        "coverage": round(hr_summary.coverage, 6),
                        "usable_fraction": round(hr_summary.usable_fraction, 6),
                    },
                    "model_input_coverage": round(observed_modalities / 2.0, 6),
                    "leakage_controls": [
                        "stage_mapping_not_inferred_from_self_report",
                        "stage_mapping_not_inferred_from_signal_shape",
                        "stage_mapping_not_inferred_from_elapsed_duration",
                        "participant_identity_preserved_for_grouped_validation",
                    ],
                },
            )
        )
    return examples
