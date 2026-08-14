#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "canonical-formalism-orientation.json"
ORIENTATION = ROOT / "docs" / "CANONICAL_FORMALISM_ORIENTATION.md"
FRONTIER = ROOT / "docs" / "DISCOVERY_FRONTIER.md"

ALLOWED_MATURITY = {
    "CANONICAL_ESTABLISHED",
    "CONSISTENT_INTERPRETATION",
    "CANDIDATE_FORMALIZATION",
    "OPEN_EMPIRICAL",
}
ALLOWED_RELATIONSHIPS = {
    "IMPLEMENTS",
    "INTEGRATES",
    "VALIDATES",
    "EXTENDS",
    "CHALLENGES",
    "OBSERVES",
}
REQUIRED_TOP_LEVEL = {
    "schema",
    "goal_id",
    "canonical_issue",
    "scope",
    "public_user_facing",
    "creates_source_formalism_authority",
    "creates_execution_authority",
    "creates_validation_authority",
    "creates_credential_authority",
    "credential_authority_for_stegverse_runtime",
    "github_token_runtime_authority",
    "worker_rule",
    "maturity_classes",
    "concepts",
    "known_orientation_hazards",
    "frontier_ref",
    "human_orientation_ref",
    "validator_ref",
}
REQUIRED_CONCEPT_FIELDS = {
    "concept_id",
    "name",
    "maturity",
    "owner_repo",
    "canonical_sources",
    "canonical_statement",
    "authority_boundary",
    "non_claims",
    "common_misinterpretations",
}
REQUIRED_DOC_MARKERS = {
    ORIENTATION: [
        "internal workers",
        "TT is structural and non-authorizing",
        "StegCore is an internal operational consumer/projection",
        "Before proposing a new foundational abstraction",
        "GitHub-token runtime authority is `NONE`",
    ],
    FRONTIER: [
        "CANONICAL_ESTABLISHED",
        "CONSISTENT_INTERPRETATION",
        "CANDIDATE_FORMALIZATION",
        "OPEN_EMPIRICAL",
        "Anti-reinvention rule",
        "Promotion rule",
    ],
}


def fail(findings: list[str], message: str) -> None:
    findings.append(message)


