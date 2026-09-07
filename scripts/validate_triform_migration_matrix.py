#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / 'data/triform-migration-matrix.json'

EXPECTED_COMPLETED = [
    'Admissible-Existence/Existence','Admissible-Existence/GTG','Admissible-Existence/ET',
    'Admissible-Existence/learning-transition-governance','Admissible-Existence/BC',
    'Admissible-Existence/CHF','Admissible-Existence/RE','Admissible-Existence/RE-Reduction',
    'Admissible-Existence/DC','Admissible-Existence/Triad','Admissible-Existence/GCAT-BCAT',
    'Admissible-Existence/ECAT-ICAT','Admissible-Existence/IICT','Admissible-Existence/HPS',
    'Admissible-Existence/FI'
]


def require(cond, finding, findings):
    if not cond:
        findings.append(finding)


def main():
    data = json.loads(MATRIX.read_text(encoding='utf-8'))
    entries = data.get('entries', [])
    repos = [e.get('repository') for e in entries]
    by = {e.get('repository'): e for e in entries}
    f = []

    require(data.get('schema') == 'admissible-existence.triform-migration-matrix/v2', 'unexpected_schema', f)
    require(data.get('refresh_goal_id') == 'AEX-TRIFORM-MIGRATION-REFRESH-015', 'refresh_goal_id_mismatch', f)
    require(data.get('selection_goal_id') == 'AEX-TRIFORM-MIGRATION-REFRESH-015-SELECTION', 'selection_goal_id_mismatch', f)
    require(data.get('registry_repository_count') == 32, 'registry_repository_count_mismatch', f)
    require(len(entries) == 32, 'entry_count_mismatch', f)
    require(len(set(repos)) == len(repos), 'duplicate_repository', f)
    require(data.get('completed_source_migrations') == 15, 'completed_source_migration_count_mismatch', f)
    require(data.get('completed_source_repositories') == EXPECTED_COMPLETED, 'completed_source_repository_set_mismatch', f)

    gtg = by.get('Admissible-Existence/GTG', {})
    et = by.get('Admissible-Existence/ET', {})
    ltg = by.get('Admissible-Existence/learning-transition-governance', {})
    bc = by.get('Admissible-Existence/BC', {})
    chf = by.get('Admissible-Existence/CHF', {})
    re = by.get('Admissible-Existence/RE', {})
    rr = by.get('Admissible-Existence/RE-Reduction', {})
    dc = by.get('Admissible-Existence/DC', {})
    triad = by.get('Admissible-Existence/Triad', {})
    gcat = by.get('Admissible-Existence/GCAT-BCAT', {})
    ecat = by.get('Admissible-Existence/ECAT-ICAT', {})
    iict = by.get('Admissible-Existence/IICT', {})
    hps = by.get('Admissible-Existence/HPS', {})
    fi = by.get('Admissible-Existence/FI', {})
    daco = by.get('Admissible-Existence/DaCo', {})
    cta = by.get('Admissible-Existence/CTA', {})
    tt = by.get('Admissible-Existence/TT', {})
    stcm = by.get('Admissible-Existence/STCM', {})

    require(gtg.get('historical_gtg_a1_a8_equivalence') == 'NOT_ESTABLISHED', 'gtg_historical_equivalence_must_remain_not_established', f)
    require(et.get('excluded_historical_equivalence_principles') == ['ET-AUTHORITY-003','ET-TEMPORAL-004'] and et.get('historical_source_replacement') is False, 'et_boundary_drift', f)
    require(ltg.get('identity_capture') is False and ltg.get('predetermined_intellectual_destination') is False and ltg.get('authority_effect') is False, 'ltg_boundary_drift', f)
    require(bc.get('bounded_identifier_provenance') == 'NEW_BINDING_IDS_NOT_HISTORICAL_SOURCE_IDS' and bc.get('authority_effect') is False, 'bc_boundary_drift', f)
    require(chf.get('bounded_identifier_provenance') == 'NEW_BINDING_IDS_NOT_HISTORICAL_SOURCE_IDS' and chf.get('authority_effect') is False and chf.get('proof_promotion') is False, 'chf_boundary_drift', f)
    require(re.get('proof_maturity') == 'tested_not_proven' and re.get('bounded_fixture_total') == 19 and re.get('base_structural_checks') == 4 and re.get('universally_proven') == 0, 're_maturity_drift', f)
    require(rr.get('triform_state') == 'BOUNDED_TRIFORM_COMPLETE_MERGED' and rr.get('bounded_identifier_provenance') == 'NEW_BINDING_IDS_NOT_HISTORICAL_SOURCE_IDS', 're_reduction_completion_drift', f)
    require(rr.get('standing_reentry_required') is True and rr.get('lineage_preserved') is True and rr.get('execution_authority_granted') is False and rr.get('source_authority_assertion_forbidden') is True and rr.get('replay_output_must_match_expected') is True and rr.get('failure_outcome') == 'FAIL_CLOSED' and rr.get('source_replacement_authorized') is False, 're_reduction_boundary_drift', f)
    require(dc.get('triform_state') == 'BOUNDED_TRIFORM_COMPLETE_MERGED' and dc.get('historical_stable_ids') == ['DC-P1','DC-P2','DC-P3','DC-P4'], 'dc_completion_or_ids_drift', f)
    require(dc.get('proof_candidates_are_theorems') is False and dc.get('proven_theorems') == 0 and dc.get('local_validity_implies_global_validity') is False and dc.get('consensus_implies_coherence') is False, 'dc_semantic_boundary_drift', f)
    require(triad.get('triform_state') == 'BOUNDED_TRIFORM_COMPLETE_MERGED', 'triad_completion_not_recorded', f)
    require(triad.get('historical_stable_ids') == ['TRIAD-SUBJECT-STANDING','TRIAD-BOUNDARY-STANDING','TRIAD-GOVERNANCE-STANDING'] and triad.get('proof_maturity') == 'tested_not_proven', 'triad_identity_or_maturity_drift', f)
    require(triad.get('review_standing_is_execution_authority') is False and triad.get('subject_boundary_governance_standing_collapsed') is False and triad.get('prior_review_substitutes_for_commit_time_governance') is False and triad.get('unknown_required_standing_is_allow') is False, 'triad_semantic_boundary_drift', f)
    require(triad.get('execution_authorized') is False and triad.get('publication_authorized') is False and triad.get('proofs_accepted') is False and triad.get('historical_source_replacement') is False and triad.get('final_admissibility_authority') == 'Admissible-Existence/AE', 'triad_authority_boundary_drift', f)
    require(gcat.get('triform_state') == 'BOUNDED_TRIFORM_COMPLETE_MERGED_ROOT_ONLY', 'gcat_completion_not_recorded', f)
    require(gcat.get('historical_stable_ids') == ['GCAT-BCAT-COMMIT-GATE','GCAT-BCAT-FAIL-CLOSED','GCAT-BCAT-TRANSITION-ECONOMICS','GCAT-BCAT-RECEIPT-REPLAY'], 'gcat_historical_ids_mismatch', f)
    require(gcat.get('commit_gate_proof_maturity') == 'tested_not_proven' and gcat.get('fail_closed_proof_maturity') == 'tested_not_proven' and gcat.get('transition_economics_proof_maturity') == 'model_bound_tested_not_proven' and gcat.get('receipt_replay_proof_maturity') == 'tested_not_proven', 'gcat_proof_maturity_drift', f)
    require(gcat.get('proposal_is_permission') is False and gcat.get('unknown_or_contradictory_required_evidence_is_allow') is False and gcat.get('replay_renews_current_authority') is False, 'gcat_semantic_boundary_drift', f)
    require(gcat.get('execution_authorized') is False and gcat.get('publication_authorized') is False and gcat.get('proofs_accepted') is False and gcat.get('final_cross_repository_validity') is False, 'gcat_authority_boundary_drift', f)
    require(gcat.get('decision_envelope_claims_satisfied') is False and gcat.get('decision_envelope_child_state') == 'CLAIMED_FOR_INTEGRATION' and gcat.get('decision_envelope_scope_must_remain_untouched') is True, 'gcat_decision_envelope_collision_boundary_drift', f)
    require(gcat.get('historical_source_replacement') is False and gcat.get('workflow_authority_effect') == 'NONE_VALIDATION_ONLY' and gcat.get('final_admissibility_authority') == 'Admissible-Existence/AE' and gcat.get('readme_status_reconciled') is True, 'gcat_preservation_boundary_drift', f)
    require(ecat.get('triform_state') == 'BOUNDED_TRIFORM_COMPLETE_MERGED', 'ecat_completion_not_recorded', f)
    require(ecat.get('historical_stable_ids') == ['ECAT-001','ICAT-001','ECAT-ICAT-001','ECAT-ICAT-002'] and ecat.get('proof_candidate_maturities') == ['tested_candidate','tested_candidate','bounded_candidate'], 'ecat_identity_or_maturity_drift', f)
    require(ecat.get('experiential_standing_grants_execution_authority') is False and ecat.get('relational_standing_grants_execution_authority') is False and ecat.get('pre_boundary_evidence_replaces_commit_time_admissibility') is False and ecat.get('replayed_historical_standing_is_present_execution_authority') is False and ecat.get('missing_required_evidence_is_authoritative_allow') is False, 'ecat_semantic_boundary_drift', f)
    require(ecat.get('execution_authorized') is False and ecat.get('publication_authorized') is False and ecat.get('proofs_accepted') is False and ecat.get('final_cross_repository_validity') is False and ecat.get('historical_source_replacement') is False and ecat.get('workflow_authority_effect') == 'NONE_VALIDATION_ONLY' and ecat.get('final_admissibility_authority') == 'Admissible-Existence/AE' and ecat.get('readme_status_reconciled') is True, 'ecat_preservation_boundary_drift', f)
    require(iict.get('triform_state') == 'BOUNDED_TRIFORM_COMPLETE_MERGED', 'iict_completion_not_recorded', f)
    require(iict.get('prior_goal') == 'IICT-PRINCIPLE-COMPLETENESS-001' and iict.get('prior_goal_state') == 'COMPLETE_RELEASED_HOSTED_VALIDATED', 'iict_prior_goal_state_mismatch', f)
    require(iict.get('repository_local_archive_readiness') is True, 'iict_archive_readiness_must_be_true', f)
    require(iict.get('historical_stable_ids') == ['IICT-001','IICT-002','IICT-003','IICT-004'] and iict.get('principle_count') == 4 and iict.get('baseline_cases') == 5, 'iict_identity_or_count_drift', f)
    require(iict.get('proof_candidate_maturities') == ['tested_candidate','tested_candidate','tested_candidate','theorem_candidate_not_proven'] and iict.get('theorem_status') == 'candidate_not_proven', 'iict_candidate_maturity_drift', f)
    require(iict.get('governance_distance_is_authority') is False and iict.get('convergence_observation_grants_execution_authority') is False and iict.get('reconstruction_creates_present_authority') is False and iict.get('baseline_support_is_universal_proof') is False, 'iict_semantic_boundary_drift', f)
    require(iict.get('execution_authorized') is False and iict.get('publication_authorized') is False and iict.get('proofs_accepted') is False and iict.get('final_cross_repository_validity') is False and iict.get('historical_source_replacement') is False and iict.get('workflow_authority_effect') == 'NONE_VALIDATION_ONLY' and iict.get('final_admissibility_authority') == 'Admissible-Existence/AE' and iict.get('readme_status_reconciled') is True, 'iict_preservation_boundary_drift', f)
    require({'IICT_MIRROR_HANDOFF.md','docs/IICT_TRIFORM_MIRROR_HANDOFF.md','formalism/triform-counterpart-inventory.json','formalism/triform-manifest.json','PR:3'}.issubset(set(iict.get('evidence',[]))), 'iict_completion_evidence_incomplete', f)

    require(data.get('logical_next_candidate') == 'Admissible-Existence/TT' and data.get('logical_candidate_state') == 'DEFER_ACTIVE_CANONICAL_CLAIM', 'logical_candidate_drift', f)
    require(tt.get('triform_state') == 'DEFER_ACTIVE_CANONICAL_CLAIM' and tt.get('claim_state') == 'CLAIMED_FOR_INTEGRATION', 'tt_deferral_not_preserved', f)
    require(stcm.get('triform_state') == 'DEFER_ACTIVE_CANONICAL_CLAIM' and stcm.get('claim_state') == 'CLAIMED_FOR_INTEGRATION', 'stcm_deferral_not_preserved', f)
    require(cta.get('triform_state') == 'DEFER_ACTIVE_CANONICAL_CLAIM' and cta.get('claim_state') == 'ACTIVE_INTEGRATION' and cta.get('active_goal') == 'Complete CTA automation and provenance-bound integration' and 'issue:1' in set(cta.get('evidence',[])), 'cta_active_collision_not_preserved', f)

    require(hps.get('triform_state') == 'BOUNDED_TRIFORM_COMPLETE_MERGED', 'hps_completion_not_recorded', f)
    require(hps.get('prior_goal') == 'HPS-PRINCIPLE-COMPLETENESS-001' and hps.get('prior_goal_state') == 'COMPLETE_VALIDATED_RELEASED', 'hps_prior_goal_state_mismatch', f)
    require(hps.get('repository_local_archive_readiness') is True, 'hps_archive_readiness_must_be_true', f)
    require(hps.get('historical_stable_ids') == ['HPS-P-001','HPS-P-002','HPS-P-003','HPS-P-004'] and hps.get('principle_count') == 4, 'hps_historical_ids_or_count_mismatch', f)
    require(hps.get('proof_candidate_maturities') == ['tested_not_universal_proof','tested_not_universal_proof','tested_not_universal_proof','tested_non_authority_contract'], 'hps_candidate_maturity_drift', f)
    require(hps.get('standing_restoration_requires_current_reconstructable_evidence') is True and hps.get('capability_standing_is_window_bound') is True and hps.get('standing_classification_is_fail_closed') is True and hps.get('prior_standing_reopens_closed_current_window') is False, 'hps_core_semantic_boundary_drift', f)
    require(hps.get('visualization_grants_authority') is False and hps.get('heartbeat_independently_grants_execution_authority') is False and hps.get('execution_authorized') is False and hps.get('publication_authorized') is False and hps.get('proofs_accepted') is False and hps.get('downstream_activation_authorized') is False, 'hps_authority_boundary_drift', f)
    require(hps.get('final_cross_repository_validity') is False and hps.get('historical_source_replacement') is False and hps.get('workflow_authority_effect') == 'NONE_VALIDATION_ONLY' and hps.get('final_admissibility_authority') == 'Admissible-Existence/AE' and hps.get('readme_status_reconciled') is True, 'hps_preservation_boundary_drift', f)
    require({'HPS_MIRROR_HANDOFF.md','docs/HPS_TRIFORM_MIRROR_HANDOFF.md','formalism/triform-counterpart-inventory.json','formalism/triform-manifest.json','PR:6'}.issubset(set(hps.get('evidence',[]))), 'hps_completion_evidence_incomplete', f)

    require(fi.get('triform_state') == 'BOUNDED_TRIFORM_COMPLETE_MERGED', 'fi_completion_not_recorded', f)
    require(fi.get('prior_goal') == 'FI-PRINCIPLE-COMPLETENESS-001' and fi.get('prior_goal_state') == 'COMPLETE_HOSTED_VALIDATED_CENTRALLY_ACTIVATED', 'fi_prior_goal_state_mismatch', f)
    require(fi.get('repository_local_archive_readiness') is True, 'fi_archive_readiness_must_be_true', f)
    require(fi.get('historical_stable_ids') == ['FI-TRANSITION-001','FI-SCALE-001','FI-OBSERVER-001'] and fi.get('principle_count') == 3 and fi.get('principle_status') == 'candidate', 'fi_identity_or_candidate_status_drift', f)
    require(fi.get('proof_candidate_maturities') == ['candidate_locally_tested_not_cross_domain_proven'] * 3, 'fi_candidate_maturity_drift', f)
    require(fi.get('destination_bootstrap_completed') is True and fi.get('canonical_continuity_execution_completed') is True and fi.get('cross_domain_evidence_intake_ready') is True, 'fi_prerequisite_completion_evidence_drift', f)
    require(fi.get('cross_domain_support_established') is False and fi.get('universal_law_established') is False, 'fi_cross_domain_or_universal_promotion', f)
    require(fi.get('execution_authorized') is False and fi.get('publication_authorized') is False and fi.get('proofs_accepted') is False and fi.get('historical_source_replacement') is False, 'fi_authority_or_source_promotion', f)
    require(fi.get('workflow_authority_effect') == 'NONE_VALIDATION_ONLY' and fi.get('final_admissibility_authority') == 'Admissible-Existence/AE', 'fi_validation_or_admissibility_boundary_drift', f)
    require(fi.get('readme_status_reconciled') is True and fi.get('prerequisite_metadata_reconciled') is True, 'fi_source_reconciliation_not_complete', f)
    require({'docs/FI_MIRROR_HANDOFF.md','docs/FI_TRIFORM_MIRROR_HANDOFF.md','formalism/triform-counterpart-inventory.json','formalism/triform-manifest.json','README.md','issue:3','PR:4','merge:3ee2c1d1b7376e2b14c3d6faf67285fcc4c90c63','validation_run:34035414344','validation_job:101492457501'}.issubset(set(fi.get('evidence',[]))), 'fi_completion_evidence_incomplete', f)

    require(data.get('next_executable_candidate') == 'Admissible-Existence/DaCo', 'unexpected_next_executable_candidate', f)
    require(data.get('selection_evidence_state') == 'EVIDENCE_PASS_COMPLETE', 'selection_evidence_state_mismatch', f)
    require({
        'Admissible-Existence/DaCo@main:docs/DACO_MIRROR_HANDOFF.md',
        'Admissible-Existence/IW@main:IW_MIRROR_HANDOFF.md',
        'Admissible-Existence/standing-proof-formalism@main:docs/STANDING_PROOF_FORMALISM_MIRROR_HANDOFF.md',
        'open_issue_check:DaCo=0,IW=0,standing-proof-formalism=0',
        'open_pr_check:DaCo=0,IW=0,standing-proof-formalism=0'
    }.issubset(set(data.get('selection_evidence',[]))), 'daco_selection_evidence_incomplete', f)
    require(daco.get('triform_state') == 'SELECTED_NEXT_EXECUTABLE_CANDIDATE', 'daco_selection_state_mismatch', f)
    require(daco.get('prior_goal') == 'DACO-PRINCIPLE-COMPLETENESS-001' and daco.get('prior_goal_state') == 'COMPLETE_AND_RELEASED', 'daco_prior_goal_state_mismatch', f)
    require(daco.get('repository_local_archive_readiness') is True, 'daco_archive_readiness_must_be_true', f)
    require(daco.get('historical_stable_ids') == ['DACO-P-001','DACO-P-002','DACO-P-003','DACO-P-004'] and daco.get('principle_count') == 4, 'daco_identity_or_count_drift', f)
    require(daco.get('continuity_equals_truth') is False and daco.get('final_cross_repository_validity') is False, 'daco_truth_or_cross_repository_promotion', f)
    require(daco.get('execution_authorized') is False and daco.get('publication_authorized') is False and daco.get('proofs_accepted') is False, 'daco_authority_promotion', f)
    require(daco.get('creates_authority') is False and daco.get('commits_execution') is False and daco.get('data_continuity_is_distributed_coherence') is False, 'daco_boundary_drift', f)
    require({'docs/DACO_MIRROR_HANDOFF.md','formalism/principle-registry.yaml','formalism/dependency-graph.yaml','formalism/proof-candidates.yaml','docs/WHOLE_REPO_THEORY_MAP.md','docs/MATHEMATICAL_NOTATION.md','docs/FALSIFICATION_AND_LIMITS.md','tools/validate_principle_completeness.py','.github/workflows/daco-validation.yml','reports/daco-principle-completeness-validation.json'}.issubset(set(daco.get('evidence',[]))), 'daco_source_evidence_incomplete', f)

    for e in entries:
        require(bool(e.get('triform_state')), f"missing_triform_state:{e.get('repository')}", f)

    print(json.dumps({
        'schema':'admissible-existence.triform-migration-validation/v2',
        'valid': not f,
        'entry_count': len(entries),
        'completed_source_migrations': data.get('completed_source_migrations'),
        'logical_next_candidate': data.get('logical_next_candidate'),
        'logical_candidate_state': data.get('logical_candidate_state'),
        'next_executable_candidate': data.get('next_executable_candidate'),
        'selection_evidence_state': data.get('selection_evidence_state'),
        'findings': f,
        'authority_effect':'NONE_VALIDATION_ONLY'
    }, indent=2, sort_keys=True))
    raise SystemExit(0 if not f else 1)


if __name__ == '__main__':
    main()
