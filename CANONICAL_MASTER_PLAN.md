# Մարդու ուղեղի և վիրտուալ աշխարհի կապ / Positive Emotion Engine / Adaptive Full-Dive Prototype

> **MANDATORY / DO NOT DEVIATE**
>
> This is the repository-local canonical execution plan. Every new chat/agent must read `AGENTS.md` and this file before implementation, architecture, research expansion, CI, or release work.
>
> Canonical Drive mirror: https://docs.google.com/document/d/1krH-xkqJTJ6tk1bLtS0vVYWiz521H2owt6t_APRv8ys/edit

## Status symbols

- ✅ — ավարտված և ընդունված։
- ❌ — դեռ չկատարված։
- ⚠️ — լուծում/կոդ/նախատիպ կա, բայց final acceptance-ը ապացուցված չէ։
- 🗑️ — այլևս հիմնական ուղղություն չէ և չի վերակենդանացվում առանց explicit user decision + canonical plan update։

## 1. Source-of-truth hierarchy

1. This file controls execution order and project logic.
2. Live GitHub controls code, branch/SHA/CI and implementation facts.
3. Project handoff material controls historical completion evidence.
4. Scientific claims must be grounded in current credible evidence; old chat assumptions do not override evidence.
5. A new idea does not override this plan. Update the canonical plan first.
6. Drive and GitHub canonical copies must remain substantively synchronized.
7. If they disagree, do not create a third roadmap; reconcile the mirrors.

## 2. Immutable product objective

Build and scientifically validate a **closed-loop Adaptive VR system** that:

- receives biosignals and behavioral data,
- estimates user state with confidence/uncertainty,
- changes bounded 3D/VR environment parameters,
- attempts to improve positive affect while preserving comfort, agency, stability, and safety,
- maintains consent, stop/exit, privacy, auditability and conservative adaptation constraints,
- keeps full-dive concepts as an evidence-separated long-term research layer, not as a current capability.

Canonical chain:

**VR/3D content → sensing → signal quality → feature extraction → affect/state inference → adaptive policy → safety supervisor → scene update → telemetry/replay → validation.**

Architecture law:

**Inference proposes. Policy selects. Safety constrains. Scene executes. Telemetry records. Validation decides. Human can stop/override.**

## 3. Scientific evidence classes

Every technical/neuroscientific claim is classified as:

- **A — Established:** well-supported scientific/engineering basis.
- **B — Plausible:** meaningful evidence exists, but application limits require validation.
- **C — Experimental:** prototype hypothesis requiring testing.
- **D — Speculative:** full-dive/brain–virtual-world future concept; never presented as current fact.

No agent may silently promote C/D to A.

## 4. Non-negotiable safety boundaries

- Human-in-the-loop and informed consent.
- Always-available stop/exit.
- Conservative adaptation/rate/intensity/duration limits.
- No pain, fear, dependency, psychological pressure, hidden persuasion, or addictive optimization target.
- No unsupported medical diagnosis/treatment claims.
- Neurostimulation, invasive BCI and other high-risk interventions are outside the core prototype implementation scope.
- Bad/uncertain signal quality reduces adaptation or returns to safe baseline.
- Safety gate always overrides emotion optimization.

## 5. Current status

- ✅ Tasks 1–40 completed according to the official handoff; do not restart them from zero.
- ✅ Tasks 41–60 completed with deterministic synthetic end-to-end pipeline, input/output schema validation, deterministic replay, safety tests, and GitHub Actions proof.
- ✅ Canonical objective, evidence separation, safety-first principles and one-path execution are frozen.
- ✅ Dedicated GitHub repository is bound: `tigpetryan-rgb/humanandvirtualworld`.
- ❌ Tasks 61–209 remain on the canonical execution chain.
- ⚠️ A completed handoff item is only as strong as its recorded evidence; code existence alone does not imply production-grade acceptance.

# 6. ACTIVE MASTER EXECUTION SEQUENCE

## PHASE 0 — PLAN FREEZE

✅ Canonical plan exists in Drive and GitHub and must be inherited by future chats/agents.

**DONE gate:** no parallel roadmap or architecture starts outside this plan.

## PHASE 1 — TASKS 41–60 — SYSTEM SPEC + MEASUREMENT FOUNDATION

✅ **COMPLETED.**

Closed measurable contracts include sensor abstraction, monotonic/session time, synchronization and quality semantics, missing-data handling, participant/session/event schemas, feature/state outputs with uncertainty, bounded environment parameters, telemetry/replay, latency/privacy boundaries, and safety interface.

