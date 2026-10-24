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
def canon(v):return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()
def sha(v):return "sha256:"+hashlib.sha256(canon(v)).hexdigest()
def _load_ledger_store():
 spec=importlib.util.spec_from_file_location("ledger_store_org", ROOT/"resident-runtime/ledger_store.py")
 module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
 return module
ledger_store=_load_ledger_store()
_kspec=importlib.util.spec_from_file_location("kernel_org_ledger", ROOT/"org-kernel/kernel.py")
kernel=importlib.util.module_from_spec(_kspec); _kspec.loader.exec_module(kernel)
# A run started from a committed request records it (B-P40 COMMITTED_REQUEST).
_rspec=importlib.util.spec_from_file_location("committed_request_org_ledger", ROOT/"scripts/read_committed_request.py")
committed_request=importlib.util.module_from_spec(_rspec); _rspec.loader.exec_module(committed_request)
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
ON_LEDGER_PREDICATE="SOURCE_RECEIPT_IS_ON_ITS_REPOSITORY_LEDGER_REACHABLE_FROM_HEAD"
UNVERIFIED_PREDICATE="SOURCE_RECEIPT_CARRIES_THIS_RUN_S_COMMITTED_REQUEST"
PAIRED_PREDICATE="SOURCE_LEDGER_IS_THE_REPOSITORY_LEDGER_PAIRED_WITH_THIS_ORG_LEDGER"
CHAIN_PREDICATE="SOURCE_REQUEST_CHAIN_IS_ACYCLIC_AND_BOUNDED"
#: The longest source_committed_request chain an aggregate follows.
SOURCE_REQUEST_CHAIN_LIMIT=8
#: This repository's own transition ledger contract: the only repository whose
#: receipts this writer can verify, on the only ledger it reads (row 8).
REPO_CONTRACT=json.loads((ROOT/".stegverse/transition-ledger/contract.json").read_text())
def repo_ledger_root():
 """This repository's own emit store, resolved exactly as emit.ledger_root resolves it.

 Never a location the source receipt or a request names: there is no source
 ledger argument, the receipt's `repository` never becomes a path (row 8),
 and a redirect is accepted only paired with the organization ledger
 (`unpaired_source_ledger`).
 """
 r=os.getenv("STEGVERSE_REPO_LEDGER_ROOT")
 if r:return ledger_store.parse_locator(r)
 return (Path(os.getenv("XDG_STATE_HOME",str(Path.home()/".local/state")))/"stegverse/repo-ledgers"/REPO_CONTRACT["repository"]).resolve()
def unpaired_source_ledger(repo_root, org_root):
 """Why `repo_root` is not the repository ledger paired with `org_root`, or None.

 A git repository ledger must be the contract namespace of the organization
 ledger's own ref in the same repository (both resolved through symlinks);
 a POSIX one is paired only with a POSIX organization ledger. A mixed pair
 is refused, so a redirect moves both ledgers together (CALLER_CHOSEN_SOURCE_LEDGER).
 """
 git_repo,git_org=(isinstance(root,ledger_store.GitLocator) for root in (repo_root,org_root))
 if git_repo!=git_org:return "a git and a POSIX ledger are not a pair: "+str(repo_root)+" with "+str(org_root)
 if not git_repo:return None
 if Path(os.path.realpath(repo_root.repository))!=Path(os.path.realpath(org_root.repository)):
  return "the repository ledger "+str(repo_root)+" is in another repository than the organization ledger "+str(org_root)
 if repo_root.ref!=org_root.ref:return "the repository ledger ref "+repo_root.ref+" is not the organization ledger ref "+org_root.ref
 namespace=REPO_CONTRACT["repository_ledger_location"]["namespace"]
 if repo_root.namespace!=namespace or org_root.namespace is not None:
  return "the repository ledger namespace "+str(repo_root.namespace)+" is not "+namespace+" beside the organization ledger"
 return None
