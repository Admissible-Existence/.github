# Admissible-Existence Formalism Mirror Handoff

**Status:** ACTIVE — authoritative coordination source

**Last updated:** 2026-07-30

**Repository Coordination Authority worker:** `AEX-COORD-20260728-01`

## Authority

This handoff is the singular source of truth for assignments, accepted percentages, cross-repository ownership, archive transfer, and publication routing across Admissible-Existence formalisms.

## Required controls

Every execution session must read and maintain `NEXT_EXECUTION_SESSION_PROMPT.md` and `HANDOFF_COMPLETENESS_STANDARD.md`. Repository handoffs must preserve material history, corrected assumptions, evidence, ownership boundaries, blockers, exact identifiers, percentages, and next actions.

## Program goal

**Goal ID:** `AEX-FORMALISM-PUBLICATION-ACTIVATION-001`

`Existence / AE → RTG → GTG → TT → validator → Publisher / Site → admissibility-wiki`

## Ownership

- Existence owns governed `%Existence` review standing and RC1 proof surface.
- AE owns the Admissible Resolution Function and commit-time determination.
- RTG owns relational-transition geometry and geometric derivation inputs.
- TT consumes AE output and operationalizes discrete allocation.
- validator evaluates standing without owning source formalisms or creating execution authority.
- ae-validation-factory discovers targets, selects profiles, invokes validator, and deposits reports.
- Master-Records preserves receipt identity, hash, custody, and standing history.

## Worker inventory

| Worker ID | Assignment | Status | Task % | Developed-files % | Goal activation % | Source-session dependency |
|---|---|---|---:|---:|---:|---|
| `AEX-COORD-20260728-01` | Coordination control plane and archive enforcement | COMPLETE / ARCHIVE_READY | 100% | 100% | 100% | false |
| `AEX-INV-20260729-01` | RTG manuscript, operational corpus, crosswalk, and publication inventory | ACTIVE / ACKNOWLEDGED | 86% | 83% | 64% | false |
| `AEX-ROUTE-20260729-01` | Canonical ownership reconciliation and propagation | COMPLETE | 100% | 100% | 96% | false |
| `AEX-EXIST-20260729-01` | Existence RC1 surfaces and hosted evidence | COMPLETE / ARCHIVE_READY | 100% | 100% | 100% | false |
| `AEX-VALID-20260729-01` | Validator contracts, receipts, custody, and supersession | COMPLETE / ARCHIVE_READY | 100% | 100% | 100% | false |
| `SITE-FORMALISM-UNASSIGNED` | Online/downloadable formalism publication | BLOCKED | 10% | 5% | 0% | n/a |

## Corrected RTG provenance

The RTG publication family is one Volume I consolidated as `Foundations-of-RTG-Volume-I-Integrated-v0.9.0`. The separate I–XV series belongs to the Standing Research Companion. The repository manifest remains the operational canonical corpus; the manuscript remains a recovered publication candidate.

Verified hashes:

- Markdown `8d9d0eb0f52ef3313cebe5121e24db6ac8b1a1947fec17d06b1a9e6dc907e13a`
- DOCX `27b569ad0e87779fc062ccfb71e5b606ebb3331e6c612c57a384cb6049e4cb83`
- PDF `ac4b3353b199c5ddeebc33981c33db80fdd88f1eb8898e3986333ec8a6f1eb91`

## 2026-07-30 RTG progress

The recovered Markdown was materialized from persistent library file `file_000000004ffc81f5ad2de4eec3845789`; its hash, 180,709-byte size, and 3,667-line count were independently verified.

A noncanonical review package was created in `Admissible-Existence/RTG`:

- review index commit `1f651ca4fcdf0cc39d981fbe9bcce43ff750f060`
- machine crosswalk commit `6f55ae81ee84b5da233d8e31607a9c59be90217d`
- human crosswalk commit `17aeb1b2764e6ec5dd828dd3db8afdd69286def5`
- structural validator commit `709d008a602af891282b5327a617a5bc45bc88f2`
- RTG handoff update commit `cbbc73187d9e7859767938e2fc2353523db25c9b`
- archive registry update commit `67fdbbe980605f0ce4b2a221117e0a9bea22ed5c`, version `1.0.5`

The exact manuscript bytes are not yet deposited because the session's GitHub contents connector did not accept a local file reference. This is recorded as a transport blocker; `repository_deposit_verified` remains false.

## Crosswalk and readiness

The initial crosswalk covers manifest terms plus definitions, theorems, symbols, schemas, fixtures, tools, and non-claims. It records normative, explanatory, experimental, duplicate, superseded, and unresolved classifications.

Primary divergences are: AE ownership overlap in manuscript admissibility material; missing manifest-verified implementations for manuscript-referenced schemas and research tooling; pending exact source deposit; and unresolved predecessor supersession.

**Consolidated specification readiness: NOT READY.** No canonicalization, release, route, or publication claim is admitted.

## Archive gate

Valid sequence: `NOT_TRANSFERRED → ASSIGNED → ACKNOWLEDGED → ARCHIVE_READY`.

`data/formalism-archive-transfer-registry.json` version `1.0.5` records coordination, Existence, and validator workers archive-ready; RTG remains acknowledged at 86%.

## Highest-value next work

1. Deposit exact recovered Markdown bytes at the review path and verify repository hash.
2. Add hosted crosswalk validation and observe terminal run/job identifiers.
3. Expand statement-level and artifact-level crosswalk coverage.
4. Resolve RTG/AE ownership divergence and predecessor supersession.
5. Recover or explicitly mark absent implementations.
6. Issue revised consolidated-specification readiness decision.
7. Bind reproducible DOCX/PDF only after accepted source establishment.
8. Route through validator and Factory only with commit-bound evidence.
9. Do not modify Site until the Site orchestrator admits the work.

Site publication remains blocked by `StegVerse-Labs/Site/docs/SITE_MIRROR_HANDOFF.md` and its active orchestration sequence.