def nonempty_list(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


def main() -> int:
    findings: list[str] = []

    for path in (REGISTRY, ORIENTATION, FRONTIER):
        if not path.is_file():
            fail(findings, f"missing_required_file:{path.relative_to(ROOT)}")

    if findings:
        print(json.dumps({"valid": False, "findings": findings}, indent=2, sort_keys=True))
        return 1

    try:
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"valid": False, "findings": [f"registry_parse_error:{exc}"]}, indent=2, sort_keys=True))
        return 1

    missing_top = sorted(REQUIRED_TOP_LEVEL - set(data))
    for field in missing_top:
        fail(findings, f"missing_top_level:{field}")

    if data.get("schema") != "admissible-existence.canonical-formalism-orientation/v1":
        fail(findings, "invalid_schema")
    if data.get("scope") != "internal_worker_orientation_only":
        fail(findings, "scope_must_be_internal_worker_orientation_only")
    if data.get("public_user_facing") is not False:
        fail(findings, "orientation_must_not_be_public_user_facing")

    for field in (
        "creates_source_formalism_authority",
        "creates_execution_authority",
        "creates_validation_authority",
        "creates_credential_authority",
    ):
        if data.get(field) is not False:
            fail(findings, f"authority_widening_forbidden:{field}")

    if data.get("credential_authority_for_stegverse_runtime") != "TV/TVC":
        fail(findings, "stegverse_runtime_credential_authority_must_be_TV_TVC")
    if data.get("github_token_runtime_authority") != "NONE":
        fail(findings, "github_token_runtime_authority_must_be_NONE")

    declared_maturity = data.get("maturity_classes")
    if set(declared_maturity or []) != ALLOWED_MATURITY:
        fail(findings, "maturity_classes_must_match_canonical_set")

    worker_rule = data.get("worker_rule") or {}
    if set(worker_rule.get("allowed_relationships_to_canon") or []) != ALLOWED_RELATIONSHIPS:
        fail(findings, "worker_relationship_classes_must_match_canonical_set")
    if worker_rule.get("extension_requires_insufficiency_record") is not True:
        fail(findings, "extension_must_require_insufficiency_record")
    if worker_rule.get("challenge_requires_falsifying_evidence") is not True:
        fail(findings, "challenge_must_require_falsifying_evidence")
    if worker_rule.get("orientation_may_widen_authority") is not False:
        fail(findings, "orientation_may_not_widen_authority")

    concepts = data.get("concepts")
    if not isinstance(concepts, list) or not concepts:
        fail(findings, "concepts_must_be_nonempty_list")
        concepts = []

    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    for index, concept in enumerate(concepts):
        if not isinstance(concept, dict):
            fail(findings, f"concept_not_object:{index}")
            continue
        missing = sorted(REQUIRED_CONCEPT_FIELDS - set(concept))
        for field in missing:
            fail(findings, f"concept_missing_field:{index}:{field}")

        concept_id = str(concept.get("concept_id") or "")
        name = str(concept.get("name") or "")
        if not concept_id.startswith("AEX-ORIENT-"):
            fail(findings, f"invalid_concept_id:{concept_id or index}")
        if concept_id in seen_ids:
            fail(findings, f"duplicate_concept_id:{concept_id}")
        seen_ids.add(concept_id)
        if not name:
            fail(findings, f"empty_concept_name:{concept_id}")
        if name in seen_names:
            fail(findings, f"duplicate_concept_name:{name}")
        seen_names.add(name)

        maturity = concept.get("maturity")
        if maturity not in ALLOWED_MATURITY:
            fail(findings, f"invalid_concept_maturity:{concept_id}:{maturity}")
        if maturity != "CANONICAL_ESTABLISHED":
            fail(findings, f"orientation_registry_concept_not_established:{concept_id}:{maturity}")

        owner = concept.get("owner_repo")
        if not isinstance(owner, str) or "/" not in owner:
            fail(findings, f"invalid_owner_repo:{concept_id}")
        if not nonempty_list(concept.get("canonical_sources")):
            fail(findings, f"missing_canonical_sources:{concept_id}")
        if not isinstance(concept.get("canonical_statement"), str) or not concept["canonical_statement"].strip():
            fail(findings, f"missing_canonical_statement:{concept_id}")
        if not isinstance(concept.get("authority_boundary"), str) or not concept["authority_boundary"].strip():
            fail(findings, f"missing_authority_boundary:{concept_id}")
        if not nonempty_list(concept.get("non_claims")):
            fail(findings, f"missing_non_claims:{concept_id}")
        if not nonempty_list(concept.get("common_misinterpretations")):
            fail(findings, f"missing_common_misinterpretations:{concept_id}")

    hazards = data.get("known_orientation_hazards")
    if not isinstance(hazards, list) or not hazards:
        fail(findings, "orientation_hazards_must_be_nonempty")
    else:
        hazard_ids: set[str] = set()
        for hazard in hazards:
            if not isinstance(hazard, dict):
                fail(findings, "hazard_not_object")
                continue
            hid = str(hazard.get("hazard_id") or "")
            if not hid.startswith("AEX-HAZARD-"):
                fail(findings, f"invalid_hazard_id:{hid}")
            if hid in hazard_ids:
                fail(findings, f"duplicate_hazard_id:{hid}")
            hazard_ids.add(hid)
            if not str(hazard.get("description") or "").strip():
                fail(findings, f"hazard_missing_description:{hid}")
            if not str(hazard.get("required_handling") or "").strip():
                fail(findings, f"hazard_missing_required_handling:{hid}")

    expected_refs = {
        "frontier_ref": "docs/DISCOVERY_FRONTIER.md",
        "human_orientation_ref": "docs/CANONICAL_FORMALISM_ORIENTATION.md",
        "validator_ref": "scripts/validate_canonical_formalism_orientation.py",
    }
    for field, expected in expected_refs.items():
        if data.get(field) != expected:
            fail(findings, f"invalid_ref:{field}:{data.get(field)}")

    for path, markers in REQUIRED_DOC_MARKERS.items():
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                fail(findings, f"missing_doc_marker:{path.relative_to(ROOT)}:{marker}")

    # Frontier items must carry an explicit maturity and may not silently claim
    # authority. This validator deliberately validates structure, not truth of
    # the frontier hypotheses.
    frontier_text = FRONTIER.read_text(encoding="utf-8")
    for maturity in ALLOWED_MATURITY:
        if f"`{maturity}`" not in frontier_text:
            fail(findings, f"frontier_missing_maturity_class:{maturity}")
    if "creates no proof, execution authority, release authority, certification authority, or credential authority" not in frontier_text:
        fail(findings, "frontier_missing_non_authority_boundary")

    result = {
        "schema": "admissible-existence.canonical-formalism-orientation-validation/v1",
        "goal_id": data.get("goal_id"),
        "valid": not findings,
        "concept_count": len(concepts),
        "hazard_count": len(hazards or []),
        "maturity_classes": sorted(ALLOWED_MATURITY),
        "credential_authority_for_stegverse_runtime": data.get("credential_authority_for_stegverse_runtime"),
        "github_token_runtime_authority": data.get("github_token_runtime_authority"),
        "authority_effect": "NONE",
        "findings": findings,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
