#!/usr/bin/env python3
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

KINDS=["INGRESS_ACCEPTED","DISPATCHED","CONSUMED","RESULT_BOUND","EGRESS_EMITTED"]

def canon(v): return json.dumps(v,sort_keys=True,separators=(",",":")).encode()
def hid(prefix,v): return prefix+"-"+hashlib.sha256(canon(v)).hexdigest()[:24]
def load(path): return json.loads(Path(path).read_text())

#: The exit-code split of Data-Continuation/.github#10 @ac8d7ea: a fault in this
#: organization's own write is non-terminal (nothing durable was written, the
#: caller retries); a bad envelope, registry or adapter outcome is terminal.
EXIT_WRITE_FAULT=75
EXIT_INPUT_FAULT=65
RETRY_ENTRYPOINT="org-boundary/runtime/process_boundary.py (same arguments)"
OWNING_GOAL="INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001"

class InputFault(Exception):
    """The envelope, the registry or the addressed service's adapter outcome is bad."""

class WriteFault(Exception):
    """This organization's own write of the execution result faulted."""

def fault_record(fault):
    write=isinstance(fault,WriteFault)
    return {"disposition":"FAIL_CLOSED",
            "failure_code":"PROCESS_BOUNDARY_WRITE_FAULT" if write else "PROCESS_BOUNDARY_INPUT_FAULT",
            "failed_predicate":"OWN_STORAGE_ACCEPTS_THE_EXECUTION_RESULT" if write else "ENVELOPE_AND_SERVICE_ARE_PROCESSABLE",
            "detail":str(fault)[:512],
            "required_evidence_or_repair":"this organization's own storage accepts the --out write" if write
            else "a well-formed envelope addressed to an installed service of this organization",
            "retry_entrypoint":RETRY_ENTRYPOINT,"owning_existing_goal":OWNING_GOAL,
            "next_attempt":"retry with the same envelope; nothing durable was written" if write
            else "the frame is refused; a corrected envelope is a new crossing",
            "terminal":not write,"derived_from_clock":False,"consequence_committed":False,
            "exit_code":EXIT_WRITE_FAULT if write else EXIT_INPUT_FAULT}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--envelope",required=True)
    ap.add_argument("--registry",default="org-boundary/registry/services.json")
    ap.add_argument("--out",required=True)
    a=ap.parse_args()

    try:
        result,svc,prev=execute(a)
    except WriteFault as fault:
        print(json.dumps(fault_record(fault),sort_keys=True)); return EXIT_WRITE_FAULT
    except InputFault as fault:
        print(json.dumps(fault_record(fault),sort_keys=True)); return EXIT_INPUT_FAULT
    except (OSError,UnicodeDecodeError,ValueError,KeyError,TypeError,AttributeError,StopIteration,RecursionError,MemoryError) as error:
        # Anything reading or interpreting the envelope, the registry or the
        # adapter's result is the input's fault, never this boundary's storage.
        print(json.dumps(fault_record(InputFault(type(error).__name__+": "+str(error))),sort_keys=True)); return EXIT_INPUT_FAULT
    try:
        Path(a.out).parent.mkdir(parents=True,exist_ok=True)
        Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    except OSError as error:
        print(json.dumps(fault_record(WriteFault(type(error).__name__+": "+str(error))),sort_keys=True)); return EXIT_WRITE_FAULT
    print(json.dumps({"status":"PASS","terminal_receipt_id":prev,"service_id":svc["service_id"]}))
    return 0

def execute(a):
    env=load(a.envelope)
    reg=load(a.registry)
    if not isinstance(env,dict) or not isinstance(reg,dict): raise InputFault("envelope-or-registry-not-an-object")
    req=["schema_version","packet_id","direction","origin","destination","carrier","intr_profile","transition","payload","evidence"]
    miss=[k for k in req if k not in env]
    if miss: raise InputFault("missing:"+",".join(miss))
    if env["destination"]["org"]!=reg["organization"]: raise InputFault("wrong-destination-org")
    svc=next((s for s in reg["services"] if s["service_id"]==env["destination"]["service"]),None)
    if not svc: raise InputFault("unknown-service")

    role=svc.get("boundary_role")
    if role=="BOUNDARY_LOCAL_DIAGNOSTIC":
        application_result={"echo":env["payload"]}
    elif role=="INTERNAL_ENDPOINT":
        adapter=svc.get("endpoint_adapter")
        if not adapter: raise InputFault("endpoint-adapter-not-installed")
        adapter_path=Path(adapter)
        if not adapter_path.is_file(): raise InputFault("endpoint-adapter-missing")
        adapter_out=Path(a.out).with_suffix(".adapter.json")
        completed=subprocess.run(
            ["python3",str(adapter_path),"--ingress",str(Path(a.envelope)),"--out",str(adapter_out)],
            capture_output=True,text=True,check=False
        )
        if not adapter_out.is_file():
            # An installed adapter always writes its result (BLOCKED on its own
            # errors) into this organization's output directory, so a missing
            # result is that write failing: non-terminal, never a quarantine.
            raise WriteFault("endpoint-adapter-output-missing:"+completed.stderr[-256:])
        application_result=load(adapter_out)
    else:
        raise InputFault("endpoint-adapter-not-installed")

    base={
      "packet_id":env["packet_id"],
      "service_id":svc["service_id"],
      "payload_hash":hashlib.sha256(canon(env["payload"])).hexdigest()
    }
    receipts=[]; prev=None
    for kind in KINDS:
        subject={**base,"kind":kind,"previous_receipt_id":prev}
        rid=hid(kind.lower(),subject)
        receipts.append({
          "kind":kind,
          "receipt_id":rid,
          "subject":svc["service_id"],
          "evidence_hash":hashlib.sha256(canon(subject)).hexdigest(),
          "previous_receipt_id":prev
        })
        prev=rid

    result={
      "schema_version":reg["organization"].lower().replace(" ","-")+".boundary-execution.v1",
      "packet_id":env["packet_id"],
      "organization":reg["organization"],
      "service_id":svc["service_id"],
      "consumed":application_result.get("state")!="BLOCKED",
      "application_result":application_result,
      "authority_effect":env["transition"]["authority_effect"],
      "receipts":receipts,
      "reconstruction":{
        "same_execution_required":True,
        "status":"RECONSTRUCTED",
        "terminal_receipt_id":prev
      }
    }
    return result,svc,prev

if __name__=="__main__":
    sys.exit(main())
