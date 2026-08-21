# Worker Blocker Fallback Invariant

**Scope:** Admissible-Existence organization workers and organization-coordinated repository workers.

## Required behavior

A blocker is a state transition, not a terminal worker condition.

When a worker encounters any blocker inside its admitted scope, it MUST:

1. preserve the blocker durably in the current repository handoff, repository-native task/issue, or the coordinating worker task/report surface when the repository itself cannot be mutated;
2. record the blocked surface, failure class, evidence, authority boundary, next admissible action, release condition, and expected completion evidence;
3. avoid claiming the blocked surface complete, activated, released, validated, or abandoned;
4. avoid retry loops that cannot change the blocker state;
5. continue immediately to the next non-duplicate, non-colliding, admissible surface inside the worker's assigned scope;
6. revisit the blocker when its release condition becomes machine-observable or when a later in-scope action changes its prerequisites;
7. terminate the worker only when every in-scope surface is either complete or durably blocked with an observable continuation owner and there is no further admissible work.

## Fallback precedence

The durable blocker destination is selected in this order:

1. repository-local `*_MIRROR_HANDOFF.md` plus an existing repository-native task/issue when mutation is authorized;
2. repository-local worker task/issue created or refreshed by the admitted worker;
3. coordinating worker task/report when repository access, authority, collision, policy, or service state prevents repository-local mutation.

Failure to mutate the preferred destination MUST itself be recorded as a blocker and MUST NOT prevent continuation to other in-scope surfaces.

## Non-authority

This invariant does not widen source-mathematics authority, proof-acceptance authority, repository administration, credential custody, execution authority, release authority, publication authority, signing authority, or deployment authority.

TV/TVC remains the only StegVerse credential authority. GitHub-token runtime authority remains `NONE` except where a bounded hosted coordination action is explicitly admitted; such hosted coordination does not become production runtime authority.

## Controller contract

Organization controllers MUST isolate each repository/surface so an unexpected exception in one item cannot abort enumeration of later items. A generated worker report MUST contain a blocker queue with enough information to continue without chat history.

Canonical organization goal: `AEX-PRINCIPLE-COMPLETENESS-001`.
