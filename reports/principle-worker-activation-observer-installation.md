# Principle worker activation observer installation

## Goal

Move post-repair worker activation observation out of chat and into a repository-native machine lane.

## Installed surfaces

- `scripts/observe_principle_worker_activation.py`
- `.github/workflows/principle-worker-activation-observer.yml`
- `data/principle-worker-activation-observer-claim.json`

## Commits

- observer script: `da7fd565a7ce1518686c4c3099ebb2573626fc36`
- observer workflow: `96f97a8d526d07f1b3745bfdeb1b3543a6490ca1`
- observer claim: `c4fc206595d0e447ca8eadcb6e48ec197bd922d5`
- worker claim update: `984960cce8ce5819f466d276c40497553adb62bb`
- canonical handoff update: `bfe2ee897dfb0951c66f9f4c3cf26112d0112cd1`

## Workflow identity

- name: `Principle worker activation observer`
- workflow ID: `328894324`
- registration state: `active`
- hosted runs observed at installation: `0`

## Triggers

- hourly schedule at minute 41;
- completion of `Principle completeness repository workers`;
- manual dispatch;
- push affecting observer files.

## Evidence contract

The observer reports one explicit state and checks:

- whether a post-repair worker run exists;
- whether that run is complete;
- whether `reports/formalism-worker-status-latest.json` exists on `main`;
- whether `reports/formalism-worker-status-latest.md` exists on `main`;
- whether the run retained `principle-completeness-worker-status`.

It emits `reports/principle-worker-activation-observation.json`, uploads a sanitized artifact, and comments issue `Admissible-Existence/.github#4`.

## Authority boundary

The observer reads GitHub Actions and repository metadata only. It does not resolve credentials, grant capability, mutate source mathematics, accept proofs, administer repositories, or release software.

## Release condition

`COMPLETE_READ_ONLY_WORKER_EVIDENCE` must be emitted for a post-repair run before the read-only worker blocker can be released. Governed apply remains separately owned by `StegVerse-Labs/TVC#13` and `StegVerse-Labs/TV` runtime custody.
