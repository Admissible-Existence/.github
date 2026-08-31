# VerFi External Formalism Mirror Handoff

## Canonical status

- Goal ID: `AEX-VERFI-EXTERNAL-FORMALISM-001`
- Repository: `Admissible-Existence/.github`
- Parent coordination authority: `FORMALISM_MIRROR_HANDOFF.md`
- Status: `PUBLIC_SOURCE_GROUNDED_EXACT_MAIN_VALIDATED_TEST_CANDIDATE`
- Registered: `2026-08-22`
- Public-source grounding added: `2026-08-23`
- Scope: bounded external-formalism registration, deterministic StegVerse governance-lane testing, and public-source semantic grounding only.
- Canonical StegVerse source authority granted: `false`
- AE admissibility authority granted: `false`
- Execution authority granted: `false`
- VerFi product/legal claims independently validated: `false`

## Installed surfaces

```text
docs/external-formalisms/VERFI.md
data/external-formalisms/verfi.json
fixtures/external-formalisms/verfi-governance-lanes.json
scripts/validate_verfi_external_formalism.py
tests/test_verfi_external_formalism.py
.github/workflows/canonical-formalism-orientation.yml
docs/external-formalisms/VERFI_PUBLIC_SOURCE_VALIDATION_REQUEST_2026-08-23.md
```

## Formal boundary

VerFi is registered as a human consent / cognitive authorization evidence candidate with the publicly represented sequence:

```text
IDENTITY -> DISCLOSURE -> COMPREHENSION -> AUTHORIZATION -> SIGNATURE -> EVIDENCE
```

The StegVerse comparison surface evaluates transition distinguishability, evidence sufficiency, continuity, temporal ordering, integrity, minimization, authority and admissibility. A VerFi-like package may supply evidence but cannot create StegVerse canonicality, AE authority, execution authority, or proof of an internal mental state.

## Public-source grounding — 2026-08-23

The candidate is no longer based only on a conversational representation. Public VerFi Holdings Inc. product pages were inspected and the machine-readable registry now records the publisher and exact source URLs while preserving `PUBLISHER_ASSERTED_NOT_INDEPENDENTLY_VERIFIED` posture.

Publicly represented record elements now bound into the candidate are:

```text
session initiation and continuity
identity-bound participant attribution
education delivery confirmation
recorded comprehension interaction and responses
timestamped authorization enablement
```

Publicly represented control semantics now preserved as claims under test include:

```text
comprehension checkpoints before consent finalization
missed checkpoint -> term re-presented -> correction preserved
exact disclosure version recorded
one procedure + one session + one identified party per record
sealed/tamper-evident record at session close
Execution Verified Token issued after required checkpoints complete
```

The public pages also declare record exclusions covering diagnoses/clinical notes/labs, clinical decision support/scoring, legal or clinical determinations, and treatment decisions/approvals/billing.

These remain publisher claims. No production consent record, evidence package, implementation schema, API output or Execution Verified Token specimen has been independently inspected.

The public semantics add two explicit future implementation-artifact tests:

```text
CHECKPOINT_CORRECTION_PRESERVATION
AUTHORIZATION_ENABLEMENT_CAUSALITY
```

The named external `Execution Verified Token` is explicitly prevented from becoming StegVerse/AE execution or admissibility authority by registry and validator invariant.

## Governance-lane matrix

The deterministic fixture suite contains ten cases:

```text
CLEAN_SEQUENCE
COMPREHENSION_MISSING
DISCLOSURE_DRIFT
AUTHORIZATION_LAPSED
EVIDENCE_TAMPER
TEMPORAL_DISORDER
AMBIGUOUS_COMPREHENSION
OVER_COLLECTION
INDEPENDENT_RECONSTRUCTION
HUMAN_MACHINE_SYMMETRY
```

Mandatory negative invariant:

```text
DISCLOSURE_ESTABLISHED
  -> COMPREHENSION_NOT_ESTABLISHED
  -> AUTHORIZATION_INADMISSIBLE
```

A signature is explicitly unable to force a successful comprehension result.

## Transition prerequisite hardening

The evaluator independently rejects missing disclosure and missing signature rather than relying on fixture defaults.

