# Phase 1 System Contract — Tasks 41–60

Status: ⚠️ implementation/reference contract in progress. This document does not authorize Tasks 61+.

## 1. Closed-loop boundary

Canonical event flow:

`SensorSample -> QualityGate -> FeatureVector -> AffectStateEstimate -> CandidateEnvironmentCommand -> SafetyDecision -> SceneAppliedEvent -> TelemetryLog -> Replay`

Phase 1 uses synthetic data only. Real sensor acquisition, learned affect models and human-subject inference are intentionally absent.

## 2. Time model

Every event carries:

- `session_id`: stable opaque identifier.
- `seq`: strictly increasing integer within a session.
- `monotonic_ns`: canonical ordering time from a monotonic clock domain.
- `source_time_ns`: optional device/source clock timestamp.
- `source_clock_id`: source clock identity.
- `sync_uncertainty_ms`: estimated alignment uncertainty to canonical session time.

Rules:

1. Ordering uses `seq` first and `monotonic_ns` second.
2. Wall-clock time is metadata only and never used for deterministic replay ordering.
3. Clock alignment uncertainty is explicit; no silent timestamp correction.
4. Events with excessive synchronization uncertainty may be retained for audit but cannot silently drive high-confidence adaptation.

## 3. Sensor abstraction

A sensor sample exposes:

- sensor identity/type,
- numeric or structured synthetic value,
- sampling metadata,
- quality status,
- confidence in `[0,1]`,
- missing/dropout/artifact flags,
- timestamps defined above.

Initial sensor type registry is interface-only: `heart`, `eda`, `respiration`, `gaze`, `pupil`, `face_motion`, `head_motion`, `body_motion`, `eeg_optional`.

No type implies clinical validity.

## 4. Signal quality contract

Canonical quality states:

- `good`
- `degraded`
- `artifact`
- `dropout`
- `missing`
- `unknown`

Quality policy:

- `good`: may contribute normally.
- `degraded`: contribution must be confidence-reduced.
- `artifact/dropout/missing/unknown`: cannot be treated as reliable evidence.
- Aggregate state confidence cannot exceed the confidence permitted by contributing evidence.
- If usable evidence is insufficient, output state is `unknown` and adaptation falls back to safe baseline/no-op.

## 5. Participant/session/privacy contract

Phase 1 fixture uses only synthetic participant IDs.

Persistent identity rules for later phases:

- no names/emails required by core runtime,
- participant IDs are pseudonymous opaque IDs,
- raw biosignals and derived features are logically separable,
- purpose and retention class are recorded in session metadata,
- data collection must be minimal for the active hypothesis,
- deletion/export boundaries must be implementable before human-study work.

Retention classes:

- `ephemeral_raw`
- `research_raw_restricted`
- `derived_features`
- `telemetry_nonbiometric`

Phase 1 uses `synthetic_only` and stores no real participant data.

## 6. Feature contract

A `FeatureVector` contains:

- feature names and finite numeric values,
- source sensor references,
- window start/end in canonical monotonic time,
- aggregate quality/confidence,
- explicit missing features.

Phase 1 synthetic features are deterministic transformations used only to prove plumbing.

## 7. Affect/state estimate contract

Required fields:

- `state`: `known` or `unknown`,
- `valence`: optional normalized `[-1,1]`,
- `arousal`: optional normalized `[0,1]`,
- `confidence`: `[0,1]`,
- `uncertainty`: `[0,1]`,
- `evidence_quality`,
- `model_id`,
- `reason_codes`.

Invariant: `confidence + uncertainty` is not required to equal 1, but both must be bounded and semantically documented.

`unknown` state must have no asserted valence/arousal and cannot be converted into a strong environment command.

## 8. Environment parameter registry

Phase 1 allows a deliberately small synthetic registry:

| Parameter | Range | Safe baseline | Max step/event |
|---|---:|---:|---:|
| `light_intensity` | 0.20–1.00 | 0.60 | 0.10 |
| `motion_intensity` | 0.00–0.60 | 0.15 | 0.10 |
| `audio_intensity` | 0.00–0.70 | 0.25 | 0.10 |
| `scene_density` | 0.10–0.80 | 0.40 | 0.10 |

These are engineering-safe prototype bounds, not physiological medical thresholds.

Any parameter outside the registry is rejected by the safety interface.

## 9. Candidate command contract

Policy output is only a candidate. It contains:

- target parameter,
- requested value,
- previous value,
- reason,
- source state estimate ID,
- deterministic policy seed/version.

The scene executor never consumes a candidate directly.

## 10. Safety supervisor interface

Input: candidate command + current scene state + state confidence/quality.

Output:

- `approved` boolean,
- `applied_value` or safe baseline/no-op,
- `decision_codes`,
- `clamped` boolean.

Mandatory behavior:

1. Unknown/unregistered parameters -> reject.
2. Non-finite values -> reject.
3. Low-confidence/unknown state -> no-op or safe baseline.
4. Out-of-range values -> clamp only when the request is otherwise valid and auditable; critical invalidity -> reject.
5. Per-event step limit -> clamp.
6. Human stop flag -> reject all adaptation and return baseline/no-op.

## 11. Telemetry/replay contract

Every pipeline transition is append-only telemetry with:

- schema version,
- session/seq/time,
- event type,
- deterministic payload,
- parent event IDs where applicable,
- component/version identifier.

Replay rules:

- replay never reads live time,
- replay never uses unseeded randomness,
- identical ordered input + component versions + seed must produce byte-equivalent normalized output,
- safety decisions are recomputed and compared, not blindly trusted from the prior log.

## 12. Latency budget

Phase 1 budget is an engineering contract, not a claim about final optimal human-perception timing.

Target steady-state budget per synthetic update:

- input normalization: <= 5 ms
- quality gate: <= 5 ms
- feature stage: <= 15 ms
- state estimate: <= 20 ms
- candidate policy: <= 10 ms
- safety supervisor: <= 5 ms
- scene command dispatch: <= 10 ms
- telemetry append: <= 10 ms

Nominal software budget: **<= 80 ms** excluding device transport/render latency.

Later phases must measure real hardware rather than assume this budget is achieved.

## 13. Phase 1 acceptance tests

Phase 1 can become ✅ only when automated evidence proves:

1. Valid synthetic events pass contract validation.
2. Invalid quality/confidence/range/timestamp cases fail safely.
3. Unknown/low-quality state cannot produce strong adaptation.
4. Safety supervisor clamps/rejects correctly.
5. Same fixture replayed twice produces identical normalized telemetry and final scene state.
6. Different seed/version is explicitly detectable rather than silently changing behavior.
7. No real human data or human-study inference is required.
