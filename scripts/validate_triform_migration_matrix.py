#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "data" / "triform-migration-matrix.json"


def main():
    data = json.loads(MATRIX.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    repos = [e.get("repository") for e in entries]
    by_repo = {e.get("repository"): e for e in entries}
    findings = []

    if data.get("schema") != "admissible-existence.triform-migration-matrix/v2":
        findings.append("unexpected_schema")
    if data.get("registry_repository_count") != 32:
        findings.append("registry_repository_count_mismatch")
    if len(entries) != 32:
        findings.append("entry_count_mismatch")
    if len(set(repos)) != len(repos):
        findings.append("duplicate_repository")
    if data.get("completed_source_migrations") != 4:
        findings.append("completed_source_migration_count_mismatch")
    if data.get("completed_source_repositories") != [
        "Admissible-Existence/Existence",
        "Admissible-Existence/GTG",
        "Admissible-Existence/ET",
        "Admissible-Existence/learning-transition-governance",
    ]:
        findings.append("completed_source_repository_set_mismatch")

    existence = by_repo.get("Admissible-Existence/Existence", {})
    if existence.get("triform_state") != "BOUNDED_TRIFORM_COMPLETE_MERGED":
        findings.append("existence_completion_not_recorded")

    gtg = by_repo.get("Admissible-Existence/GTG", {})
    if gtg.get("triform_state") != "BOUNDED_TRIFORM_COMPLETE_MERGED_HISTORICAL_COLLISION_OPEN":
        findings.append("gtg_completion_or_collision_state_mismatch")
    if gtg.get("historical_gtg_a1_a8_equivalence") != "NOT_ESTABLISHED":
        findings.append("gtg_historical_equivalence_must_remain_not_established")

    et = by_repo.get("Admissible-Existence/ET", {})
    if et.get("triform_state") != "BOUNDED_TRIFORM_COMPLETE_MERGED_SEMANTIC_EXCLUSIONS":
        findings.append("et_completion_or_exclusion_state_mismatch")
    if et.get("bounded_principle_count") != 4:
        findings.append("et_bounded_principle_count_mismatch")
    if et.get("excluded_historical_equivalence_principles") != [
        "ET-AUTHORITY-003",
        "ET-TEMPORAL-004",
    ]:
        findings.append("et_semantic_exclusion_set_mismatch")
    if et.get("historical_source_replacement") is not False:
        findings.append("et_historical_source_replacement_must_remain_false")

    ltg = by_repo.get("Admissible-Existence/learning-transition-governance", {})
    if ltg.get("triform_state") != "BOUNDED_TRIFORM_COMPLETE_MERGED":
        findings.append("ltg_completion_not_recorded")
    if ltg.get("bounded_principle_count") != 4:
        findings.append("ltg_bounded_principle_count_mismatch")
    if ltg.get("identity_capture") is not False:
        findings.append("ltg_identity_capture_must_remain_false")
    if ltg.get("predetermined_intellectual_destination") is not False:
        findings.append("ltg_predetermined_destination_must_remain_false")
    if ltg.get("authority_effect") is not False:
        findings.append("ltg_authority_effect_must_remain_false")

    tt = by_repo.get("Admissible-Existence/TT", {})
    if data.get("logical_next_candidate") != "Admissible-Existence/TT":
        findings.append("unexpected_logical_next_candidate")
    if data.get("logical_candidate_state") != "DEFER_ACTIVE_CANONICAL_CLAIM":
        findings.append("tt_logical_candidate_must_be_deferred")
    if tt.get("triform_state") != "DEFER_ACTIVE_CANONICAL_CLAIM":
        findings.append("tt_entry_not_deferred")
    if tt.get("claim_state") != "CLAIMED_FOR_INTEGRATION":
        findings.append("tt_active_claim_not_preserved")

    stcm = by_repo.get("Admissible-Existence/STCM", {})
    if stcm.get("triform_state") != "DEFER_ACTIVE_CANONICAL_CLAIM":
        findings.append("stcm_entry_not_deferred")
    if stcm.get("claim_state") != "CLAIMED_FOR_INTEGRATION":
        findings.append("stcm_active_claim_not_preserved")

    if data.get("next_executable_candidate") is not None:
        findings.append("next_executable_candidate_requires_evidence_pass")
    if data.get("selection_evidence_state") != "EVIDENCE_PASS_REQUIRED":
        findings.append("selection_evidence_state_mismatch")

    for entry in entries:
        if not entry.get("triform_state"):
            findings.append(f"missing_triform_state:{entry.get('repository')}")

    valid = not findings
    print(json.dumps({
        "schema": "admissible-existence.triform-migration-validation/v2",
        "valid": valid,
        "entry_count": len(entries),
        "completed_source_migrations": data.get("completed_source_migrations"),
        "logical_next_candidate": data.get("logical_next_candidate"),
        "logical_candidate_state": data.get("logical_candidate_state"),
        "next_executable_candidate": data.get("next_executable_candidate"),
        "selection_evidence_state": data.get("selection_evidence_state"),
        "findings": findings,
        "authority_effect": "NONE_VALIDATION_ONLY"
    }, indent=2, sort_keys=True))
    raise SystemExit(0 if valid else 1)


if __name__ == "__main__":
    main()
