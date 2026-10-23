#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, json, os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("org_kernel",ROOT/"org-kernel"/"kernel.py")
K=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(K)
GWSPEC=importlib.util.spec_from_file_location("federation_gateway_transport",ROOT/"resident-runtime"/"federation_gateway_transport.py")
GW=importlib.util.module_from_spec(GWSPEC); GWSPEC.loader.exec_module(GW)
EPOCH_RETRY_ENTRYPOINT="resident-runtime/federation_cycle.py --hb-epoch (or HB_EPOCH)"

def main(argv=None):
    # The cycle record references the supplied epoch. An absent or invalid one
    # is the six-field refusal before anything is consumed or written, and no
    # clock is read.
    parser=argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--hb-epoch",default=None)
    args=parser.parse_args(argv)
    hb_epoch=args.hb_epoch if args.hb_epoch is not None else (os.getenv("HB_EPOCH") or None)
    refusal=K.writer_epoch_refusal(hb_epoch,retry_entrypoint=EPOCH_RETRY_ENTRYPOINT)
    if refusal is not None:
        print(json.dumps(refusal,sort_keys=True))
        return 1
    hb=K.supplied_hb_reference(hb_epoch,retry_entrypoint=EPOCH_RETRY_ENTRYPOINT)
    if os.getenv("STEGVERSE_ORG_FEDERATION_GATEWAY_URL","").strip():
        receipt=GW.resident_gateway_cycle(ROOT)
        receipt["heartbeat_reference"]=hb
        receipt["transport"]="SHARED_SERVICE_GATEWAY"
    else:
        results=K.consume_and_respond(ROOT)
        consumed=sum(1 for x in results if (x.get("result") or {}).get("status")=="CONSUMED")
        responses=sum(1 for x in results if x.get("response_publication"))
        receipt={
          "schema_version":"stegverse.org-federation-cycle.v1",
          "organization":K.load_registry(ROOT)["organization"],
          "heartbeat_reference":hb,
          "frames_seen":len(results),
          "frames_consumed":consumed,
          "responses_emitted":responses,
          "authority_effect":"NONE_CARRIER_ONLY",
          "transport":"LOCAL_SPOOL_FALLBACK"
        }
    out=ROOT/"resident-runtime"/"federation"/"latest-cycle.json"
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
