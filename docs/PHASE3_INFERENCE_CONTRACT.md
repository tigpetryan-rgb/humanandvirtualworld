# Phase 3 Inference Target / Ground-Truth Contract

Status: ⚠️ implementation contract established; Phase 3 DONE gate is not yet proven.

## 1. Exact inference target

Canonical target for the first interpretable Phase 3 baseline:

`self_reported_stress_0_10`

This is a bounded regression target representing a participant's self-reported perceived stress level around a protocol stage.

It is **not**:

- direct measurement of emotion,
- negative valence,
- private thought content,
- a medical diagnosis,
- proof that one biosignal decodes a subjective state.

The first baseline is intentionally narrower than general affect recognition because the ground truth must match the dataset's actual labels.

## 2. Data-concept separation

Three concepts remain separate throughout Phase 3:

1. **Observed physiological features** — e.g. mean EDA, heart-rate estimate derived from IBI; these are measurements/proxies.
2. **Context / condition labels** — e.g. Baseline, Stroop, TMCT, Rest, Real Opinion, Opposite Opinion, Subtract; these describe protocol context and are not emotion labels.
3. **Ground truth** — participant self-reported stress score on the dataset scale.

No layer may rename a condition such as `TMCT` or `stress protocol` into `negative valence` or another psychological construct without separate evidence.

## 3. Selected public/deidentified validation dataset

Dataset: **Wearable Device Dataset from Induced Stress and Structured Exercise Sessions**, PhysioNet v1.0.1.

Reference: Hongn A, Bosch F, Prado L, Bonomini P. PhysioNet (2025), DOI `10.13026/he0v-tf17`.

Relevant properties for this phase:

- Empatica E4 physiological streams,
- 36 healthy volunteers in stress sessions,
- protocol stages interleaving baseline/rest and acute-stress tasks,
- participant self-reported stress levels recorded around stages,
- public PhysioNet distribution with deidentified subject identifiers,
- V1 and V2 protocol cohorts must be handled explicitly rather than silently merged as identical protocols.

The stress-session self-report files are used as the target source. Exercise labels are out of scope for the first Phase 3 target.

## 4. Inference states

Every result must be exactly one of:

- `known` — adequate model inputs, quality, calibration support and no strong distribution-shift flag.
- `uncertain` — a numeric estimate is allowed, but evidence is incomplete/degraded/partly out-of-distribution and uncertainty is explicitly widened.
- `unknown` — the system abstains because available signals are too low-quality for a responsible estimate.
- `no_signal` — the system abstains because none of the model features are available.

`unknown` and `no_signal` must never be converted to high-confidence numeric output by downstream policy.

## 5. Confidence, uncertainty and calibration

These terms are distinct:

- **Signal quality** comes from Phase 2 acquisition/quality logic.
- **Model confidence** is a bounded indicator of support for the specific estimate; it is not a probability that a private state is "true".
- **Uncertainty** is represented separately, initially as an approximate prediction interval widened by residual error, degraded quality, missing modalities and distribution shift.
- **Calibration** is evaluated by comparing nominal prediction-interval coverage with empirical held-out coverage.

A good Phase 2 quality score does not automatically imply high affect/state confidence.

## 6. First interpretable baseline

The initial model is standardized ridge linear regression using the Phase 2-compatible feature pair:

- `mean_eda_us`
- `heart_rate_bpm`

Design constraints:

- deterministic fit and prediction,
- explicit coefficients and feature scaling,
- no opaque deep model,
- participant-independent evaluation via leave-one-participant-out where data coverage permits,
- mean imputation only for partial modality loss and always marked `uncertain`,
- full abstention when no model feature exists or quality is below the hard threshold,
- Phase 2 provenance carried into every inference result.

## 7. Required metrics

The regression report must include at least:

- MAE,
- RMSE,
- R²,
- participant count / fold count,
- abstention count,
- `known / uncertain / unknown / no_signal` counts,
- nominal vs empirical prediction-interval coverage.

Accuracy alone is not a valid Phase 3 acceptance metric.

## 8. Current evidence and remaining gate

Implemented now:

- target/ground-truth semantic contract,
- deterministic interpretable ridge baseline,
- explicit abstention and uncertainty states,
- quality/provenance propagation,
- participant-independent evaluation function,
- regression/calibration metrics,
- deterministic synthetic tests for missing/low-quality inputs.

Still required before Phase 3 can become ✅:

- parse the selected PhysioNet stress-session files and stage boundaries,
- join physiological feature windows to the correct self-report/stage labels without leakage,
- run participant-independent validation on actual deidentified recordings,
- record exact dataset subset/version, code SHA and CI run,
- inspect calibration, distribution shift, cohort V1/V2 differences and failure cases,
- keep Phase 4 closed until the recorded-data DONE gate is proven.
