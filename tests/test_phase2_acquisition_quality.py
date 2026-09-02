import copy
import json
from pathlib import Path

import jsonschema
import pytest

from positive_emotion_engine.acquisition_quality import AcquisitionContractError, run_phase2_recording, validate_recording

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = json.loads((ROOT / "fixtures/phase2_scenarios.v1.json").read_text())["scenarios"]
SCHEMA = json.loads((ROOT / "schemas/phase2_recording.v1.schema.json").read_text())


def source_time(session_ms, offset=0.0, drift_ppm=0.0):
    return round(session_ms * (1.0 + drift_ppm / 1_000_000.0) + offset, 6)


def make_recording(name):
    scenario = SCENARIOS[name]
    eda_offset = scenario.get("eda_offset_ms", 20.0)
    eda_drift = scenario.get("eda_drift_ppm", 20.0)
    recording = {
        "schema_version": "2.0.0",
        "session_id": f"synthetic-{name}",
        "data_class": "synthetic_recorded",
        "channels": [
            {"name": "heart_ibi_ms", "unit": "ms", "nominal_hz": 1.0, "clock": {"offset_ms": 0.0, "drift_ppm": 0.0}, "samples": []},
            {"name": "eda_us", "unit": "uS", "nominal_hz": 4.0, "clock": {"offset_ms": eda_offset, "drift_ppm": eda_drift}, "samples": []},
            {"name": "respiration_norm", "unit": "normalized", "nominal_hz": 4.0, "clock": {"offset_ms": -10.0, "drift_ppm": -15.0}, "samples": []},
        ],
    }
    for seq, (t, value) in enumerate(zip([0, 1000, 2000, 3000], [800, 790, 810, 805])):
        recording["channels"][0]["samples"].append({"seq": seq, "source_time_ms": source_time(t), "value": value})

    times = [i * 250 for i in range(13)]
    eda_values = [2.0 + 0.1 * i for i in range(13)]
    drop = set(scenario.get("eda_drop_seqs", []))
    for seq, (t, value) in enumerate(zip(times, eda_values)):
        if seq in drop:
            continue
        if seq == scenario.get("eda_artifact_seq"):
            value = 150.0
        recording["channels"][1]["samples"].append({"seq": seq, "source_time_ms": source_time(t, eda_offset, eda_drift), "value": value})

    resp_values = [0.0, 0.4, 0.8, 0.4, 0.0, -0.4, -0.8, -0.4, 0.0, 0.4, 0.8, 0.4, 0.0]
    for seq, (t, value) in enumerate(zip(times, resp_values)):
        if seq == scenario.get("resp_missing_seq"):
            value = None
        recording["channels"][2]["samples"].append({"seq": seq, "source_time_ms": source_time(t, -10.0, -15.0), "value": value})
    return recording


@pytest.mark.parametrize("name", ["clean", "noisy", "missing", "misaligned", "drifted"])
def test_recording_fixtures_validate(name):
    recording = make_recording(name)
    jsonschema.validate(recording, SCHEMA)
    validate_recording(recording)


def test_clean_replay_is_deterministic_and_multimodal():
    recording = make_recording("clean")
    a = run_phase2_recording(recording)
    b = run_phase2_recording(copy.deepcopy(recording))
    assert a == b
    assert a["replay_digest"] == b["replay_digest"]
    assert len(a["channel_summaries"]) == 3
    assert a["scientific_boundary"]["signal_quality_is_not_affect_confidence"] is True
    assert all("heart_rate_bpm" in w["features"] for w in a["windows"])


def test_noisy_artifact_is_explicit_and_not_used_as_clean():
    result = run_phase2_recording(make_recording("noisy"))
    summary = result["channel_summaries"]["eda_us"]
    assert summary["quality_counts"]["artifact"] >= 1
    flagged = [s for s in result["normalized_samples"] if s["channel"] == "eda_us" and s["quality"] == "artifact"]
    assert flagged
    assert "outside_channel_range" in flagged[0]["reason_codes"]


def test_missing_fixture_preserves_dropouts_and_explicit_missing_values():
    result = run_phase2_recording(make_recording("missing"))
    assert result["dropout_intervals"]
    resp_missing = [s for s in result["normalized_samples"] if s["channel"] == "respiration_norm" and s["quality"] == "missing"]
    assert resp_missing
    assert result["channel_summaries"]["eda_us"]["estimated_missing_samples"] >= 1


def test_large_clock_offset_is_quality_degradation_not_silent_alignment():
    result = run_phase2_recording(make_recording("misaligned"))
    diag = result["channel_summaries"]["eda_us"]["clock"]
    assert diag["quality"] == "degraded"
    assert "clock_offset_large" in diag["reason_codes"]
    assert any(s["channel"] == "eda_us" and s["quality"] == "degraded" for s in result["normalized_samples"])


def test_large_clock_drift_is_quality_degradation():
    result = run_phase2_recording(make_recording("drifted"))
    diag = result["channel_summaries"]["eda_us"]["clock"]
    assert diag["quality"] == "degraded"
    assert "clock_drift_large" in diag["reason_codes"]


def test_nonmonotonic_source_time_is_rejected():
    recording = make_recording("clean")
    recording["channels"][1]["samples"][2]["source_time_ms"] = recording["channels"][1]["samples"][1]["source_time_ms"]
    with pytest.raises(AcquisitionContractError):
        validate_recording(recording)


def test_unit_mismatch_is_rejected():
    recording = make_recording("clean")
    recording["channels"][0]["unit"] = "bpm"
    with pytest.raises(AcquisitionContractError):
        validate_recording(recording)


def test_no_emotion_labels_are_created_by_phase2():
    result = run_phase2_recording(make_recording("clean"))
    serialized = json.dumps(result).lower()
    assert '"valence"' not in serialized
    assert '"arousal"' not in serialized
    assert '"emotion"' not in serialized