Evidence:
- exact accepted SHA: `e510258772a1698b712ef8a35dba06750043cdff`
- workflow: `Phase 1 Contracts`
- run: `33626870757`
- conclusion: `success`
- job: `phase1-contracts` → success
- synthetic session: schema-valid, deterministic replay, output/telemetry schema-valid
- fault cases: bad quality → unknown/no-op; human stop override; safety clamp/reject; invalid sequence/time rejected

**DONE gate:** proven.

## PHASE 2 — TASKS 61–80 — BIOSIGNAL ACQUISITION + QUALITY

❌ **CURRENT ACTIVE PHASE.**

Build and validate a multimodal input layer without pretending that any single sensor directly reveals emotion.

Primary channels:
- HR / inter-beat intervals / HRV-derived features,
- EDA/GSR,
- respiration,
- eye/gaze/pupil when hardware permits,
- face/head/body motion where useful.

EEG is not a default requirement. It enters only when a real device and a clearly defined scientific value justify the added complexity/noise burden.

Required outputs:
- device-agnostic sensor adapter interface,
- recorded-file/replay adapter,
- calibration metadata,
- clock alignment and timestamp diagnostics,
- dropout detection,
- artifact detection/flags,
- per-channel and per-window quality/confidence,
- explicit missing/unknown semantics,
- synchronized clean feature windows,
- deterministic recorded-data replay,
- test fixtures for clean, noisy, missing, drifted and misaligned data.

Scientific law for this phase:
- sensor quality is measured separately from emotional-state confidence,
- low-quality data must never be silently imputed into high-confidence affect inference,
- derived physiological features are measurements/proxies, not direct mind-reading labels.

**DONE gate:** a recorded multimodal dataset is ingested through the device-agnostic layer, clocks are aligned/diagnosed, artifacts/dropouts are explicitly marked, synchronized feature windows are produced deterministically, and bad/missing data remain visible instead of being hidden.

Do not start Phase 3 before this gate is proven.

## PHASE 3 — TASKS 81–100 — MULTIMODAL AFFECT / STATE INFERENCE

❌ Start with interpretable baselines before complex ML.

Required output: defined state vector such as valence/arousal, confidence/uncertainty, personalization state, and unknown/no-signal state.

**DONE gate:** offline validation + calibration metrics + robustness tests without unsupported “mind reading” claims.

## PHASE 4 — TASKS 101–120 — ADAPTIVE VR PARAMETER ENGINE

❌ Bounded controls for lighting, color temperature, motion intensity, camera behavior, spatial audio, music parameters, pacing, density, character behavior and environmental calm/excitement.

Required: hard bounds, transition smoothing, deterministic state transitions, manual override.

**DONE gate:** same input state + same seed gives the same scene transition and every change remains inside the safety envelope.

## PHASE 5 — TASKS 121–140 — POSITIVE EMOTION ENGINE / CLOSED LOOP

❌ Connect inference to adaptation.

Objective is multi-factor: **positive affect + comfort + agency + stability + safety**, never “maximum emotion intensity.”

Start rule-based/controller-first. More complex personalization such as conservative contextual bandits is allowed only if evidence justifies it.

**DONE gate:** simulator/replay improves the predefined objective without violating safety constraints.

## PHASE 6 — TASKS 141–155 — SAFETY SUPERVISOR

❌ Independent superior control layer.

Required: stop logic, physiological/behavioral anomaly triggers, adaptation cooldown, max intensity/duration limits, cybersickness/discomfort controls, emergency exit, audit trail.

**DONE gate:** fault-injection tests prove unsafe commands never reach the scene executor.

## PHASE 7 — TASKS 156–170 — EXPERIMENTAL SCIENCE + PROTOCOL

❌ Define a reproducible human-study protocol before real testing.

Required: hypotheses, endpoints, controls/baselines, design rationale, power/sample-size planning, consent, exclusion/stop rules, adverse-event logging, preregistration-ready analysis plan.

**DONE gate:** an independent researcher can review the protocol without major hidden decisions.

## PHASE 8 — TASKS 171–185 — INTEGRATED VR PROTOTYPE

❌ Integrate VR runtime, sensors, inference, adaptation, safety and telemetry.

Required: scene abstraction, content packs, device abstraction, session start/calibrate/run/stop/replay workflow.

