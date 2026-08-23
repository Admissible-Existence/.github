#!/usr/bin/env python3
"""Validate the bounded VerFi external-formalism candidate and governance fixtures."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "external-formalisms" / "verfi.json"
FIXTURES = ROOT / "fixtures" / "external-formalisms" / "verfi-governance-lanes.json"
DOC = ROOT / "docs" / "external-formalisms" / "VERFI.md"

REQUIRED_SEQUENCE = [
    "IDENTITY",
    "DISCLOSURE",
    "COMPREHENSION",
    "AUTHORIZATION",
    "SIGNATURE",
    "EVIDENCE",
]
REQUIRED_PUBLIC_SOURCES = {
    "https://verfisystems.com/",
    "https://verfisystems.com/consent-records",
}
REQUIRED_PUBLIC_RECORD_ELEMENTS = {
    "session_initiation_and_continuity",
    "identity_bound_participant_attribution",
    "education_delivery_confirmation",
    "recorded_comprehension_interaction_and_responses",
    "timestamped_authorization_enablement",
}
REQUIRED_CASES = {
    "CLEAN_SEQUENCE": "ALLOW_CANDIDATE",
    "COMPREHENSION_MISSING": "AUTHORIZATION_INADMISSIBLE",
    "DISCLOSURE_DRIFT": "REVIEW",
    "AUTHORIZATION_LAPSED": "DENY",
    "EVIDENCE_TAMPER": "FAIL_CLOSED",
    "TEMPORAL_DISORDER": "FAIL_CLOSED",
    "AMBIGUOUS_COMPREHENSION": "REVIEW",
    "OVER_COLLECTION": "REVIEW_MINIMIZATION",
    "INDEPENDENT_RECONSTRUCTION": "ALLOW_CANDIDATE",
    "HUMAN_MACHINE_SYMMETRY": "STRUCTURAL_COMPARISON_ONLY",
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def evaluate(case: dict) -> str:
    if case.get("id") == "HUMAN_MACHINE_SYMMETRY":
        require(case.get("machine_comparison_only") is True, "symmetry lane must remain comparison-only")
        return "STRUCTURAL_COMPARISON_ONLY"
    if not case.get("evidence_integrity") or not case.get("temporal_order_valid"):
        return "FAIL_CLOSED"
    if case.get("disclosure") is not True:
        return "DISCLOSURE_NOT_ESTABLISHED"
    if case.get("presented_hash") != case.get("authorized_hash"):
        return "REVIEW"
    comprehension = case.get("comprehension_evidence")
    if comprehension == "ABSENT":
        return "AUTHORIZATION_INADMISSIBLE"
    if comprehension != "DISTINGUISHABLE":
        return "REVIEW"
    if not case.get("authorization_valid_at_commit"):
        return "DENY"
    if case.get("signature") is not True:
        return "SIGNATURE_NOT_ESTABLISHED"
    if not case.get("minimum_information_satisfied"):
        return "REVIEW_MINIMIZATION"
    if not case.get("reconstructable"):
        return "FAIL_CLOSED"
    return "ALLOW_CANDIDATE"


def main() -> int:
    registry = load_json(REGISTRY)
    fixtures = load_json(FIXTURES)
    doc = DOC.read_text(encoding="utf-8")

    require(registry.get("external_formalism_id") == "VERFI-HUMAN-TRANSITION-EVIDENCE-001", "wrong formalism id")
    require(registry.get("status") == "BOUNDARY_REVIEW_TEST_CANDIDATE", "candidate must remain bounded")

    source = registry.get("source_basis", {})
    require(source.get("type") == "publisher_public_product_representation", "candidate must record publisher public-source posture")
    require(source.get("publisher") == "VerFi Holdings Inc.", "unexpected publisher identity")
    require(source.get("sequence") == REQUIRED_SEQUENCE, "unexpected external sequence")
    require(set(source.get("sources", [])) == REQUIRED_PUBLIC_SOURCES, "public source set changed")
    require(set(source.get("publicly_declared_record_elements", [])) == REQUIRED_PUBLIC_RECORD_ELEMENTS, "public record-element set changed")
    require(source.get("claim_posture") == "PUBLISHER_ASSERTED_NOT_INDEPENDENTLY_VERIFIED", "publisher claims must remain explicitly unverified")
    require(source.get("publicly_declared_control_semantics", {}).get("comprehension_checkpoints_required_before_consent_finalization") is True, "checkpoint gate claim missing")
    require(source.get("publicly_declared_control_semantics", {}).get("missed_checkpoint_re_presents_term_and_preserves_correction") is True, "checkpoint correction claim missing")
    require(source.get("publicly_declared_control_semantics", {}).get("exact_disclosure_version_recorded") is True, "disclosure-version claim missing")
    require(source.get("publicly_declared_control_semantics", {}).get("execution_verified_token_claimed") is True, "Execution Verified Token public claim missing")
    require(source.get("implementation_artifact_available") is False, "do not claim implementation artifact")
    require(source.get("schema_available") is False, "do not claim external schema")
    require(source.get("api_output_available") is False, "do not claim external API output")
    require(source.get("execution_verified_token_artifact_available") is False, "do not claim Execution Verified Token artifact")

    boundary = registry.get("stegverse_boundary", {})
    require(boundary.get("admissibility_resolver") == "Admissible-Existence/AE", "AE resolver boundary changed")
    for forbidden in (
        "external_package_creates_admissibility_authority",
        "external_package_creates_execution_authority",
        "external_package_creates_canonicality",
        "external_package_proves_internal_mental_state",
        "external_package_proves_requested_effect_realized",
        "external_execution_verified_token_creates_stegverse_authority",
    ):
        require(boundary.get(forbidden) is False, f"forbidden authority/claim enabled: {forbidden}")

    require(registry.get("authority_effect") == "NONE_VALIDATION_ONLY", "validator may not create authority")
    require(registry.get("mandatory_negative_outcome") == [
        "DISCLOSURE_ESTABLISHED",
        "COMPREHENSION_NOT_ESTABLISHED",
        "AUTHORIZATION_INADMISSIBLE",
    ], "mandatory negative outcome changed")

    transition_targets = set(registry.get("transition_targets", []))
    require("CHECKPOINT_FAILED->TERM_REPRESENTED->CORRECTION_PRESERVED" in transition_targets, "checkpoint correction target missing")
    require("AUTHORIZATION_DISABLED->AUTHORIZATION_ENABLED" in transition_targets, "authorization enablement target missing")

    cases = fixtures.get("cases", [])
    require(len(cases) == 10, "expected exactly 10 initial governance-lane cases")
    by_id = {case.get("id"): case for case in cases}
    require(set(by_id) == set(REQUIRED_CASES), "lane ids do not match required matrix")

    for case_id, expected in REQUIRED_CASES.items():
        case = by_id[case_id]
        require(case.get("expected") == expected, f"fixture expected value mismatch: {case_id}")
        observed = evaluate(case)
        require(observed == expected, f"deterministic lane result mismatch for {case_id}: {observed} != {expected}")

    negative = by_id["COMPREHENSION_MISSING"]
    require(negative.get("disclosure") is True, "negative invariant requires established disclosure")
    require(negative.get("signature") is True, "negative invariant must survive presence of signature")
    require(evaluate(negative) == "AUTHORIZATION_INADMISSIBLE", "signature must not force comprehension success")

    reconstruction = by_id["INDEPENDENT_RECONSTRUCTION"]
    require(reconstruction.get("reconstructable") is True, "reconstruction fixture must be reconstructable")

    required_doc_markers = [
        "BOUNDARY_REVIEW / TEST_CANDIDATE",
        "Admissible-Existence/AE",
        "COMPREHENSION_NOT_ESTABLISHED",
        "AUTHORIZATION_INADMISSIBLE",
        "HUMAN_MACHINE_SYMMETRY",
        "Execution Verified Token",
        "CHECKPOINT_CORRECTION_PRESERVATION",
        "AUTHORIZATION_ENABLEMENT_CAUSALITY",
        "publisher assertions",
    ]
    for marker in required_doc_markers:
        require(marker in doc, f"documentation missing marker: {marker}")

    print(json.dumps({
        "valid": True,
        "external_formalism_id": registry["external_formalism_id"],
        "status": registry["status"],
        "lane_count": len(cases),
        "negative_invariant": "PASS",
        "public_source_grounding": "PASS",
        "execution_verified_token_authority_boundary": "PASS",
        "authority_effect": registry["authority_effect"],
        "admissibility_resolver": boundary["admissibility_resolver"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
