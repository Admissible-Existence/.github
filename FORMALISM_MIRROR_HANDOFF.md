# Admissible-Existence Formalism Mirror Handoff

**Status:** ACTIVE — authoritative coordination source

**Last updated:** 2026-07-29

**Repository Coordination Authority worker:** `AEX-COORD-20260728-01`

## 1. Authority

This handoff is the source of truth for assigning, tracking, transferring, and closing work that affects Admissible-Existence formalisms and their StegVerse publication surfaces.

The Repository Coordination Authority is the singular session permitted to maintain repository contact, register workers and assignments, declare canonical ownership, accept completion evidence, update percentages, authorize mirroring/publication, close source-session dependencies, and move the program to its next integration goal.

Worker sessions may implement bounded assignments, but may not independently change repository-wide completion, canonical ownership, volume numbering, publication authority, or program goals.

## 2. Current integration goal

**Goal ID:** `AEX-FORMALISM-PUBLICATION-ACTIVATION-001`

Establish a collision-resistant path from findings and formal development into canonical repositories, consolidated specifications, validation, and public Site publication.

`Existence / AE → RTG → GTG → TT → validator → Publisher / Site → admissibility-wiki`

## 3. Current repository inventory

| Organization / Repository | Intended role | Current verified status | Canonical handoff status |
|---|---|---|---|
| `Admissible-Existence/Existence` | Existence formalism | Existing | Repo-specific handoff not yet verified |
| `Admissible-Existence/AE` | Admissible Existence formalism | Existing | Repo-specific handoff not yet verified |
| `Admissible-Existence/RTG` | Relational Transition Geometry | Existing; manifest corpus and operational build verified; Volume I–XV provenance unresolved | RTG handoff, corpus inventory, and volume matrix active |
| `Admissible-Existence/GTG` | Generalized Transition Governance | Seven-volume formal draft and validation surface present | `docs/GTG_MIRROR_HANDOFF.md` verified |
| `Admissible-Existence/TT` | Transition Table formalism | Strict resolution chain and RTG-TT test interface present | `docs/TT_MIRROR_HANDOFF.md` verified |
| `Admissible-Existence/validator` | Formalism validation/invalidation | Existing | Repo-specific handoff not yet verified |
| `GCAT-BCAT-Engine/Publisher` | Publication projection | External dependency | Formalism publication path requires verification |
| `StegVerse-Labs/Site` | Public rendered/downloadable surface | Existing; TT not admitted | Complete RTG/GTG/TT paths not verified |
| `StegVerse-Labs/admissibility-wiki` | Public evidence/determination surface | TT bounded receipt reported installed | Public determination unauthorized |
| `StegVerse-002/stegguardian-wiki` | Guardian/governance public surface | Dependency blocked | Upstream evidence required |

## 4. Worker inventory

| Worker ID | Assignment | Destination | Status | Task % | Developed-files % | Goal activation % | Source-session dependency |
|---|---|---|---|---:|---:|---:|---|
| `AEX-COORD-20260728-01` | Maintain coordination, worker ledger, archive gate, and repository inventory | `Admissible-Existence/.github` | ACTIVE | 80% | 75% | 45% | false |
| `AEX-INV-20260729-01` | Inventory and reconcile RTG, GTG, TT, and publication surfaces | RTG / GTG / TT / Site | ACTIVE | 52% | 42% | 30% | false |
| `AEX-ROUTE-20260729-01` | Reconcile canonical ownership and AE/RTG/TT boundaries | `Admissible-Existence/.github` | ACTIVE | 72% | 70% | 60% | false |
| `SITE-FORMALISM-UNASSIGNED` | Build verified online and downloadable formalism paths | `StegVerse-Labs/Site` | BLOCKED | 0% | 0% | 0% | n/a |

## 5. Task ledger

### `AEX-COORD-001` — Coordination control plane

- **Worker:** `AEX-COORD-20260728-01`
- **Status:** ACTIVE
- **Completion:** 80%
- **Completed:** singular authority; central ledger; archive-transfer rules; RTG/GTG/TT discovery; GTG/TT handoff verification; RTG handoff, corpus inventory, and volume provenance matrix; inventory and routing workers.
- **Remaining:** verify AE, Existence, and validator handoffs; import active workers; create machine-verifiable archive validation; propagate authority links.

### `AEX-INV-001` — Formalism corpus inventory

