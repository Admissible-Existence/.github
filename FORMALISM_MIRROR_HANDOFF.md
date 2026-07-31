# Admissible-Existence Formalism Mirror Handoff

**Status:** ACTIVE — authoritative coordination source

**Last updated:** 2026-07-30

**Repository Coordination Authority worker:** `AEX-COORD-20260728-01`

## Authority

This handoff is the singular source of truth for assignments, accepted percentages, cross-repository ownership, archive transfer, and publication routing across Admissible-Existence formalisms.

Every execution session must read and maintain `NEXT_EXECUTION_SESSION_PROMPT.md` and `HANDOFF_COMPLETENESS_STANDARD.md`.

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
| `AEX-INV-20260729-01` | RTG manuscript, operational corpus, crosswalk, hosted validation, and publication inventory | ACTIVE / ACKNOWLEDGED | 88% | 85% | 66% | false |
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

The persistent Library Markdown was materialized and independently reverified in the current session as 180,709 bytes, 3,667 lines, and the expected SHA-256. Exact repository deposit remains false because the connected GitHub writer exposes complete UTF-8 text but no safe local-file or connector-file transport.

## 2026-07-30 RTG progress

A machine-readable statement inventory was added at `Admissible-Existence/RTG/review/volume-I-integrated-v0.9.0/crosswalk/rtg-statement-inventory.json` in commit `0adfd46312fd33333b8439ae5e8a40a359c51492`.

It enumerates all 131 stable statement identifiers in the recovered manuscript: 67 definitions, 10 axioms, 48 theorems, and 6 hypotheses. Definitions, axioms, and theorems remain `normative_or_unresolved` until item-level classification, manifest mapping, proof/implementation posture, predecessor comparison, and AE/RTG ownership reconciliation are recorded. Hypotheses are experimental.

RTG handoff update commit: `fa54e2ed24cf58f54ec158960285edc3687886e4`.
Archive registry update commit: `d8a178331667d374ea4be25ebc04d137be460b46`; registry version `1.0.7`.

The hosted workflow remains defined at `Admissible-Existence/RTG/.github/workflows/manifest-manuscript-crosswalk.yml`, creation commit `700f3321633fc8efe9e518c8485d9930938c9bb2`. The available commit-run enumeration action still filters to pull-request-triggered runs, so no terminal push-run ID, job ID, conclusion, step result, or artifact ID is accepted.

A connected GitHub search did not locate the manuscript-referenced Lean, TLA+, schema, Experiment 1, claims-register, falsification-register, or independent-digest artifacts. This is recorded as unresolved, not as proof of historical absence.

## Crosswalk and readiness

Identifier enumeration is complete, but statement-level classification and mapping are not. Primary divergences remain AE ownership overlap in manuscript admissibility material; missing manifest-verified implementations; pending exact source deposit; pending terminal hosted validation evidence; incomplete notation and symbol audit; incomplete claims/non-claims and artifact crosswalk; and unresolved predecessor supersession.

**Consolidated specification readiness: NOT READY.** No canonicalization, release, route, or publication claim is admitted.

## Archive gate

Valid sequence: `NOT_TRANSFERRED → ASSIGNED → ACKNOWLEDGED → ARCHIVE_READY`.

`data/formalism-archive-transfer-registry.json` version `1.0.7` records RTG at 88%, acknowledged, source-session dependency false.

## Highest-value next work

1. Deposit exact recovered Markdown bytes using a GitHub transport that accepts a local or connector file.
2. Read committed bytes back and verify SHA-256 before changing the repository-deposit flag.
3. Observe and record a terminal hosted run, job, steps, conclusion, and artifact IDs.
4. Expand the 131-item inventory with exact title, manuscript line, manifest counterpart, classification, proof status, implementation status, and ownership posture.
5. Resolve RTG/AE ownership divergence and predecessor supersession item by item.
6. Recover or explicitly mark absent manuscript implementation artifacts through Git history and Library evidence.
7. Issue a revised evidence-bound readiness decision.
8. Bind reproducible DOCX/PDF only after accepted commit-bound source establishment.
9. Route through validator and Factory only with commit-bound source and terminal hosted evidence.
10. Do not modify Site until the Site orchestrator admits the work.

Site publication remains blocked by `StegVerse-Labs/Site/docs/SITE_MIRROR_HANDOFF.md` and its active orchestration sequence. No Site mutation was performed.