def _bound_requests(store,head):
 """{committed request sha256: that request's source_committed_request sha256 or None} for every
 receipt reachable from `head` that is bound to a committed request (the direct field)."""
 bound={}; cursor=head.get("receipt_sha256") if isinstance(head,dict) else None; seen=set()
 while isinstance(cursor,str) and cursor not in seen:
  seen.add(cursor); receipt=store.get(ledger_store.receipt_key(cursor))
  if not isinstance(receipt,dict):break
  evidence=receipt.get("evidence") if isinstance(receipt.get("evidence"),dict) else {}
  own=evidence.get("committed_request"); source=evidence.get("source_committed_request")
  if isinstance(own,dict) and isinstance(own.get("sha256"),str):
   bound.setdefault(own["sha256"],source.get("sha256") if isinstance(source,dict) else None)
  cursor=receipt.get("previous_receipt_sha256")
 return bound
def _source_chain_failure(bound,request,source):
 """(code, detail) when the named source chain does not resolve on the ledger, or None.

 Each named digest must be a committed request with a receipt bound to it on
 the ledger; the chain may not return to a request already on it (the run's
 own included) and may not exceed SOURCE_REQUEST_CHAIN_LIMIT links.
 """
 seen={request["sha256"]} if request else set(); link=source["sha256"]; depth=0
 while link:
  if link in seen:return "COMMITTED_REQUEST_DIGEST_UNVERIFIED","the source request chain returns to "+link
  seen.add(link); depth+=1
  if depth>SOURCE_REQUEST_CHAIN_LIMIT:
   return "SOURCE_REQUEST_CHAIN_TOO_DEEP","the source request chain exceeds "+str(SOURCE_REQUEST_CHAIN_LIMIT)+" requests"
  if link not in bound:return "COMMITTED_REQUEST_DIGEST_UNVERIFIED","committed request "+link+" has no receipt bound to it on the ledger"
  link=bound[link]
 return None