- **Worker:** `AEX-INV-20260729-01`
- **Status:** ACTIVE
- **Completion:** 52%
- **Verified findings:**
  - RTG's current manifest requires a compact implementation/validation corpus, not a fifteen-volume set;
  - `tools/run_rtg_build.py` runs manifest verification, bridge-index generation, IICT fixtures, and status generation;
  - `PRODUCTION-COMPLETE-SEED` is an internal build-state record tied to three IICT fixtures and two bridges, not publication completion;
  - a fifteen-row Volume I–XV provenance matrix now exists, but source paths and hashes remain 0/15 verified;
  - GTG has seven volumes and formal-draft-complete machinery but no release or independent verification;
  - TT has strict receipt-chain validation and hosted evidence but remains destination/publication blocked;
  - Site public and downloadable full-document paths remain unverified.
- **Remaining:** exact volume filenames/files and hashes; classification and supersession map; repository file inventories; AE/RTG ownership resolution; Site path verification; consolidated-readiness decision.

### `AEX-ROUTE-001` — Canonical repository decision

- **Worker:** `AEX-ROUTE-20260729-01`
- **Status:** ACTIVE — provisional ownership established
- **Completion:** 72%
- **Current owners:** RTG → `Admissible-Existence/RTG`; GTG → `Admissible-Existence/GTG`; TT → `Admissible-Existence/TT`.
- **Conflict:** TT assigns the Admissible Resolution Function and geometric minimum to AE, while RTG owns relational-transition geometry generally. The final rule must distinguish geometry definitions from admissibility-resolution derivation.

### `AEX-PUBLISH-001` — Public formalism publication

- **Worker:** UNASSIGNED
- **Status:** BLOCKED BY `AEX-INV-001` and final `AEX-ROUTE-001`
- **Completion:** 0%
- **Scope:** publish complete online and downloadable editions with ownership, version, status, provenance, supersession, validation, and non-authority boundaries.

## 6. Finding intake and archive transfer

LinkedIn posts, external discussions, experiments, and session insights must be routed as findings rather than automatically becoming long-running implementation sessions.

Valid archive sequence:

`NOT_TRANSFERRED → ASSIGNED → ACKNOWLEDGED → ARCHIVE_READY`

Required confirmation:

> Repository Coordination Authority has registered worker `<WORKER-ID>`, assigned task `<TASK-ID>`, recorded `<PERCENT>%` completion, and updated `<HANDOFF-PATH>`. Worker `<WORKER-ID>` no longer references the originating session; the handoff is now the authoritative source for continuation.

## 7. Completion model

1. **Task completion** — accepted deliverables / required assigned deliverables.
2. **Developed-files completion** — substantive required files / all required files; scaffolding and stubs do not count.
3. **Goal activation completion** — accepted activation conditions / all operational conditions.

Only the Repository Coordination Authority accepts repository-wide or program-wide values.

## 8. Release and propagation rule

At release/tag readiness, create or verify release and propagation tasks for:

- `StegVerse-Labs/Site`;
- `GCAT-BCAT-Engine/Publisher`;
- `StegVerse-Labs/admissibility-wiki`;
- `StegVerse-002/stegguardian-wiki`.

## 9. Immediate next work

`AEX-INV-20260729-01` must obtain the downloaded Volume I–XV filenames/files, calculate hashes, populate the provenance matrix, compare the volumes against the manifest corpus, and verify direct Site publication paths.

`AEX-ROUTE-20260729-01` must define the AE/RTG boundary for geometric definitions versus admissibility-resolution derivation.

No new volume, consolidated specification, release, or publication path may be declared canonical until those records are accepted.

## 10. Transfer confirmations

Repository Coordination Authority has registered worker `AEX-COORD-20260728-01`, assigned task `AEX-COORD-001`, recorded `80%` completion, and updated this handoff. Worker `AEX-COORD-20260728-01` no longer references the originating discussion; this handoff is authoritative.

Repository Coordination Authority has registered worker `AEX-INV-20260729-01`, assigned task `AEX-INV-001`, recorded `52%` completion, and updated this handoff plus `Admissible-Existence/RTG/docs/RTG_MIRROR_HANDOFF.md`, `RTG_CORPUS_INVENTORY_STATUS.md`, and `RTG_VOLUME_PROVENANCE_MATRIX.md`. Worker `AEX-INV-20260729-01` no longer references the originating session; these handoffs are authoritative for continuation.
