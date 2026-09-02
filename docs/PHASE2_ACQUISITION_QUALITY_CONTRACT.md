# Phase 2 — Biosignal Acquisition + Quality Contract

**Canonical scope:** Tasks 61–80 only. This document does not authorize Phase 3 affect inference.

## 1. Purpose

Phase 2 converts recorded or live physiological/behavioral channels into synchronized, quality-annotated measurement windows. It does **not** infer private thoughts or emotion labels.

Canonical flow:

**device/file adapter → channel/unit validation → source timestamps → clock normalization/diagnostics → dropout/artifact flags → per-channel quality → synchronized measurement windows → deterministic replay**

## 2. Evidence classification

- **A / Established engineering:** monotonic ordering checks, explicit units, sampling-gap detection, reproducible timestamp transforms, schema validation and deterministic replay.
- **A/B / Established-to-plausible measurement practice:** broad range checks, artifact flags, sampling completeness and clock-quality diagnostics. Exact thresholds are device/channel dependent and therefore must remain configurable in later hardware adapters.
- **C / Experimental prototype choices:** the current broad `CHANNEL_SPECS`, quality weights, 100 ms offset warning, 200 ppm drift warning and 1.75× gap factor. These are safe engineering diagnostics for the prototype, not universal physiological truth.

## 3. Supported reference channels

Current reference contracts:

- `heart_ibi_ms` — inter-beat intervals in milliseconds; derived heart-rate value is only a measurement transform.
- `eda_us` — electrodermal conductance in microsiemens.
- `respiration_norm` — normalized respiratory waveform reference channel.

Future eye/gaze/pupil or motion adapters must use the same explicit channel/clock/quality interface. EEG is not a default Phase 2 requirement.

## 4. Clock model

Reference model:

`source_clock = session_clock × (1 + drift_ppm/1e6) + offset_ms`

The normalized session timestamp reverses that declared mapping. Large declared offsets or drift do not disappear silently: they lower channel quality and add reason codes.

This is a deterministic reference contract. Real devices may require sync anchors, host timestamps, hardware timestamps, resampling or more sophisticated clock estimation, but those adapters must expose diagnostics rather than hide uncertainty.

## 5. Missing data and dropouts

Two distinct cases are preserved:

- explicit missing sample: a sample exists with `value = null`;
- sampling dropout: the gap between source timestamps exceeds the configured expected-period tolerance.

Neither is silently interpolated into a clean measurement. Later interpolation, if ever used for a specific feature, must preserve provenance and cannot increase confidence beyond source evidence.

## 6. Artifact flags

The reference layer applies intentionally broad channel range and step checks. A flagged value receives `artifact` quality and zero quality weight in synchronized means.

These checks are **not medical validators** and must not be interpreted as diagnostic thresholds.

## 7. Quality is not affect confidence

Non-negotiable invariant:

**signal quality/confidence ≠ emotional-state confidence**

Phase 2 output contains physiological/behavioral measurements and their provenance only. It must not create `valence`, `arousal`, `emotion`, diagnosis, persuasion target or treatment label.

## 8. Deterministic fixtures

Reference scenarios:

- `clean`
- `noisy`
- `missing`
- `misaligned`
- `drifted`

The scenario file defines perturbations; tests construct deterministic multimodal recordings and prove that quality failures remain visible.

## 9. Current acceptance status

Synthetic/recorded-reference implementation exists and is locally testable. Phase 2 remains **⚠️ / not final** until GitHub CI is green and the same adapter/quality path is demonstrated against at least one actual recorded, deidentified dataset or real device recording with documented units/timestamps.

## 10. DONE gate

Phase 2 becomes ✅ only when:

1. schema-valid multimodal recorded data is ingested through the device-agnostic layer;
2. timestamp/clock diagnostics are explicit;
3. dropouts/artifacts/missing values remain visible;
4. synchronized measurement windows are deterministic;
5. clean/noisy/missing/drift/misalignment tests pass in CI;
6. an actual recorded/deidentified dataset or device capture passes the same contract without special hidden bypasses.