def unverified_source_refusal(repo_receipt, digest, request, source=None):
 """The six-field refusal of a source receipt, or None.

 Unconditionally, the source receipt must be this repository's, read from
 the repository ledger paired with this organization ledger
 (SOURCE_LEDGER_NOT_PAIRED), and be the receipt at `digest` there, byte for
 byte, reachable from HEAD (SOURCE_RECEIPT_NOT_ON_LEDGER). Its
 committed_request must then be this run's own (`request`, None outside a
 committed-request run) or, when the run's request names `source`, exactly
 that request, whose chain resolves on the ledger
 (COMMITTED_REQUEST_DIGEST_UNVERIFIED, SOURCE_REQUEST_CHAIN_TOO_DEEP). Any
 refusal comes before anything is written. The ledger is only read: a
 corrupt stored document is a terminal refusal, an I/O fault a retryable one.
 """
 terminal=True; code,predicate="SOURCE_RECEIPT_NOT_ON_LEDGER",ON_LEDGER_PREDICATE
 repository=REPO_CONTRACT["repository"]
 if repo_receipt.get("repository")!=repository:
  detail="source "+digest+" is "+str(repo_receipt.get("repository"))+"'s receipt; only "+repository+"'s own ledger is read"
 else:
  try:
   repo_root=repo_ledger_root()
   detail=unpaired_source_ledger(repo_root,ledger_root())
   if detail is not None:
    code,predicate="SOURCE_LEDGER_NOT_PAIRED",PAIRED_PREDICATE
   else:
    store=ledger_store.open_store(repo_root)
    head=store.get(ledger_store.HEAD_KEY)
    if not (isinstance(head,dict) and head.get("repository")==repository):head=None
    cursor=head.get("receipt_sha256") if head else None
    seen=set()
    while isinstance(cursor,str) and cursor!=digest and cursor not in seen:
     seen.add(cursor); prior=store.get(ledger_store.receipt_key(cursor))
     cursor=prior.get("previous_receipt_sha256") if isinstance(prior,dict) else None
    if cursor!=digest or canon(store.get(ledger_store.receipt_key(digest)))!=canon(repo_receipt):
     detail="source "+digest+" is not, byte for byte, a receipt reachable from its repository ledger HEAD"
    else:
     code,predicate="COMMITTED_REQUEST_DIGEST_UNVERIFIED",UNVERIFIED_PREDICATE
     evidence=repo_receipt.get("evidence")
     carried=evidence.get("committed_request") if isinstance(evidence,dict) else None
     expected=request if source is None else {**request,"sha256":source["sha256"]}
     if carried!=expected:
      detail=("source "+digest+" carries committed_request "+json.dumps(carried,sort_keys=True)
              +", not "+("this run's" if source is None else "the named source request")+" "+json.dumps(expected,sort_keys=True))
     elif source is not None:
      failure=_source_chain_failure(_bound_requests(store,head),request,source)
      if failure is not None:
       code,detail=failure
       if code=="SOURCE_REQUEST_CHAIN_TOO_DEEP":predicate=CHAIN_PREDICATE
  except (OSError,ledger_store.LedgerWriteFault) as exc:
   # The ledger could not be read: not verified, and retryable.
   terminal=False; detail=("the repository ledger could not be read: "+type(exc).__name__+": "+str(exc))[:512]
  except (ValueError,TypeError,RecursionError,MemoryError) as exc:
   # A stored document is corrupt (truncated, not JSON, not UTF-8): not verified, and terminal.
   detail=("a stored repository ledger document is corrupt: "+type(exc).__name__+": "+str(exc))[:512]
 if detail is None:return None
 return {"disposition":"FAIL_CLOSED","failure_code":code,"failed_predicate":predicate,
         "detail":detail,"required_evidence_or_repair":"pass the source receipt as recorded on the repository ledger paired with this organization ledger, from this run's committed request or the one it names as source_committed_request",
         "retry_entrypoint":EPOCH_RETRY_ENTRYPOINT,"owning_existing_goal":kernel.HB_EPOCH_OWNING_EXISTING_GOAL,
         "next_attempt":"nothing was written: no organization receipt, no source copy, no HEAD change",
         "terminal":terminal,"derived_from_clock":False,"consequence_committed":False}
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
 evidence,refused=committed_request.bind(boundary_evidence,"boundary_evidence")
 if refused is not None:raise OrgLedgerEpochRefused(refused)
 refused=unverified_source_refusal(repo_receipt,rd,evidence.get("committed_request"),evidence.get("source_committed_request"))
 if refused is not None:raise OrgLedgerEpochRefused(refused)
 root=ledger_root(); store=ledger_store.open_store(root); store.initialize()
 retained={ledger_store.source_key(rd): repo_receipt}
 for _attempt in range(128):
  guard=store.exclusive() if hasattr(store, "exclusive") else nullcontext()
  with guard:
   expected=store.get(ledger_store.HEAD_KEY)
   head=expected if isinstance(expected, dict) else {}
   prior=_recorded_for_repo(store, head, rd, org_transition_class)
   if prior is not None:
    if idempotent and prior.get("boundary_evidence")==evidence: return prior
    # A retry of an append that already completed returns the recorded
    # receipt; only different content under the transition collides.
    if (prior.get("predecessor_org_state_sha256"),prior.get("successor_org_state_sha256"),prior.get("boundary_evidence"),prior.get("authority_effect"))==(predecessor,successor,evidence,authority_effect): return prior
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
 # Bad input is the caller's: terminal six fields, read before anything is written.
 try:
  repo_receipt=kernel.read_json_input(a.repo_receipt,argument="--repo-receipt",retry_entrypoint=EPOCH_RETRY_ENTRYPOINT)
  try:verify_repo(repo_receipt)
  except SystemExit as exc:raise kernel.CliInputRefused(kernel.cli_input_refusal("--repo-receipt",str(exc.code),expect=dict,retry_entrypoint=EPOCH_RETRY_ENTRYPOINT)) from None
  boundary_evidence=kernel.parse_json_argument(a.boundary_evidence_json,argument="--boundary-evidence-json",retry_entrypoint=EPOCH_RETRY_ENTRYPOINT)
 except kernel.CliInputRefused as exc:print(json.dumps(exc.refusal,sort_keys=True));raise SystemExit(1)
 try:rec=append(repo_receipt,a.org_transition_class,a.predecessor_org_state_sha256,a.successor_org_state_sha256,boundary_evidence,a.authority_effect,hb_epoch=a.hb_epoch)
 except OrgLedgerEpochRefused as exc:print(json.dumps(exc.refusal,sort_keys=True));raise SystemExit(1)
 except Exception as exc:
  # A torn write or a collision is six fields and exit 1, never a traceback.
  refusal=kernel.writer_cli_refusal(exc,failure_code="ORG_LEDGER_WRITE_FAILED",retry_entrypoint=EPOCH_RETRY_ENTRYPOINT)
  if refusal is None:raise
  print(json.dumps(refusal,sort_keys=True));raise SystemExit(1)
 print(json.dumps(rec,sort_keys=True))
if __name__=="__main__":main()
