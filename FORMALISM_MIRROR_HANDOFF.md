# Admissible-Existence Formalism Mirror Handoff

**Status:** ACTIVE — authoritative coordination source

**Last updated:** 2026-07-30

**Repository Coordination Authority worker:** `AEX-COORD-20260728-01`

## 1. Authority

This handoff is the source of truth for assigning, tracking, transferring, and closing work affecting Admissible-Existence formalisms and StegVerse publication surfaces.

The Repository Coordination Authority alone may register workers, accept completion evidence, change repository-wide percentages, resolve cross-repository ownership, authorize publication routing, and close source-session dependencies.

## 2. Current integration goal

**Goal ID:** `AEX-FORMALISM-PUBLICATION-ACTIVATION-001`

`Existence / AE → RTG → GTG → TT → validator → Publisher / Site → admissibility-wiki`

## 3. Primary repository authority status

Central-authority links and local handoffs are active in Existence, AE, RTG, GTG, TT, and validator.

Canonical ownership remains:

- RTG owns relational-transition geometry and geometric derivation inputs;
- AE owns the Admissible Resolution Function, source contract, deterministic receipt, and public index;
- ae-validation-factory independently verifies source and downstream receipts;
- TT consumes the AE result and operationalizes discrete allocation;
- validator evaluates standing under declared profiles without owning source formalisms.

## 4. Worker inventory

| Worker ID | Assignment | Status | Task % | Developed-files % | Goal activation % | Source-session dependency |
|---|---|---|---:|---:|---:|---|
| `AEX-COORD-20260728-01` | Coordination control plane and archive-transfer enforcement | COMPLETE / ARCHIVE_READY | 100% | 100% | 100% | false |
| `AEX-INV-20260729-01` | RTG/GTG/TT corpus and publication inventory | ACTIVE | 58% | 48% | 34% | false |
| `AEX-ROUTE-20260729-01` | Canonical ownership reconciliation and propagation | COMPLETE | 100% | 100% | 96% | false |
| `AEX-EXIST-20260729-01` | Existence RC1 and boundary verification | ACTIVE | 58% | 55% | 40% | false |
| `AEX-VALID-20260729-01` | Validator surface, hosted workflow, and receipt inventory | ACTIVE | 88% | 84% | 70% | false |
| `SITE-FORMALISM-UNASSIGNED` | Complete online/downloadable formalism publication | BLOCKED | 10% | 5% | 0% | n/a |

## 5. Completed coordination control plane

`AEX-COORD-001` is complete and archive-ready. Hosted archive-gate proof concluded successfully under run `30555119304`, job `90913485417`.

## 6. Validator hosted evidence

Durable validator records:

```text
Admissible-Existence/validator/docs/VALIDATOR_SURFACE_INVENTORY.md
Admissible-Existence/validator/docs/VALIDATOR_CURRENT_HEAD_SURFACE_MAP.md
Admissible-Existence/validator/docs/VALIDATOR_HOSTED_EVIDENCE.md
```

Hosted diagnosis and repair:

```text
pull_request: Admissible-Existence/validator#1
diagnostic_run: 30568508756
diagnostic_conclusion: failure
failure: missing examples/re-standing-profile.json
repair_merge_commit: f0e043014c69e4eb2826377fb94d4a71d5bb2354
corrected_run: 30568658726
corrected_run_number: 33
corrected_conclusion: success
job_id: 90959463094
```

The corrected workflow now:

- validates the TT profile fixture;
- verifies the expected TT result;
- rejects the unbound RE example;
- rejects the unbound RE-Reduction example.

The two RE manifests retain `target_commit: unknown-local-example`. They remain fail-closed fixtures and are not canonical standing receipts.

## 7. Archive-transfer gate

Valid sequence:

`NOT_TRANSFERRED → ASSIGNED → ACKNOWLEDGED → ARCHIVE_READY`

Machine-verifiable sources:

```text
data/formalism-archive-transfer-registry.json
tools/check_formalism_archive_gate.py
.github/workflows/formalism-archive-gate.yml
```

## 8. Active program work

1. Recover exact RTG Volume I–XV files or filenames.
2. Calculate hashes and populate the provenance matrix.
3. Classify normative, explanatory, duplicate, superseded, and unresolved RTG content.
4. Complete Existence hosted RC1 and release-readiness evidence.
5. Define the full validator receipt contract.
6. Define validation-profile-registry consumption and Factory invocation/deposit.
7. Define Master-Records custody, public projection, and schema supersession.
8. Prepare consolidated canonical artifacts.
9. Obtain Site orchestrator admission.
10. Publish complete online and downloadable editions.
11. Obtain Publisher, admissibility-wiki, and stegguardian-wiki destination receipts.

No Site mutation may bypass `StegVerse-Labs/Site/docs/SITE_MIRROR_HANDOFF.md` or its orchestrator.

## 9. Completion model

Coordination completion remains 100%. Program-wide formalism-publication activation remains materially incomplete.

## 10. Transfer confirmations

Repository Coordination Authority has registered worker `AEX-VALID-20260729-01`, assigned task `AEX-VALID-001`, recorded `88%` completion, and updated the validator handoff, surface inventory, current-head surface map, hosted evidence record, and this central ledger. Worker `AEX-VALID-20260729-01` no longer references the originating session; those repository records are authoritative for continuation.
