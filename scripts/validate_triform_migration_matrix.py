#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MATRIX=ROOT/'data/triform-migration-matrix.json'

def main():
    data=json.loads(MATRIX.read_text(encoding='utf-8'))
    entries=data.get('entries',[]); repos=[e.get('repository') for e in entries]; by={e.get('repository'):e for e in entries}; f=[]
    if data.get('schema')!='admissible-existence.triform-migration-matrix/v2': f.append('unexpected_schema')
    if data.get('refresh_goal_id')!='AEX-TRIFORM-MIGRATION-REFRESH-013': f.append('refresh_goal_id_mismatch')
    if data.get('registry_repository_count')!=32: f.append('registry_repository_count_mismatch')
    if len(entries)!=32: f.append('entry_count_mismatch')
    if len(set(repos))!=len(repos): f.append('duplicate_repository')
    expected=['Admissible-Existence/Existence','Admissible-Existence/GTG','Admissible-Existence/ET','Admissible-Existence/learning-transition-governance','Admissible-Existence/BC','Admissible-Existence/CHF','Admissible-Existence/RE','Admissible-Existence/RE-Reduction','Admissible-Existence/DC','Admissible-Existence/Triad','Admissible-Existence/GCAT-BCAT','Admissible-Existence/ECAT-ICAT','Admissible-Existence/IICT']
    if data.get('completed_source_migrations')!=13: f.append('completed_source_migration_count_mismatch')
    if data.get('completed_source_repositories')!=expected: f.append('completed_source_repository_set_mismatch')
    gtg=by.get('Admissible-Existence/GTG',{}); et=by.get('Admissible-Existence/ET',{}); ltg=by.get('Admissible-Existence/learning-transition-governance',{}); bc=by.get('Admissible-Existence/BC',{}); chf=by.get('Admissible-Existence/CHF',{}); re=by.get('Admissible-Existence/RE',{}); rr=by.get('Admissible-Existence/RE-Reduction',{}); dc=by.get('Admissible-Existence/DC',{}); triad=by.get('Admissible-Existence/Triad',{}); gcat=by.get('Admissible-Existence/GCAT-BCAT',{}); ecat=by.get('Admissible-Existence/ECAT-ICAT',{}); iict=by.get('Admissible-Existence/IICT',{}); tt=by.get('Admissible-Existence/TT',{}); stcm=by.get('Admissible-Existence/STCM',{})
    if gtg.get('historical_gtg_a1_a8_equivalence')!='NOT_ESTABLISHED': f.append('gtg_historical_equivalence_must_remain_not_established')
    if et.get('excluded_historical_equivalence_principles')!=['ET-AUTHORITY-003','ET-TEMPORAL-004'] or et.get('historical_source_replacement') is not False: f.append('et_boundary_drift')
    if ltg.get('identity_capture') is not False or ltg.get('predetermined_intellectual_destination') is not False or ltg.get('authority_effect') is not False: f.append('ltg_boundary_drift')
    if bc.get('bounded_identifier_provenance')!='NEW_BINDING_IDS_NOT_HISTORICAL_SOURCE_IDS' or bc.get('authority_effect') is not False: f.append('bc_boundary_drift')
    if chf.get('bounded_identifier_provenance')!='NEW_BINDING_IDS_NOT_HISTORICAL_SOURCE_IDS' or chf.get('authority_effect') is not False or chf.get('proof_promotion') is not False: f.append('chf_boundary_drift')
    if re.get('proof_maturity')!='tested_not_proven' or re.get('bounded_fixture_total')!=19 or re.get('base_structural_checks')!=4 or re.get('universally_proven')!=0: f.append('re_maturity_drift')
    if rr.get('triform_state')!='BOUNDED_TRIFORM_COMPLETE_MERGED' or rr.get('bounded_identifier_provenance')!='NEW_BINDING_IDS_NOT_HISTORICAL_SOURCE_IDS': f.append('re_reduction_completion_drift')
    if rr.get('standing_reentry_required') is not True or rr.get('lineage_preserved') is not True or rr.get('execution_authority_granted') is not False or rr.get('source_authority_assertion_forbidden') is not True or rr.get('replay_output_must_match_expected') is not True or rr.get('failure_outcome')!='FAIL_CLOSED' or rr.get('source_replacement_authorized') is not False: f.append('re_reduction_boundary_drift')
    if dc.get('triform_state')!='BOUNDED_TRIFORM_COMPLETE_MERGED' or dc.get('historical_stable_ids')!=['DC-P1','DC-P2','DC-P3','DC-P4']: f.append('dc_completion_or_ids_drift')
    if dc.get('proof_candidates_are_theorems') is not False or dc.get('proven_theorems')!=0 or dc.get('local_validity_implies_global_validity') is not False or dc.get('consensus_implies_coherence') is not False: f.append('dc_semantic_boundary_drift')
    if triad.get('triform_state')!='BOUNDED_TRIFORM_COMPLETE_MERGED': f.append('triad_completion_not_recorded')
    if triad.get('historical_stable_ids')!=['TRIAD-SUBJECT-STANDING','TRIAD-BOUNDARY-STANDING','TRIAD-GOVERNANCE-STANDING'] or triad.get('proof_maturity')!='tested_not_proven': f.append('triad_identity_or_maturity_drift')
    if triad.get('review_standing_is_execution_authority') is not False or triad.get('subject_boundary_governance_standing_collapsed') is not False or triad.get('prior_review_substitutes_for_commit_time_governance') is not False or triad.get('unknown_required_standing_is_allow') is not False: f.append('triad_semantic_boundary_drift')
    if triad.get('execution_authorized') is not False or triad.get('publication_authorized') is not False or triad.get('proofs_accepted') is not False or triad.get('historical_source_replacement') is not False or triad.get('final_admissibility_authority')!='Admissible-Existence/AE': f.append('triad_authority_boundary_drift')
    if gcat.get('triform_state')!='BOUNDED_TRIFORM_COMPLETE_MERGED_ROOT_ONLY': f.append('gcat_completion_not_recorded')
    if gcat.get('historical_stable_ids')!=['GCAT-BCAT-COMMIT-GATE','GCAT-BCAT-FAIL-CLOSED','GCAT-BCAT-TRANSITION-ECONOMICS','GCAT-BCAT-RECEIPT-REPLAY']: f.append('gcat_historical_ids_mismatch')
    if gcat.get('commit_gate_proof_maturity')!='tested_not_proven' or gcat.get('fail_closed_proof_maturity')!='tested_not_proven' or gcat.get('transition_economics_proof_maturity')!='model_bound_tested_not_proven' or gcat.get('receipt_replay_proof_maturity')!='tested_not_proven': f.append('gcat_proof_maturity_drift')
    if gcat.get('proposal_is_permission') is not False or gcat.get('unknown_or_contradictory_required_evidence_is_allow') is not False or gcat.get('replay_renews_current_authority') is not False: f.append('gcat_semantic_boundary_drift')
    if gcat.get('execution_authorized') is not False or gcat.get('publication_authorized') is not False or gcat.get('proofs_accepted') is not False or gcat.get('final_cross_repository_validity') is not False: f.append('gcat_authority_boundary_drift')
    if gcat.get('decision_envelope_claims_satisfied') is not False or gcat.get('decision_envelope_child_state')!='CLAIMED_FOR_INTEGRATION' or gcat.get('decision_envelope_scope_must_remain_untouched') is not True: f.append('gcat_decision_envelope_collision_boundary_drift')
    if gcat.get('historical_source_replacement') is not False or gcat.get('workflow_authority_effect')!='NONE_VALIDATION_ONLY' or gcat.get('final_admissibility_authority')!='Admissible-Existence/AE' or gcat.get('readme_status_reconciled') is not True: f.append('gcat_preservation_boundary_drift')
    if ecat.get('triform_state')!='BOUNDED_TRIFORM_COMPLETE_MERGED': f.append('ecat_completion_not_recorded')
    if ecat.get('historical_stable_ids')!=['ECAT-001','ICAT-001','ECAT-ICAT-001','ECAT-ICAT-002'] or ecat.get('proof_candidate_maturities')!=['tested_candidate','tested_candidate','bounded_candidate']: f.append('ecat_identity_or_maturity_drift')
    if ecat.get('experiential_standing_grants_execution_authority') is not False or ecat.get('relational_standing_grants_execution_authority') is not False or ecat.get('pre_boundary_evidence_replaces_commit_time_admissibility') is not False or ecat.get('replayed_historical_standing_is_present_execution_authority') is not False or ecat.get('missing_required_evidence_is_authoritative_allow') is not False: f.append('ecat_semantic_boundary_drift')
    if ecat.get('execution_authorized') is not False or ecat.get('publication_authorized') is not False or ecat.get('proofs_accepted') is not False or ecat.get('final_cross_repository_validity') is not False or ecat.get('historical_source_replacement') is not False or ecat.get('workflow_authority_effect')!='NONE_VALIDATION_ONLY' or ecat.get('final_admissibility_authority')!='Admissible-Existence/AE' or ecat.get('readme_status_reconciled') is not True: f.append('ecat_preservation_boundary_drift')
    if iict.get('triform_state')!='BOUNDED_TRIFORM_COMPLETE_MERGED': f.append('iict_completion_not_recorded')
    if iict.get('prior_goal')!='IICT-PRINCIPLE-COMPLETENESS-001' or iict.get('prior_goal_state')!='COMPLETE_RELEASED_HOSTED_VALIDATED': f.append('iict_prior_goal_state_mismatch')
    if iict.get('repository_local_archive_readiness') is not True: f.append('iict_archive_readiness_must_be_true')
    if iict.get('historical_stable_ids')!=['IICT-001','IICT-002','IICT-003','IICT-004']: f.append('iict_historical_ids_mismatch')
    if iict.get('principle_count')!=4 or iict.get('baseline_cases')!=5: f.append('iict_count_mismatch')
    if iict.get('proof_candidate_maturities')!=['tested_candidate','tested_candidate','tested_candidate','theorem_candidate_not_proven'] or iict.get('theorem_status')!='candidate_not_proven': f.append('iict_candidate_maturity_drift')
    if iict.get('governance_distance_is_authority') is not False or iict.get('convergence_observation_grants_execution_authority') is not False or iict.get('reconstruction_creates_present_authority') is not False or iict.get('baseline_support_is_universal_proof') is not False: f.append('iict_semantic_boundary_drift')
    if iict.get('execution_authorized') is not False or iict.get('publication_authorized') is not False or iict.get('proofs_accepted') is not False or iict.get('final_cross_repository_validity') is not False: f.append('iict_authority_boundary_drift')
    if iict.get('historical_source_replacement') is not False or iict.get('workflow_authority_effect')!='NONE_VALIDATION_ONLY' or iict.get('final_admissibility_authority')!='Admissible-Existence/AE' or iict.get('readme_status_reconciled') is not True: f.append('iict_preservation_boundary_drift')
    required_iict={'IICT_MIRROR_HANDOFF.md','docs/IICT_TRIFORM_MIRROR_HANDOFF.md','formalism/triform-counterpart-inventory.json','formalism/triform-manifest.json','PR:3'}
    if not required_iict.issubset(set(iict.get('evidence',[]))): f.append('iict_completion_evidence_incomplete')
    if data.get('logical_next_candidate')!='Admissible-Existence/TT' or data.get('logical_candidate_state')!='DEFER_ACTIVE_CANONICAL_CLAIM': f.append('logical_candidate_drift')
    if tt.get('triform_state')!='DEFER_ACTIVE_CANONICAL_CLAIM' or tt.get('claim_state')!='CLAIMED_FOR_INTEGRATION': f.append('tt_deferral_not_preserved')
    if stcm.get('triform_state')!='DEFER_ACTIVE_CANONICAL_CLAIM' or stcm.get('claim_state')!='CLAIMED_FOR_INTEGRATION': f.append('stcm_deferral_not_preserved')
    if data.get('next_executable_candidate') is not None: f.append('next_executable_candidate_requires_fresh_evidence_pass')
    if data.get('selection_evidence_state')!='EVIDENCE_PASS_REQUIRED': f.append('selection_evidence_state_mismatch')
    for e in entries:
        if not e.get('triform_state'): f.append(f"missing_triform_state:{e.get('repository')}")
    print(json.dumps({'schema':'admissible-existence.triform-migration-validation/v2','valid':not f,'entry_count':len(entries),'completed_source_migrations':data.get('completed_source_migrations'),'logical_next_candidate':data.get('logical_next_candidate'),'logical_candidate_state':data.get('logical_candidate_state'),'next_executable_candidate':data.get('next_executable_candidate'),'selection_evidence_state':data.get('selection_evidence_state'),'findings':f,'authority_effect':'NONE_VALIDATION_ONLY'},indent=2,sort_keys=True))
    raise SystemExit(0 if not f else 1)

if __name__=='__main__': main()
