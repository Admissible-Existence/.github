# Formalism Worker Completion Standard

## Goal

Advance each canonical Admissible-Existence formalism from repository documentation to peer-review publication grade through repository-native GitHub or StegVerse workers, then publish only finished papers to the StegVerse Site papers page.

## Required stages

A formalism is not complete until all stages are evidenced:

1. **Inventory** — canonical documents, notation, definitions, axioms, propositions, theorems, hypotheses, proofs, examples, citations, schemas, validators, and rendering sources are enumerated.
2. **Formal development** — undefined terms, contradictory definitions, notation collisions, dependency gaps, circular claims, and unresolved placeholders are tracked and closed or explicitly bounded.
3. **Mathematical validation** — every theorem-like claim is classified as proved, computationally checked, empirically supported, conjectural, or unresolved. Plausible prose must never be relabeled as proof.
4. **Consistency and coherence** — internal links resolve; notation is stable; definitions are non-conflicting; theorem dependencies exist; assumptions are declared; cross-repository references point to current canonical owners; no superseded statement is silently active.
5. **Peer-review preparation** — manuscript structure, abstract, related work, methods, results, limitations, bibliography, claim-to-evidence crosswalk, theorem-to-proof crosswalk, reviewer packet, and response ledger are present.
6. **Publication readiness** — deterministic render succeeds; page count, bytes, hashes, figures, references, metadata, source commit, and license are recorded; readiness is fail-closed.
7. **Site publication verification** — the paper is accepted by the Site papers-page intake, deployed, directly observed, and linked back to its canonical source and publication receipt.

## Periodic coherence audit

The organization coordination worker must run at least weekly and on demand. It must inspect every registered formalism repository for:

- applicable `*_MIRROR_HANDOFF.md`;
- canonical README and formal documents;
- broken local Markdown links;
- unresolved TODO, FIXME, TBD, placeholder, stub, or pending markers;
- mathematical signal and declared notation;
- duplicate or conflicting definition labels where detectable;
- theorem-like statements without proof classification;
- stale or missing cross-repository owner references;
- publication claims without readiness and deployment receipts;
- inaccessible repositories or incomplete evidence.

Missing access or missing evidence is `BLOCKED`, never `PASS`.

## Worker state model

Every worker must persist one of:

- `COMPLETE`
- `BLOCKED`
- `RETRY`
- `REVIEW_REQUIRED`
- `FAILED`
- `IN_PROGRESS`

Every non-complete state must name the next executable task, owner repository, target path, and release condition.

## Publication gate

No paper may be marked finished or published merely because Markdown, PDF, tests, workflows, or receipts exist. Publication requires all seven stages, an immutable source commit, a deterministic artifact hash, a readiness receipt, and direct Site observation.
