# Admissible-Existence Formalism Mirror Handoff

**Status:** ACTIVE — authoritative coordination source

**Last updated:** 2026-07-29

**Repository Coordination Authority worker:** `AEX-COORD-20260728-01`

## 1. Authority

This handoff is the source of truth for assigning, tracking, transferring, and closing work that affects Admissible-Existence formalisms and their StegVerse publication surfaces.

The Repository Coordination Authority is the singular session permitted to:

- maintain contact with the governed repositories;
- register workers and assignments;
- declare canonical ownership and destination paths;
- accept completion evidence and update percentages;
- authorize publication or mirroring to Site;
- confirm that an originating session no longer remains a source dependency;
- move the program to the next integration goal.

Worker sessions may implement bounded assignments, but they may not independently change repository-wide completion, canonical ownership, volume numbering, publication authority, or program goals.

## 2. Current integration goal

**Goal ID:** `AEX-FORMALISM-PUBLICATION-ACTIVATION-001`

Establish a collision-resistant path from findings and formal development into canonical repositories, consolidated specifications, validation, and public Site publication.

Current governing sequence:

`Existence / AE → RTG → GTG → TT → validator → Publisher / Site → admissibility-wiki`

## 3. Current repository inventory

| Organization / Repository | Intended role | Current verified status | Canonical handoff status |
|---|---|---|---|
| `Admissible-Existence/Existence` | Existence formalism | Existing | Repo-specific handoff not yet verified |
| `Admissible-Existence/AE` | Admissible Existence formalism | Existing | Repo-specific handoff not yet verified |
| `Admissible-Existence/RTG` | Relational Transition Geometry | Existing; README defines role and build goal | `docs/RTG_MIRROR_HANDOFF.md` installed 2026-07-29 |
| `Admissible-Existence/GTG` | Generalized Transition Governance | Existing; seven-volume formal draft and validation surface present | `docs/GTG_MIRROR_HANDOFF.md` verified |
| `Admissible-Existence/TT` | Transition Table formalism | Existing; strict resolution chain and user-facing RTG-TT test interface present | `docs/TT_MIRROR_HANDOFF.md` verified |
| `Admissible-Existence/validator` | Formalism validation/invalidation | Existing | Repo-specific handoff not yet verified |
| `GCAT-BCAT-Engine/Publisher` | Publication projection | External dependency | Destination awareness exists for TT; formalism publication path requires verification |
| `StegVerse-Labs/Site` | Public rendered and downloadable surface | Existing | RTG/GTG/TT complete-document paths not yet verified; TT state is NOT_ADMITTED |
| `StegVerse-Labs/admissibility-wiki` | Public evidence and determination surface | Existing external dependency | TT bounded receipt reported installed; public determination unauthorized |
| `StegVerse-002/stegguardian-wiki` | Guardian/governance public surface | Existing external dependency | TT dependency blocked |

## 4. Worker inventory

| Worker ID | Assignment | Destination | Status | Task % | Developed-files % | Goal activation % | Source-session dependency |
|---|---|---|---|---:|---:|---:|---|
| `AEX-COORD-20260728-01` | Maintain formalism coordination, worker ledger, archive transfer gate, and repository inventory | `Admissible-Existence/.github` | ACTIVE | 75% | 70% | 40% | false |
| `AEX-INV-20260729-01` | Inventory and reconcile RTG, GTG, and TT corpus, handoffs, publication surfaces, and ownership | RTG / GTG / TT / Site | ACTIVE | 35% | 30% | 20% | false |
| `AEX-ROUTE-20260729-01` | Confirm canonical ownership now that dedicated RTG, GTG, and TT repos are visible | `Admissible-Existence/.github` | ACTIVE | 70% | 70% | 60% | false |
| `SITE-FORMALISM-UNASSIGNED` | Build verified online and downloadable formalism publication paths | `StegVerse-Labs/Site` | BLOCKED | 0% | 0% | 0% | n/a |

## 5. Task ledger

### `AEX-COORD-001` — Coordination control plane

- **Worker:** `AEX-COORD-20260728-01`
- **Status:** ACTIVE
- **Completion:** 75%
- **Completed:**
  - singular coordination authority declared;
  - central worker inventory and task ledger established;
  - archive transfer and source-session independence rules established;
  - dedicated RTG, GTG, and TT repositories located;
  - GTG and TT handoffs verified;
  - RTG repo-specific handoff installed;
  - inventory worker assigned.
- **Remaining:**
  - verify AE, Existence, and validator handoffs;
  - import any active workers from other sessions;
  - create machine-verifiable archive-gate validation;
  - propagate central-authority links into all governed repositories.

### `AEX-INV-001` — Formalism corpus inventory

