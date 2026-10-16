#!/usr/bin/env python3
import argparse,hashlib,importlib.util,json,os
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/".stegverse/transition-ledger/org-contract.json").read_text())
def canon(v):return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def sha(v):return "sha256:"+hashlib.sha256(canon(v)).hexdigest()
def _load_ledger_store():
 spec=importlib.util.spec_from_file_location("ledger_store_org", ROOT/"resident-runtime/ledger_store.py")
 module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
 return module
ledger_store=_load_ledger_store()
def ledger_root():
 o=os.getenv("STEGVERSE_ORG_LEDGER_ROOT")
 if o:return Path(o).expanduser().resolve()
 return (Path(os.getenv("XDG_STATE_HOME",str(Path.home()/".local/state")))/"stegverse/org-ledgers"/C["organization"]).resolve()
def load(p):return json.loads(Path(p).read_text())
def verify_repo(r):
 if r.get("schema")!="stegverse.repo-transition-receipt/v1":raise SystemExit("repo receipt schema mismatch")
 if not str(r.get("repository","")).startswith(C["organization"]+"/"):raise SystemExit("repo outside organization")
 claimed=r.get("receipt_sha256"); body=dict(r);body.pop("receipt_sha256",None)
 if claimed!=sha(body):raise SystemExit("repo receipt hash mismatch")
 return claimed
def _recorded_for_repo(store, head, repo_digest, org_class):
 cursor=head.get("receipt_sha256") if isinstance(head, dict) else None
 while isinstance(cursor, str) and cursor:
  receipt=store.get(ledger_store.receipt_key(cursor))
  if not isinstance(receipt, dict): return None
  if receipt.get("repo_receipt_sha256")==repo_digest and receipt.get("org_transition_class")==org_class: return receipt
  cursor=receipt.get("previous_receipt_sha256")
 return None
def append(repo_receipt, org_transition_class, predecessor, successor, boundary_evidence, authority_effect="NONE", hb_epoch=None, idempotent=False):
 """Append one organization receipt that preserves the repository receipt digest."""
 rd=verify_repo(repo_receipt); evidence=dict(boundary_evidence); root=ledger_root(); store=ledger_store.open_store(root); head=store.get(ledger_store.HEAD_KEY) or {}
 prior=_recorded_for_repo(store, head, rd, org_transition_class)
 if prior is not None:
  if idempotent and prior.get("boundary_evidence")==evidence: return prior
  raise ValueError("ledger_receipt_collision")
 previous=head.get("receipt_sha256") if isinstance(head, dict) else None
 hb={"epoch":int(hb_epoch),"authority_effect":"NONE"} if hb_epoch is not None else None
 body={"schema":"stegverse.organization-transition-receipt/v1","organization":C["organization"],"source_repository":repo_receipt["repository"],"repo_receipt_sha256":rd,"repo_transition_id":repo_receipt["transition_id"],"org_transition_class":org_transition_class,"predecessor_org_state_sha256":predecessor,"successor_org_state_sha256":successor,"boundary_evidence":evidence,"authority_effect":authority_effect,"hb_reference":hb,"observed_at":datetime.now(timezone.utc).isoformat(),"previous_receipt_sha256":previous}
 digest=sha(body); record={**body,"receipt_sha256":digest}; key=ledger_store.receipt_key(digest)
 store.put(key, record)
 store.put(ledger_store.HEAD_KEY, {"organization":C["organization"],"receipt_sha256":digest,"receipt_path":str(root/key)})
 return record
def main():
 p=argparse.ArgumentParser();p.add_argument("--repo-receipt",required=True);p.add_argument("--org-transition-class",default="REPO_STATE_PROPAGATION");p.add_argument("--predecessor-org-state-sha256",required=True);p.add_argument("--successor-org-state-sha256",required=True);p.add_argument("--boundary-evidence-json",default="{}");p.add_argument("--authority-effect",default="NONE");a=p.parse_args()
 rr=load(a.repo_receipt);rd=verify_repo(rr);root=ledger_root();d=root/"receipts";d.mkdir(parents=True,exist_ok=True);h=root/"HEAD.json";prev=load(h).get("receipt_sha256") if h.exists() else None
 b={"schema":"stegverse.organization-transition-receipt/v1","organization":C["organization"],"source_repository":rr["repository"],"repo_receipt_sha256":rd,"repo_transition_id":rr["transition_id"],"org_transition_class":a.org_transition_class,"predecessor_org_state_sha256":a.predecessor_org_state_sha256,"successor_org_state_sha256":a.successor_org_state_sha256,"boundary_evidence":json.loads(a.boundary_evidence_json),"authority_effect":a.authority_effect,"observed_at":datetime.now(timezone.utc).isoformat(),"previous_receipt_sha256":prev}
 dg=sha(b);rec={**b,"receipt_sha256":dg};fp=d/(dg.split(":",1)[1]+".json")
 if fp.exists() and load(fp)!=rec:raise SystemExit("org receipt collision")
 if not fp.exists():fp.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
 h.write_text(json.dumps({"organization":C["organization"],"receipt_sha256":dg,"receipt_path":str(fp)},indent=2,sort_keys=True)+"\n");print(json.dumps(rec,sort_keys=True))
if __name__=="__main__":main()
