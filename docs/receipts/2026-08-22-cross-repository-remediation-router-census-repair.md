# Cross-repository remediation router census repair — 2026-08-22

Goal: `AEX-CROSS-REPOSITORY-REMEDIATION-001`

## Triggering evidence

- Failed hosted run: `32563411754`
- Job: `route` / `97008376193`
- Source commit: `de1d7abde69e6b1456f5e0aa1c559ff3bc6d1a82`
- Contract tests: `9 passed`
- Router output counts: `COMPLETE_NOTIFY_ONLY=27`, `CONTROL_PLANE=1`, `DIRECT_SOURCE_UPDATE=2`, `INTEGRATION_NOTIFY_ONLY=1`, `OBSERVE_NOTIFY_ONLY=1`
- Failure: workflow-local expected counts still asserted the earlier pre-completion census (`COMPLETE_NOTIFY_ONLY=15`, `DIRECT_SUPPORT_UPDATE=4`, `DISPOSITION_REQUIRED=2`, `HOSTED_VALIDATION_BLOCKED=6`).

## Handoff reconciliation

`docs/CROSS_REPOSITORY_REMEDIATION_MIRROR_HANDOFF.md` already records the exhausted support, disposition, and hosted-validation cohorts and the current 32-repository routing census:

- `CONTROL_PLANE: 1`
- `DIRECT_SOURCE_UPDATE: 2`
- `DIRECT_SUPPORT_UPDATE: 0`
- `DISPOSITION_REQUIRED: 0`
- `OBSERVE_NOTIFY_ONLY: 1`
- `COMPLETE_NOTIFY_ONLY: 27`
- `INTEGRATION_NOTIFY_ONLY: 1`
- `HOSTED_VALIDATION_BLOCKED: 0`

The run therefore failed because validation lagged canonical state, not because the router regressed repository routing.

## Repair

Commit `a6a1cc13bc86edc7213ab7c74c3b93a5905e44e8` updates `.github/workflows/cross-repository-remediation-router.yml` so the hosted gate matches the canonical exhausted-cohort census and requires STCM, learning-transition-governance, BC, CHF, RE, and RE-Reduction to remain `COMPLETE_NOTIFY_ONLY` rather than the obsolete `HOSTED_VALIDATION_BLOCKED` state.

No source-repository claimant, TV/TVC dependency, TT integration authority, propagation authority, or execution authority was changed.

## State

Repair installed on `main`; hosted post-repair proof remains required before this failure class is closed.
