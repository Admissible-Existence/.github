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
    expected=['Admissible-Existence/Existence','Admissible-Existence/GTG','Admissible-Existence/ET','Admissible-Existence/learning-transition-governance','Admissible-Existence/BC','Admissible-Existence/CHF','Admissible-Existence/RE','Admissible-Existence/RE-Reduction']
    if data.get('completed_source_migrations')!=8: f.append('completed_source_migration_count_mismatch')
    if data.get('completed_source_repositories')!=expected: f.append('completed_source_repository_set_mismatch')
    gtg=by.get('Admissible-Existence/GTG',{}); et=by.get('Admissible-Existence/ET',{}); ltg=by.get('Admissible-Existence/learning-transition-governance',{}); bc=by.get('Admissible-Existence/BC',{}); chf=by.get('Admissible-Existence/CHF',{}); re=by.get('Admissible-Existence/RE',{}); rr=by.get('Admissible-Existence/RE-Reduction',{}); dc=by.get('Admissible-Existence/DC',{}); tt=by.get('Admissible-Existence/TT',{}); stcm=by.get('Admissible-Existence/STCM',{})
    if gtg.get('historical_gtg_a1_a8_equivalence')!='NOT_ESTABLISHED': f.append('gtg_historical_equivalence_must_remain_not_established')
    if et.get('excluded_historical_equivalence_principles')!=['ET-AUTHORITY-003','ET-TEMPORAL-004'] or et.get('historical_source_replacement') is not False: f.append('et_boundary_drift')
    if ltg.get('identity_capture') is not False or ltg.get('predetermined_intellectual_destination') is not False or ltg.get('authority_effect') is not False: f.append('ltg_boundary_drift')
    if bc.get('bounded_identifier_provenance')!='NEW_BINDING_IDS_NOT_HISTORICAL_SOURCE_IDS' or bc.get('authority_effect') is not False: f.append('bc_boundary_drift')
    if chf.get('bounded_identifier_provenance')!='NEW_BINDING_IDS_NOT_HISTORICAL_SOURCE_IDS' or chf.get('authority_effect') is not False or chf.get('proof_promotion') is not False: f.append('chf_boundary_drift')
    if re.get('proof_maturity')!='tested_not_proven' or re.get('bounded_fixture_total')!=19 or re.get('base_structural_checks')!=4 or re.get('universally_proven')!=0: f.append('re_maturity_drift')
    if rr.get('triform_state')!='BOUNDED_TRIFORM_COMPLETE_MERGED' or rr.get('bounded_identifier_provenance')!='NEW_BINDING_IDS_NOT_HISTORICAL_SOURCE_IDS': f.append('re_reduction_completion_drift')
    if rr.get('standing_reentry_required') is not True or rr.get('lineage_preserved') is not True or rr.get('execution_authority_granted') is not False or rr.get('source_authority_assertion_forbidden') is not True or rr.get('replay_output_must_match_expected') is not True or rr.get('failure_outcome')!='FAIL_CLOSED' or rr.get('source_replacement_authorized') is not False: f.append('re_reduction_boundary_drift')
    if data.get('logical_next_candidate')!='Admissible-Existence/TT' or data.get('logical_candidate_state')!='DEFER_ACTIVE_CANONICAL_CLAIM': f.append('logical_candidate_drift')
    if tt.get('triform_state')!='DEFER_ACTIVE_CANONICAL_CLAIM' or tt.get('claim_state')!='CLAIMED_FOR_INTEGRATION': f.append('tt_deferral_not_preserved')
    if stcm.get('triform_state')!='DEFER_ACTIVE_CANONICAL_CLAIM' or stcm.get('claim_state')!='CLAIMED_FOR_INTEGRATION': f.append('stcm_deferral_not_preserved')
    if data.get('next_executable_candidate')!='Admissible-Existence/DC': f.append('unexpected_next_executable_candidate')
    if data.get('selection_evidence_state')!='EVIDENCE_PASS_COMPLETE': f.append('selection_evidence_state_mismatch')
    required={'Admissible-Existence/DC@main:docs/DC_MIRROR_HANDOFF.md','Admissible-Existence/DC@main:formalism/principle-registry.yaml','Admissible-Existence/DC@main:reports/dc-deterministic-validation-receipt.json','Admissible-Existence/DC#1'}
    if not required.issubset(set(data.get('selection_evidence',[]))): f.append('dc_selection_evidence_incomplete')
    if dc.get('triform_state')!='SELECTED_NEXT_EXECUTABLE_CANDIDATE': f.append('dc_selection_state_mismatch')
    if dc.get('prior_goal')!='DC-PRINCIPLE-COMPLETENESS-001' or dc.get('prior_goal_state')!='COMPLETE_RELEASED_HOSTED_VALIDATED': f.append('dc_prior_goal_state_mismatch')
    if dc.get('repository_local_archive_readiness') is not True: f.append('dc_archive_readiness_must_be_true')
    if dc.get('historical_stable_ids')!=['DC-P1','DC-P2','DC-P3','DC-P4']: f.append('dc_historical_ids_mismatch')
    if dc.get('principle_count')!=4: f.append('dc_principle_count_mismatch')
    if dc.get('authority_effect') is not False or dc.get('final_cross_repository_validity') is not False: f.append('dc_authority_boundary_mismatch')
    if dc.get('readme_status_reconciliation_required') is not True: f.append('dc_readme_reconciliation_must_be_required')
    for e in entries:
        if not e.get('triform_state'): f.append(f"missing_triform_state:{e.get('repository')}")
    print(json.dumps({'schema':'admissible-existence.triform-migration-validation/v2','valid':not f,'entry_count':len(entries),'completed_source_migrations':data.get('completed_source_migrations'),'logical_next_candidate':data.get('logical_next_candidate'),'logical_candidate_state':data.get('logical_candidate_state'),'next_executable_candidate':data.get('next_executable_candidate'),'selection_evidence_state':data.get('selection_evidence_state'),'findings':f,'authority_effect':'NONE_VALIDATION_ONLY'},indent=2,sort_keys=True))
    raise SystemExit(0 if not f else 1)

if __name__=='__main__': main()
