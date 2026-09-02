from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Sequence

TARGET_NAME = "self_reported_stress_0_10"
TARGET_MIN = 0.0
TARGET_MAX = 10.0
FEATURE_NAMES = ("mean_eda_us", "heart_rate_bpm")

TARGET_CONTRACT: dict[str, Any] = {
    "target_name": TARGET_NAME,
    "semantic_type": "participant_self_report",
    "range": [TARGET_MIN, TARGET_MAX],
    "dataset_reference": {
        "name": "Wearable Device Dataset from Induced Stress and Structured Exercise Sessions",
        "version": "1.0.1",
        "publisher": "PhysioNet",
        "doi": "10.13026/he0v-tf17",
        "stress_participants": 36,
    },
    "ground_truth_is": "self-reported perceived stress level recorded around protocol stages",
    "ground_truth_is_not": [
        "direct measurement of emotion",
        "negative valence",
        "private thought content",
        "medical diagnosis",
    ],
    "context_labels_are_separate": True,
    "physiology_is_observation_not_ground_truth": True,
    "allowed_inference_status": ["known", "uncertain", "unknown", "no_signal"],
}


class InferenceContractError(ValueError):
    pass


@dataclass(frozen=True)
class TrainingExample:
    participant_id: str
    features: dict[str, float | None]
    self_reported_stress: float
    quality_score: float
    provenance: dict[str, Any]


@dataclass(frozen=True)
class RidgeStressModel:
    feature_names: tuple[str, ...]
    means: tuple[float, ...]
    scales: tuple[float, ...]
    coefficients: tuple[float, ...]
    residual_sigma: float
    training_count: int
    ridge_alpha: float


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def validate_example(example: TrainingExample) -> None:
    if not example.participant_id:
        raise InferenceContractError("participant_id is required")
    if not (TARGET_MIN <= float(example.self_reported_stress) <= TARGET_MAX):
        raise InferenceContractError("self_reported_stress must be within 0..10")
    if not (0.0 <= float(example.quality_score) <= 1.0):
        raise InferenceContractError("quality_score must be within 0..1")
    for name in FEATURE_NAMES:
        value = example.features.get(name)
        if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(float(value))):
            raise InferenceContractError(f"invalid feature: {name}")


