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
| `AEX-INV-20260729-01` | RTG manuscript, operational corpus, crosswalk, hosted validation, and publication inventory | ACTIVE / ACKNOWLEDGED | 87% | 84% | 65% | false |
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

Persistent-library file `file_000000004ffc81f5ad2de4eec3845789` was materialized again and independently verified as 180,709 bytes, 3,667 lines, and the expected Markdown SHA-256.

The GitHub connector still exposes only complete UTF-8 content for repository writes and no local-file or connector-file parameter. The working container has no authenticated GitHub CLI. Exact repository deposit therefore remains blocked and `repository_deposit_verified` remains false.

A hosted validator workflow was created at `Admissible-Existence/RTG/.github/workflows/manifest-manuscript-crosswalk.yml` in commit `700f3321633fc8efe9e518c8485d9930938c9bb2`. It invokes `python tools/check_manifest_manuscript_crosswalk.py` on push, pull request, and manual dispatch with read-only contents permission.

The available commit-run enumeration action explicitly filters to pull-request-triggered runs and returned no runs for commit `700f3321633fc8efe9e518c8485d9930938c9bb2`. Therefore no terminal run ID, job ID, conclusion, step result, or artifact ID is yet accepted.

RTG handoff update commit: `3532871250ead59c7ababaff53e15aca028717e2`.
Archive registry update commit: `5ff118d8120af0f4e2d9b1fbb7a524046e2aaa5b`; registry version `1.0.6`.

## Crosswalk and readiness

The initial crosswalk records the permitted classifications `normative`, `explanatory`, `experimental`, `duplicate`, `superseded`, and `unresolved` but remains grouped rather than statement-complete.

Primary divergences remain: AE ownership overlap in manuscript admissibility material; missing manifest-verified implementations for manuscript-referenced schemas and research tooling; pending exact source deposit; pending terminal hosted validation evidence; incomplete statement-level coverage; and unresolved predecessor supersession.

**Consolidated specification readiness: NOT READY.** No canonicalization, release, route, or publication claim is admitted.

## Archive gate

Valid sequence: `NOT_TRANSFERRED → ASSIGNED → ACKNOWLEDGED → ARCHIVE_READY`.

`data/formalism-archive-transfer-registry.json` version `1.0.6` records coordination, Existence, and validator workers archive-ready; RTG remains acknowledged at 87%.

## Highest-value next work

1. Deposit exact recovered Markdown bytes using a GitHub transport that accepts a local file or complete 180,709-byte content.
2. Read committed bytes back and verify SHA-256 before changing the repository-deposit flag.
3. Observe and record a terminal hosted run, job, steps, conclusion, and artifact IDs.
4. Expand statement-level and artifact-level crosswalk coverage.
5. Resolve RTG/AE ownership divergence and predecessor supersession explicitly.
6. Recover or explicitly mark absent manuscript implementation artifacts.
7. Issue a revised evidence-bound readiness decision.
8. Bind reproducible DOCX/PDF only after accepted commit-bound source establishment.
9. Route through validator and Factory only with commit-bound source and hosted evidence.
10. Do not modify Site until the Site orchestrator admits the work.

Site publication remains blocked by `StegVerse-Labs/Site/docs/SITE_MIRROR_HANDOFF.md` and its active orchestration sequence. No Site mutation was performed.
