#!/usr/bin/env python3
import argparse,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("org_kernel",ROOT/"org-kernel/kernel.py")
K=importlib.util.module_from_spec(spec);spec.loader.exec_module(K)
def load(p):return json.loads(Path(p).read_text())
def main():
 p=argparse.ArgumentParser();p.add_argument("--org-receipt",required=True);p.add_argument("--predecessor-ecosystem-state-sha256",required=True);p.add_argument("--successor-ecosystem-state-sha256",required=True);p.add_argument("--relation-evidence-json",default="{}")
 # Standing is declared, never derived here. The ecosystem-state digests above
 # chain this lane; the contract's own finding refuses to equate lane-local
 # chaining with cross-lane predecessor standing, so they are not reused as a
 # predecessor binding. There is no default: a silent one would be the
 # defaulting the contract forbids.
 p.add_argument("--standing",required=True,help="JSON file declaring mode, node_ref and the predecessor key")
 a=p.parse_args()
 # Bad input is the caller's: a terminal six-field CLI_INPUT_INVALID, read before anything is published.
 entry="resident-runtime/submit_org_transition_to_master_records.py (same arguments)"
 try:
  receipt=K.read_json_input(a.org_receipt,argument="--org-receipt",retry_entrypoint=entry)
  relation_evidence=K.parse_json_argument(a.relation_evidence_json,argument="--relation-evidence-json",retry_entrypoint=entry)
  standing=K.read_json_input(a.standing,argument="--standing",retry_entrypoint=entry)
 except K.CliInputRefused as exc:print(json.dumps(exc.refusal,sort_keys=True));raise SystemExit(1)
 if receipt.get("schema")!="stegverse.organization-transition-receipt/v1":raise SystemExit("organization receipt schema mismatch")
 if receipt.get("organization")!="Admissible-Existence":raise SystemExit("organization receipt owner mismatch")
 payload={"operation":"CUSTODY_ORGANIZATION_TRANSITION","organization_receipt":receipt,"predecessor_ecosystem_state_sha256":a.predecessor_ecosystem_state_sha256,"successor_ecosystem_state_sha256":a.successor_ecosystem_state_sha256,"relation_evidence":relation_evidence,"authority_transfer":False}
 if not isinstance(standing,dict) or "predecessor" not in standing:raise SystemExit("standing must declare the predecessor key; null is explicit genesis")
 packet=K.build_packet(origin_org="Admissible-Existence",origin_service="admissible-existence.org-control",destination_org="master-records",destination_service="master-records.ecosystem-transition-ledger",payload=payload,standing=standing,transition_reference="ecosystem.transition.custody.v1",authority_effect="NONE")
 published=K.publish_packet(packet)
 print(json.dumps({"status":"PUBLISHED_FOR_CUSTODY","packet_id":packet["packet_id"],"frame_sha256":published["frame"]["frame_sha256"],"authority_effect":"NONE"},sort_keys=True))
if __name__=="__main__":main()
