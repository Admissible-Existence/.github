# Tri-Form Formalism Contract

## Status

Candidate organization-level conformance contract for `AEX-TRIFORM-FORMALISM-001`.

## Purpose

A mathematical formalism is not considered fully bound merely because prose, equations, and code all exist. A conforming Tri-Form formalism must trace the same bounded semantic claims across three co-equal forms:

1. **Prose form** — human-readable semantics, scope, assumptions, limitations, counterexamples, and falsification conditions.
2. **Mathematical form** — formal objects, domains, relations, operators, invariants, unknown classes, transition functions, propositions, proofs/counterexamples, and admissibility conditions.
3. **Code form** — executable semantics, validators, witnesses, fixtures, deterministic tests, and reference implementations that instantiate the declared mathematical semantics.

The contract does not make prose mathematically equivalent to code in an unrestricted philosophical sense. It requires bounded traceable equivalence claims through stable semantic identifiers.

## Stable semantic identifiers

Every normative claim or principle participating in Tri-Form binding MUST have a stable identifier. Each identifier MUST map to explicit prose, mathematical, and code bindings.

A binding MAY identify propositions or hypotheses that are not yet proved, but the proof status MUST be explicit and MUST NOT be upgraded by structural conformance alone.

## Required binding dimensions

Each bound principle MUST declare:

- `principle_id`;
- `title`;
- normative/non-normative status;
- prose binding;
- mathematical binding;
- code binding;
- assumptions;
- invariants;
- unknown-class relevance;
- witness/test bindings;
- counterexample bindings where applicable;
- proof status;
- falsification conditions;
- equivalence status.

## Unknown classes

Unknowns are first-class candidate state semantics when the runtime can represent uncertainty.

A conforming formalism that handles unknowns SHOULD distinguish at minimum:

- known value;
- unknown domain;
- partially constrained unknown;
- conflicting evidence;
- unresolved predicate;
- unobservable/out-of-model fact.

Unknown domains MAY contract, expand, persist, or resolve across transitions. If governance can recognize a class of uncertainty at runtime, admissibility behavior for that class MUST be declared rather than delegated to an unspecified external decision mechanism.

A fully unobservable fact is not retroactively equivalent to a condition the runtime evaluated.

## Transition learning

A transition MAY change both known and unknown attributes. A conforming executable semantics SHOULD be able to represent changes to the relevant attribute state across the transition, including information gain, information loss, domain contraction/expansion, newly created conflicts, or predicate resolution.

Learning claims MUST remain bounded to what the formalism actually represents and measures.

## Maturity states

Suggested maturity sequence:

`THESIS -> PROSE_DEFINED -> MATHEMATICALLY_FORMALIZED -> EXECUTABLY_FORMALIZED -> TRIFORM_BOUND -> SIMULATED -> PROOF_COUNTEREXAMPLE_REVIEW -> INDEPENDENTLY_VALIDATED`

`TRIFORM_BOUND` is a structural and semantic binding state only. It does not imply proof, empirical truth, runtime activation, publication, release, credential, execution, or admissibility authority.

## Fail-closed conformance

The Tri-Form validator MUST fail when a required normative principle lacks any required counterpart or when its declared binding is internally incomplete.

The validator MUST NOT infer semantic equivalence from filenames, repository presence, workflow success, prose similarity, or common identifiers alone.

## Native ownership

The coordination repository MAY define schemas and organization conformance checks, but native source repositories retain ownership of their mathematics and executable semantics.

A cross-repository manifest is a binding record, not a transfer of mathematical authority.

## Pilot

The first pilot binds the existing relational-admissibility formalism in this repository. The pilot is intentionally bounded to prove the contract machinery and does not elevate the existing candidate propositions to proved status.
