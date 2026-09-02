import json
from pathlib import Path

import jsonschema

from positive_emotion_engine.acquisition_quality import run_phase2_recording, validate_recording
from positive_emotion_engine.empatica_e4_adapter import build_recording_from_empatica

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas/phase2_recording.v1.schema.json").read_text())

EDA = """1700000000\n4\n1.0\n1.1\n1.2\n1.3\n1.4\n1.5\n1.6\n1.7\n1.8\n1.9\n2.0\n2.1\n"""
IBI = """1700000000,\n0.80,0.80\n1.62,0.82\n2.41,0.79\n"""


def test_empatica_adapter_preserves_regular_eda_and_event_ibi():
    recording = build_recording_from_empatica(EDA, IBI, session_id="deidentified-e4-test")
    jsonschema.validate(recording, SCHEMA)
    validate_recording(recording)
    channels = {c["name"]: c for c in recording["channels"]}
    assert channels["eda_us"]["sampling_mode"] == "regular"
    assert channels["eda_us"]["nominal_hz"] == 4.0
    assert channels["heart_ibi_ms"]["sampling_mode"] == "event"
    assert channels["heart_ibi_ms"]["nominal_hz"] is None


def test_event_ibi_does_not_create_regular_sampling_gap_dropouts():
    recording = build_recording_from_empatica(EDA, IBI, session_id="deidentified-e4-test")
    result = run_phase2_recording(recording)
    assert not [x for x in result["dropout_intervals"] if x["channel"] == "heart_ibi_ms"]
    assert result["channel_summaries"]["heart_ibi_ms"]["sampling_mode"] == "event"


def test_adapter_result_remains_measurement_only():
    result = run_phase2_recording(build_recording_from_empatica(EDA, IBI, session_id="deidentified-e4-test"))
    text = json.dumps(result).lower()
    assert '"valence"' not in text
    assert '"arousal"' not in text
    assert '"emotion"' not in text