```text
validator hardening commit: 72c976ba81997d41d61b889a2fc7cb50ca95e469
test hardening commit: 2f3e9a8fc68615b620221f0ebdedba3a51c0e06e
disclosure != established -> DISCLOSURE_NOT_ESTABLISHED
authorization established but signature absent -> SIGNATURE_NOT_ESTABLISHED
signature present + comprehension absent -> AUTHORIZATION_INADMISSIBLE
```

## Public-source validation implementation

```text
registry grounding commit: 7c9355429fba47a99159ba98a9181ee058ad77a8
document grounding commit: 278fee222fdb480bec63cd353e455b2dc9583189
validator grounding commit: 0a93acefe88d831c47aafdd58b994fe0e7194a1d
validation-request commits on main: 26dfacaeb92e5dbd0b48be275a663b3623a34b6a, 9a8407a5c8f4c699b386fc6db18cb97f4261edec
```

The validator now fails if the publisher-source posture disappears, the source set changes silently, publisher claims become marked as independently verified, a production artifact is falsely claimed, or the external Execution Verified Token is granted StegVerse authority.

## Hosted validation evidence — public-source-grounded tree

A branch was created from current `main` after the grounding changes and PR `Admissible-Existence/.github#14` forced the existing credential-clean workflow to execute.

```text
PR head: 738155c2fabc82df43692615d88242c590e76bee
Canonical Formalism Orientation Validation run: 32669672912
job: 97268432680
result: SUCCESS
VerFi parse: SUCCESS
VerFi boundary/lane validation: SUCCESS
VerFi regression tests: SUCCESS
validation-only authority proof: SUCCESS
merge commit: 06b70dbc3376752bd3147d43ec7c383c069b6301
```

This proves the hosted PR tree carrying the public-source-grounded candidate passes the existing formalism validation lane. It does **not** collapse the stricter exact-current-`main` gate into PR-tree validation.

## Maturity boundary

Current maturity remains bounded because no actual VerFi evidence envelope, implementation schema, API output, consent/execution record, or Execution Verified Token specimen has been supplied for independent inspection.

Next maturity path:

```text
obtain actual VerFi implementation artifact
-> bind immutable artifact identity
-> reconstruct disclosure/checkpoint/correction/authorization sequence
-> test authorization-enablement causality
-> run negative cases
-> compare result with publisher-declared semantics
-> preserve PASS / REVIEW / DENY / FAIL_CLOSED without authority promotion
```

## Deliverable accounting

Scope expanded on 2026-08-23 to include publisher-source grounding, so the denominator is reset to 9 deliverables.

```text
1 external-formalism boundary document: COMPLETE
2 machine-readable registry: COMPLETE_PUBLIC_SOURCE_GROUNDED
3 deterministic 10-case lane fixture: COMPLETE
4 deterministic validator: COMPLETE_HARDENED_AND_SOURCE_GROUNDED
5 regression tests: COMPLETE_HARDENED
6 existing workflow integration: COMPLETE
7 durable task/handoff state: COMPLETE
8 hosted validation of public-source-grounded tree: COMPLETE
9 exact-current-main hosted validation evidence: COMPLETE
```

Current bounded completion: `9/9 = 100%` for the source-grounded registration and exact-main validation goal.

Developed source/control surfaces: `8/8`; scaffolding/stubs: `0`; missing planned source files: `0`.

Implementation-level VerFi interoperability is a separate downstream gate and remains open until a genuine external artifact is obtained.

## Archive / continuation

This handoff is sufficient to continue without chat history. Do not promote beyond `TEST_CANDIDATE` until exact-current-main validation is bound and a genuine VerFi artifact is independently reconstructed and negative-tested.


## Exact-main validation closure — 2026-08-31

The previously pending exact-current-main gate was already satisfied by a directly inspected
main-branch Canonical Formalism Orientation Validation run:

```text
run: 32669717663
job: 97268542920
head: ac6839f4a36b3e77cfd761a9d1d82fa7d811fcee
branch: main
conclusion: success
VerFi parse: success
VerFi boundary/lane validation: success
VerFi regression tests: success
workflow authority effect: NONE_VALIDATION_ONLY
```

The registration goal is therefore COMPLETE/RELEASED at TEST_CANDIDATE maturity. A genuine VerFi
implementation artifact would admit a new, separate interoperability/reconstruction task; its absence
does not keep this exact-main validation task active.
