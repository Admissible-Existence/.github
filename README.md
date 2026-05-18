# Admissible Existence

## Organization Status

This organization contains early formalism repositories for the **Admissible Existence** stack.

The purpose of this organization is to develop a family of related formalisms for understanding how coherent existence, boundaries, consequence, distributed coherence, and data continuity interact across physical, computational, biological, social, and governance systems.

This is research-stage work. The repositories are intended to preserve definitions, develop mathematical structure, test examples, and eventually support implementation inside StegVerse and related governed-execution systems.

## Core Thesis

Existence is not merely presence.

Existence becomes formally meaningful when presence persists coherently across admissible transition.

A thing does not fully exist in the formal sense merely because it appears. It exists as a coherent entity when it can persist, transform, interact, record consequence, and remain reconstructable across transition without losing the conditions that make it what it is.

> Existence is coherent persistence across admissible transition.

## Why This Organization Exists

The formalisms in this organization began from a recurring cross-scale observation:

> Stable things appear to require boundary conditions.

Across scale, coherent entities tend to appear with some kind of shell, boundary, horizon, field structure, envelope, membrane, atmosphere, halo, or interface.

Examples include:

| Scale | Boundary / Shell / Interface |
|---|---|
| Particle | field excitation / interaction boundary |
| Nucleus | strong-force binding region |
| Atom | electron probability structure |
| Molecule | bonding geometry / electron cloud |
| Cell | membrane |
| Organism | skin / immune / metabolic boundary |
| Ecosystem | nutrient-cycle / climate / trophic boundary |
| Planet | atmosphere / magnetosphere / crust / biosphere |
| Solar system | heliosphere / gravitational sphere of influence |
| Galaxy | dark-matter halo / baryonic disk / gravitational boundary |
| Black hole | event horizon |
| Observable universe | causal horizon / cosmological boundary |
| Software system | commit boundary / execution boundary / state boundary |
| Institution | jurisdiction / legitimacy boundary / authority boundary |
| AI system | tool-use boundary / authority boundary / consequence boundary |

These are not the same physical mechanism.

A cell membrane is not a galaxy halo.  
An atmosphere is not an electron cloud.  
A black-hole event horizon is not a software commit boundary.

But formally, they answer a similar structural question:

> What allows this region of reality to remain itself while interacting with everything else?

## Repository Stack

The current organization contains five foundational repositories:

```text
AE    Admissible Existence
BC    Boundary-Coherence
CHF   Consequence Horizon Formalism
DC    Distributed Coherence
DaCo  Data Continuity
```

The preferred conceptual structure is:

```text
AE
  └── BC
        ├── CHF
        ├── DC
        └── DaCo
```

This is not a strict linear dependency chain. It is a layered formal architecture.

AE is the root formalism.

BC is the first structural mechanism below AE.

CHF, DC, and DaCo are distinct child layers that address different consequences of bounded coherence.

## Repository Roles

### AE — Admissible Existence

**Question:** What permits coherent existence at all?

AE defines the highest-level claim:

> Existence is coherent persistence across admissible transition.

AE studies the conditions under which a state, entity, system, observer, process, or domain can exist in a way that remains coherent, recoverable, observable, and compositionally compatible with the reality that contains it.

AE is concerned with:

- presence;
- coherence;
- transition capacity;
- recoverability;
- observability;
- compositional compatibility;
- admissibility of continued existence.

AE does not merely ask whether something appears.

It asks whether that thing can persist across change without destroying the conditions that allow coherent existence to continue.

### BC — Boundary-Coherence

**Question:** How does existence become bounded and entity-like?

BC defines the first structural mechanism of AE:

> A thing exists when a boundary allows it to remain coherent across transitions.

BC studies the role of boundaries, shells, horizons, membranes, fields, interfaces, and transition surfaces in preserving coherent identity.

BC is concerned with:

- interior/exterior distinction;
- regulated exchange;
- state continuity;
- boundary throughput;
- absorption capacity;
- recoverability;
- coherence preservation;
- boundary overload.

BC does not claim all boundaries are physically identical.

It claims that coherent systems across scale appear to require some form of boundary-mediated transition regulation.

### CHF — Consequence Horizon Formalism

**Question:** When does transition become binding consequence?

CHF studies boundaries where transitions cross from reversible possibility into binding consequence.

Before the consequence horizon, a system may still inspect, deny, revise, simulate, or contain a transition.

At the horizon, the transition becomes committed.

