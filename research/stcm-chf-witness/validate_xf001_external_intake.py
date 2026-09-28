#!/usr/bin/env python3
"""Fail-closed XF-001 external intake preflight.

This validates only evidence-envelope readiness. It does not execute STCM, CHF,
Flint accounting, SDK/InTr, or grant authority.
"""
import json, re, sys
from pathlib import Path

HASH = re.compile(r"^sha256:[0-9a-f]{64}$")
GOAL = "STCM-CHF-THERMODYNAMIC-WITNESS-COMPARISON-001"
COSV = "10111010112000"

def disposition(obj):
    if obj.get("protocol_id") != "XF-001":
        return "FAIL_CLOSED_XF001_PROTOCOL_ID"
    if obj.get("goal_task_id") != GOAL or obj.get("cosv_id") != COSV:
        return "FAIL_CLOSED_CANONICAL_OWNER_BINDING"
    for key in ("specimen_id","transition_id"):
        if not isinstance(obj.get(key), str) or not obj[key]:
            return "FAIL_CLOSED_SPECIMEN_IDENTITY"
    for key in ("original_state","resulting_state"):
        blob=obj.get(key)
        if not isinstance(blob,dict) or not HASH.match(str(blob.get("sha256",""))) or not blob.get("format"):
            return "FAIL_CLOSED_EXACT_STATE_BINDING"
    bindings=obj.get("source_bindings")
    if not isinstance(bindings,list) or not bindings:
        return "FAIL_CLOSED_SOURCE_BINDINGS"
    if any(not isinstance(x,dict) or not HASH.match(str(x.get("sha256",""))) or not x.get("format") for x in bindings):
        return "FAIL_CLOSED_SOURCE_BINDINGS"
    witness=obj.get("independent_witness")
    if not isinstance(witness,dict) or not witness.get("identity") or not HASH.match(str(witness.get("evidence_sha256",""))):
        return "FAIL_CLOSED_INDEPENDENT_WITNESS"
    if witness.get("custody_status") != "verified":
        return "FAIL_CLOSED_WITNESS_CUSTODY"
    ext=obj.get("external_accounting")
    if not isinstance(ext,dict) or not HASH.match(str(ext.get("receipt_sha256",""))):
        return "FAIL_CLOSED_EXTERNAL_RECEIPT_BINDING"
    return "ALLOW_XF001_NATIVE_EVALUATION_INPUT_READY"

def main():
    obj=json.loads(Path(sys.argv[1]).read_text())
    print(json.dumps({"protocol_id":"XF-001","disposition":disposition(obj),"authority_effect":"NONE"},sort_keys=True))
if __name__=="__main__":
    main()
