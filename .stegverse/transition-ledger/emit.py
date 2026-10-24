#!/usr/bin/env python3
import argparse, hashlib, importlib.util, json, os
from contextlib import nullcontext
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2]
CONTRACT=json.loads((ROOT/".stegverse/transition-ledger/contract.json").read_text())
HB_ANCHOR_EPOCH=32
#: G4 / NWI-S1 (SV_LLM_LEDGER_APPEND_CLOCK_FALLBACK family): hb_reference no
#: longer derives an epoch from the host clock. The shared supplied-epoch rule
#: below is vendored byte-identical (function segment sha256 SHARED_RULE_SHA256).
HB_EPOCH_PREDICATE="SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH"
SHARED_RULE_SHA256="726248a585904b52cfe2eec1754e7ce582f67d6b501bd664bb7bee80bce9b7ef"
OWNING_EXISTING_GOAL="StegVerse-org/.github#162 / INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001 (NWI-S1)"
EPOCH_RETRY_ENTRYPOINT=".stegverse/transition-ledger/emit.py::append(hb_epoch=<supplied>) / --hb-epoch"


def supplied_epoch_failure(hb_epoch: Any, reference: Any = None) -> tuple[str, str] | None:
    """The shared supplied-epoch rule (SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH).

    Byte-identical in StegVerse-org/.github#185 and StegVerse-Labs/.github#3212
    and #3213. `hb_epoch` absent (None) is HB_EPOCH_NOT_SUPPLIED. Otherwise it
    must be ASCII [0-9]+ only -- an int is read as its decimal text; a bool, a
    float or anything coerced ('+33', ' 33', '3_3', '33.0') is refused -- with
    integer value >= 32 (the HB32 anchor). `reference`, the carrier frame's
    heartbeat reference when there is one, must be an object, and a
    `derived_from_clock` it carries must be exactly false. Any failure is
    HB_EPOCH_INVALID. Returns (failure_code, detail), or None when the epoch is
    supplied. No clock is read.
    """
    if reference is not None and not isinstance(reference, dict):
        return "HB_EPOCH_INVALID", "the carrier's heartbeat reference is not an object"
    if hb_epoch is None:
        return "HB_EPOCH_NOT_SUPPLIED", "no hb_epoch was supplied and no clock is read"
    if isinstance(hb_epoch, bool):
        text = None
    elif isinstance(hb_epoch, int):
        text = str(hb_epoch)
    elif isinstance(hb_epoch, str):
        text = hb_epoch
    else:
        text = None
    if text is None or not text.isascii() or not text.isdigit():
        return "HB_EPOCH_INVALID", "hb_epoch " + repr(hb_epoch) + " is not ASCII [0-9]+"
    if int(text) < 32:
        return "HB_EPOCH_INVALID", "hb_epoch " + text + " is below the HB32 anchor (32)"
    if reference is not None and "derived_from_clock" in reference \
            and reference["derived_from_clock"] is not False:
        return "HB_EPOCH_INVALID", ("the carrier's derived_from_clock is not exactly false; "
                                    "a clock-derived epoch is not a supplied one")
    return None


class RepoLedgerEpochRefused(ValueError):
    """An append refused because its epoch is absent or invalid; `refusal` is the six-field FAIL_CLOSED."""
    def __init__(self, refusal):
        super().__init__(refusal["failure_code"]+":"+refusal["detail"])
        self.refusal=dict(refusal)
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
def observed_at_from_epoch(hb_epoch, hb):
    """observed_at provenance from the supplied heartbeat epoch, never a wall-clock read: same epoch, same receipt."""
    return "SUPPLIED_HB_EPOCH:%d"%hb["epoch"]
def epoch_refusal(epoch):
    """The six-field FAIL_CLOSED refusal of a supplied epoch, or None. No clock is read."""
    failure=supplied_epoch_failure(epoch)
    if failure is None: return None
    code,detail=failure
    return {"disposition":"FAIL_CLOSED","failure_code":code,"failed_predicate":HB_EPOCH_PREDICATE,"detail":detail,
            "required_evidence_or_repair":"supply hb_epoch as ASCII [0-9]+ with value >= %d; it is never derived from a clock"%HB_ANCHOR_EPOCH,
            "retry_entrypoint":EPOCH_RETRY_ENTRYPOINT,"owning_existing_goal":OWNING_EXISTING_GOAL,
            "next_attempt":"append again with the supplied epoch; nothing was written","authority_effect":"NONE"}
def hb_reference(epoch=None):
    """The heartbeat reference for a supplied epoch, or its six-field FAIL_CLOSED refusal (never a clock value)."""
    refusal=epoch_refusal(epoch)
    if refusal is not None: return refusal
    epoch=int(str(epoch))
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
    hb=hb_reference(hb_epoch)
    if hb.get("disposition")=="FAIL_CLOSED": raise RepoLedgerEpochRefused(hb)  # before the store is opened
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
            body={"schema":"stegverse.repo-transition-receipt/v1","repository":CONTRACT["repository"],"transition_id":transition_id,"transition_class":transition_class,"predecessor_state_sha256":predecessor,"successor_state_sha256":successor,"evidence":evidence,"authority_effect":authority_effect,"hb_reference":hb,"observed_at":observed_at_from_epoch(hb_epoch, hb),"previous_receipt_sha256":previous}
            digest=sha(body); record={**body,"receipt_sha256":digest}; key=ledger_store.receipt_key(digest)
            new_head={"repository":CONTRACT["repository"],"receipt_sha256":digest,"receipt_path":store.locator(key)}
            compared=expected if isinstance(expected, dict) else None
            if store.append_transaction(key, record, compared, new_head): return record
    raise RuntimeError("REPO_LEDGER_APPEND_CONTENTION_EXHAUSTED")
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--transition-id",required=True); ap.add_argument("--transition-class",required=True); ap.add_argument("--predecessor-state-sha256",required=True); ap.add_argument("--successor-state-sha256",required=True); ap.add_argument("--evidence-json",default="{}"); ap.add_argument("--authority-effect",default="NONE"); ap.add_argument("--hb-epoch",type=str,default=None); ap.add_argument("--hb-ref",type=str,default=None); a=ap.parse_args()
    epoch=a.hb_epoch if a.hb_epoch is not None else a.hb_ref
    try: record=append(a.transition_id,a.transition_class,a.predecessor_state_sha256,a.successor_state_sha256,json.loads(a.evidence_json),a.authority_effect,hb_epoch=epoch)
    except RepoLedgerEpochRefused as refused:
        print(json.dumps(refused.refusal,sort_keys=True)); raise SystemExit(1)
    print(json.dumps(record,sort_keys=True))
if __name__=="__main__": main()
