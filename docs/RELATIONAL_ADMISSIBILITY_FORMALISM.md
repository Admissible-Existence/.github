# Relational Admissibility and Successor-State Formalism

**Goal ID:** `AEX-RELATIONAL-ADMISSIBILITY-001`  
**Coordination owner:** `Admissible-Existence/.github`  
**Admissibility resolver:** `Admissible-Existence/AE`  
**Task:** `Admissible-Existence/.github#9`  
**Maturity:** `CANDIDATE_FORMALIZATION`  
**Authority effect:** `NONE`

## 1. Scope and ownership

This document defines a cross-repository mathematical contract for representing governed state transitions from singular state variables through coupled multi-manifold systems. It does not centralize source mathematics in this repository.

The repositories in `Admissible-Existence` are adjacent mathematical projections. Each repository retains ownership of its native mathematical objects. This repository coordinates the relation registry, conformance rules, and cross-repository validation surface. `Admissible-Existence/AE` retains final commit-time admissibility resolution.

The formalism therefore distinguishes:

1. **source mathematics** owned by adjacent repositories;
2. **relations among source mathematics** represented by a cross-repository graph;
3. **admissibility resolution** owned by AE;
4. **organization-level conformance** checked here without granting execution, proof, publication, release, or credential authority.

For StegVerse runtime interactions, credential authority remains `TV/TVC`; GitHub-token runtime authority is `NONE`. No Render dependency or authority is introduced.

## 2. Primitive state

Let a distinguishable state be

\[
S_i \in \mathcal S.
\]

`S_i` may be discrete, continuous, hybrid, partially observed, relational, or composite. Time, persistence, purpose, continuity, and goal are not required as primitives of the transition relation.

A candidate or implicated transition is written

\[
p_i : S_i \rightsquigarrow \mathcal S.
\]

The symbol `\rightsquigarrow` denotes a sought or implicated possibility. It does not assert that the sought effect has occurred.

## 3. Governed admissibility resolution

For predecessor state `S_i`, candidate `p_i`, admissible evidence/context `E_i`, and governing state `G_i`, define the admissibility resolver

\[
\mathcal A(S_i,p_i,E_i,G_i)=(R_i,S_j,Q_{ij}).
\]

where:

- `R_i` is a governed **resolution classification**;
- `S_j` is the **realized successor state**;
- `Q_{ij}` is the set of relations established, confirmed, contradicted, removed, or newly implicated by the resolution and its observation.

A resolution classification may include `ALLOW`, `DENY`, `REVIEW`, `FAIL_CLOSED`, or profile-defined extensions. The classification vocabulary does not enumerate successor-state space.

### Definition D1 — Resolution validity

`resolution_valid(A_i)` means that the resolver produced a structurally and evidentially valid governed resolution under the applicable profile. It is independent of whether the sought effect was authorized or realized.

### Definition D2 — Requested-effect authorization

`requested_effect_authorized(A_i)` states whether the sought effect may be realized under the resolution.

Therefore

\[
resolution\_valid \not\equiv requested\_effect\_authorized.
\]

A valid `DENY`, `REVIEW`, or `FAIL_CLOSED` may satisfy `resolution_valid=true` while `requested_effect_authorized=false`.

### Definition D3 — Requested-effect realization

`requested_effect_realized(A_i)` records whether the sought effect became part of the successor state. It is distinct from both resolution validity and authorization.

This separates three questions:

\[
\text{Was the resolution valid?}
\]

\[
\text{Was the requested effect authorized?}
\]

\[
\text{Was the requested effect realized?}
\]

## 4. Axioms

### Axiom A1 — Resolution realization

Every governed admissibility resolution incorporated into system history realizes a successor state:

\[
\forall A_i\in H,\; \exists S_j\in\mathcal S:
\mathcal A(S_i,p_i,E_i,G_i)=(R_i,S_j,Q_{ij}).
\]

