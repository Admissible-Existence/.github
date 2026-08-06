# Admissible-Existence Organization Mathematical Architecture

**Organization:** `Admissible-Existence`  
**Program:** `AEX-PRINCIPLE-COMPLETENESS-001`  
**Status:** ACTIVE — ORGANIZATION MATHEMATICAL CONTROL PLANE  
**Updated:** 2026-08-06

## Purpose

This document defines the intended mathematical architecture of the `Admissible-Existence` organization and the rules for tracking which repositories contain:

- intended mathematical objects;
- formalized definitions, axioms, operators, equations, invariants, or predicates;
- executable or computational support;
- proof candidates;
- reviewed proofs;
- simulations or witnesses;
- validation evidence;
- bounded support machinery rather than source-formalism authority.

The machine-readable companion is `data/organization-mathematics-registry.yaml`.

This repository coordinates and tracks mathematics. It does **not** create mathematical authority for source repositories. Canonical definitions, theorems, proofs, and counterexamples remain owned by their fully qualified source repositories.

## Organization-level mathematical object

Let the organization contain repositories

```text
R = {r_1, r_2, ..., r_n}
```

and let each repository expose a finite set of declared mathematical components

```text
M(r_i) = {m_i1, m_i2, ..., m_ik}.
```

For every component `m`, define the status vector

```text
S(m) = (I, T, X, F, P_c, P_r, W, V, E, H)
```

where:

- `I` = stable identity exists;
- `T` = theory and assumptions are declared;
- `X` = explicit mathematical representation exists;
- `F` = falsification and limits are declared;
- `P_c` = at least one proof candidate exists;
- `P_r` = at least one proof is independently reviewed and accepted;
- `W` = computational witness or simulation exists;
- `V` = validator or executable correspondence exists;
- `E` = evidence is bound to current artifacts;
- `H` = current handoff binds the claim.

Each coordinate is Boolean for minimum-standard evaluation, while maturity is separately classified using:

```text
THESIS < DEFINED < FORMALIZED < PROOF_CANDIDATE < PROVED < SIMULATED < VALIDATED
```

`SIMULATED` and `VALIDATED` are not automatically greater than `PROVED`; they are orthogonal evidence dimensions. A component may be both `PROVED` and `VALIDATED`, or simulated without being proved.

## Repository completeness functions

For a source repository `r`, define minimum mathematical coverage:

```text
C_math(r) = (1 / |M(r)|) × Σ_m [I_m T_m X_m F_m H_m].
```

Define proof-candidate coverage:

```text
C_pc(r) = (1 / |M(r)|) × Σ_m P_c,m.
```

Define reviewed-proof coverage:

```text
C_pr(r) = (1 / |M(r)|) × Σ_m P_r,m.
```

Define executable-support coverage:

```text
C_exec(r) = (1 / |M(r)|) × Σ_m [W_m ∨ V_m].
```

A source repository exceeds the minimum standard only when:

```text
C_math(r) = 1
```

and all dependencies, whole-repository roles, cross-repository relationships, and evidence paths are explicit. Proof-candidate and reviewed-proof coverage remain separately reported; a repository may exceed the minimum standard without every component being proved only when every unproved component is explicitly bounded as a definition, hypothesis, conjecture, open problem, or review-required claim.

For support repositories, completeness is evaluated against support obligations rather than original theorem production:

```text
C_support(r) = coverage × contract × non_authority × evidence_binding × handoff_binding.
```

## Organization-wide architecture

The intended mathematics is organized into six interacting layers.

### Layer A — existence and admissibility

Primary repositories:

- `Admissible-Existence/AE`
- `Admissible-Existence/Existence`

Core mathematical concerns:

- governed existence standing;
- admissible persistence;
- identity and individuation;
- viability and recoverability;
- authority compatibility;
- purpose and convergence;
- compositional coherence;
- reconstructability.

Current known state:

- `Admissible-Existence/AE` has 31 registered components and multiple computational witnesses; proof candidates and proof-review status remain mixed.
- `Admissible-Existence/Existence` has 10 registered principles and validated RC1 scoring behavior; principle-level independent validation remains open.

### Layer B — transition mathematics

Primary repositories:

- `Admissible-Existence/RTG`
- `Admissible-Existence/GTG`
- `Admissible-Existence/TT`
- `Admissible-Existence/STCM`
- `Admissible-Existence/ET`
- `Admissible-Existence/learning-transition-governance`

Core mathematical concerns:

- transition relations and admissible regions;
- generalized transition governance;
- transition tables and topology;
- conservation, closure, and state-transition consistency;
- evolution or execution transition semantics;
- learning, policy update, drift, and convergence.

`Admissible-Existence/RTG` remains collision-bounded under existing machine-owned rendering, evidence-closure, theorem-packet, and readiness lanes.

### Layer C — boundary, consequence, and recovery mathematics

Primary repositories:

- `Admissible-Existence/BC`
- `Admissible-Existence/CHF`
- `Admissible-Existence/RE`
- `Admissible-Existence/RE-Reduction`

Core mathematical concerns:

- boundary coherence and purpose inversion;
- consequence horizons and irreversibility;
- recovery basins and reversible entropy;
- reduction mappings, preserved invariants, and information loss.

### Layer D — distributed, relational, and authority mathematics

Primary repositories:

- `Admissible-Existence/DC`
- `Admissible-Existence/Triad`
- `Admissible-Existence/GCAT-BCAT`
- `Admissible-Existence/ECAT-ICAT`
- `Admissible-Existence/IICT`
- `Admissible-Existence/CTA`
- `Admissible-Existence/HPS`
- `Admissible-Existence/FI`

Core mathematical concerns:

- local-to-global coherence;
- coupled multi-entity dynamics;
- governance and boundary scoring;
- experiential and inter-entity standing;
- identity and inter-entity continuity;
- consent, delegation, revocation, and authority;
- additional source formalisms whose canonical expansions must remain explicit in their repositories.

### Layer E — continuity, observation, and proof standing

Primary repositories:

- `Admissible-Existence/DaCo`
- `Admissible-Existence/IW`
- `Admissible-Existence/standing-proof-formalism`

Core mathematical concerns:

- ordered evidence chains and reconstruction;
- inference windows, observability, and evidence bounds;
- proof standing, proof obligations, admissible evidence, and review status.

### Layer F — validation and control infrastructure

Support and coordination repositories:

- `Admissible-Existence/.github`
- `Admissible-Existence/core-lite`
- `Admissible-Existence/validator`
- `Admissible-Existence/tracker`
- `Admissible-Existence/telemetry`
- `Admissible-Existence/ae-validation-factory`
- `Admissible-Existence/ae-validation-research`
- `Admissible-Existence/validation-profile-registry`
- `Admissible-Existence/SOL` pending role disposition

These repositories must not invent source mathematics merely to appear complete. They must define bounded mathematical contracts for coverage, validation, evidence, task state, telemetry, reproducibility, profiles, or research.

## Proof-candidate tracking

A proof candidate is a durable artifact that contains:

1. a stable theorem, lemma, proposition, or invariant identifier;
2. a canonical statement;
3. declared premises and domain;
4. a proof body or derivation;
5. dependencies;
6. known gaps or unresolved obligations;
7. source commit or blob binding;
8. review status.

The allowed proof states are:

```text
NONE
CANDIDATE
REVIEW_REQUIRED
ACCEPTED
REJECTED
SUPERSEDED
```

A deterministic witness is not automatically a proof. A workflow success is not automatically a proof. A rendered paper is not automatically a proof. A receipt is not automatically a proof. The registry must preserve those distinctions.

## Organization invariants

1. Every source mathematical claim has exactly one fully qualified canonical repository owner.
2. Coordination records may summarize but never silently redefine source mathematics.
3. Every proof candidate names its canonical statement and source artifact.
4. Every accepted proof names the review evidence and reviewed artifact identity.
5. Every simulated or validated claim states whether it is existential, universal, empirical, or implementation-specific.
6. Every cross-repository dependency uses a fully qualified identity.
7. Empty active repositories cannot satisfy the minimum standard.
8. Historical `COMPLETE` or `ARCHIVE_READY` states remain scoped to their original goals unless revalidated under this architecture.
9. Missing evidence fails closed.
10. Organization-level completeness is not the arithmetic average of repository percentages; every required repository must independently satisfy its applicable contract.

## Current organization state

- Non-archived repositories: 32.
- Directly touched by the principle-completeness program: `Admissible-Existence/.github`, `Admissible-Existence/AE`, and `Admissible-Existence/Existence`.
- Proven complete under this architecture: 0.
- Empty active repositories at baseline: `Admissible-Existence/ae-validation-research` and `Admissible-Existence/SOL`.
- Known repository containing multiple proof candidates and theorem packets: `Admissible-Existence/RTG`, under existing collision boundaries.
- Known repository containing constructive witness-based theorem candidates: `Admissible-Existence/AE`.

## Required repository projection

Every source repository must eventually expose:

```text
formalism/principle-registry.yaml
formalism/dependency-graph.yaml
formalism/proof-candidates.yaml
docs/WHOLE_REPO_THEORY_MAP.md
docs/MATHEMATICAL_NOTATION.md
docs/FALSIFICATION_AND_LIMITS.md
docs/<REPOSITORY>_MIRROR_HANDOFF.md
```

Every support repository must eventually expose:

```text
docs/SUPPORT_ROLE_AND_NON_AUTHORITY.md
data/source-coverage-map.yaml
data/validation-or-support-contract.yaml
docs/<REPOSITORY>_MIRROR_HANDOFF.md
```

The organization registry records presence, maturity, evidence, and proof-candidate status without replacing these canonical repository-local records.

## Completion boundary

This architecture is complete as a coordination model when:

- all 32 repositories appear in the machine-readable registry;
- each repository has a declared role and intended mathematical contribution;
- source repositories expose component counts and proof-candidate counts;
- support repositories expose bounded contracts and source coverage;
- every status is evidence-bound;
- the registry validator and hosted workflow pass;
- the latest organization handoff binds the resulting receipt.

It does not establish that all source mathematics is correct or proved. Those conclusions require repository-local evidence and independent review.