**DONE gate:** one controlled end-to-end demo session is fully replayable from logs.

## PHASE 9 — TASKS 186–195 — ROBUSTNESS + VALIDATION

❌ Validate latency, dropout, noisy data, participant/content/device variation and adaptation edge cases.

Required: regression tests, failure fixtures, calibration-drift tests, false-positive/false-adaptation analysis.

**DONE gate:** known failure modes are controlled or explicitly documented as limitations.

## PHASE 10 — TASKS 196–205 — ADVANCED IMMERSION / FULL-DIVE-ADJACENT RESEARCH

❌ Non-invasive, evidence-separated research only: presence, embodiment, multisensory integration, subjective time, memory/attention effects, dream-like experience design, agency/ownership illusions and adaptive narrative.

🗑️ “Real full-dive is already possible” is not a project direction.

**DONE gate:** every sub-idea has an evidence map: established / plausible / experimental / speculative, plus a prototype-safe test boundary.

## PHASE 11 — TASKS 206–209 — FINAL DEMO + DOCUMENTATION + HANDOFF

❌ Stabilize release-candidate prototype, reproducibility bundle, scientific limitations, safety case and continuation handoff.

**DONE gate:** a new chat can continue from canonical plan + current checkpoint + repository state without needing full historical conversation.

## 7. Explicitly removed primary directions

- 🗑️ Emotion intensity as a standalone optimization target.
- 🗑️ Unsupported “brain reading” or reliable decoding of specific private thoughts.
- 🗑️ Full-dive as a near-term software feature.
- 🗑️ Hidden persuasion/addiction optimization.
- 🗑️ Invasive/high-risk neurointervention as the main prototype path.
- 🗑️ Unrelated AI/3D/BCI research that does not close the active DONE gate.
- 🗑️ Architecture/framework rewrites merely because they are more interesting.

## 8. Repository governance

Root must contain:
- `AGENTS.md`
- `CANONICAL_MASTER_PLAN.md`
- `README.md`

Governance docs:
- `docs/SCIENTIFIC_AND_SAFETY_RULES.md`
- `docs/CURRENT_CHECKPOINT.md`
- `docs/archive/` for superseded roadmaps/handoffs when needed.

Contradiction handling:
1. Historical value → archive/deprecate and point to canonical plan.
2. Actively wrong direction with no historical value → replace/delete.
3. README/AGENTS/current docs must never contradict the canonical plan.
4. Code is not deleted solely for ideological disagreement if it may be a dependency/regression artifact; inspect usage/tests first.
5. Preserve Git history before destructive cleanup.

## 9. Mandatory new-chat / agent inheritance protocol

Every new chat/agent must:
1. Read root `AGENTS.md`.
2. Read this `CANONICAL_MASTER_PLAN.md`.
3. Read `docs/CURRENT_CHECKPOINT.md`.
4. Read only relevant archive/handoff material after the plan.
5. Re-check live branch, exact SHA, CI/tests and open PR state when relevant.
6. Declare exactly one active phase and one concrete next objective.
7. Never open the next phase until the current DONE gate is proven.
8. Never change ⚠️ to ✅ merely because code exists.
9. Never revive 🗑️ directions without explicit user instruction + plan update.
10. End significant sessions by updating the checkpoint: what changed, evidence/tests, status, remaining work and exact next action.
11. If the canonical plan changes by explicit user decision, mirror the same substantive change to Drive and GitHub.

## 10. Completion evidence rule

✅ is allowed only when the corresponding DONE gate has verifiable evidence: test result, reproducible output, dataset analysis, validated design artifact or explicit acceptance evidence.

Code existence alone is insufficient. A documented scientific hypothesis is not a confirmed hypothesis. Human-study findings are not generalized beyond their evidence.

## 11. CURRENT CHECKPOINT

**Active phase:** PHASE 2 — TASKS 61–80 — BIOSIGNAL ACQUISITION + QUALITY.

**Exact objective:** implement the device-agnostic recorded-data acquisition/quality pipeline first, with deterministic replay and explicit quality/missing-data semantics, then connect real sensors only through that same contract.

**Do not do next:** Phase 3 emotion inference, adaptive policy, full-dive research or human-subject work until Phase 2 DONE gate is proven.

## 12. Canonical update rule

This plan changes only when the user explicitly changes the objective/priority/acceptance criteria, or new evidence shows the current phase is technically invalid/impossible.

Every canonical change records what changed, why, affected status/task range, new active phase and exact next action.
