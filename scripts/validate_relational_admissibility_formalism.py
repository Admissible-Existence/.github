#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FORMALISM = ROOT / "data" / "relational-admissibility-formalism.json"
DOC = ROOT / "docs" / "RELATIONAL_ADMISSIBILITY_FORMALISM.md"
SCHEMA = ROOT / "schemas" / "relational-admissibility-transition.schema.json"
FIXTURES = ROOT / "fixtures" / "relational-admissibility" / "cases.json"

EXPECTED_SCHEMA = "admissible-existence.relational-admissibility-formalism/v1"
EXPECTED_TRANSITION_SCHEMA = "admissible-existence.relational-admissibility-transition/v1"
EXPECTED_AXIOMS = {f"A{i}" for i in range(1, 10)}
EXPECTED_CASES = {
    "ALLOW_REALIZES_REQUESTED_EFFECT",
    "DENY_IS_REAL_SUCCESSOR_TRANSITION",
    "REVIEW_CREATES_OBLIGATION_SUCCESSOR",
    "FAIL_CLOSED_RECORDS_EVIDENCE_GAP",
    "CONFIRMATION_CHANGES_TOTAL_STATE_WITHOUT_OBJECT_CHANGE",
    "COMPOSITION_CHANGES_RELATIONAL_RESOLUTION",
}
NON_ALLOW = {"DENY", "REVIEW", "FAIL_CLOSED"}
RELATION_STATES = {
    "CHANGED",
    "CONFIRMED_INVARIANT",
    "CONTRADICTED",
    "EMERGED",
    "DISAPPEARED",
    "DEPENDENCY_ESTABLISHED",
    "DEPENDENCY_REMOVED",
    "CONTINUITY_ESTABLISHED",
    "MANIFOLD_IMPLICATED",
    "MANIFOLD_DEIMPLICATED",
    "UNOBSERVED",
}
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
REQUIRED_TRANSITION_FIELDS = {
    "schema_version",
    "transition_id",
    "predecessor_state",
    "candidate",
    "governance_context",
    "resolution",
    "successor_state",
    "relations",
    "affected_components",
    "newly_implicated_components",
    "deimplicated_components",
    "observation_trigger",
    "authority_effect",
    "credential_authority",
    "github_token_runtime_authority",
}
DOC_MARKERS = [
    "Every governed admissibility resolution incorporated into system history realizes a successor state",
    "DENY != no transition",
    "Resolution classification is not the successor state",
    "Confirmation non-nullity",
    "confirmed unchanged",
    "not observed",
    "Local admissibility is not necessarily closed under composition",
    "A heartbeat, carrier, polling interval, or reference frame may transport",
    "The repositories in `Admissible-Existence` are adjacent mathematical projections",
    "`Admissible-Existence/AE` retains final commit-time admissibility resolution",
]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _require(condition: bool, findings: list[str], code: str) -> None:
    if not condition:
        findings.append(code)


def validate_state(state: Any, prefix: str) -> list[str]:
    findings: list[str] = []
    if not isinstance(state, dict):
        return [f"{prefix}:state_not_object"]
    for field in ("state_id", "state_hash", "component_states", "relation_states"):
        _require(field in state, findings, f"{prefix}:state_missing:{field}")
    if "state_hash" in state:
        _require(bool(SHA256_RE.match(str(state["state_hash"]))), findings, f"{prefix}:invalid_state_hash")
    _require(isinstance(state.get("component_states"), dict), findings, f"{prefix}:component_states_not_object")
    _require(isinstance(state.get("relation_states"), dict), findings, f"{prefix}:relation_states_not_object")
    return findings