A non-ALLOW result is not the absence of a transition. It is a realized governed transition whose successor state differs from the successor state sought by the candidate where the sought effect is not realized.

Consequently:

```text
DENY != no transition
REVIEW != no transition
FAIL_CLOSED != no transition
```

### Axiom A2 — Resolution-class / successor-state separation

\[
R_i \neq S_j.
\]

`R_i` classifies the governed resolution. `S_j` is the full resulting state. Two transitions with identical resolution classifications may produce different successor states.

### Axiom A3 — Requested-effect separation

Let the candidate seek `S_x`:

\[
p_i:S_i\rightsquigarrow S_x.
\]

A governed resolution may produce

\[
S_i\xrightarrow{R_i}S_j
\]

with

\[
S_j\neq S_x.
\]

Therefore non-realization of `S_x` does not imply absence of transition information or absence of successor state.

### Axiom A4 — Confirmation non-nullity

Let an observed object-level quantity satisfy

\[
x_j=x_i.
\]

If the transition establishes a new evidentiary, provenance, continuity, or relational fact

\[
q=\operatorname{Confirm}(x_i,x_j),
\]

then

\[
\Delta x=0
\]

does not imply

\[
\Delta S=0.
\]

The exact confirmation relation is part of successor state. `confirmed unchanged`, `not observed`, and `contradicted` are therefore distinguishable successor conditions.

### Axiom A5 — Relational closure

A transition is not completely represented by its nominal target value. Its successor representation MUST include all known material relation changes and confirmations implicated by the transition within the applicable concern boundary.

If `Q(M_a,M_b)` is a material relation and a transition changes or establishes its state, then the successor representation includes that relational consequence even when `M_b`'s primary object value is invariant.

### Axiom A6 — Concern-set propagation

For a transition originating in manifold or component `M_i`, define the direct concern set `C_0={M_i}`. Relational closure expands concern by material coupling:

\[
C_{k+1}=C_k\cup\{M_j\mid \exists M_a\in C_k:\operatorname{MaterialRelation}(M_a,M_j)\}.
\]

Evaluation need not expand to every manifold merely because the organization exists. Expansion follows material transition relations. The stable concerned set is

\[
C^*=\bigcup_{k\ge0}C_k
\]

subject to the governing profile's bounded observability and evidence conditions.

### Axiom A7 — Transition-caused observation

Observation of a realized transition is consequent to state transition, not to elapsed periodic time:

\[
T_i\Rightarrow O_i.
\]

A heartbeat, carrier, polling interval, or reference frame may transport, synchronize, index, decompose, or test observations. It is not the primitive cause of the observed state transition.

A clock-derived condition may itself become operative state only when an applicable governing profile explicitly represents it as such.

### Axiom A8 — Composition sensitivity

Local admissibility is not necessarily closed under composition.

For transitions `a` and `b`, it does not generally follow that

\[
A(a)=\mathrm{valid}\land A(b)=\mathrm{valid}
\]

implies

\[
A(a\circ b)=\mathrm{valid}.
\]

Ordering, coupling, concurrent effects, shared dependencies, authority, evidence, or relation changes may alter the admissibility of the composite successor state.

### Axiom A9 — Authority non-generation

Observation, validation, confirmation, relational coherence, workflow execution, repository publication, and this formalism do not themselves generate execution authority, source-mathematics authority, credential authority, release authority, or proof standing.

## 5. Observation relation

For realized predecessor and successor states define an observation relation

\[
\mathcal O(S_i,S_j,E_{ij})=Q_{ij}.
\]

`Q_{ij}` may contain relations such as:

- `CHANGED`;
- `CONFIRMED_INVARIANT`;
- `CONTRADICTED`;
- `EMERGED`;
- `DISAPPEARED`;
- `DEPENDENCY_ESTABLISHED`;
- `DEPENDENCY_REMOVED`;
- `CONTINUITY_ESTABLISHED`;
- `MANIFOLD_IMPLICATED`;
- `MANIFOLD_DEIMPLICATED`;
- profile-defined relation predicates.

