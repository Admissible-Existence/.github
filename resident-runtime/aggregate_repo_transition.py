#!/usr/bin/env python3
"""Append one organization receipt that preserves the repository receipt.

The repository receipt is verified, retained under ``source-receipts/``, and
named from the organization receipt. The receipt and HEAD are one store
transaction on the location the caller supplies, including a git ref.

Authority and time are constraint variables. The disposition carried in
boundary evidence is transition evidence only.
"""
import argparse, hashlib, importlib.util, json, os
from contextlib import nullcontext
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
_kspec=importlib.util.spec_from_file_location("kernel_org_ledger", ROOT/"org-kernel/kernel.py")
kernel=importlib.util.module_from_spec(_kspec); _kspec.loader.exec_module(kernel)
#: An append's epoch is supplied by its caller and checked by the kernel's
#: shared rule (SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH); an absent or invalid
#: one is refused six-field FAIL_CLOSED before anything is written, as
#: StegVerse-Labs/.github@bc608a3 defines it.
EPOCH_RETRY_ENTRYPOINT="resident-runtime/aggregate_repo_transition.py::append (hb_epoch=, or --hb-epoch)"
OrgLedgerEpochRefused=kernel.SuppliedEpochRefused
def epoch_refusal(hb_epoch):
 """The six-field FAIL_CLOSED refusal of an append's epoch, or None."""
 return kernel.writer_epoch_refusal(hb_epoch,retry_entrypoint=EPOCH_RETRY_ENTRYPOINT)
def require_supplied_epoch(hb_epoch):
 """The heartbeat reference of the supplied epoch, or OrgLedgerEpochRefused. No clock is read."""
 return kernel.supplied_hb_reference(hb_epoch,retry_entrypoint=EPOCH_RETRY_ENTRYPOINT)
SOURCE_PREDICATE="SOURCE_RECEIPT_CARRIES_A_SUPPLIED_HB_EPOCH"
CLOCK_SOURCE_REPAIR=("a WU-B13 migration transition that rebinds the legacy repo receipt under a supplied epoch "
                     "with provenance CARRIED:LEGACY_CLOCK_RECEIPT + source sha; existing receipts are never mutated")
def source_refusal(repo_receipt):
 """The six-field refusal of a source repository receipt whose epoch is not a supplied one, or None.

 A clock reference (derived_from_clock true, or no marker with sampled_unix_ns)
 is SOURCE_RECEIPT_IS_CLOCK_PROVENANCE. Any other reference must pass the
 shared rule against itself; one that marks nothing is HB_EPOCH_PROVENANCE_UNMARKED.
 """
 ref=repo_receipt.get("hb_reference") if isinstance(repo_receipt,dict) else None
 if isinstance(ref,dict) and (ref.get("derived_from_clock") is True
                              or ("derived_from_clock" not in ref and "sampled_unix_ns" in ref)):
  code,detail,repair="SOURCE_RECEIPT_IS_CLOCK_PROVENANCE","the source repository receipt's epoch was read from a clock",CLOCK_SOURCE_REPAIR
 else:
  failure=(kernel.supplied_epoch_failure(ref.get("epoch"),ref) if isinstance(ref,dict)
           else ("HB_EPOCH_PROVENANCE_UNMARKED","the source repository receipt carries no heartbeat reference"))
  if failure is None:return None
  code,detail=failure
  repair="the source repository receipt carries a supplied hb_reference (derived_from_clock false) that passes the shared rule"
 return {"disposition":"FAIL_CLOSED","failure_code":code,"failed_predicate":SOURCE_PREDICATE,
         "detail":"source "+str(repo_receipt.get("receipt_sha256") if isinstance(repo_receipt,dict) else None)+": "+detail,
         "required_evidence_or_repair":repair,"retry_entrypoint":EPOCH_RETRY_ENTRYPOINT,
         "owning_existing_goal":kernel.HB_EPOCH_OWNING_EXISTING_GOAL,
         "next_attempt":"nothing was written: no organization receipt, no source copy, no HEAD change",
         "derived_from_clock":False,"consequence_committed":False}
