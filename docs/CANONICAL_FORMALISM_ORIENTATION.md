# Canonical Formalism Orientation

**Goal:** `AEX-CANONICAL-FORMALISM-ORIENTATION-001`  
**Canonical task:** `Admissible-Existence/.github#5`  
**Audience:** internal workers, maintainers, AI development sessions, and repository-native automation  
**Public/user-facing:** no  
**Authority effect:** none

## Purpose

This document exists so internal workers begin from the current Admissible-Existence architecture instead of rediscovering, flattening, or silently replacing already-developed formalism.

It is an orientation layer only. It does not become the source of AE, TT, GTG, Existence, BC, CHF, DC/DaCo, validation, StegCore, TV/TVC, or Master Records semantics. Every statement below points back to a canonical owner.

Before proposing a new foundational abstraction, a worker MUST:

1. read this document and `data/canonical-formalism-orientation.json`;
2. read the cited canonical source/handoff for the relevant concept;
3. classify its work as `IMPLEMENTS`, `INTEGRATES`, `VALIDATES`, `EXTENDS`, `CHALLENGES`, or `OBSERVES`;
4. if `EXTENDS`, name the exact insufficiency in the existing formalism;
5. if `CHALLENGES`, identify falsifying or contradictory evidence;
6. preserve source ownership and authority boundaries.

A conversation, implementation task, or worker may not create a new foundational concept merely because it entered through a downstream repository and did not first inspect the upstream formalism.

## Canonical layer orientation

### Admissible-Existence/AE

Owns the theory of admissible existence and coherent persistence across transition. Canonical AE distinguishes presence, individuation, coherence, transition capacity, viability, observability, reconstructability, compositional compatibility, authority, purpose, relational admissibility, recoverability classes, and contextual/joint coherent state.

**Do not collapse:** presence into existence; technical control into legitimate authority; observability into reconstructability; isolated endpoint state into relational standing.

**Does not create:** component execution authority.

Canonical source: `Admissible-Existence/AE/docs/papers/coherent-life-and-admissible-existence.md`.

### Admissible-Existence/TT

Owns Transition Table element identity, structural relationships, standing requirements, registry structure, bounded local allocation, outcome-region structure, receipt obligations, and transition classifications.

TT is structural and non-authorizing. Its descriptive/testable derivation chain does not create execution authority.

**Do not describe TT as:** a capability issuer, execution authority, release authority, or a replacement for component governance.

Canonical sources include:

- `Admissible-Existence/TT/FORMAL_STANDING_SPEC.md`
- `Admissible-Existence/TT/TT_ELEMENTS.json`
- `Admissible-Existence/TT/docs/WHOLE_REPO_THEORY_MAP.md`
- `Admissible-Existence/TT/docs/TT_MIRROR_HANDOFF.md`

### Admissible-Existence/GTG

Owns bounded reconstruction structures including causal reconstruction, authority reconstruction, and reality-contact reconstruction.

Reconstruction results may be `PASS`, `PARTIAL`, or `FAIL_CLOSED` according to source semantics. Reconstruction does not independently create execution, certification, release, mathematical-closure, empirical-validity, or universal-admissibility authority.

Canonical source: `Admissible-Existence/GTG/GTG_MIRROR_HANDOFF.md` and its R3-R5 contracts.

### Admissible-Existence/Existence

Owns `%Existence` vocabulary, review-standing schemas, scoring/round-trip fixtures, proof-path documentation, validation, and receipts. `%Existence` standing is not final admissibility and does not grant execution authority.

Canonical source: `Admissible-Existence/Existence/docs/EXISTENCE_MIRROR_HANDOFF.md`.

### Boundary / consequence / continuity layers

AE's canonical paper situates Boundary-Coherence, Consequence Horizon Formalism, Distributed Coherence, and Data Continuity as distinct roles within the broader theory. Workers must read the relevant repository handoff before declaring a missing concept.

A boundary remaining physically intact does not prove authority, purpose, continuity, or relational coherence. A consequence boundary determines when standing must be checked before reality-binding effect. Continuity/reconstructability preserve recoverable transition history; they do not grant new execution authority.

### Admissible-Existence/ae-validation-factory

Owns bounded independent validation support. It may recompute and test target claims while remaining separate from target doctrine and target authority.

