from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest

from positive_emotion_engine.reference_pipeline import (
    AffectState,
    ContractError,
    run_session,
    safety_decision,
    validate_bundle,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas/session_bundle.v1.schema.json").read_text())
FIXTURE = json.loads((ROOT / "fixtures/synthetic_session.v1.json").read_text())


def test_fixture_is_valid_json_schema_and_contract():
    jsonschema.validate(FIXTURE, SCHEMA)
    validate_bundle(FIXTURE)


def test_deterministic_replay_is_identical():
    first = run_session(FIXTURE)
    second = run_session(copy.deepcopy(FIXTURE))
    assert first == second
    assert first["replay_digest"] == second["replay_digest"]
    assert first["safety"]["approved"] is True


def test_policy_seed_change_is_detectable():
    changed = copy.deepcopy(FIXTURE)
    changed["policy"]["seed"] += 1
    first = run_session(FIXTURE)
    second = run_session(changed)
    assert first["policy_seed"] != second["policy_seed"]
    assert first["replay_digest"] != second["replay_digest"]


def test_bad_quality_forces_unknown_and_noop():
    degraded = copy.deepcopy(FIXTURE)
    for sample in degraded["samples"]:
        sample["quality"] = "artifact"
        sample["confidence"] = 0.1
    result = run_session(degraded)
    assert result["state"]["state"] == "unknown"
    assert result["state"]["valence"] is None
    assert result["safety"]["approved"] is False
    assert "low_confidence_or_unknown_state" in result["safety"]["decision_codes"]
    assert result["final_scene"] == degraded["initial_scene"]


def test_human_stop_overrides_known_state():
    stopped = copy.deepcopy(FIXTURE)
    stopped["session"]["stop_requested"] = True
    result = run_session(stopped)
    assert result["safety"]["approved"] is False
    assert "human_stop" in result["safety"]["decision_codes"]


def test_safety_clamps_large_step_and_range():
    state = AffectState(
        "known", 0.5, 0.5, 0.9, 0.1,
        "synthetic_usable", "synthetic-estimator-v1", ("test",)
    )
    decision = safety_decision(
        {"parameter": "motion_intensity", "previous_value": 0.15, "requested_value": 9.0},
        state,
    )
    assert decision["approved"] is True
    assert decision["clamped"] is True
    assert decision["applied_value"] == pytest.approx(0.25)


def test_unregistered_parameter_is_rejected():
    state = AffectState(
        "known", 0.5, 0.5, 0.9, 0.1,
        "synthetic_usable", "synthetic-estimator-v1", ("test",)
    )
    decision = safety_decision(
        {"parameter": "secret_intensity", "previous_value": 0.1, "requested_value": 0.2},
        state,
    )
    assert decision["approved"] is False
    assert decision["decision_codes"] == ["unregistered_parameter"]


def test_nonmonotonic_sequence_fails_contract():
    invalid = copy.deepcopy(FIXTURE)
    invalid["samples"][2]["seq"] = 1
    with pytest.raises(ContractError):
        validate_bundle(invalid)


def test_nonmonotonic_time_fails_contract():
    invalid = copy.deepcopy(FIXTURE)
    invalid["samples"][2]["monotonic_ns"] = 1
    with pytest.raises(ContractError):
        validate_bundle(invalid)


def test_phase1_rejects_non_synthetic_participant():
    invalid = copy.deepcopy(FIXTURE)
    invalid["session"]["participant_id"] = "real-person-001"
    invalid["session"]["synthetic"] = False
    with pytest.raises(ContractError):
        validate_bundle(invalid)