Beyond the horizon, the system must absorb, adapt to, propagate, or suffer the consequence of the transition.

CHF is concerned with:

- irreversible or semi-irreversible transition;
- event-horizon-like behavior;
- commit boundaries;
- consequence domains;
- consequence overload;
- observability loss;
- recoverability loss;
- entropy as transition-record cost;
- ALLOW / DENY / FAIL-CLOSED / QUARANTINE logic.

Core line:

> The commit boundary matters because it is the last controllable surface before a transition crosses the consequence horizon.

### DC — Distributed Coherence

**Question:** How do multiple coherent systems remain coherent together?

DC studies coherence across multiple entities, nodes, observers, repositories, agents, domains, or systems that are each changing.

A node can remain coherent locally while the distributed system fails globally.

DC is concerned with:

- multi-entity coherence;
- local pass / global fail;
- split-brain coherence;
- authority drift;
- lag-induced invalidity;
- conflicting receipts;
- distributed quarantine;
- global reconciliation;
- ecosystem-level recoverability.

Core line:

> Distributed Coherence is the preservation of coherent relation among systems that are each changing.

### DaCo — Data Continuity

**Question:** How is transition continuity preserved and reconstructed?

DaCo defines the record-preservation layer required for coherent systems to remain reconstructable across transition.

DaCo is not merely storage.

A file, log, hash, or backup is not automatically continuity.

Continuity requires a recoverable relationship between:

```text
prior state
transition
post state
residue
record
reconstruction path
```

DaCo is concerned with:

- receipt chains;
- state references;
- transition identity;
- provenance;
- authority basis;
- admissibility basis;
- hash integrity;
- reconstruction paths;
- known gaps;
- replay;
- continuity failure modes.

Core line:

> Data Continuity is reconstructable state relationship across transition.

## Relationship Between the Repositories

The five repositories are meant to work together.

```text
AE defines the admissibility of coherent existence.

BC defines the boundary architecture through which coherent existence becomes entity-like.

CHF defines the point where transition becomes binding consequence.

DC defines whether multiple bounded systems remain coherent together.

DaCo defines whether transition history remains reconstructable after change.
```

A compact dependency view:

```text
No admissible existence → no stable formal entity.
No boundary-coherence → no distinguishable coherent entity.
No consequence-horizon awareness → no protection before irreversible transition.
No distributed coherence → no ecosystem-level stability.
No data continuity → no reconstruction of how state became state.
```

## Relation to StegVerse

This organization is conceptually aligned with StegVerse.

StegVerse focuses on governed execution, admissibility at commit, receipt chains, state reconstruction, deterministic replay, and recoverability.

The Admissible Existence stack explains the deeper formal reason those mechanisms matter.

```text
Admissible Existence
    ↓
Boundary-Coherence
    ↓
Consequence Horizon / Distributed Coherence / Data Continuity
    ↓
Admissibility at Commit
    ↓
GCAT / BCAT
    ↓
Rigel Recoverability
    ↓
Receipts / Reconstruction / Proof Surfaces
```

In StegVerse terms:

- AE explains why existence must be admissible across transition.
- BC explains why systems require governed boundaries.
- CHF explains why commit-time validation matters.
- DC explains why multi-repo and multi-agent systems require ecosystem coherence.
- DaCo explains why receipts and reconstruction are not optional.

## Key Shared Principles

### 1. Existence Is Not Mere Presence

Something can appear without being stably or admissibly existent.

Formal existence requires coherent persistence through transition.

### 2. Boundary Is Constitutive

Boundaries are not merely containers.

A boundary is the structure by which a system remains itself while interacting with an exterior.

### 3. Conservation Is Not Stability

A system may preserve local conserved quantities while still becoming globally unstable.

Conservation is evidence of continuity, not proof of admissibility.

### 4. Consequence Requires Horizon Awareness

A transition becomes dangerous when it crosses a boundary after which observability, reversibility, recoverability, or absorption can no longer be guaranteed.

### 5. Distributed Validity Is Stronger Than Local Validity

A node may be valid locally while the distributed system fails globally.

Consensus is not coherence if the agreed state is inadmissible.

### 6. Continuity Is Not Storage

Data continuity requires reconstructable state relationship across transition, not merely retained files.

### 7. Entropy Records Transition

Entropy can be treated not only as disorder, but as the cost reality pays to remember that a transition happened.

## Early Formal Vocabulary