def validate_transition(case_id: str, transition: Any) -> list[str]:
    findings: list[str] = []
    if not isinstance(transition, dict):
        return [f"{case_id}:transition_not_object"]

    for field in sorted(REQUIRED_TRANSITION_FIELDS - set(transition)):
        findings.append(f"{case_id}:missing_transition_field:{field}")
    if findings:
        return findings

    _require(transition.get("schema_version") == EXPECTED_TRANSITION_SCHEMA, findings, f"{case_id}:invalid_transition_schema")

    findings.extend(validate_state(transition.get("predecessor_state"), f"{case_id}:predecessor"))
    findings.extend(validate_state(transition.get("successor_state"), f"{case_id}:successor"))

    predecessor = transition.get("predecessor_state") or {}
    successor = transition.get("successor_state") or {}
    if isinstance(predecessor, dict) and isinstance(successor, dict):
        _require(predecessor.get("state_hash") != successor.get("state_hash"), findings, f"{case_id}:successor_state_hash_must_change")
        _require(predecessor.get("state_id") != successor.get("state_id"), findings, f"{case_id}:successor_state_id_must_change")

    candidate = transition.get("candidate")
    _require(isinstance(candidate, dict), findings, f"{case_id}:candidate_not_object")
    if isinstance(candidate, dict):
        for field in ("candidate_id", "sought_effect", "origin_component"):
            _require(field in candidate, findings, f"{case_id}:candidate_missing:{field}")

    governance = transition.get("governance_context")
    _require(isinstance(governance, dict), findings, f"{case_id}:governance_context_not_object")
    if isinstance(governance, dict):
        for field in ("evidence_refs", "policy_refs", "authority_basis_refs"):
            _require(isinstance(governance.get(field), list), findings, f"{case_id}:governance_field_not_list:{field}")

    resolution = transition.get("resolution")
    _require(isinstance(resolution, dict), findings, f"{case_id}:resolution_not_object")
    if isinstance(resolution, dict):
        for field in (
            "classification",
            "resolution_valid",
            "requested_effect_authorized",
            "requested_effect_realized",
            "reason_codes",
        ):
            _require(field in resolution, findings, f"{case_id}:resolution_missing:{field}")
        _require(resolution.get("resolution_valid") is True, findings, f"{case_id}:resolution_must_be_valid")
        _require(isinstance(resolution.get("requested_effect_authorized"), bool), findings, f"{case_id}:authorization_not_boolean")
        _require(isinstance(resolution.get("requested_effect_realized"), bool), findings, f"{case_id}:realization_not_boolean")
        _require(isinstance(resolution.get("reason_codes"), list) and bool(resolution.get("reason_codes")), findings, f"{case_id}:reason_codes_required")

        classification = resolution.get("classification")
        if classification in NON_ALLOW:
            _require(resolution.get("requested_effect_authorized") is False, findings, f"{case_id}:non_allow_must_not_authorize_requested_effect")
            _require(resolution.get("requested_effect_realized") is False, findings, f"{case_id}:non_allow_must_not_realize_requested_effect")
            # Non-ALLOW is still a realized governed transition. The changed
            # successor state checks above prove it is not represented as null.

    relations = transition.get("relations")
    _require(isinstance(relations, list), findings, f"{case_id}:relations_not_list")
    if isinstance(relations, list):
        for index, relation in enumerate(relations):
            rp = f"{case_id}:relation:{index}"
            _require(isinstance(relation, dict), findings, f"{rp}:not_object")
            if not isinstance(relation, dict):
                continue
            for field in (
                "relation_id",
                "subjects",
                "predicate",
                "state",
                "predecessor_value",
                "successor_value",
                "evidence_refs",
            ):
                _require(field in relation, findings, f"{rp}:missing:{field}")
            _require(relation.get("state") in RELATION_STATES, findings, f"{rp}:invalid_relation_state:{relation.get('state')}")
            _require(isinstance(relation.get("subjects"), list) and bool(relation.get("subjects")), findings, f"{rp}:subjects_required")
            _require(isinstance(relation.get("evidence_refs"), list), findings, f"{rp}:evidence_refs_not_list")

    affected = transition.get("affected_components")
    _require(isinstance(affected, list) and bool(affected), findings, f"{case_id}:affected_components_required")
    if isinstance(candidate, dict) and isinstance(affected, list):
        _require(candidate.get("origin_component") in affected, findings, f"{case_id}:origin_component_must_be_affected")

    _require(isinstance(transition.get("newly_implicated_components"), list), findings, f"{case_id}:newly_implicated_not_list")
    _require(isinstance(transition.get("deimplicated_components"), list), findings, f"{case_id}:deimplicated_not_list")

    _require(
        transition.get("observation_trigger") in {"STATE_TRANSITION", "EXPLICIT_CLOCK_STATE_TRANSITION"},
        findings,
        f"{case_id}:invalid_observation_trigger",
    )
    _require(transition.get("observation_trigger") != "PERIODIC_HEARTBEAT", findings, f"{case_id}:periodic_heartbeat_may_not_be_primitive_trigger")
    _require(transition.get("authority_effect") == "NONE", findings, f"{case_id}:authority_effect_must_be_NONE")
    _require(transition.get("credential_authority") == "TV/TVC", findings, f"{case_id}:credential_authority_must_be_TV_TVC")
    _require(transition.get("github_token_runtime_authority") == "NONE", findings, f"{case_id}:github_token_runtime_authority_must_be_NONE")

    if case_id == "CONFIRMATION_CHANGES_TOTAL_STATE_WITHOUT_OBJECT_CHANGE":
        _require(predecessor.get("component_states") == successor.get("component_states"), findings, f"{case_id}:fixture_must_preserve_object_values")
        _require(predecessor.get("state_hash") != successor.get("state_hash"), findings, f"{case_id}:confirmation_must_change_total_state_hash")
        _require(
            any(isinstance(r, dict) and r.get("state") == "CONFIRMED_INVARIANT" for r in relations or []),
            findings,
            f"{case_id}:confirmation_relation_required",
        )

    if case_id == "COMPOSITION_CHANGES_RELATIONAL_RESOLUTION":
        _require(resolution.get("classification") == "REVIEW", findings, f"{case_id}:composition_fixture_must_resolve_review")
        _require(len(affected or []) >= 3, findings, f"{case_id}:composition_fixture_must_cross_components")

    return findings


