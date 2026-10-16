#!/usr/bin/env python3
import argparse, hashlib, importlib.util, json, os
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CONTRACT=json.loads((ROOT/".stegverse/transition-ledger/contract.json").read_text())
HB_ANCHOR_EPOCH=32
HB_ANCHOR_UNIX_NS=1_787_511_600_000_000_000
HB_PERIOD_NS=10_000_000
def canon(v): return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def sha(v): return "sha256:"+hashlib.sha256(v if isinstance(v,(bytes,bytearray)) else canon(v)).hexdigest()
def _load_ledger_store():
    spec=importlib.util.spec_from_file_location("ledger_store", ROOT/"resident-runtime/ledger_store.py")
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module
ledger_store=_load_ledger_store()
def ledger_root():
    """The repository ledger location supplied to this execution.

    A `git+<repository>#<ref>` or `git+<repository>#<ref>:<namespace>` names a
    git ref (see `ledger_store.parse_locator`). A plain path is a directory.
    With no supplied root, the machine-local directory remains the fallback
    for a caller that has not been pointed at the designated ref.
    """
    override=os.getenv("STEGVERSE_REPO_LEDGER_ROOT")
    if override: return ledger_store.parse_locator(override)
    base=Path(os.getenv("XDG_STATE_HOME",str(Path.home()/".local/state")))
    return (base/"stegverse/repo-ledgers"/CONTRACT["repository"]).resolve()
def lr():
    return ledger_root()
def hb_reference(epoch=None):
    if epoch is None:
        now_ns=int(datetime.now(timezone.utc).timestamp()*1_000_000_000)
        if now_ns<HB_ANCHOR_UNIX_NS: epoch=HB_ANCHOR_EPOCH
        else:
            quanta,_=divmod(now_ns-HB_ANCHOR_UNIX_NS, HB_PERIOD_NS)
            epoch=HB_ANCHOR_EPOCH+quanta
    epoch=int(epoch)
    return {"epoch":epoch,"generation":epoch,"heartbeat_id":f"HB:{epoch}","frequency_hz":100,"progression_dependency":"OSCILLATOR_ONLY","authority_effect":"NONE"}
def recorded(store, head, transition_id, transition_class):
    cursor=head.get("receipt_sha256") if isinstance(head, dict) else None
    while isinstance(cursor, str) and cursor:
        receipt=store.get(ledger_store.receipt_key(cursor))
        if not isinstance(receipt, dict):
            raise ValueError("REPO_LEDGER_CHAIN_BREAK")
        if receipt.get("transition_id")==transition_id and receipt.get("transition_class")==transition_class: return receipt
        cursor=receipt.get("previous_receipt_sha256")
    return None
def append(transition_id, transition_class, predecessor, successor, evidence, authority_effect="NONE", hb_epoch=None, idempotent_on=None):
    """Append one repository receipt. A matching idempotent replay returns the recorded receipt.

    The receipt, and HEAD, are one store transaction. A lost compare-and-swap
    writes nothing and the attempt reads the chain again. Authority and time
    stay constraint variables. The disposition inside `evidence` is transition
    evidence only.
    """
    evidence=dict(evidence)
    root=lr(); store=ledger_store.open_store(root); store.initialize()
    for _attempt in range(128):
        guard=store.exclusive() if hasattr(store, "exclusive") else nullcontext()
        with guard:
            expected=store.get(ledger_store.HEAD_KEY)
            head=expected if isinstance(expected, dict) else {}
            prior=recorded(store, head, transition_id, transition_class)
            if prior is not None:
                observed=prior.get("evidence") or {}
                fields=tuple(idempotent_on or ())
                if fields and all(observed.get(name)==evidence.get(name) for name in fields): return prior
                raise ValueError("ledger_receipt_collision")
            previous=head.get("receipt_sha256") if head else None
            body={"schema":"stegverse.repo-transition-receipt/v1","repository":CONTRACT["repository"],"transition_id":transition_id,"transition_class":transition_class,"predecessor_state_sha256":predecessor,"successor_state_sha256":successor,"evidence":evidence,"authority_effect":authority_effect,"hb_reference":hb_reference(hb_epoch),"observed_at":datetime.now(timezone.utc).isoformat(),"previous_receipt_sha256":previous}
            digest=sha(body); record={**body,"receipt_sha256":digest}; key=ledger_store.receipt_key(digest)
            new_head={"repository":CONTRACT["repository"],"receipt_sha256":digest,"receipt_path":store.locator(key)}
            compared=expected if isinstance(expected, dict) else None
            if store.append_transaction(key, record, compared, new_head): return record
    raise RuntimeError("REPO_LEDGER_APPEND_CONTENTION_EXHAUSTED")
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--transition-id",required=True); ap.add_argument("--transition-class",required=True); ap.add_argument("--predecessor-state-sha256",required=True); ap.add_argument("--successor-state-sha256",required=True); ap.add_argument("--evidence-json",default="{}"); ap.add_argument("--authority-effect",default="NONE"); ap.add_argument("--hb-epoch",type=int,default=None); ap.add_argument("--hb-ref",default=None); a=ap.parse_args()
    epoch=a.hb_epoch if a.hb_epoch is not None else (int(a.hb_ref) if a.hb_ref is not None else None)
    record=append(a.transition_id,a.transition_class,a.predecessor_state_sha256,a.successor_state_sha256,json.loads(a.evidence_json),a.authority_effect,hb_epoch=epoch)
    print(json.dumps(record,sort_keys=True))
if __name__=="__main__": main()
