import math

from positive_emotion_engine.state_inference import (
    TARGET_CONTRACT,
    TrainingExample,
    fit_interpretable_baseline,
    leave_one_participant_out,
    predict_stress,
)


def _examples():
    rows = []
    for p in range(6):
        pid = f"P{p+1:02d}"
        offset = (p - 2.5) * 0.08
        for level in (1.0, 2.5, 4.0, 5.5, 7.0):
            rows.append(
                TrainingExample(
                    participant_id=pid,
                    features={
                        "mean_eda_us": 0.5 + 0.32 * level + offset,
                        "heart_rate_bpm": 58.0 + 4.1 * level + offset * 4,
                    },
                    self_reported_stress=level,
                    quality_score=0.95,
                    provenance={"phase2_window": f"{pid}-{level}"},
                )
            )
    return rows


def test_contract_keeps_target_semantics_narrow():
    assert TARGET_CONTRACT["target_name"] == "self_reported_stress_0_10"
    assert TARGET_CONTRACT["semantic_type"] == "participant_self_report"
    assert "negative valence" in TARGET_CONTRACT["ground_truth_is_not"]
    assert TARGET_CONTRACT["physiology_is_observation_not_ground_truth"] is True


def test_model_is_deterministic_and_interpretable():
    examples = _examples()
    m1 = fit_interpretable_baseline(examples)
    m2 = fit_interpretable_baseline(examples)
    assert m1 == m2
    assert len(m1.coefficients) == 3
    assert m1.training_count == len(examples)


def test_no_signal_and_low_quality_abstain():
    model = fit_interpretable_baseline(_examples())
    no_signal = predict_stress(model, features={}, quality_score=1.0, provenance={"q": "none"})
    assert no_signal["status"] == "no_signal"
    assert no_signal["estimate"] is None

    low_quality = predict_stress(
        model,
        features={"mean_eda_us": 2.0, "heart_rate_bpm": 80.0},
        quality_score=0.2,
        provenance={"q": "bad"},
    )
    assert low_quality["status"] == "unknown"
    assert low_quality["estimate"] is None


def test_missing_modality_produces_uncertain_not_fake_certainty():
    model = fit_interpretable_baseline(_examples())
    result = predict_stress(
        model,
        features={"mean_eda_us": 2.0, "heart_rate_bpm": None},
        quality_score=0.95,
        provenance={"source": "phase2"},
    )
    assert result["status"] == "uncertain"
    assert result["estimate"] is not None
    assert "missing_modality_mean_imputed" in result["reason_codes"]
    assert result["quality_provenance"] == {"source": "phase2"}


def test_participant_independent_evaluation_reports_metrics_and_calibration():
    report = leave_one_participant_out(_examples())
    assert report["evaluation"] == "leave_one_participant_out"
    assert report["participants"] == 6
    assert report["metrics"]["mae"] < 0.5
    assert report["metrics"]["rmse"] < 0.75
    assert math.isfinite(report["metrics"]["r2"])
    assert report["calibration"]["interval_count"] > 0
    assert 0.0 <= report["calibration"]["empirical_interval_coverage"] <= 1.0
