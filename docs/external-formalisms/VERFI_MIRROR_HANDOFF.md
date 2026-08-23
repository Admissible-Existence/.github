# VerFi External Formalism Mirror Handoff

## Canonical status

- Goal ID: `AEX-VERFI-EXTERNAL-FORMALISM-001`
- Repository: `Admissible-Existence/.github`
- Parent coordination authority: `FORMALISM_MIRROR_HANDOFF.md`
- Status: `IMPLEMENTED_PENDING_EXACT_HEAD_VALIDATION`
- Registered: `2026-08-22`
- Scope: bounded external-formalism registration and deterministic StegVerse governance-lane testing only.
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
```

## Formal boundary

VerFi is registered as a human consent / cognitive authorization evidence candidate with the publicly represented sequence:

```text
IDENTITY -> DISCLOSURE -> COMPREHENSION -> AUTHORIZATION -> SIGNATURE -> EVIDENCE
```

The StegVerse comparison surface evaluates transition distinguishability, evidence sufficiency, continuity, temporal ordering, integrity, minimization, authority and admissibility. A VerFi-like package may supply evidence but cannot create StegVerse canonicality, AE authority, execution authority, or proof of an internal mental state.

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

A signature is therefore explicitly unable to force a successful comprehension result.

## Transition prerequisite hardening — 2026-08-22

A post-install review found that the first deterministic evaluator did not independently reject a missing disclosure or a missing signature when all other fields were positive. That would have allowed an incomplete declared sequence to reach `ALLOW_CANDIDATE` in direct evaluator use even though canonical fixtures happened to set both fields true.

The defect is repaired on `main`:

```text
validator hardening commit: 72c976ba81997d41d61b889a2fc7cb50ca95e469
test hardening commit: 2f3e9a8fc68615b620221f0ebdedba3a51c0e06e
```

The evaluator now preserves explicit bounded failures:

```text
disclosure != established -> DISCLOSURE_NOT_ESTABLISHED
authorization established but signature absent -> SIGNATURE_NOT_ESTABLISHED
signature present + comprehension absent -> AUTHORIZATION_INADMISSIBLE
```

The regression suite now constructs a fully valid base sequence and independently removes disclosure, comprehension, signature, authorization validity, integrity, and minimization conditions. This prevents optional-field omission in tests from masking transition-order defects.

## Validation lane

The existing credential-clean `Canonical Formalism Orientation Validation` workflow has been extended rather than creating a new workflow/control plane. It parses the VerFi candidate registry and fixtures, runs `scripts/validate_verfi_external_formalism.py`, then runs `tests.test_verfi_external_formalism`.

The workflow remains `permissions: {}` with empty GitHub/GH/StegVerse/TVC token environment variables and retains `NONE_VALIDATION_ONLY` authority effect.

The hardening commits changed validation-controlled paths, so exact-current-main hosted validation must bind a head at or after `2f3e9a8fc68615b620221f0ebdedba3a51c0e06e`. Earlier green runs do not satisfy this gate.

## Maturity boundary

Current maturity is bounded because no actual VerFi evidence envelope, implementation schema, or API output has been supplied for independent inspection. The next maturity gate is:

```text
obtain actual VerFi evidence envelope/schema/API output
-> bind immutable artifact identity
-> run negative cases
-> run independent reconstruction
-> compare result with declared VerFi semantics
-> preserve PASS / REVIEW / DENY / FAIL_CLOSED without authority promotion
```

## Deliverable accounting

Denominator: 8 deliverables.

```text
1 external-formalism boundary document: COMPLETE
2 machine-readable registry: COMPLETE
3 deterministic 10-case lane fixture: COMPLETE
4 deterministic validator: COMPLETE_HARDENED
5 regression tests: COMPLETE_HARDENED
6 existing workflow integration: COMPLETE
7 durable task/handoff state: COMPLETE
8 exact-current-main hosted validation evidence: PENDING
```

Current bounded completion: `7/8 = 87.5%`.

Developed source/control surfaces: `7/7`; scaffolding/stubs: `0`; missing planned source files: `0`.

## Archive / continuation

This handoff is sufficient to continue the VerFi candidate lane without chat history. The lane must not be promoted beyond `TEST_CANDIDATE` until exact-current-main validation succeeds and an actual external VerFi artifact becomes available for independent reconstruction testing.
