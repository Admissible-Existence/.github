# Admissible-Existence Formalism Mirror Handoff

**Status:** ACTIVE — authoritative coordination source

**Last updated:** 2026-07-30

**Repository Coordination Authority worker:** `AEX-COORD-20260728-01`

## 1. Authority

This handoff is the singular source of truth for assignments, accepted percentages, cross-repository ownership, archive transfer, and publication routing across Admissible-Existence formalisms.

## 2. Cross-session execution controls

Every substantive execution session must read and maintain:

```text
Admissible-Existence/.github/NEXT_EXECUTION_SESSION_PROMPT.md
Admissible-Existence/.github/HANDOFF_COMPLETENESS_STANDARD.md
```

The next-session prompt must be updated whenever the highest-value task, required reading order, authoritative paths, blockers, or execution sequence changes. Every user-facing substantive progress response must end with the complete paste-ready next-session prompt.

Repository handoffs must preserve all material history, corrections, current evidence, current goals, end goals, ownership boundaries, blockers, exact identifiers, completion accounting, and next executable steps required to continue without archived chat context.

## 3. Current integration goal

**Goal ID:** `AEX-FORMALISM-PUBLICATION-ACTIVATION-001`

`Existence / AE → RTG → GTG → TT → validator → Publisher / Site → admissibility-wiki`

## 4. Canonical ownership

- Existence owns governed `%Existence` review standing and its RC1 proof surface.
- AE owns the Admissible Resolution Function and commit-time admissibility-resolution contract.
- RTG owns relational-transition geometry and geometric derivation inputs.
- TT consumes the AE result and operationalizes discrete allocation.
- validation-profile-registry owns reusable declarative profiles.
- validator evaluates standing without owning source formalisms or creating execution authority.
- ae-validation-factory discovers targets, selects profiles, invokes validator, and deposits reports.
- Master-Records preserves receipt identity, hash, custody, and standing history.

## 5. Worker inventory

| Worker ID | Assignment | Status | Task % | Developed-files % | Goal activation % | Source-session dependency |
|---|---|---|---:|---:|---:|---|
| `AEX-COORD-20260728-01` | Coordination control plane and archive enforcement | COMPLETE / ARCHIVE_READY | 100% | 100% | 100% | false |
| `AEX-INV-20260729-01` | RTG manuscript, operational corpus, and publication inventory | ACTIVE | 82% | 78% | 58% | false |
| `AEX-ROUTE-20260729-01` | Canonical ownership reconciliation and propagation | COMPLETE | 100% | 100% | 96% | false |
| `AEX-EXIST-20260729-01` | Existence RC1 surfaces, hosted checks, artifacts, and authority boundary | COMPLETE / ARCHIVE_READY | 100% | 100% | 100% | false |
| `AEX-VALID-20260729-01` | Validator surfaces, hosted behavior, receipt, integration, custody, and supersession contracts | COMPLETE / ARCHIVE_READY | 100% | 100% | 100% | false |
| `SITE-FORMALISM-UNASSIGNED` | Complete online/downloadable formalism publication | BLOCKED | 10% | 5% | 0% | n/a |

## 6. Corrected RTG publication provenance

Persistent-library recovery established that the RTG publication family is one Volume I developed through part releases and consolidated as:

```text
Foundations-of-RTG-Volume-I-Integrated-v0.9.0
```

Recovered integrated format hashes:

```text
Markdown  8d9d0eb0f52ef3313cebe5121e24db6ac8b1a1947fec17d06b1a9e6dc907e13a
DOCX      27b569ad0e87779fc062ccfb71e5b606ebb3331e6c612c57a384cb6049e4cb83
PDF       ac4b3353b199c5ddeebc33981c33db80fdd88f1eb8898e3986333ec8a6f1eb91
```

The separately observed Volume I–XV sequence belongs to `Standing Research Companion`, not RTG. The prior fifteen-volume RTG assumption is rejected and must not be used in corpus-completeness or publication claims.

Durable records:

```text
Admissible-Existence/RTG/docs/RTG_LIBRARY_ARTIFACT_RECOVERY.md
Admissible-Existence/RTG/docs/RTG_VOLUME_PROVENANCE_MATRIX.md
Admissible-Existence/RTG/docs/RTG_CORPUS_INVENTORY_STATUS.md
Admissible-Existence/RTG/docs/RTG_MIRROR_HANDOFF.md
```

The repository manifest remains the operational canonical corpus. The integrated manuscript is a recovered publication candidate pending repository deposit, crosswalk, validation, and acceptance.

## 7. Completed Existence and validator layers

Existence RC1 verification and validator control-plane tasks are complete and archive-ready, with hosted evidence and durable receipts or contracts.

## 8. Archive-transfer gate

Valid sequence:

`NOT_TRANSFERRED → ASSIGNED → ACKNOWLEDGED → ARCHIVE_READY`

Machine-verifiable sources:

```text
data/formalism-archive-transfer-registry.json
tools/check_formalism_archive_gate.py
.github/workflows/formalism-archive-gate.yml
```

The registry records coordination, Existence, and validator workers at 100% and `ARCHIVE_READY`; RTG inventory remains active at 82% and `ACKNOWLEDGED`.

## 9. Active program work

1. Deposit or reconstruct the recovered integrated RTG Markdown manuscript in a reviewable repository path.
2. Build definition, theorem, symbol, schema, and fixture crosswalks against the manifest corpus.
3. Classify normative, explanatory, experimental, duplicate, and superseded content.
4. Resolve manuscript-to-manifest divergence and produce consolidated-specification readiness decision.
5. Bind reproducible DOCX/PDF generation to the accepted Markdown source.
6. Obtain validator acceptance.
7. Obtain Site orchestrator admission.
8. Publish complete online and downloadable editions.
9. Obtain Publisher, admissibility-wiki, and stegguardian-wiki destination receipts.

No Site mutation may bypass `StegVerse-Labs/Site/docs/SITE_MIRROR_HANDOFF.md` or its orchestrator.

## 10. Completion model

Coordination, Existence RC1 verification, and validator tasks are complete. The largest remaining technical dependency is no longer locating fifteen RTG volumes; it is integrating and crosswalking the recovered v0.9.0 manuscript against the canonical operational corpus.

Program-wide formalism-publication activation remains incomplete because consolidation, validation, Site admission, and destination receipts remain open.

## 11. Transfer confirmation

Repository Coordination Authority has registered worker `AEX-INV-20260729-01`, assigned task `AEX-INV-001`, recorded `82%` completion, and updated the RTG handoff, library recovery record, provenance matrix, corpus inventory, archive-transfer registry, reusable execution prompt, handoff completeness standard, and this central ledger. Worker `AEX-INV-20260729-01` no longer references the originating session; those repository records are authoritative for continuation.
