#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MATRIX=ROOT/'data/triform-migration-matrix.json'

def main():
    data=json.loads(MATRIX.read_text(encoding='utf-8'))
    entries=data.get('entries',[]); repos=[e.get('repository') for e in entries]; by={e.get('repository'):e for e in entries}; f=[]
    if data.get('schema')!='admissible-existence.triform-migration-matrix/v2': f.append('unexpected_schema')
    if data.get('registry_repository_count')!=32: f.append('registry_repository_count_mismatch')
    if len(entries)!=32: f.append('entry_count_mismatch')
    if len(set(repos))!=len(repos): f.append('duplicate_repository')
    expected=['Admissible-Existence/Existence','Admissible-Existence/GTG','Admissible-Existence/ET','Admissible-Existence/learning-transition-governance','Admissible-Existence/BC','Admissible-Existence/CHF','Admissible-Existence/RE','Admissible-Existence/RE-Reduction','Admissible-Existence/DC','Admissible-Existence/Triad']
    if data.get('completed_source_migrations')!=10: f.append('completed_source_migration_count_mismatch')
    if data.get('completed_source_repositories')!=expected: f.append('completed_source_repository_set_mismatch')
    gtg=by.get('Admissible-Existence/GTG',{}); et=by.get('Admissible-Existence/ET',{}); ltg=by.get('Admissible-Existence/learning-transition-governance',{}); bc=by.get('Admissible-Existence/BC',{}); chf=by.get('Admissible-Existence/CHF',{}); re=by.get('Admissible-Existence/RE',{}); rr=by.get('Admissible-Existence/RE-Reduction',{}); dc=by.get('Admissible-Existence/DC',{}); triad=by.get('Admissible-Existence/Triad',{}); gcat=by.get('Admissible-Existence/GCAT-BCAT',{}); tt=by.get('Admissible-Existence/TT',{}); stcm=by.get('Admissible-Existence/STCM',{})
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
    if data.get('logical_next_candidate')!='Admissible-Existence/TT' or data.get('logical_candidate_state')!='DEFER_ACTIVE_CANONICAL_CLAIM': f.append('logical_candidate_drift')
    if tt.get('triform_state')!='DEFER_ACTIVE_CANONICAL_CLAIM' or tt.get('claim_state')!='CLAIMED_FOR_INTEGRATION': f.append('tt_deferral_not_preserved')
    if stcm.get('triform_state')!='DEFER_ACTIVE_CANONICAL_CLAIM' or stcm.get('claim_state')!='CLAIMED_FOR_INTEGRATION': f.append('stcm_deferral_not_preserved')
    if data.get('next_executable_candidate')!='Admissible-Existence/GCAT-BCAT': f.append('unexpected_next_executable_candidate')
    if data.get('selection_evidence_state')!='EVIDENCE_PASS_COMPLETE': f.append('selection_evidence_state_mismatch')
    required={'Admissible-Existence/GCAT-BCAT@main:GCAT_BCAT_MIRROR_HANDOFF.md','Admissible-Existence/GCAT-BCAT@main:formalism/principle-registry.yaml','Admissible-Existence/GCAT-BCAT@main:reports/gcat-bcat-principle-completeness-validation.json','Admissible-Existence/GCAT-BCAT@main:README.md','Admissible-Existence/GCAT-BCAT#2','Admissible-Existence/GCAT-BCAT@main:docs/DECISION_ENVELOPE_MIRROR_HANDOFF.md'}
    if not required.issubset(set(data.get('selection_evidence',[]))): f.append('gcat_selection_evidence_incomplete')
    if gcat.get('triform_state')!='SELECTED_NEXT_EXECUTABLE_CANDIDATE_ROOT_ONLY': f.append('gcat_selection_state_mismatch')
    if gcat.get('prior_goal')!='GCAT-BCAT-PRINCIPLE-COMPLETENESS-001' or gcat.get('prior_goal_state')!='COMPLETE_RELEASED_HOSTED_VALIDATED': f.append('gcat_prior_goal_state_mismatch')
    if gcat.get('historical_stable_ids')!=['GCAT-BCAT-COMMIT-GATE','GCAT-BCAT-FAIL-CLOSED','GCAT-BCAT-TRANSITION-ECONOMICS','GCAT-BCAT-RECEIPT-REPLAY']: f.append('gcat_historical_ids_mismatch')
    if gcat.get('principle_count')!=4: f.append('gcat_principle_count_mismatch')
    if gcat.get('execution_authorized') is not False or gcat.get('publication_authorized') is not False or gcat.get('proofs_accepted') is not False: f.append('gcat_authority_boundary_mismatch')
    if gcat.get('decision_envelope_claims_satisfied') is not False or gcat.get('decision_envelope_child_state')!='CLAIMED_FOR_INTEGRATION' or gcat.get('decision_envelope_scope_must_remain_untouched') is not True: f.append('gcat_decision_envelope_collision_boundary_drift')
    if gcat.get('final_admissibility_authority')!='Admissible-Existence/AE': f.append('gcat_final_admissibility_authority_mismatch')
    if gcat.get('readme_current_root_state_accurate') is not True: f.append('gcat_readme_state_mismatch')
    for e in entries:
        if not e.get('triform_state'): f.append(f"missing_triform_state:{e.get('repository')}")
    print(json.dumps({'schema':'admissible-existence.triform-migration-validation/v2','valid':not f,'entry_count':len(entries),'completed_source_migrations':data.get('completed_source_migrations'),'logical_next_candidate':data.get('logical_next_candidate'),'logical_candidate_state':data.get('logical_candidate_state'),'next_executable_candidate':data.get('next_executable_candidate'),'selection_evidence_state':data.get('selection_evidence_state'),'findings':f,'authority_effect':'NONE_VALIDATION_ONLY'},indent=2,sort_keys=True))
    raise SystemExit(0 if not f else 1)

if __name__=='__main__': main()