def validate_repository() -> dict[str, Any]:
    findings: list[str] = []
    for path in (FORMALISM, DOC, SCHEMA, FIXTURES):
        _require(path.is_file(), findings, f"missing_required_file:{path.relative_to(ROOT)}")
    if findings:
        return {"valid": False, "findings": findings}

    formalism = load(FORMALISM)
    schema = load(SCHEMA)
    fixtures = load(FIXTURES)

    _require(formalism.get("schema") == EXPECTED_SCHEMA, findings, "formalism:invalid_schema")
    _require(formalism.get("goal_id") == "AEX-RELATIONAL-ADMISSIBILITY-001", findings, "formalism:invalid_goal_id")
    _require(formalism.get("maturity") == "CANDIDATE_FORMALIZATION", findings, "formalism:invalid_maturity")
    _require(formalism.get("coordination_repository") == "Admissible-Existence/.github", findings, "formalism:invalid_coordination_repository")
    _require(formalism.get("admissibility_resolver") == "Admissible-Existence/AE", findings, "formalism:AE_must_remain_resolver")
    _require(formalism.get("source_mathematics_model") == "ADJACENT_REPOSITORY_PROJECTIONS", findings, "formalism:invalid_source_mathematics_model")

    for field in (
        "creates_source_formalism_authority",
        "creates_execution_authority",
        "creates_validation_authority",
        "creates_credential_authority",
        "creates_publication_authority",
        "creates_release_authority",
        "render_dependency",
    ):
        _require(formalism.get(field) is False, findings, f"formalism:authority_or_dependency_must_be_false:{field}")

    _require(formalism.get("credential_authority_for_stegverse_runtime") == "TV/TVC", findings, "formalism:credential_authority_must_be_TV_TVC")
    _require(formalism.get("github_token_runtime_authority") == "NONE", findings, "formalism:github_token_runtime_authority_must_be_NONE")

    axioms = formalism.get("axioms")
    _require(isinstance(axioms, list), findings, "formalism:axioms_not_list")
    axiom_ids = {a.get("id") for a in axioms if isinstance(a, dict)} if isinstance(axioms, list) else set()
    _require(axiom_ids == EXPECTED_AXIOMS, findings, f"formalism:axiom_set_mismatch:{sorted(axiom_ids)}")

    requirements = formalism.get("conformance_requirements") or {}
    for key in (
        "resolution_validity_independent_of_allow",
        "non_allow_has_successor_state",
        "confirmation_changes_total_state",
        "confirmed_invariant_distinct_from_unobserved",
        "material_cross_component_relations_preserved",
        "local_validity_not_sufficient_for_org_admissibility",
        "observation_triggered_by_transition",
        "periodic_heartbeat_not_primitive_cause",
        "composition_may_change_resolution",
    ):
        _require(requirements.get(key) is True, findings, f"formalism:missing_conformance_requirement:{key}")

    schema_required = set(schema.get("required") or [])
    _require(schema_required == REQUIRED_TRANSITION_FIELDS, findings, "schema:required_fields_must_match_formalism")

    doc_text = DOC.read_text(encoding="utf-8")
    for marker in DOC_MARKERS:
        _require(marker in doc_text, findings, f"doc:missing_marker:{marker}")

    cases = fixtures.get("cases")
    _require(isinstance(cases, list) and bool(cases), findings, "fixtures:cases_required")
    seen: set[str] = set()
    if isinstance(cases, list):
        for case in cases:
            if not isinstance(case, dict):
                findings.append("fixtures:case_not_object")
                continue
            case_id = str(case.get("case_id") or "")
            _require(bool(case_id), findings, "fixtures:case_id_required")
            _require(case_id not in seen, findings, f"fixtures:duplicate_case:{case_id}")
            seen.add(case_id)
            _require(case.get("expected_valid") is True, findings, f"{case_id}:expected_valid_must_be_true")
            findings.extend(validate_transition(case_id, case.get("transition")))

    _require(seen == EXPECTED_CASES, findings, f"fixtures:case_coverage_mismatch:{sorted(seen)}")

    result = {
        "schema": "admissible-existence.relational-admissibility-validation/v1",
        "goal_id": formalism.get("goal_id"),
        "valid": not findings,
        "axiom_count": len(axiom_ids),
        "fixture_count": len(seen),
        "admissibility_resolver": formalism.get("admissibility_resolver"),
        "coordination_repository": formalism.get("coordination_repository"),
        "credential_authority_for_stegverse_runtime": formalism.get("credential_authority_for_stegverse_runtime"),
        "github_token_runtime_authority": formalism.get("github_token_runtime_authority"),
        "authority_effect": "NONE",
        "findings": findings,
    }
    return result


def main() -> int:
    result = validate_repository()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
