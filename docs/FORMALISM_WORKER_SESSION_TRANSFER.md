# Formalism worker session transfer

**Goal ID:** `AEX-FORMALISM-WORKER-PUBLICATION-001`  
**Originating session goal:** create GitHub or StegVerse workers in `Admissible-Existence` that develop formal documentation and mathematics to peer-review publication grade, periodically verify cross-repository consistency and coherence, and publish only finished papers to the StegVerse Site papers page.  
**Canonical coordination handoff:** `Admissible-Existence/.github/FORMALISM_MIRROR_HANDOFF.md`  
**Implementation branch:** `goal/formalism-worker-system`  
**Pull request:** `Admissible-Existence/.github#2`  
**State:** `MERGED_INTO_CANONICAL_WORKSTREAM` at the requirements and coordination level; implementation remains active in PR #2.

## Requirements transferred from the originating session

1. Repository inventory is discovery input, not the program goal.
2. Every qualifying formalism repository must have a repository-native worker or an explicit shared-worker assignment.
3. Workers must advance formalism development, mathematical validation, peer-review preparation, deterministic rendering, publication readiness, and Site publication verification.
4. Mathematical authority remains in each source repository; the organization worker coordinates, audits, dispatches, and observes.
5. Documentation and mathematics must be periodically checked for internal and cross-repository consistency and coherence.
6. Missing access, missing evidence, unresolved proof obligations, and unobserved workflows must fail closed.
7. Duplicate ChatGPT sessions must coordinate through durable claims and task states rather than duplicating repository work.
8. Site publication is allowed only after a fail-closed publication-readiness receipt and direct deployment verification.
9. Publisher, `admissibility-wiki`, `stegguardian-wiki`, and other propagation targets remain blocked until source readiness and authority contracts permit propagation.
10. Session archival is allowed only after all unique requirements are implemented, superseded, or preserved in the canonical workstream.

## Installed implementation

- `data/formalism-worker-registry.json`
- `docs/FORMALISM_WORKER_COMPLETION_STANDARD.md`
- `scripts/audit_formalism_coherence.py`
- `.github/workflows/formalism-coherence-audit.yml`
- `docs/FORMALISM_WORKER_SYSTEM_STATUS.md`
- `schemas/formalism-task-state.schema.json`
- `data/formalism-task-claims.json`
- `scripts/dispatch_formalism_tasks.py`
- `tests/test_dispatch_formalism_tasks.py`

## Canonical claims and collision boundaries

- RTG rendering, evidence closure, theorem-review packets, and readiness convergence are already machine-owned in `Admissible-Existence/RTG`. This branch must observe or validate those lanes, not duplicate them.
- Organization-wide coherence auditing and task derivation are claimed by `Admissible-Existence/.github#2` until the PR is merged and a hosted run is inspected.
- Source-formalism development for `AE`, `Existence`, `GTG`, `TT`, `STCM`, `HPS`, and `FI` remains unassigned until source handoffs and task states are reconciled.

## Exact continuation path

1. Merge PR #2 after branch validation permits.
2. Dispatch `formalism-coherence-audit.yml` from `main`.
3. Inspect run, jobs, logs, artifact, `reports/formalism-coherence-latest.json`, and `reports/formalism-task-state-latest.json`.
4. Convert each `UNCLAIMED`, `BLOCKED`, or `MISSING` task into a source-repository machine lane only after reading that repository's canonical `*_MIRROR_HANDOFF.md`.
5. Preserve existing RTG machine ownership and repair only directly observed defects.
6. Add publication-readiness and Site intake contracts after source-repository task states are machine-observable.

## Archive condition for the originating session

The session may be archived when this transfer record, PR #2, the canonical claims registry, and the organization handoff together contain all unique session requirements and there is no remaining session-only implementation authority. Until the PR is merged and hosted evidence is observed, this session retains a distinct integration and validation role.
