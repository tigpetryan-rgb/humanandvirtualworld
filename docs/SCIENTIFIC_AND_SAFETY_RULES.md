# Scientific and Safety Rules

This file is mandatory and subordinate only to the explicit user decision reflected in `CANONICAL_MASTER_PLAN.md`.

## Evidence labels

Every scientific/technical claim used to justify design is tagged:

- **A — Established**: strong replicated scientific or engineering basis.
- **B — Plausible**: useful evidence exists, but limits/generalization remain uncertain.
- **C — Experimental**: project hypothesis requiring validation.
- **D — Speculative**: future/full-dive-adjacent concept; never presented as an existing capability.

No implementation may silently convert C/D into A.

## Safety hierarchy

1. Human stop/exit/override.
2. Safety supervisor and hard constraints.
3. Signal-quality/uncertainty gate.
4. Adaptive policy.
5. Positive-affect optimization.

Lower layers may never bypass higher layers.

## Prohibited optimization directions

- pain, fear, panic or distress as desired targets,
- compulsion/addiction/dependency optimization,
- hidden persuasion or manipulation,
- maximizing arousal/intensity without comfort, agency and safety,
- unsupported decoding of private thoughts or “brain reading”,
- medical diagnosis/treatment claims without appropriate clinical evidence,
- invasive BCI/neurostimulation as part of the core prototype.

## Required runtime behavior

- Low-confidence or missing signals reduce adaptation or return to a safe baseline.
- Every adaptive action has bounded parameters and an audit record.
- Every session supports immediate stop/exit.
- Adaptation must support cooldown/rate limits and eventually explicit duration/intensity ceilings.
- User agency is an optimization constraint, not an optional UI feature.
- Raw biosignal retention is minimized; derived features should be preferred when sufficient.
- Synthetic data is used for Phase 1; no human-subject testing begins before the dedicated protocol phase.

## Scientific language discipline

Allowed wording distinguishes observation, inference and hypothesis. A state estimator produces an estimate with uncertainty, not a claim of direct access to subjective experience.

Full-dive-adjacent ideas remain separated into established/plausible/experimental/speculative evidence layers and are only opened in the canonical later phase.
