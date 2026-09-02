from datetime import datetime, timedelta

import pytest

from positive_emotion_engine.physionet_stress_dataset import (
    DatasetContractError,
    PROTOCOL_STAGES,
    RegularEmpaticaStream,
    StressLabel,
)
from positive_emotion_engine.recorded_stage_windows import (
    StageTagMapping,
    build_stage_training_examples,
    validate_stage_tag_mapping,
)


def _tags():
    start = datetime(2020, 1, 1, 0, 0, 1)
    return tuple(start + timedelta(seconds=i) for i in range(8))


def _mappings():
    return tuple(
        StageTagMapping(stage=stage, start_tag_index=i, end_tag_index=i + 1)
        for i, stage in enumerate(PROTOCOL_STAGES["v2"])
    )


def _labels():
    return tuple(
        StressLabel(
            participant_id="f10",
            protocol_version="v2",
            stage=stage,
            self_reported_stress=float(i),
        )
        for i, stage in enumerate(PROTOCOL_STAGES["v2"])
    )


def _eda():
    return RegularEmpaticaStream(
        session_start_utc="2020-01-01 00:00:00",
        sample_rate_hz=4.0,
        values=tuple(i / 4.0 for i in range(80)),
        unit="uS",
    )


def _hr(start="2020-01-01 00:00:01"):
    return RegularEmpaticaStream(
        session_start_utc=start,
        sample_rate_hz=1.0,
        values=tuple(60.0 + i for i in range(20)),
        unit="bpm",
    )


def test_mapping_must_preserve_exact_protocol_semantics():
    validate_stage_tag_mapping("v2", _mappings(), tag_count=8)
    with pytest.raises(DatasetContractError):
        validate_stage_tag_mapping("v2", _mappings()[:-1], tag_count=8)


def test_mapping_cannot_reorder_or_rename_stages():
    mappings = list(_mappings())
    mappings[0] = StageTagMapping("TMCT", 0, 1)
    with pytest.raises(DatasetContractError):
        validate_stage_tag_mapping("v2", mappings, tag_count=8)


def test_explicit_timestamp_windows_align_streams_with_independent_starts():
    examples = build_stage_training_examples(
        participant_id="f10",
        protocol_version="v2",
        labels=_labels(),
        tags=_tags(),
        eda=_eda(),
        hr=_hr(),
        mappings=_mappings(),
    )
    assert len(examples) == 7
    assert examples[0].features["mean_eda_us"] == pytest.approx(1.375)
    assert examples[0].features["heart_rate_bpm"] == pytest.approx(60.0)
    assert examples[-1].features["heart_rate_bpm"] == pytest.approx(66.0)
    assert examples[0].provenance["eda"]["stream_start_utc"] != examples[0].provenance["hr"]["stream_start_utc"]
    assert examples[0].provenance["model_input_coverage"] == 1.0
    assert examples[0].provenance["stage_semantics"] == "context_only_not_emotion_ground_truth"


def test_missing_modality_is_explicit_not_silently_filled_by_stage_extractor():
    examples = build_stage_training_examples(
        participant_id="f10",
        protocol_version="v2",
        labels=_labels(),
        tags=_tags(),
        eda=_eda(),
        hr=_hr(start="2020-01-01 00:00:20"),
        mappings=_mappings(),
    )
    first = examples[0]
    assert first.features["mean_eda_us"] is not None
    assert first.features["heart_rate_bpm"] is None
    assert first.provenance["model_input_coverage"] == 0.5
    assert first.quality_score == 1.0


def test_label_join_is_exact_participant_stage_identity_not_signal_inference():
    examples = build_stage_training_examples(
        participant_id="f10",
        protocol_version="v2",
        labels=_labels(),
        tags=_tags(),
        eda=_eda(),
        hr=_hr(),
        mappings=_mappings(),
    )
    assert [e.self_reported_stress for e in examples] == [float(i) for i in range(7)]
    assert all(
        "stage_mapping_not_inferred_from_self_report" in e.provenance["leakage_controls"]
        for e in examples
    )
