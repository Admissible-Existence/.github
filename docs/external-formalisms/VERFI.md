# VerFi External Formalism Candidate

## Status

`BOUNDARY_REVIEW / TEST_CANDIDATE`

This record registers VerFi as an external formalism candidate for bounded comparison and interoperability testing. It does **not** treat VerFi as canonical StegVerse mathematics, does not grant execution or admissibility authority, and does not imply endorsement, integration, or independent validation of VerFi's product claims.

## External formalism family

Human consent / cognitive authorization evidence.

Publicly represented sequence under review:

```text
IDENTITY
  -> DISCLOSURE
  -> COMPREHENSION
  -> AUTHORIZATION
  -> SIGNATURE
  -> EVIDENCE
```

The comparison target is specifically the transition-evidence claim that a consent or authorization record can preserve evidence about what was shown, what was asked, what was answered, and how those observations relate to an eventual authorization/signature act.

## Public source grounding — 2026-08-23

The candidate is now grounded in public VerFi Systems product representations rather than only a conversational paraphrase. Public pages state that a VerFi execution record is generated within a single controlled execution session and records session continuity, identity-bound attribution, education delivery, recorded comprehension interaction/responses, and timestamped authorization enablement. VerFi also publicly states that each record is bound to one procedure, one session and one identified party.

The public product description further states that:

```text
comprehension checkpoints are required before consent finalization
missed checkpoints re-present the term and preserve the correction
exact disclosure version shown is recorded
session evidence is sealed at close as a tamper-evident package
an Execution Verified Token is issued after required checkpoints complete
```

These are **publisher assertions**, not independently verified implementation facts. No production consent record, schema, API output, Execution Verified Token specimen or cryptographic package has yet been supplied to this repository.

Publicly declared record exclusions are also material to the comparison boundary: VerFi states that its consent record excludes diagnoses/clinical notes/lab results, clinical decision support/scoring, legal or clinical determinations, and treatment decisions/approvals/billing.

Source pages observed:

- `https://verfisystems.com/`
- `https://verfisystems.com/consent-records`

## StegVerse boundary

StegVerse does not equate a completed signature ceremony with proof of comprehension, authority, admissibility, or execution legitimacy.

The candidate mapping is:

```text
VerFi-like evidence producer
  -> human-transition evidence package
  -> StegVerse governance lane
  -> transition distinguishability evaluation
  -> evidence sufficiency evaluation
  -> ordering / continuity evaluation
  -> authority / admissibility evaluation
  -> governed successor state
```

A VerFi package may therefore contribute evidence to a StegVerse decision, but it cannot by itself create:

- StegVerse canonicality;
- AE admissibility authority;
- execution authority;
- release or publication authority;
- proof that an internal mental state occurred;
- proof that the requested effect was authorized or realized.

The publicly named `Execution Verified Token` is treated as an external evidence/control artifact only. Even if a future specimen validates exactly as VerFi describes, it does not become StegVerse execution or admissibility authority merely because of its name or external effect.

`Admissible-Existence/AE` remains the commit-time admissibility resolver.

## Minimum-information rule

Testing follows the rule:

> Do not require more information to establish a transition than is necessary to distinguish the transition being claimed.

Accordingly, the governed target is not "prove the person's mind." The target is whether available evidence is sufficient to distinguish relevant transitions such as:

```text
COMPREHENSION_NOT_ESTABLISHED -> COMPREHENSION_ESTABLISHED
AUTHORIZATION_NOT_ESTABLISHED -> AUTHORIZATION_ESTABLISHED
CHECKPOINT_FAILED -> TERM_REPRESENTED -> CORRECTION_PRESERVED
AUTHORIZATION_DISABLED -> AUTHORIZATION_ENABLED
```

or to preserve a valid non-authorization successor state when the evidence is insufficient.

## Required governance-lane cases

The deterministic candidate suite covers:

1. `CLEAN_SEQUENCE` — disclosure, comprehension evidence, authorization, signature and evidence integrity are present in order.
2. `COMPREHENSION_MISSING` — disclosure and signature exist but comprehension is not established.
3. `DISCLOSURE_DRIFT` — signed/authorized content differs from the content presented for comprehension.
4. `AUTHORIZATION_LAPSED` — comprehension evidence exists but authorization is not valid at commit.
5. `EVIDENCE_TAMPER` — evidence integrity fails.
6. `TEMPORAL_DISORDER` — authorization/signature evidence precedes required disclosure/comprehension evidence.
7. `AMBIGUOUS_COMPREHENSION` — evidence shows acknowledgement but does not distinguish comprehension.
8. `OVER_COLLECTION` — the package contains information beyond the minimum needed for the claimed transition; governance must preserve the transition result while flagging minimization failure.
9. `INDEPENDENT_RECONSTRUCTION` — a verifier can reconstruct the same claimed sequence and bounded result from the sealed evidence package.
10. `HUMAN_MACHINE_SYMMETRY` — compare the human transition sequence with a governed machine-decision sequence without equating human cognition and machine state.

The newly public checkpoint/correction semantics create two explicit future artifact tests once a real VerFi record is available:

```text
CHECKPOINT_CORRECTION_PRESERVATION
AUTHORIZATION_ENABLEMENT_CAUSALITY
```

The first must establish whether an incorrect response, re-presentation and correction remain reconstructable as ordered evidence. The second must establish whether authorization enablement is cryptographically/structurally bound to completion of required prior checkpoints rather than merely reported afterward.

## Mandatory negative invariant

A conforming external-formalism test surface MUST permit this outcome:

```text
DISCLOSURE_ESTABLISHED
  -> COMPREHENSION_NOT_ESTABLISHED
  -> AUTHORIZATION_INADMISSIBLE
```

A system that forces every completed ceremony into `COMPREHENSION_ESTABLISHED` is not accepted as transition-evidence proof merely because a signature was produced.

## Human / machine comparison lane

The comparison is structural, not ontological:

```text
Human:
DISCLOSURE -> COMPREHENSION_EVIDENCE -> AUTHORIZATION -> SIGNATURE/COMMIT

Machine:
INPUT -> INTERPRETATION_STATE -> ADMISSIBILITY -> AUTHORITY -> DECISION -> COMMIT
```

The lane asks whether both sequences can be represented using a common transition vocabulary while retaining distinct evidence requirements and authority semantics.

## Authority and claim discipline

Validation of this candidate only establishes that the candidate declaration and deterministic fixtures conform to their stated StegVerse boundary. It does not validate VerFi's implementation, legal sufficiency, cognitive-science claims, evidentiary admissibility in any jurisdiction, or production evidence envelopes.

A future integration may advance beyond `TEST_CANDIDATE` only after an actual VerFi consent/execution record, evidence envelope, schema, API output, Execution Verified Token specimen, or equivalent sufficiently precise implementation artifact is available for independent reconstruction and negative testing.