- **Worker:** `AEX-INV-20260729-01`
- **Status:** ACTIVE
- **Completion:** 35%
- **Scope:** Locate and classify all RTG, GTG, and TT files, including volumes, consolidated drafts, schemas, examples, tests, PDFs, Site pages, and superseded copies.
- **Verified findings:**
  - RTG dedicated repository exists and identifies its mathematical role, but its complete volume and publication inventory remains unresolved;
  - GTG has a canonical seven-volume set, contracts, schemas, fixtures, validators, tests, and a formal-draft-complete posture;
  - TT has a large exploratory README plus a strict AE/Factory/TT receipt chain, transition elements T-060 through T-065, hosted validation evidence, and a user-facing RTG-TT test interface;
  - GTG is not release-ready or independently verified;
  - TT is not release-, tag-, publication-, execution-, or certification-authorized and remains blocked on destination admission;
  - complete public RTG/GTG/TT document and download paths on Site are not yet verified.
- **Required outputs remaining:**
  - complete RTG Volumes I–XV provenance map;
  - repository file inventories for RTG, GTG, and TT;
  - duplicate/conflict and missing-file reports;
  - consolidated-specification readiness report;
  - Site path and download verification report.

### `AEX-ROUTE-001` — Canonical repository decision

- **Worker:** `AEX-ROUTE-20260729-01`
- **Status:** ACTIVE — provisional decision established
- **Completion:** 70%
- **Current decision:**
  - `Admissible-Existence/RTG` is the canonical RTG owner;
  - `Admissible-Existence/GTG` is the canonical GTG owner;
  - `Admissible-Existence/TT` is the canonical TT owner.
- **Remaining:**
  - reconcile RTG handoff ownership language with AE references;
  - reconcile TT statements that place some RTG ownership in AE;
  - confirm which repository owns consolidated cross-formalism publication manifests;
  - record explicit supersession/provenance rules.

### `AEX-PUBLISH-001` — Public formalism publication

- **Worker:** UNASSIGNED
- **Status:** BLOCKED BY `AEX-INV-001` and final `AEX-ROUTE-001` reconciliation
- **Completion:** 0%
- **Scope:** Publish complete online documents and downloadable releases to Site with canonical repository, version, status, provenance, supersession, validation, and non-authority links.

## 6. Finding intake rule

A LinkedIn post, external discussion, experiment, or session insight must not automatically become a new long-running implementation session.

The originating session records the finding, affected concepts, destination, requested task, evidence, urgency, and dependencies. The Repository Coordination Authority then registers the worker and assignment here or in the destination handoff.

## 7. Archive transfer gate

Valid state sequence:

`NOT_TRANSFERRED → ASSIGNED → ACKNOWLEDGED → ARCHIVE_READY`

Every archive transfer must identify the task, destination, handoff, worker, completion baseline, acknowledgment, and source-session independence.

Required confirmation line:

> Repository Coordination Authority has registered worker `<WORKER-ID>`, assigned task `<TASK-ID>`, recorded `<PERCENT>%` completion, and updated `<HANDOFF-PATH>`. Worker `<WORKER-ID>` no longer references the originating session; the handoff is now the authoritative source for continuation.

A session may use `READY FOR ARCHIVE` only after that statement is factually true.

## 8. Completion model

Three percentages remain separate:

1. **Task completion** — accepted deliverables divided by required assigned deliverables.
2. **Developed-files completion** — substantive required files divided by all required files; scaffolding and stubs do not count as developed.
3. **Goal activation completion** — accepted activation conditions divided by all conditions required for operational use.

Workers may propose values. Only the Repository Coordination Authority accepts repository-wide or program-wide values.

## 9. Release and propagation rule

At release/tag readiness, the coordinator must create or verify the release task and follow-on propagation verification for:

- `StegVerse-Labs/Site`;
- `GCAT-BCAT-Engine/Publisher`;
- `StegVerse-Labs/admissibility-wiki`;
- `StegVerse-002/stegguardian-wiki`.

## 10. Immediate next work

`AEX-INV-20260729-01` must complete the RTG Volumes I–XV provenance and file inventory, then verify whether consolidated RTG, GTG, and TT documents are publicly readable and downloadable from Site.

No new volume, consolidated specification, release, or publication path may be declared canonical until that inventory is recorded.

## 11. Transfer confirmations

Repository Coordination Authority has registered worker `AEX-COORD-20260728-01`, assigned task `AEX-COORD-001`, recorded `75%` task completion, and updated `Admissible-Existence/.github/FORMALISM_MIRROR_HANDOFF.md`. Worker `AEX-COORD-20260728-01` no longer references the originating discussion as its operational source; this handoff is now authoritative.

Repository Coordination Authority has registered worker `AEX-INV-20260729-01`, assigned task `AEX-INV-001`, recorded `35%` task completion, and updated `Admissible-Existence/.github/FORMALISM_MIRROR_HANDOFF.md` and `Admissible-Existence/RTG/docs/RTG_MIRROR_HANDOFF.md`. Worker `AEX-INV-20260729-01` no longer references the originating session; these handoffs are now the authoritative sources for continuation.