This list is extensible and is not an exhaustive ontology.

Once established and retained, `Q_{ij}` contributes to the system's next distinguishable state. Thus observation is not merely discarded metadata.

## 6. Continuity as derived relation

For an observed sequence

\[
S_0,S_1,\ldots,S_n,
\]

with relations

\[
Q_{01},Q_{12},\ldots,Q_{n-1,n},
\]

continuity may be derived as

\[
\mathcal C(S_0,\ldots,S_n)=F(Q_{01},Q_{12},\ldots,Q_{n-1,n}).
\]

This formalism does not require continuity as the primitive explanation for transition. Continuity is established from relations among distinguishable observations where the applicable formalism supports that inference.

## 7. Multi-manifold state

Let an operative system state contain manifolds

\[
\mathfrak M_i=\{M_i^1,M_i^2,\ldots,M_i^n\}.
\]

A realized transition is

\[
T_i:\mathfrak M_i\rightarrow\mathfrak M_j.
\]

Its relational consequence set may include

\[
Q_{ij}=\{\Delta M^k,\operatorname{Confirm}(M^\ell),\Delta Q(M^a,M^b),+M^c,-M^d\}.
\]

where `+M` denotes newly implicated concern and `-M` denotes de-implicated concern. These are representational operators, not claims that manifolds are created or destroyed by notation alone.

## 8. Adjacent-repository mathematical graph

Let each repository or formal component be a vertex:

\[
V=\{C_1,C_2,\ldots,C_n\}.
\]

Let material mathematical relations be edges:

\[
E=\{Q_{ab}\}.
\]

The organization-level state is

\[
\Omega=(\mathbf S,\mathbf Q,\mathbf E_v)
\]

where:

- `\mathbf S` is the set of component/source states;
- `\mathbf Q` is the set of declared cross-component mathematical relations;
- `\mathbf E_v` is evidence/provenance establishing or challenging those relations.

No single repository is required to contain the entire formalism. Each source repository exposes a projection

\[
\pi_i:\mathcal F\rightarrow F_i
\]

of the larger formal structure into its native domain.

The `.github` coordination layer registers and validates relations among projections. It does not become the mathematical source of each projection.

## 9. Organization-level relational admissibility

For organization state `\Omega_n` and a candidate local change `p_i`, define

\[
\mathcal A_\Omega(\Omega_n,p_i,E_n,G_n)
=(R_n,\Omega_{n+1},\Delta Q_n).
\]

A repository-local change is not organizationally admissible merely because its local tests pass. Material relations to concerned adjacent components must remain valid, be newly resolved, or produce an applicable non-ALLOW successor state.

Therefore:

\[
\operatorname{LocalValid}(p_i)
\not\Rightarrow
\operatorname{RelationallyAdmissible}(p_i).
\]

Conversely, confirming that a relation remains invariant is itself successor-state information and MUST be distinguishable from failure to observe the relation.

## 10. Recursive transition-observation structure

The general recursion is

\[
p_i
\rightarrow
\mathcal A
\rightarrow
S_j
\rightarrow
\mathcal O
\rightarrow
Q_{ij}
\rightarrow
C^*
\rightarrow
\{p_{j1},p_{j2},\ldots\}.
\]

Any newly sought effects again require governed admissibility resolution. The observer does not obtain self-authorization from observation.

This recursion is driven by state-transition consequences. Periodic heartbeat may remain useful for reference coordinates, liveness evidence, synchronization, freshness, or signal decomposition, but it is secondary to transition-caused observation.

## 11. Minimum transition receipt structure

A conforming transition receipt MUST be able to preserve, when applicable:

1. predecessor state identity/hash;
2. candidate or implicated transition identity;
3. governing evidence/context references;
4. resolution classification;
5. resolution validity;
6. requested-effect authorization;
7. requested-effect realization;
8. realized successor state identity/hash;
9. object-level changes;
10. confirmed invariants;
11. contradictions;
12. emerged/disappeared relations;
13. affected manifolds/components;
14. newly implicated and de-implicated manifolds/components;
15. provenance for established relations;
16. observation trigger semantics;
17. authority-effect declaration.

The receipt schema does not require every domain to use identical internal state representations. It requires sufficient structure to reconstruct the governed successor relation.

## 12. Conformance rules

An organization-level conformance validator MUST reject a transition representation that:

- equates admissibility with `ALLOW`;
- sets resolution validity solely from `classification == ALLOW`;
- treats `DENY`, `REVIEW`, or `FAIL_CLOSED` as absence of a successor transition;
- conflates resolution classification with successor state;
- records invariant object values as `no transition` when a new confirmation relation was established;
- conflates `confirmed invariant` with `not observed`;
- omits known material cross-component relation changes from the concerned successor state;
- assumes repository-local PASS proves organization-level admissibility;
- treats periodic heartbeat as the causal primitive of observation;
- grants execution, credential, source, release, proof, or publication authority from validation or observation.

## 13. Formal propositions for further proof development

The following are candidate propositions, not yet accepted theorems.

### P1 — Non-ALLOW information preservation

Under A1-A5, a valid non-ALLOW resolution preserves non-null successor-state information even when the requested effect is not realized.

### P2 — Confirmation distinguishability

Under A4 and content-addressed successor-state representation, a newly established confirmation relation is distinguishable from an unobserved invariant.

### P3 — Relational closure necessity

Under A5-A6, local successor-state sufficiency fails whenever a material relation outside the local component changes and is omitted from the successor representation.

### P4 — Composition counterexample existence

Under A8, there exist coupled systems where two individually valid local transitions yield a composite state requiring a different resolution classification.

### P5 — Observation recursion without periodic causation

Under A7, a transition-observation chain may propagate through realized transition consequences without treating periodic heartbeat as the causal primitive.

These propositions require proof or counterexample development in the owning mathematical repositories before promotion to accepted theorem status.

## 14. Relationship to existing Admissible-Existence repositories

This coordination formalism is intended to map onto adjacent repositories rather than replace them. Expected relations include:

- `AE`: admissibility resolver and theory integration;
- `Existence`: distinguishable existence/standing representation;
- `RTG`: relational transition geometry;
- `GTG`: governed/reconstructive transition structures;
- `TT`: transition element/table structure and outcome regions;
- `STCM`, `IICT`, `CTA`, `BC`, `CHF`, `DC`, `DaCo`, and others: domain-specific mathematical projections where live source contracts establish a relation;
- `validator`, `ae-validation-factory`, `validation-profile-registry`: conformance and independent-validation support without source ownership.

No mapping is considered established solely because it is listed here. Exact mappings require source-specific evidence and repository-native admission.

## 15. Promotion path

Current maturity is `CANDIDATE_FORMALIZATION`.

Promotion requires:

1. deterministic structural validation of this coordination representation;
2. explicit mapping into `Admissible-Existence/AE` without collision with current canonical AE work;
3. proof/counterexample review of P1-P5;
4. source-repository relation contracts for each claimed adjacent mapping;
5. independent validation in the appropriate validation repository;
6. no inference of runtime, publication, release, or ecosystem activation from CI success alone.

## 16. Non-claims

This document:

- does not claim external-standard status;
- does not claim P1-P5 are proven theorems;
- does not claim every listed adjacent repository has already been mapped;
- does not authorize source-repository changes;
- does not authorize production/runtime execution;
- does not authorize publication or release;
- does not create credential authority;
- does not create Master Records authority;
- does not create wallet, trade, signing, or broadcast authority;
- does not use or require NON-TV/TVC secrets or tokens.