| Term | Working Meaning |
|---|---|
| Presence | Detectable appearance of a state, entity, process, or relation |
| Existence | Coherent persistence across transition |
| Admissibility | Permission of a state or transition under coherence, recoverability, and compatibility constraints |
| Boundary | Interface across which transition is regulated |
| Shell | Boundary structure that contributes to coherence preservation |
| Horizon | Boundary where access, reversibility, observability, or causal relation changes |
| Consequence Horizon | Horizon where transition becomes binding consequence |
| Consequence Domain | Downstream domain that must absorb a committed transition |
| Coherence | Preservation of system identity across transition |
| Recoverability | Ability to remain within, return to, or reconstruct coherent state |
| Absorption Capacity | Amount of transition load a system can admit without coherence failure |
| Distributed Coherence | Coherent relation among multiple changing systems |
| Data Continuity | Reconstructable state relationship across transition |
| Receipt | Structured residue proving or describing a transition |
| Reconstruction | Process of recovering how state became state |
| Gap Honesty | Explicit representation of unknowns, missing state, or degraded reconstruction confidence |

## Early Research Roadmap

### Phase 1 — Baseline Definitions

Each repository should define its core terms, scope, non-claims, examples, and relationship to the other repositories.

Current baseline repositories:

```text
AE
BC
CHF
DC
DaCo
```

### Phase 2 — Shared Glossary

Create a shared glossary that normalizes terms across all repositories.

Candidate terms:

```text
admissibility
boundary
coherence
consequence
consequence horizon
continuity
distributed coherence
entropy
existence
horizon
presence
receipt
recoverability
reconstruction
transition
```

### Phase 3 — Cross-Scale Examples

Develop examples across:

```text
quantum systems
atoms
molecules
cells
organisms
ecosystems
planets
solar systems
galaxies
black holes
universes
software systems
AI agents
institutions
economies
StegVerse repos and orgs
```

Each example should mark whether the analogy is:

```text
physical
mathematical
formal
metaphorical
operational
```

### Phase 4 — Mathematical Skeletons

Each repo should define minimal variables and conditions.

Examples:

```text
C(t)      coherence
R(t)      recoverability
O(t)      observability
A(t)      absorption capacity
F_B(t)    boundary flux
F_H(t)    horizon flux
Q(t)      conserved-state vector
S(t)      system state
u         transition
Φ(S,u)    post-transition state
```

### Phase 5 — Failure Modes

Define failure modes across the stack.

Examples:

```text
bare presence
coherence collapse
boundary overload
consequence horizon breach
local pass / global fail
receipt divergence
data continuity break
silent mutation
reconstruction failure
composition failure
```

### Phase 6 — Simple Test Harnesses

Each repository should eventually include minimal tests.

Possible tests:

```text
AE     admissible existence state classifier
BC     boundary throughput / absorption simulator
CHF    consequence horizon ALLOW / DENY / FAIL-CLOSED evaluator
DC     distributed coherence reconciliation simulator
DaCo   receipt-chain continuity verifier
```

### Phase 7 — StegVerse Integration

Map each formalism into StegVerse governance architecture.

Expected integrations:

```text
admissibility at commit
GCAT / BCAT
Rigel recoverability
receipt chains
master-records
state reconstruction
deterministic replay
multi-org ingestion
quarantine and remediation
```

## Non-Claims

This organization does not claim:

- that all shells are physically identical;
- that all systems are conscious;
- that black holes are confirmed to contain child universes;
- that metaphors are proofs;
- that conservation alone proves stability;
- that consensus alone proves coherence;
- that storage alone proves continuity;
- that the mathematical work is complete.

The current claim is narrower and more disciplined:

> Across scale, coherent existence appears to require bounded, recoverable, reconstructable transition under admissibility constraints.

## Immediate Repository Tasks

Each repository should maintain:

```text
README.md
glossary.md
examples.md
roadmap.md
```

Note: if creating a GitHub organization profile page, this file belongs at:

```text
.github/profile/README.md
```

For display in this document, the leading dot may be removed as:

```text
github/profile/README.md
```

But the actual GitHub path must preserve the leading dot.

## Core Lines

> Existence is coherent persistence across admissible transition.

> A boundary is the mechanism by which reality allows coherence to persist while change continues.

> A consequence horizon is the boundary where transition becomes binding.

> Distributed coherence is the preservation of coherent relation among systems that are each changing.

> Data continuity is reconstructable state relationship across transition.

> Governance is the artificial construction of boundary-coherence for systems whose transitions can produce irreversible consequence.
