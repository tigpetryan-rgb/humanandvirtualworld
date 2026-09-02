# Phase 3 Inference Target / Ground-Truth Contract

Status: ⚠️ implementation contract established and partially validated; Phase 3 DONE gate is not yet proven.

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

1. **Observed physiological features** — e.g. mean EDA and heart-rate summary; these are measurements/proxies.
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
- V1 and V2 protocol cohorts are handled explicitly rather than silently merged as identical protocols.

The stress-session self-report files are used as the target source. Exercise labels are out of scope for the first Phase 3 target.

The distributed stress-level CSVs contain observed values in the `0..10` range. Those file values are preserved exactly; they are not silently coerced to a prose-only `1..10` interpretation.

Known dataset caveats are explicit. Current validation policy excludes or specially handles at least:

- `S02` — duplicated data,
- `f07` — wristband protection cover not removed / signals not all valid,
- `f14` — recording split into two parts.

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
- mean imputation only for partial modality loss at inference time and always marked `uncertain`,
- full abstention when no model feature exists or quality is below the hard threshold,
- Phase 2/data-window provenance carried into every inference result.

## 7. Recorded-data alignment contract

Raw recorded data must reach the baseline through an explicit, leakage-safe stage-window layer.

Rules:

- V1 and V2 keep their exact, distinct protocol stage orders.
- Published EDA and HR streams keep their independent UTC start timestamps; equal starts are not assumed.
- Stream windows are aligned by absolute timestamps and each stream's own sample rate.
- Stage boundaries require an explicit verified `StageTagMapping`.
- No default mapping may be inferred from event duration, signal shape, self-report values, task difficulty or neighboring participants.
- Label joins use exact participant + protocol version + stage identity.
- Missing modalities remain explicit; stage extraction does not silently manufacture a value.
- Provenance records participant, protocol version, stage, tag indices, absolute window times, stream coverage and leakage controls.

Until the dataset-specific V1/V2 tag-index mapping is verified from the official protocol notebook or an equivalent primary source, full recorded-data inference is deliberately blocked rather than guessed.

## 8. Required metrics

The regression report must include at least:

- MAE,
- RMSE,
- R²,
- participant count / fold count,
- abstention count,
- `known / uncertain / unknown / no_signal` counts,
- nominal vs empirical prediction-interval coverage,
- V1/V2 cohort behavior where sample size permits,
- distribution-shift and failure-case analysis.

Accuracy alone is not a valid Phase 3 acceptance metric.

## 9. Current evidence

Implemented and CI-evidenced now:

- target/ground-truth semantic contract,
- deterministic interpretable ridge baseline,
- explicit abstention and uncertainty states,
- quality/provenance propagation,
- participant-independent evaluation function,
- regression/calibration metrics,
- deterministic synthetic tests for missing/low-quality inputs,
- PhysioNet v1.0.1 label parser preserving V1/V2 semantics,
- pinned public-file SHA-256 verification,
- actual deidentified `f10` EDA/HR/tags format probe,
- explicit dataset caveat/exclusion policy,
- preservation of independent stream start timestamps,
- explicit leakage-safe stage-window extraction contract and regression tests.

CI evidence:

- `Phase 3 Inference Baseline` run `33634956562` → success, SHA `04f98834ef5ef13f5ac8f1cfa0312d26fc1e1a0e`.
- `Phase 3 Public Recorded Dataset` run `33635986542` → success, evidence SHA `85a4775c294780158d9693fad1118e36c96e3002`.
- `Phase 3 Stage Window Contract` run `33636491215` → success, workflow SHA `8eba4ee9b7172b3cd3ccbf5a9a295ebe7938a8f9`.

## 10. Remaining gate before Phase 3 can become ✅

Still required:

1. Recover and verify the exact dataset-specific V1/V2 `tag index → stage boundary` mapping from the official PhysioNet protocol notebook or equivalent primary source.
2. Process the eligible full stress cohort with the explicit caveat/exclusion policy.
3. Join real physiological stage windows to the exact published self-report labels without leakage.
4. Run participant-independent / leave-one-participant-out validation on the actual deidentified recordings.
5. Record final MAE, RMSE, R², abstention/state counts, calibration coverage, V1/V2 behavior, distribution-shift/failure analysis, exact dataset subset/version, code SHA and CI run.
6. Keep Phase 4 closed until that recorded-data DONE gate is proven.
