#!/usr/bin/env python3
import argparse, hashlib, importlib.util, json, os
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CONTRACT=json.loads((ROOT/".stegverse/transition-ledger/contract.json").read_text())
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
EPOCH_NOT_SUPPLIED="HB_EPOCH_NOT_SUPPLIED_PATH_LIVE"
class EpochNotSupplied(ValueError):
    """A receipt was asked for with no supplied heartbeat epoch. Nothing was written.

    The six fields say what failed and how to retry. No clock is read to fill
    the epoch in.
    """
    def __init__(self):
        self.fields={"failure_code":EPOCH_NOT_SUPPLIED,
            "failed_predicate":"RECEIPT_HB_EPOCH_IS_SUPPLIED_BY_THE_CALLER",
            "required_evidence_or_repair":"pass an integer hb_epoch (--hb-epoch) to the ledger writer; the epoch is not derived from a clock",
            "retry_entrypoint":".stegverse/transition-ledger/emit.py::append",
            "owning_existing_goal":"StegVerse-Labs/.github#2897 / StegVerse-org/.github#162 P0-runtime-and-custody",
            "next_attempt":"rerun with the supplied epoch; the store was not opened and no receipt or ref was written"}
        super().__init__(EPOCH_NOT_SUPPLIED)
def require_supplied_epoch(epoch):
    if epoch is None or isinstance(epoch,bool): raise EpochNotSupplied()
    return int(epoch)
def hb_reference(epoch):
    epoch=require_supplied_epoch(epoch)
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

    An unsupplied epoch raises `EpochNotSupplied` before the store opens.
    The receipt, and HEAD, are one store transaction. A lost compare-and-swap
    writes nothing and the attempt reads the chain again. Authority and time
    stay constraint variables. The disposition inside `evidence` is transition
    evidence only.
    """
    hb=hb_reference(hb_epoch)
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
            body={"schema":"stegverse.repo-transition-receipt/v1","repository":CONTRACT["repository"],"transition_id":transition_id,"transition_class":transition_class,"predecessor_state_sha256":predecessor,"successor_state_sha256":successor,"evidence":evidence,"authority_effect":authority_effect,"hb_reference":hb,"observed_at":datetime.now(timezone.utc).isoformat(),"previous_receipt_sha256":previous}
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
