# Admissible-Existence Formalism Mirror Handoff

**Status:** ACTIVE — authoritative coordination source

**Last updated:** 2026-07-28

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

| Organization / Repository | Intended role | Current status | Canonical handoff status |
|---|---|---:|---|
| `Admissible-Existence/Existence` | Existence formalism | Existing | Repo-specific handoff not yet verified |
| `Admissible-Existence/AE` | Admissible Existence formalism | Existing | Repo-specific handoff not yet verified |
| `Admissible-Existence/RTG` | Relational Transition Geometry | **Repository not presently visible** | Creation/ownership decision required |
| `Admissible-Existence/GTG` | Generalized Transition Governance | **Repository not presently visible** | Creation/ownership decision required |
| `Admissible-Existence/TT` | Transition Table formalism | **Repository not presently visible** | Creation/ownership decision required |
| `Admissible-Existence/validator` | Formalism validation/invalidation | Existing | Repo-specific handoff not yet verified |
| `GCAT-BCAT-Engine/Publisher` | Publication projection | External dependency | Handoff/path verification required |
| `StegVerse-Labs/Site` | Public rendered and downloadable surface | Existing | Site mirror controls exist; formalism publication path not yet verified |
| `admissibility-wiki` | Public evidence and determination surface | External dependency | Update path required at release readiness |
| `stegguardian-wiki` | Guardian/governance public surface | External dependency | Update path required at release readiness |

## 4. Worker inventory

| Worker ID | Assignment | Destination | Status | Task % | Goal activation % | Source-session dependency |
|---|---|---|---|---:|---:|---|
| `AEX-COORD-20260728-01` | Establish and maintain formalism coordination, worker ledger, archive transfer gate, and repository inventory | `Admissible-Existence/.github` | ACTIVE | 60% | 25% | false after this handoff commit |
| `AEX-INV-UNASSIGNED` | Inventory canonical RTG Volumes I–XV, GTG, and TT materials across accessible repositories and Site | To be assigned by coordinator | UNASSIGNED | 0% | 0% | n/a |
| `AEX-ROUTE-UNASSIGNED` | Define canonical repository ownership for RTG, GTG, and TT, including whether new repos must be created | To be assigned by coordinator | BLOCKED | 0% | 0% | n/a |
| `SITE-FORMALISM-UNASSIGNED` | Build verified online and downloadable formalism publication paths | `StegVerse-Labs/Site` | BLOCKED | 0% | 0% | n/a |

## 5. Task ledger

### `AEX-COORD-001` — Coordination control plane

- **Worker:** `AEX-COORD-20260728-01`
- **Status:** ACTIVE
- **Completion:** 60%
- **Completed:**
  - singular coordination authority declared;
  - central worker inventory established;
  - central task ledger established;
  - archive transfer confirmation language established;
  - source-session independence rule established.
- **Remaining:**
  - verify repo-specific `*_MIRROR_HANDOFF.md` files;
  - register active workers from other sessions;
  - accept or reject their overlapping assignments;
  - create machine-verifiable archive-gate validation;
  - propagate the authority link into governed repositories.

### `AEX-INV-001` — Formalism corpus inventory

- **Worker:** UNASSIGNED
- **Status:** READY FOR ASSIGNMENT
- **Completion:** 0%
- **Scope:** Locate and classify all RTG, GTG, and TT files, including Volumes I–XV, consolidated drafts, schemas, examples, tests, PDFs, Site pages, and superseded copies.
- **Required output:** canonical inventory, provenance map, duplicate/conflict report, missing-file report, and recommended repository ownership.

### `AEX-ROUTE-001` — Canonical repository decision

- **Worker:** UNASSIGNED
- **Status:** BLOCKED BY `AEX-INV-001`
- **Completion:** 0%
- **Scope:** Decide whether RTG, GTG, and TT remain under an existing formalism repository or receive dedicated repositories under `Admissible-Existence`.

### `AEX-PUBLISH-001` — Public formalism publication

- **Worker:** UNASSIGNED
- **Status:** BLOCKED BY `AEX-INV-001` and `AEX-ROUTE-001`
- **Completion:** 0%
- **Scope:** Publish complete online documents and downloadable releases to Site with canonical repository, version, status, provenance, and supersession links.

## 6. Finding intake rule

A LinkedIn post, external discussion, experiment, or session insight must not automatically become a new long-running implementation session.

The originating session must record:

- finding ID;
- concise finding;
- primary and secondary StegVerse concepts affected;
- destination organization/repository;
- requested task;
- evidence or source reference;
- urgency and dependency information.

The Repository Coordination Authority then registers a worker and assignment in this handoff or the destination repo handoff.

## 7. Archive transfer gate

A session is not archive-ready merely because it documented a finding or suggested work.

Valid state sequence:

`NOT_TRANSFERRED → ASSIGNED → ACKNOWLEDGED → ARCHIVE_READY`

Every archive transfer must include:

- finding or task ID;
- destination organization and repository;
- governing handoff path;
- assigned worker ID;
- assigned task;
- completion baseline;
- worker acknowledgment;
- confirmation that the worker does not depend on the originating conversation.

Required confirmation line:

> Repository Coordination Authority has registered worker `<WORKER-ID>`, assigned task `<TASK-ID>`, recorded `<PERCENT>%` completion, and updated `<HANDOFF-PATH>`. Worker `<WORKER-ID>` no longer references the originating session; the handoff is now the authoritative source for continuation.

A session may use `READY FOR ARCHIVE` only after that statement is factually true.

## 8. Completion model

Three percentages must remain separate:

1. **Task completion** — accepted assigned deliverables divided by required assigned deliverables.
2. **Developed-files completion** — substantive required files divided by all required files; scaffolding and stubs do not count as developed.
3. **Goal activation completion** — accepted activation conditions divided by all conditions required for operational use.

Workers may propose completion values. Only the Repository Coordination Authority accepts and records repository-wide or program-wide values.

## 9. Release and propagation rule

When a governed repository reaches release/tag readiness, the coordinator must:

1. create or verify the release/tag task;
2. create a follow-on verification task for applicable propagation to:
   - `StegVerse-Labs/Site`;
   - `GCAT-BCAT-Engine/Publisher`;
   - `admissibility-wiki`;
   - `stegguardian-wiki`;
3. record evidence and completion in this handoff.

## 10. Immediate next assignment

Priority assignment candidate: `AEX-INV-001`.

The next worker must inventory the actual RTG, GTG, and TT corpus before any new volume, consolidated specification, dedicated repository, or Site publication path is declared canonical.

## 11. Transfer confirmation for this coordination task

Repository Coordination Authority has registered worker `AEX-COORD-20260728-01`, assigned task `AEX-COORD-001`, recorded `60%` task completion, and updated `Admissible-Existence/.github/FORMALISM_MIRROR_HANDOFF.md`. Worker `AEX-COORD-20260728-01` no longer references the originating discussion as its operational source; this handoff is now the authoritative source for continuation.
