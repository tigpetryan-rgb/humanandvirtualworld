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
- ✅ Tasks 41–60 completed with deterministic synthetic end-to-end pipeline, schema validation, deterministic replay, safety tests and exact-SHA GitHub CI proof.
- ✅ Tasks 61–80 completed with device-agnostic acquisition/quality contracts, regular/event sampling semantics, deterministic quality fixtures, Empatica E4 adapter, public deidentified recorded-data validation and CI proof.
- ✅ Canonical objective, evidence separation, safety-first principles and one-path execution are frozen.
- ✅ Dedicated GitHub repository is bound: `tigpetryan-rgb/humanandvirtualworld`.
- ❌ Tasks 81–209 remain on the canonical execution chain.
- ⚠️ A completed handoff item is only as strong as its recorded evidence; code existence alone does not imply production-grade acceptance.

# 6. ACTIVE MASTER EXECUTION SEQUENCE

## PHASE 0 — PLAN FREEZE

✅ Canonical plan exists in Drive and GitHub and must be inherited by future chats/agents.

**DONE gate:** no parallel roadmap or architecture starts outside this plan.

## PHASE 1 — TASKS 41–60 — SYSTEM SPEC + MEASUREMENT FOUNDATION

✅ **COMPLETED.**

Evidence:
- accepted implementation SHA: `e510258772a1698b712ef8a35dba06750043cdff`
- workflow `Phase 1 Contracts`, run `33626870757` → success
- schema-valid synthetic session, deterministic replay, output/telemetry schema validation
- bad quality → unknown/no-op, human stop override, safety clamp/reject, invalid sequence/time rejection

**DONE gate:** proven.

## PHASE 2 — TASKS 61–80 — BIOSIGNAL ACQUISITION + QUALITY

✅ **COMPLETED.**

Implemented and retained:
- device-agnostic recorded/replay acquisition contract,
- explicit units and channel metadata,
- regular vs event-stream sampling semantics,
- timestamp normalization and clock offset/drift diagnostics,
- explicit sampling-gap/dropout detection for regular streams,
- artifact/missing-data quality flags,
- per-channel/per-window quality independent of affect confidence,
- deterministic synchronized measurement windows,
- clean/noisy/missing/misaligned/drifted fixtures,
- Empatica E4 EDA + IBI adapter with IBI preserved as an irregular event stream,
- no affect labels emitted by the acquisition layer.

Evidence:
- implementation/public-data SHA: `8f1af8c1b945530e99eb67a14231a10dc618e741`
- public recorded-data workflow: `Phase 2 Public Recorded Dataset`
- run `33632614887`, job `physionet-empatica-recorded-data` → success
- source dataset: PhysioNet `A Wearable Exam Stress Dataset for Predicting Cognitive Performance in Real-World Settings` v1.0.0, subject S8 Final, deidentified EDA + IBI
- acquisition-regression SHA: `086066f9cba48cb39ce0745cd56a92cf84b11264`
- workflow `Phase 2 Acquisition Quality`, run `33632737145`, job `phase2-acquisition-quality` → success
- Phase 1 regression + Phase 2 quality + Empatica adapter tests all pass
- compare `8f1af8…` → `086066…`: only `.github/workflows/phase2-acquisition-quality.yml` changed; acquisition/adapter implementation is unchanged.

Scientific boundary retained:
- physiological measurements are proxies/observations, not private-thought labels,
- signal quality confidence is distinct from affect-state confidence,
- bad/missing data remain explicit rather than being silently upgraded.

**DONE gate:** proven with synthetic fault fixtures + actual deidentified recorded data.

## PHASE 3 — TASKS 81–100 — MULTIMODAL AFFECT / STATE INFERENCE

❌ **CURRENT ACTIVE PHASE.**

Build an interpretable, uncertainty-aware state-estimation baseline before complex ML.

Required work:
- define the target state representation and what it explicitly does **not** claim,
- separate observed physiological features, contextual labels and self-report/ground-truth labels,
- define `known / uncertain / unknown / no-signal` states,
- define confidence vs uncertainty vs calibration,
- create a feature-to-state baseline that can be explained and audited,
- validate on labeled/deidentified recorded data,
- use participant-independent evaluation where the dataset permits it,
- report calibration and classification/regression metrics, not accuracy alone,
- test low-quality/missing-modality behavior,
- ensure no single biosignal is treated as a direct decoder of a private mental state,
- preserve provenance from Phase 2 quality through every inference result.

Initial target representation may use bounded valence/arousal or a narrower explicitly labeled state variable, but the chosen representation must match available ground truth. A dataset label such as “stress condition” must not be silently renamed “negative valence” without evidence.

Complex deep learning, opaque end-to-end models and personalization are not first-step requirements. Start with interpretable baselines and only increase complexity if they fail a defined gate.

**DONE gate:** offline validation on labeled/deidentified data with participant-independent or leave-session robustness where feasible, confidence/uncertainty outputs, calibration metrics, explicit unknown behavior under low-quality/missing input, and no unsupported “mind reading” claims.

Do not start Phase 4 before this gate is proven.

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

Root must contain `AGENTS.md`, `CANONICAL_MASTER_PLAN.md`, `README.md`.
Governance docs include `docs/SCIENTIFIC_AND_SAFETY_RULES.md`, `docs/CURRENT_CHECKPOINT.md`, and `docs/archive/` when superseded material exists.

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
10. End significant sessions by updating the checkpoint with what changed, evidence/tests, status, remaining work and exact next action.
11. If the canonical plan changes by explicit user decision, mirror the same substantive change to Drive and GitHub.

## 10. Completion evidence rule

✅ is allowed only when the corresponding DONE gate has verifiable evidence: test result, reproducible output, dataset analysis, validated design artifact or explicit acceptance evidence.

Code existence alone is insufficient. A documented scientific hypothesis is not a confirmed hypothesis. Human-study findings are not generalized beyond their evidence.

## 11. CURRENT CHECKPOINT

**Active phase:** PHASE 3 — TASKS 81–100 — MULTIMODAL AFFECT / STATE INFERENCE.

**Exact objective:** define the inference target/ground-truth contract and implement the first interpretable, calibrated, uncertainty-aware offline baseline on labeled deidentified data, carrying Phase 2 quality provenance forward.

**Do not do next:** Phase 4 adaptation engine, full-dive research, human-subject work or opaque complex ML before the Phase 3 baseline/validation gate is proven.

## 12. Canonical update rule

This plan changes only when the user explicitly changes the objective/priority/acceptance criteria, or new evidence shows the current phase is technically invalid/impossible.

Every canonical change records what changed, why, affected status/task range, new active phase and exact next action.