def _solve_linear_system(a: list[list[float]], b: list[float]) -> list[float]:
    n = len(b)
    aug = [list(map(float, row)) + [float(rhs)] for row, rhs in zip(a, b)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < 1e-12:
            raise InferenceContractError("singular normal equation")
        aug[col], aug[pivot] = aug[pivot], aug[col]
        scale = aug[col][col]
        aug[col] = [v / scale for v in aug[col]]
        for row in range(n):
            if row == col:
                continue
            factor = aug[row][col]
            if factor == 0:
                continue
            aug[row] = [rv - factor * cv for rv, cv in zip(aug[row], aug[col])]
    return [aug[i][-1] for i in range(n)]


def fit_interpretable_baseline(
    examples: Sequence[TrainingExample],
    *,
    ridge_alpha: float = 1.0,
    min_quality: float = 0.75,
) -> RidgeStressModel:
    if ridge_alpha < 0:
        raise InferenceContractError("ridge_alpha must be non-negative")
    clean: list[TrainingExample] = []
    for example in examples:
        validate_example(example)
        if example.quality_score < min_quality:
            continue
        if all(example.features.get(name) is not None for name in FEATURE_NAMES):
            clean.append(example)
    if len(clean) < len(FEATURE_NAMES) + 2:
        raise InferenceContractError("insufficient high-quality complete training examples")

    columns = [[float(e.features[name]) for e in clean] for name in FEATURE_NAMES]
    means = [sum(col) / len(col) for col in columns]
    scales: list[float] = []
    for col, mean in zip(columns, means):
        variance = sum((v - mean) ** 2 for v in col) / max(1, len(col) - 1)
        scales.append(math.sqrt(variance) if variance > 1e-12 else 1.0)

    x: list[list[float]] = []
    y = [float(e.self_reported_stress) for e in clean]
    for e in clean:
        row = [1.0]
        for name, mean, scale in zip(FEATURE_NAMES, means, scales):
            row.append((float(e.features[name]) - mean) / scale)
        x.append(row)

    p = len(FEATURE_NAMES) + 1
    xtx = [[0.0 for _ in range(p)] for _ in range(p)]
    xty = [0.0 for _ in range(p)]
    for row, target in zip(x, y):
        for i in range(p):
            xty[i] += row[i] * target
            for j in range(p):
                xtx[i][j] += row[i] * row[j]
    for i in range(1, p):
        xtx[i][i] += ridge_alpha

    coefficients = _solve_linear_system(xtx, xty)
    residuals = []
    for row, target in zip(x, y):
        pred = sum(c * v for c, v in zip(coefficients, row))
        residuals.append(target - pred)
    dof = max(1, len(residuals) - p)
    sigma = math.sqrt(sum(r * r for r in residuals) / dof)
    sigma = max(sigma, 0.25)

    return RidgeStressModel(
        feature_names=FEATURE_NAMES,
        means=tuple(means),
        scales=tuple(scales),
        coefficients=tuple(coefficients),
        residual_sigma=sigma,
        training_count=len(clean),
        ridge_alpha=float(ridge_alpha),
    )


def predict_stress(
    model: RidgeStressModel,
    *,
    features: dict[str, float | None],
    quality_score: float,
    provenance: dict[str, Any],
) -> dict[str, Any]:
    if not 0.0 <= float(quality_score) <= 1.0:
        raise InferenceContractError("quality_score must be within 0..1")

    observed = [name for name in model.feature_names if features.get(name) is not None]
    if not observed:
        return {
            "target_name": TARGET_NAME,
            "status": "no_signal",
            "estimate": None,
            "confidence": 0.0,
            "uncertainty": {"kind": "abstained", "reason": "no_model_features"},
            "reason_codes": ["no_model_features"],
            "quality_provenance": provenance,
            "scientific_boundary": "estimate_of_self_reported_stress_not_direct_emotion_or_thought_readout",
        }
    if quality_score < 0.4:
        return {
            "target_name": TARGET_NAME,
            "status": "unknown",
            "estimate": None,
            "confidence": 0.0,
            "uncertainty": {"kind": "abstained", "reason": "insufficient_signal_quality"},
            "reason_codes": ["insufficient_signal_quality"],
            "quality_provenance": provenance,
            "scientific_boundary": "estimate_of_self_reported_stress_not_direct_emotion_or_thought_readout",
        }

    standardized: list[float] = []
    z_distances: list[float] = []
    missing: list[str] = []
    for name, mean, scale in zip(model.feature_names, model.means, model.scales):
        value = features.get(name)
        if value is None:
            standardized.append(0.0)
            missing.append(name)
        else:
            z = (float(value) - mean) / scale
            standardized.append(z)
            z_distances.append(abs(z))

    row = [1.0, *standardized]
    raw = sum(c * v for c, v in zip(model.coefficients, row))
    estimate = _clip(raw, TARGET_MIN, TARGET_MAX)
    coverage = len(observed) / len(model.feature_names)
    max_z = max(z_distances) if z_distances else math.inf
    ood_factor = 1.0 if max_z <= 2.5 else max(0.1, 2.5 / max_z)
    calibration_factor = 1.0 / (1.0 + model.residual_sigma)
    confidence = _clip(float(quality_score) * coverage * ood_factor * calibration_factor, 0.0, 1.0)

    reasons: list[str] = []
    if missing:
        reasons.append("missing_modality_mean_imputed")
    if quality_score < 0.75:
        reasons.append("degraded_signal_quality")
    if max_z > 2.5:
        reasons.append("feature_distribution_shift")
    status = "known"
    if missing or quality_score < 0.75 or max_z > 2.5 or confidence < 0.35:
        status = "uncertain"

    half_width = 1.645 * model.residual_sigma / max(confidence, 0.15)
    interval = [
        _clip(estimate - half_width, TARGET_MIN, TARGET_MAX),
        _clip(estimate + half_width, TARGET_MIN, TARGET_MAX),
    ]
    return {
        "target_name": TARGET_NAME,
        "status": status,
        "estimate": round(estimate, 6),
        "confidence": round(confidence, 6),
        "uncertainty": {
            "kind": "approximate_90_percent_prediction_interval",
            "lower": round(interval[0], 6),
            "upper": round(interval[1], 6),
            "residual_sigma": round(model.residual_sigma, 6),
        },
        "reason_codes": reasons,
        "quality_provenance": provenance,
        "scientific_boundary": "estimate_of_self_reported_stress_not_direct_emotion_or_thought_readout",
    }


def regression_metrics(y_true: Sequence[float], y_pred: Sequence[float]) -> dict[str, float]:
    if len(y_true) != len(y_pred) or not y_true:
        raise InferenceContractError("metric inputs must be non-empty and equal length")
    errors = [float(p) - float(t) for t, p in zip(y_true, y_pred)]
    mae = sum(abs(e) for e in errors) / len(errors)
    rmse = math.sqrt(sum(e * e for e in errors) / len(errors))
    mean_y = sum(float(v) for v in y_true) / len(y_true)
    ss_tot = sum((float(v) - mean_y) ** 2 for v in y_true)
    ss_res = sum(e * e for e in errors)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else 0.0
    return {"mae": round(mae, 6), "rmse": round(rmse, 6), "r2": round(r2, 6)}


def leave_one_participant_out(
    examples: Sequence[TrainingExample],
    *,
    ridge_alpha: float = 1.0,
) -> dict[str, Any]:
    participants = sorted({e.participant_id for e in examples})
    if len(participants) < 3:
        raise InferenceContractError("participant-independent evaluation needs at least 3 participants")

    predictions: list[dict[str, Any]] = []
    for held_out in participants:
        train = [e for e in examples if e.participant_id != held_out]
        test = [e for e in examples if e.participant_id == held_out]
        model = fit_interpretable_baseline(train, ridge_alpha=ridge_alpha)
        for e in test:
            result = predict_stress(
                model,
                features=e.features,
                quality_score=e.quality_score,
                provenance=e.provenance,
            )
            predictions.append({
                "participant_id": held_out,
                "ground_truth": e.self_reported_stress,
                "prediction": result,
            })

    scored = [p for p in predictions if p["prediction"]["estimate"] is not None]
    metrics = regression_metrics(
        [float(p["ground_truth"]) for p in scored],
        [float(p["prediction"]["estimate"]) for p in scored],
    )
    intervals = [
        p for p in scored
        if p["prediction"]["uncertainty"]["kind"].startswith("approximate_90")
    ]
    coverage = 0.0
    if intervals:
        hits = 0
        for p in intervals:
            lo = float(p["prediction"]["uncertainty"]["lower"])
            hi = float(p["prediction"]["uncertainty"]["upper"])
            y = float(p["ground_truth"])
            hits += int(lo <= y <= hi)
        coverage = hits / len(intervals)

    abstained = [p for p in predictions if p["prediction"]["estimate"] is None]
    status_counts = {status: 0 for status in ("known", "uncertain", "unknown", "no_signal")}
    for p in predictions:
        status_counts[p["prediction"]["status"]] += 1

    return {
        "evaluation": "leave_one_participant_out",
        "participants": len(participants),
        "examples": len(examples),
        "scored_examples": len(scored),
        "abstained_examples": len(abstained),
        "metrics": metrics,
        "calibration": {
            "interval_nominal_coverage": 0.90,
            "empirical_interval_coverage": round(coverage, 6),
            "interval_count": len(intervals),
        },
        "status_counts": status_counts,
        "predictions": predictions,
        "scientific_boundary": TARGET_CONTRACT["ground_truth_is_not"],
    }
