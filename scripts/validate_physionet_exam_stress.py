from __future__ import annotations

import argparse
import json
from pathlib import Path

import jsonschema

from positive_emotion_engine.acquisition_quality import run_phase2_recording, validate_recording
from positive_emotion_engine.empatica_e4_adapter import build_recording_from_empatica


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eda", type=Path, required=True)
    parser.add_argument("--ibi", type=Path, required=True)
    parser.add_argument("--schema", type=Path, default=Path("schemas/phase2_recording.v1.schema.json"))
    parser.add_argument("--duration-s", type=float, default=300.0)
    args = parser.parse_args()

    recording = build_recording_from_empatica(
        args.eda.read_text(),
        args.ibi.read_text(),
        session_id="physionet-wearable-exam-stress-S8-final",
        data_class="deidentified_recorded",
        max_duration_s=args.duration_s,
    )
    schema = json.loads(args.schema.read_text())
    jsonschema.validate(recording, schema)
    validate_recording(recording)

    first = run_phase2_recording(recording)
    second = run_phase2_recording(recording)
    if first != second or first["replay_digest"] != second["replay_digest"]:
        raise SystemExit("deterministic replay failure")

    summaries = first["channel_summaries"]
    if set(summaries) != {"eda_us", "heart_ibi_ms"}:
        raise SystemExit(f"unexpected channels: {sorted(summaries)}")
    if summaries["eda_us"]["observed_samples"] < 100:
        raise SystemExit("insufficient recorded EDA samples")
    if summaries["heart_ibi_ms"]["observed_samples"] < 10:
        raise SystemExit("insufficient recorded IBI samples")
    if summaries["heart_ibi_ms"]["sampling_mode"] != "event":
        raise SystemExit("IBI must remain an event stream")
    if len(first["windows"]) < 30:
        raise SystemExit("insufficient synchronized windows")

    serialized = json.dumps(first).lower()
    for prohibited in ('"valence"', '"arousal"', '"emotion"'):
        if prohibited in serialized:
            raise SystemExit(f"Phase 2 leaked affect label: {prohibited}")

    print(json.dumps({
        "dataset": "PhysioNet wearable-exam-stress v1.0.0 / S8 / Final",
        "data_class": recording["data_class"],
        "duration_s": args.duration_s,
        "recording_digest": first["recording_digest"],
        "replay_digest": first["replay_digest"],
        "eda_observed": summaries["eda_us"]["observed_samples"],
        "eda_usable_fraction": summaries["eda_us"]["usable_fraction"],
        "ibi_observed": summaries["heart_ibi_ms"]["observed_samples"],
        "ibi_usable_fraction": summaries["heart_ibi_ms"]["usable_fraction"],
        "windows": len(first["windows"]),
        "dropout_intervals": len(first["dropout_intervals"]),
        "status": "PASS"
    }, sort_keys=True))


if __name__ == "__main__":
    main()
