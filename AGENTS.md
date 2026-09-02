# AGENTS.md — MANDATORY REPOSITORY WORKING CONTRACT

**Scope: entire repository.**

Before doing anything else, every ChatGPT/agent/coding/review/research/CI session MUST read, in order:

1. [`CANONICAL_MASTER_PLAN.md`](./CANONICAL_MASTER_PLAN.md)
2. [`docs/CURRENT_CHECKPOINT.md`](./docs/CURRENT_CHECKPOINT.md)
3. [`docs/SCIENTIFIC_AND_SAFETY_RULES.md`](./docs/SCIENTIFIC_AND_SAFETY_RULES.md)
4. Only then, material relevant to the current active phase.

Canonical Drive mirror:
https://docs.google.com/document/d/1krH-xkqJTJ6tk1bLtS0vVYWiz521H2owt6t_APRv8ys/edit

## Non-negotiable rules

- Work on exactly one active phase and one concrete next objective.
- Current phase is **PHASE 2 — TASKS 61–80 — BIOSIGNAL ACQUISITION + QUALITY**.
- Phase 1 / Tasks 41–60 are ✅ completed and must not be reopened without evidence of a defect.
- Do not start Tasks 81+ until Phase 2 DONE gate is proven.
- The plan controls execution order; live GitHub controls code/SHA/test facts.
- `⚠️` does not become `✅` because code exists.
- `🗑️` directions stay inactive unless the user explicitly changes the canonical plan.
- Safety always overrides affect optimization.
- No hidden persuasion, addiction optimization, fear/pain optimization, unsupported mind-reading claims, medical claims, invasive BCI or neurostimulation as core prototype work.
- Sensor quality/confidence is distinct from inferred emotional-state confidence.
- Bad, missing, drifted or misaligned biosignal data must remain explicit and must not be silently converted to high-confidence affect inference.
- Full-dive concepts remain evidence-separated long-term research, not current product claims.
- Do not create competing master roadmaps.
- Do not rewrite unrelated completed work without evidence that it blocks the active DONE gate.
- Preserve deterministic replay, auditability, explicit uncertainty and human stop/override.
- If Drive and GitHub canonical copies disagree, stop architectural drift and reconcile the mirrors rather than inventing a third direction.

## Phase 2 exact objective

Build the device-agnostic acquisition/quality layer around recorded/replay data first, then connect real sensors only through the same contract.

Required evidence before Phase 3:
- multimodal recorded data ingestion,
- deterministic replay,
- timestamp/clock-alignment diagnostics,
- explicit dropout/artifact flags,
- per-channel and per-window quality,
- synchronized feature windows,
- bad/missing data preserved as visible quality state,
- automated clean/noisy/missing/drift/misalignment fixtures and tests.

## Required end-of-session checkpoint

Update `docs/CURRENT_CHECKPOINT.md` with:
- active phase,
- exact next objective,
- branch + exact SHA when relevant,
- tests/evidence,
- what changed,
- status changes (✅ / ❌ / ⚠️ / 🗑️),
- what remains,
- exact next action.