def ledger_root():
 """The organization ledger location supplied to this execution.

 A ``git+<repository>#<ref>`` names the designated ref. A plain path is a
 directory. With no supplied root, the machine-local directory remains the
 fallback for a caller that has not been pointed at the designated ref.
 """
 o=os.getenv("STEGVERSE_ORG_LEDGER_ROOT")
 if o:return ledger_store.parse_locator(o)
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
  if not isinstance(receipt, dict): raise ledger_store.LedgerWriteFault("ORG_LEDGER_CHAIN_BREAK")
  if receipt.get("repo_receipt_sha256")==repo_digest and receipt.get("org_transition_class")==org_class: return receipt
  cursor=receipt.get("previous_receipt_sha256")
 return None
def append(repo_receipt, org_transition_class, predecessor, successor, boundary_evidence, authority_effect="NONE", hb_epoch=None, idempotent=False):
 """Append one organization receipt that preserves the repository receipt digest.

 An absent or invalid epoch raises `OrgLedgerEpochRefused` before the store
 opens or any directory is created. So does a source receipt whose epoch is
 not a supplied one (`source_refusal`). `observed_at` is the supplied epoch's
 heartbeat id; no clock is read.
 """
 hb=require_supplied_epoch(hb_epoch)
 rd=verify_repo(repo_receipt)
 refusal=source_refusal(repo_receipt)
 if refusal is not None:raise OrgLedgerEpochRefused(refusal)
 evidence=dict(boundary_evidence); root=ledger_root(); store=ledger_store.open_store(root); store.initialize()
 retained={ledger_store.source_key(rd): repo_receipt}
 for _attempt in range(128):
  guard=store.exclusive() if hasattr(store, "exclusive") else nullcontext()
  with guard:
   expected=store.get(ledger_store.HEAD_KEY)
   head=expected if isinstance(expected, dict) else {}
   prior=_recorded_for_repo(store, head, rd, org_transition_class)
   if prior is not None:
    if idempotent and prior.get("boundary_evidence")==evidence: return prior
    raise ValueError("ledger_receipt_collision")
   previous=head.get("receipt_sha256") if head else None
   body={"schema":"stegverse.organization-transition-receipt/v1","organization":C["organization"],"source_repository":repo_receipt["repository"],"source_transition_sha256":rd,"repo_receipt_sha256":rd,"repo_transition_id":repo_receipt["transition_id"],"org_transition_class":org_transition_class,"predecessor_org_state_sha256":predecessor,"successor_org_state_sha256":successor,"boundary_evidence":evidence,"authority_effect":authority_effect,"hb_reference":hb,"observed_at":hb["heartbeat_id"],"previous_receipt_sha256":previous}
   digest=sha(body); record={**body,"receipt_sha256":digest}; key=ledger_store.receipt_key(digest)
   new_head={"organization":C["organization"],"receipt_sha256":digest,"receipt_path":store.locator(key)}
   compared=expected if isinstance(expected, dict) else None
   if store.append_transaction(key, record, compared, new_head, immutable=retained): return record
 raise ledger_store.LedgerWriteFault("ORG_LEDGER_APPEND_CONTENTION_EXHAUSTED")
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument("--repo-receipt",required=True);p.add_argument("--org-transition-class",default="REPO_STATE_PROPAGATION");p.add_argument("--predecessor-org-state-sha256",required=True);p.add_argument("--successor-org-state-sha256",required=True);p.add_argument("--boundary-evidence-json",default="{}");p.add_argument("--authority-effect",default="NONE");p.add_argument("--hb-epoch",default=None);a=p.parse_args()
 refusal=epoch_refusal(a.hb_epoch)
 if refusal is not None:print(json.dumps(refusal,sort_keys=True));raise SystemExit(1)
 try:rec=append(load(a.repo_receipt),a.org_transition_class,a.predecessor_org_state_sha256,a.successor_org_state_sha256,json.loads(a.boundary_evidence_json),a.authority_effect,hb_epoch=a.hb_epoch)
 except OrgLedgerEpochRefused as exc:print(json.dumps(exc.refusal,sort_keys=True));raise SystemExit(1)
 print(json.dumps(rec,sort_keys=True))
if __name__=="__main__":main()