**Never infer:** validation completion = source ownership, execution authority, release authority, certification authority, or Master Records custody.

Canonical source: `Admissible-Existence/ae-validation-factory/AE_VALIDATION_FACTORY_MIRROR_HANDOFF.md`.

### StegVerse-Labs/StegCore

StegCore is an internal operational consumer/projection of the upstream formalism, not an external entry point and not a replacement for Admissible-Existence theory.

The recent Core lifecycle `DECLARED -> STANDING -> ADMISSIBLE -> ACTIVATED` and capability registry are bounded operational structures. Core structural checks can block but cannot widen canonical StegGate or component-owner authority. The Core primitive performs no external execution and mints no continuity receipt.

Canonical source: `StegVerse-Labs/StegCore/docs/ADMISSIBLE_EXISTENCE_CAPABILITY_MODEL_MIRROR_HANDOFF.md`.

### StegVerse runtime authority

Runtime/route/credential authority remains with the explicitly governed component owner. For current StegVerse runtime credential semantics, TV/TVC is the authority boundary; GitHub-token runtime authority is `NONE`.

This orientation file does not create, store, request, or infer credentials.

## Settled distinctions workers must preserve

- existence != presence
- executable != admissible
- observation != authority
- observability != reconstructability
- reconstruction != execution
- validation != source doctrine
- TT structural relationship != execution authority
- sandbox/repair evidence != commit authority
- hosted workflow success != production activation
- source completion != live activation
- endpoint co-presence != automatically established relational continuity
- Core capability lifecycle != complete upstream AE theory

## Continuity and relationship interpretation

The canonical AE source already separates continuity recoverability, relational recoverability, observability, and reconstructability. Recent internal discussion has identified a useful interpretation: continuity can be considered through the observable/reconstructable relationship across otherwise distinct states or existences.

That interpretation is NOT silently promoted here to new canonical doctrine. Its current maturity and supporting sources are tracked in `docs/DISCOVERY_FRONTIER.md`.

Workers must therefore avoid both errors:

1. pretending this interpretation is absent from the architecture and reinventing the underlying components; or
2. declaring the interpretation a theorem/source invariant before its formal maturity is established.

## Reconstruction Singularity orientation

Reconstructive Singularity work already exists in the canonical program. A new worker must inspect existing RS records before proposing a new RS primitive.

Recent discussion around reality imprint, reconstruction resolution, latent endpoint discovery, resolution-dependent reconstruction boundaries, composite observers, and minimal-commitment discovery paths is preserved as a discovery frontier, not as automatically accepted formalism.

See `docs/DISCOVERY_FRONTIER.md`.

## Known orientation hazards

### 13 target elements vs 76 operational elements

`TT/FORMAL_STANDING_SPEC.md` contains an invariant referring to exactly 13 target transition elements, while the current TT handoff reports 76 unique transition elements across 11 registries.

Do not infer either contradiction or equivalence from those two numbers alone. The current registry hierarchy must be read before asserting the relationship. If the foundational-target -> expanded-operational relationship is not already explicit in current TT source, the clarification belongs to TT, not this coordination repository.

### Normative protocol vs source implementation

A normative protocol-documentation surface may remain planned inside AE while source doctrine or a reconstruction implementation is already complete in another canonical repository. Do not label completed source work missing merely because a separately governed normative publication surface is not yet complete.

### Internal Core implementation vs public-facing product map

The recent StegCore AE implementation is internal development infrastructure. The absence of a public/user-facing consumer map is not an implementation defect and must not be introduced as a requirement unless a separately admitted product/release goal creates it.

## Discovery frontier rule

The purpose of durable formalism is to increase the starting resolution of future work.

A worker should begin from settled architecture and push outward from the current frontier. It should not spend implementation cycles reconstructing already-durable concepts from chat history.

Canonical frontier: `docs/DISCOVERY_FRONTIER.md`.
Machine-readable orientation: `data/canonical-formalism-orientation.json`.
Validator: `scripts/validate_canonical_formalism_orientation.py`.

## Authority and security boundary

This orientation layer:

- creates no source-formalism authority;
- accepts no proof;
- creates no execution authority;
- creates no publication or release authority;
- creates no credential authority;
- requires no GitHub token runtime authority;
- does not create any NON-TV/TVC secret or token path.
