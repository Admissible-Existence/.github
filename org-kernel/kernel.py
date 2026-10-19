#!/usr/bin/env python3
"""Universal StegVerse organization resident kernel.

Organization-neutral runtime behavior extracted from StegVerse-Labs/.github.
No GitHub, hosted scheduler, provider, or carrier sets authority. Authority and time are constraint variables; a disposition is transition evidence only.
"""
from __future__ import annotations
import base64, hashlib, importlib.util, json, os, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HB_ANCHOR_EPOCH=32
HB_ANCHOR_UNIX_NS=1_787_511_600_000_000_000
HB_PERIOD_NS=10_000_000
HB_HZ=100
CHANNEL_COUNT=16
SCHEMA="stegverse.org-resident-kernel/v1"
CARRIER_SCHEMA="stegverse.org-resident-kernel.carrier/v1"
PACKET_SCHEMA="stegverse.intr.org-boundary.v1"

def canon(v:Any)->bytes:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()

def sha(v:Any)->str:
    raw=v if isinstance(v,(bytes,bytearray)) else canon(v)
    return "sha256:"+hashlib.sha256(bytes(raw)).hexdigest()

def hb_reference(now_ns:int|None=None, *, epoch:int|None=None)->dict[str,Any]:
    if epoch is not None:
        if now_ns is not None: raise ValueError("supply_epoch_or_sample_not_both")
        if not isinstance(epoch,int) or isinstance(epoch,bool) or epoch<HB_ANCHOR_EPOCH:
            raise ValueError("epoch_precedes_hb32_anchor")
        return {"epoch":epoch,"generation":epoch,"heartbeat_id":f"HB:{epoch}",
                "phase_offset_ns":0,"frequency_hz":HB_HZ,"progression_dependency":"OSCILLATOR_ONLY",
                "derived_from_clock":False,"authority_effect":"NONE"}
    if now_ns is None:
        now_ns=int(datetime.now(timezone.utc).timestamp()*1_000_000_000)
    if now_ns<HB_ANCHOR_UNIX_NS:
        raise ValueError("sample_precedes_hb32_anchor")
    q,phase=divmod(now_ns-HB_ANCHOR_UNIX_NS,HB_PERIOD_NS)
    epoch=HB_ANCHOR_EPOCH+q
    return {"epoch":epoch,"generation":epoch,"heartbeat_id":f"HB:{epoch}","sampled_unix_ns":now_ns,
            "phase_offset_ns":phase,"frequency_hz":HB_HZ,"progression_dependency":"OSCILLATOR_ONLY",
            "authority_effect":"NONE"}

#: A receipt writer's supplied heartbeat epoch. The shared rule, refusal and
#: reference below are byte-identical to StegVerse-Labs/.github@bc608a3
#: (org-kernel/kernel.py). No clock is read on this path.
HB_EPOCH_NOT_SUPPLIED="HB_EPOCH_NOT_SUPPLIED"
HB_EPOCH_INVALID="HB_EPOCH_INVALID"
HB_EPOCH_PREDICATE="SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH"
HB_EPOCH_OWNING_EXISTING_GOAL="INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001"

def supplied_epoch_failure(hb_epoch: Any, reference: Any = None) -> tuple[str, str] | None:
    """The shared supplied-epoch rule (SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH).

    Byte-identical in StegVerse-org/.github#185 and StegVerse-Labs/.github#3212
    and #3213. `hb_epoch` absent (None) is HB_EPOCH_NOT_SUPPLIED. Otherwise it
    must be ASCII [0-9]+ only -- an int is read as its decimal text; a bool, a
    float or anything coerced ('+33', ' 33', '3_3', '33.0') is refused -- with
    integer value >= 32 (the HB32 anchor). `reference`, the carrier frame's
    heartbeat reference when there is one, must be an object, checked in this
    order: a `derived_from_clock` present and not exactly false is
    HB_EPOCH_INVALID; a `sampled_unix_ns` present is HB_EPOCH_INVALID (a clock
    sample is never a supplied epoch); a `derived_from_clock` absent is
    HB_EPOCH_PROVENANCE_UNMARKED. Any other failure is HB_EPOCH_INVALID.
    Returns (failure_code, detail), or None when the epoch is supplied. No
    clock is read.
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
    if reference is not None and "sampled_unix_ns" in reference:
        return "HB_EPOCH_INVALID", "the carrier's heartbeat reference carries sampled_unix_ns; a clock sample is not a supplied epoch"
    if reference is not None and "derived_from_clock" not in reference:
        return "HB_EPOCH_PROVENANCE_UNMARKED", "the carrier's heartbeat reference does not mark derived_from_clock"
    return None

class SuppliedEpochRefused(ValueError):
    """A receipt writer's refusal of an absent or invalid supplied epoch.

    `refusal` is the six-field FAIL_CLOSED from `writer_epoch_refusal`. Raised
    before anything is written; no clock is read to stand in for the epoch.
    """
    def __init__(self, refusal:dict[str,Any])->None:
        super().__init__(refusal["failure_code"]+": "+refusal["detail"])
        self.disposition=refusal["disposition"]
        self.failed_predicate=refusal["failed_predicate"]
        self.refusal=dict(refusal)

def writer_epoch_refusal(hb_epoch:Any, *, retry_entrypoint:str)->dict[str,Any]|None:
    """The six-field FAIL_CLOSED of a receipt writer's epoch, or None when it is supplied.

    The shape StegVerse-org/.github#189 gave the organization ledger
    (`epoch_refusal`): a receipt references the heartbeat epoch its caller
    supplies, checked by `supplied_epoch_failure`; an absent one is
    HB_EPOCH_NOT_SUPPLIED and is never derived from a clock.
    """
    failure=supplied_epoch_failure(hb_epoch)
    if failure is None:
        return None
    code,detail=failure
    return {"disposition":"FAIL_CLOSED","failure_code":code,"failed_predicate":HB_EPOCH_PREDICATE,
            "detail":detail,
            "required_evidence_or_repair":("the caller supplies hb_epoch= (or --hb-epoch): ASCII digits with "
                                           "value >= "+str(HB_ANCHOR_EPOCH)+"; it is never derived from a clock"),
            "retry_entrypoint":retry_entrypoint,
            "owning_existing_goal":HB_EPOCH_OWNING_EXISTING_GOAL,
            "next_attempt":"call again with the supplied epoch; nothing was written",
            "derived_from_clock":False,"consequence_committed":False}

def supplied_hb_reference(hb_epoch:Any, *, retry_entrypoint:str)->dict[str,Any]:
    """The heartbeat reference of a supplied epoch, or SuppliedEpochRefused. No clock is read."""
    refusal=writer_epoch_refusal(hb_epoch,retry_entrypoint=retry_entrypoint)
    if refusal is not None:
        raise SuppliedEpochRefused(refusal)
    return hb_reference(epoch=int(str(hb_epoch)))

class BoundaryFailClosed(ValueError):
    """A six-field FAIL_CLOSED refusal raised before anything is written or published."""
    def __init__(self, failure_code:str, failed_predicate:str, detail:str, *,
                 required_evidence_or_repair:str, retry_entrypoint:str, next_attempt:str)->None:
        super().__init__(failure_code+": "+detail)
        self.disposition="FAIL_CLOSED"
        self.failed_predicate=failed_predicate
        self.refusal={"disposition":"FAIL_CLOSED","failure_code":failure_code,"failed_predicate":failed_predicate,
                      "detail":detail,"required_evidence_or_repair":required_evidence_or_repair,
                      "retry_entrypoint":retry_entrypoint,"owning_existing_goal":HB_EPOCH_OWNING_EXISTING_GOAL,
                      "next_attempt":next_attempt,"derived_from_clock":False,"consequence_committed":False}

def writer_cli_refusal(error:BaseException, *, failure_code:str, retry_entrypoint:str)->dict[str,Any]|None:
    """The six-field result a ledger writer's CLI prints for `error`, or None to re-raise.

    A fault in the writer's own storage (`is_own_state_fault`) is `failure_code`,
    terminal:false: written steps replay idempotently, so the same call
    completes once. A different record already bound to the transition is
    LEDGER_RECEIPT_COLLISION, terminal: the recorded transition stands.
    """
    if is_own_state_fault(error):
        return {"disposition":"FAIL_CLOSED","failure_code":failure_code,
                "failed_predicate":"OWN_STORAGE_ACCEPTS_THE_WRITE",
                "detail":(type(error).__name__+": "+str(error))[:512],
                "required_evidence_or_repair":"this writer's own storage accepts the write",
                "retry_entrypoint":retry_entrypoint,"owning_existing_goal":HB_EPOCH_OWNING_EXISTING_GOAL,
                "next_attempt":"run again with the same epoch and input; written steps replay idempotently",
                "terminal":False,"derived_from_clock":False}
    if isinstance(error,ValueError) and str(error)=="ledger_receipt_collision":
        return {"disposition":"FAIL_CLOSED","failure_code":"LEDGER_RECEIPT_COLLISION",
                "failed_predicate":"ONE_TRANSITION_ID_BINDS_ONE_RECORD",
                "detail":"the transition is already recorded with different content",
                "required_evidence_or_repair":"the recorded transition stands; a different record needs its own transition id",
                "retry_entrypoint":retry_entrypoint,"owning_existing_goal":HB_EPOCH_OWNING_EXISTING_GOAL,
                "next_attempt":"nothing was written for this attempt",
                "terminal":True,"derived_from_clock":False,"consequence_committed":False}
    return None

CARRIED_NOT_ACCEPTED="CARRIED_NOT_ACCEPTED_BY_DESTINATION"

def carried_frame_epoch(frame:dict[str,Any])->tuple[int|None,tuple[str,str]|None]:
    """The epoch a carrier frame carries as supplied, or (None, failure).

    The frame's heartbeat reference must pass the shared rule with itself as
    the reference: a clock-sampled or unmarked reference carries no epoch, and
    its generation and heartbeat_id must match its epoch. A reference that
    passes those content checks and asserts a CARRIED `source` or
    `head_receipt_sha` is CARRIED_NOT_ACCEPTED_BY_DESTINATION: this
    organization declares `accepts_carried_crossings: false`
    (resident-runtime/activation-manifest.json), so a sender forwards a
    SUPPLIED epoch instead. That is not a finding of forgery.
    """
    reference=frame.get("heartbeat_reference") if isinstance(frame,dict) else None
    epoch=reference.get("epoch") if isinstance(reference,dict) else None
    carried=isinstance(reference,dict) and ("source" in reference or "head_receipt_sha" in reference)
    failure=supplied_epoch_failure(epoch,reference if reference is not None else {})
    if failure is not None:
        # A CARRIED claim on a clock-form reference (flagged or sampled) whose
        # epoch is otherwise well formed is still a CARRIED crossing: it is
        # refused as not accepted, never consumed as a clock frame. A
        # malformed epoch keeps its own content code.
        if carried and failure[0]=="HB_EPOCH_INVALID" and supplied_epoch_failure(epoch) is None:
            return None,(CARRIED_NOT_ACCEPTED,
                         "this destination declares accepts_carried_crossings false; the frame carries a CARRIED "
                         "source or head_receipt_sha on a clock-form reference instead of a SUPPLIED epoch")
        return None,failure
    value=int(str(epoch))
    if reference.get("generation")!=value or reference.get("heartbeat_id")!="HB:"+str(value):
        return None,("HB_REFERENCE_INVALID",
                     "the frame's heartbeat generation or heartbeat_id does not match its epoch "+str(value))
    if "source" in reference or "head_receipt_sha" in reference:
        return None,(CARRIED_NOT_ACCEPTED,
                     "this destination declares accepts_carried_crossings false; the frame carries a CARRIED "
                     "source or head_receipt_sha instead of a SUPPLIED epoch")
    return value,None

def derive_channel(payload_hash:str)->dict[str,Any]:
    if not isinstance(payload_hash,str) or not payload_hash.startswith("sha256:") or len(payload_hash)!=71:
        raise ValueError("payload_hash_invalid")
    slot=int(payload_hash[7:23],16)%CHANNEL_COUNT
    return {"channel_id":f"HB:H1:P{slot}","phase_slot":slot,"phase_slot_count":CHANNEL_COUNT,
            "derivation":"PAYLOAD_SHA256_FIRST64_MOD_16","authority_effect":"NONE_CARRIER_ONLY"}

def carrier_frame(packet:dict[str,Any], *, now_ns:int|None=None, epoch:int|None=None)->dict[str,Any]:
    """A carrier frame. A supplied `epoch` stamps its heartbeat reference and no clock is read."""
    raw=canon(packet); payload_hash=sha(packet.get("payload",{})); ref=hb_reference(now_ns,epoch=epoch); channel=derive_channel(payload_hash)
    body={"schema":CARRIER_SCHEMA,"packet_id":packet["packet_id"],"packet_sha256":sha(raw),
          "packet_base64":base64.b64encode(raw).decode("ascii"),"heartbeat_reference":ref,
          "channel":channel,"origin_org":packet["origin"]["org"],"destination_org":packet["destination"]["org"],
          "intr_profile":packet["intr_profile"],"authority_effect":"NONE_CARRIER_ONLY"}
    return {**body,"frame_sha256":sha(body)}

def recover_packet(frame:dict[str,Any])->dict[str,Any]:
    body=dict(frame); claimed=body.pop("frame_sha256",None)
    if claimed!=sha(body): raise ValueError("carrier_frame_hash_mismatch")
    raw=base64.b64decode(frame["packet_base64"].encode("ascii"),validate=True)
    if sha(raw)!=frame["packet_sha256"]: raise ValueError("packet_hash_mismatch")
    packet=json.loads(raw)
    if packet["packet_id"]!=frame["packet_id"]: raise ValueError("packet_id_mismatch")
    if packet["destination"]["org"]!=frame["destination_org"]: raise ValueError("destination_org_mismatch")
    return packet

def receipt(kind:str, packet_id:str, subject:str, previous:str|None, detail:dict[str,Any])->dict[str,Any]:
    body={"kind":kind,"packet_id":packet_id,"subject":subject,"previous_receipt_id":previous,"detail":detail}
    rid=kind.lower()+"-"+hashlib.sha256(canon(body)).hexdigest()[:24]
    return {**body,"receipt_id":rid,"evidence_hash":sha(body)}

def load_registry(root:Path)->dict[str,Any]:
    return json.loads((root/"org-boundary/registry/services.json").read_text())

def node_standing(root:Path):
    """Load the organization's node-standing module from its boundary runtime.

    Standing is a precondition of ingress, not a capability, so it resolves here
    rather than being something a crossing can be addressed to. Resolved from the
    dispatch root because this kernel is organization-neutral, and a root without
    it fails closed: a boundary that cannot validate the predecessor it is
    required to carry must not admit a crossing claiming one.
    """
    path=root/"org-boundary/runtime/node_standing.py"
    if not path.is_file(): raise ValueError("org_boundary_node_standing_missing")
    spec=importlib.util.spec_from_file_location("node_standing",path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

#: The boundary role whose dispatch resolves a bound capability's address.
#:
#: The role vocabulary is this kernel's, as ``BOUNDARY_LOCAL_DIAGNOSTIC`` and
#: ``BOUNDARY_LOCAL_CONTROL`` already are. ``capability_ingress.ROLE`` is that
#: module's assertion of which role it serves. A resolver serving a role the
#: kernel never dispatches would be unreachable.
CAPABILITY_INGRESS_ROLE="BOUNDARY_LOCAL_CAPABILITY_INGRESS"

def capability_ingress(root:Path):
    """Load the organization's capability-ingress module from its boundary runtime.

    A registered capability is bound to a receiving operation in the
    organization's own overlay. This resolves the address to that operation.
    Loaded only when a capability address is dispatched: a root that never
    serves one is not defective for having no resolver until it is addressed.
    """
    path=root/"org-boundary/runtime/capability_ingress.py"
    if not path.is_file(): raise ValueError("org_boundary_capability_ingress_missing")
    spec=importlib.util.spec_from_file_location("capability_ingress",path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def carried_standing(request_packet:dict[str,Any])->dict[str,Any]:
    """Carry a request's standing onto its response, unchanged and marked as carried.

    A response is not a new crossing and has no standing of its own to establish,
    so the only truthful options are to carry the request's standing forward or
    to refuse.
    """
    declared=request_packet.get("standing")
    if not isinstance(declared,dict): raise ValueError("response_requires_request_standing")
    return {**declared,"standing_carried_forward_from_request":True}

def dispatch(root:Path, packet:dict[str,Any], *, mesh_root:Path|None=None,
             hb_epoch:int|None=None)->dict[str,Any]:
    """Dispatch one packet. `hb_epoch` is the epoch its frame carried, checked by the shared rule."""
    registry=load_registry(root)
    if packet["destination"]["org"]!=registry["organization"]: raise ValueError("wrong_destination_org")
    service=next((s for s in registry["services"] if s["service_id"]==packet["destination"]["service"]),None)
    if service is None: raise ValueError("unknown_service")
    # Resolved before the role branch, because the contract covers every ingress
    # class rather than every boundary role: an INTERNAL_ENDPOINT returns early
    # below, so standing checked inside either arm would gate only one of them.
    # Refused as the contract's own disposition rather than a bare error, so a
    # caller is never left guessing which of ALLOW/DENY/FAIL_CLOSED it earned.
    standing_module=node_standing(root)
    try:
        standing=standing_module.require(standing_module.load_contract(root),packet)
    except SystemExit as refused:
        raise ValueError("node_standing_refused:"+str(refused)) from None
    role=service.get("boundary_role")
    adapter=service.get("endpoint_adapter")
    if role=="INTERNAL_ENDPOINT" and adapter:
        processor=root/"org-boundary/runtime/process_boundary.py"
        if not processor.is_file(): raise ValueError("org_boundary_processor_missing")
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); envelope=td/"packet.json"; out=td/"execution.json"
            envelope.write_text(json.dumps(packet,indent=2,sort_keys=True)+"\n")
            completed=subprocess.run(["python3",str(processor),"--envelope",str(envelope),"--out",str(out)],cwd=root,capture_output=True,text=True,check=False)
            if completed.returncode!=0 or not out.is_file():
                raise ValueError("endpoint_adapter_execution_failed:"+completed.stderr[-512:])
            result=json.loads(out.read_text())
            if not isinstance(result,dict): raise ValueError("endpoint_adapter_result_invalid")
            return {**result,**standing}
    if role not in {"BOUNDARY_LOCAL_DIAGNOSTIC","BOUNDARY_LOCAL_CONTROL",CAPABILITY_INGRESS_ROLE}:
        raise BoundaryFailClosed(
            "ENDPOINT_ADAPTER_NOT_INSTALLED","ADDRESSED_SERVICE_HAS_AN_INSTALLED_ENDPOINT_ADAPTER",
            str(service["service_id"])+" ("+str(role)+") has no installed endpoint adapter",
            required_evidence_or_repair="install the service's endpoint_adapter in org-boundary/registry/services.json",
            retry_entrypoint="org-kernel/kernel.py::ingest_frame",
            next_attempt="resend the frame once the adapter is installed; nothing was dispatched or written")
    prev=None; receipts=[]
    for kind in ("INGRESS_ACCEPTED","DISPATCHED","CONSUMED","RESULT_BOUND","EGRESS_EMITTED"):
        r=receipt(kind,packet["packet_id"],service["service_id"],prev,{"payload_hash":sha(packet["payload"])})
        receipts.append(r); prev=r["receipt_id"]
    if role==CAPABILITY_INGRESS_ROLE:
        # The address resolves to the receiving operation the overlay binds.
        # That operation records both ledger levels itself. A refusal here is
        # this boundary's refusal. The in-memory receipt chain above is what a
        # later closure recomputes; this dispatch does not write a second
        # ledger receipt for the same frame.
        try:
            application_result=capability_ingress(root).receive(
                root,service,packet,registry=registry,mesh_root=mesh_root,hb_epoch=hb_epoch)
        except SystemExit as refused:
            raise ValueError("capability_ingress_refused:"+str(refused)) from None
    elif role=="BOUNDARY_LOCAL_CONTROL":
        application_result=handle_control_message(root,packet,registry,hb_epoch=hb_epoch)
    else:
        application_result={"echo":packet["payload"]}
    result={"schema_version":SCHEMA,"organization":registry["organization"],"packet_id":packet["packet_id"],
            "service_id":service["service_id"],"consumed":True,"application_result":application_result,
            **standing,
            "authority_effect":packet["transition"]["authority_effect"],"receipts":receipts,
            "reconstruction":{"same_execution_required":True,"status":"RECONSTRUCTED","terminal_receipt_id":prev}}
    if role==CAPABILITY_INGRESS_ROLE:
        result["processing_selection"]="BOUNDARY_LOCAL_NO_PROCESSOR_SELECTED"
    return result

def persist_outbox(root:Path, frame:dict[str,Any])->Path:
    out=root/"resident-runtime/federation/outbox"; out.mkdir(parents=True,exist_ok=True)
    path=out/(hashlib.sha256(frame["packet_id"].encode()).hexdigest()+".json")
    if path.exists():
        if json.loads(path.read_text())!=frame: raise ValueError("write_once_collision")
        return path
    path.write_text(json.dumps(frame,indent=2,sort_keys=True)+"\n")
    return path

INGEST_REFUSED_FRAME_CODES=frozenset({"HB_EPOCH_PROVENANCE_UNMARKED",CARRIED_NOT_ACCEPTED,
                                      "HB_REFERENCE_INVALID"})
FRAME_INTEGRITY_ERRORS=frozenset({"carrier_frame_hash_mismatch","packet_hash_mismatch",
                                  "packet_id_mismatch","destination_org_mismatch"})

def frame_ingest_refusal(frame:Any, error:BaseException)->dict[str,Any]:
    """The six-field refusal of a frame whose ingest raised. Nothing was dispatched or written."""
    if isinstance(error,ValueError) and str(error) in FRAME_INTEGRITY_ERRORS:
        code,predicate="FRAME_INTEGRITY_INVALID","FRAME_AND_PACKET_HASHES_RECOMPUTE"
        repair="the sender republishes an intact frame whose frame_sha256 and packet_sha256 recompute"
    else:
        code,predicate="FRAME_INGEST_FAILED",type(error).__name__
        repair="a frame this boundary can ingest without error"
    return {"status":"FAIL_CLOSED","packet_id":frame.get("packet_id") if isinstance(frame,dict) else None,
            "disposition":"FAIL_CLOSED","failure_code":code,"failed_predicate":predicate,
            "detail":(type(error).__name__+": "+str(error))[:512],
            "required_evidence_or_repair":repair,
            "retry_entrypoint":"org-kernel/kernel.py::ingest_frame","owning_existing_goal":HB_EPOCH_OWNING_EXISTING_GOAL,
            "next_attempt":"the frame is refused and not retried; nothing was dispatched or written",
            "derived_from_clock":False,"consequence_committed":False}

FRAME_DISPATCH_IO_FAILED="FRAME_DISPATCH_IO_FAILED"

def is_own_state_fault(error:BaseException)->bool:
    """An OSError, or a ledger store's LedgerWriteFault (marked `own_state_write_fault`):
    a fault in this boundary's own state, never the frame's defect."""
    return isinstance(error,OSError) or getattr(error,"own_state_write_fault",False) is True

def dispatch_io_refusal(frame:Any, error:BaseException)->dict[str,Any]:
    """The six-field refusal of a frame this boundary could not finish for an
    I/O failure of its own (its ledger, its state). The frame is not at fault:
    no marker is written, so it stays pending and the next cycle consumes it."""
    return {"status":"PENDING_IO","packet_id":frame.get("packet_id") if isinstance(frame,dict) else None,
            "disposition":"FAIL_CLOSED","failure_code":FRAME_DISPATCH_IO_FAILED,
            "failed_predicate":type(error).__name__,"detail":(type(error).__name__+": "+str(error))[:512],
            "required_evidence_or_repair":"this boundary's own storage accepts the write",
            "retry_entrypoint":"org-kernel/kernel.py::consume_and_respond (next cycle)",
            "owning_existing_goal":HB_EPOCH_OWNING_EXISTING_GOAL,
            "next_attempt":"the frame stays pending; the next cycle consumes it exactly once (ledger appends replay idempotently)",
            "terminal":False,"derived_from_clock":False,"consequence_committed":False}

def ingest_frame(root:Path, frame:dict[str,Any], *, mesh_root:Path|None=None)->dict[str,Any]:
    """Ingest one frame. The guard is total: any error is a six-field refusal,
    so one frame never aborts a consume cycle or starves the frames after it.
    An OSError is this boundary's own I/O and leaves the frame pending
    (FRAME_DISPATCH_IO_FAILED); any other error is the frame's own defect
    (FRAME_INTEGRITY_INVALID or FRAME_INGEST_FAILED) and is terminal."""
    try:
        return _ingest_frame(root,frame,mesh_root=mesh_root)
    except Exception as error:
        # A fault in this boundary's own state is caught before the content
        # guard: the frame stays pending. Anything else is the frame's defect.
        if is_own_state_fault(error):
            return dispatch_io_refusal(frame,error)
        return frame_ingest_refusal(frame,error)

def _ingest_frame(root:Path, frame:dict[str,Any], *, mesh_root:Path|None=None)->dict[str,Any]:
    packet=recover_packet(frame)
    registry=load_registry(root)
    if frame["destination_org"]!=registry["organization"]:
        return {"status":"IGNORED_NOT_ADDRESSED","packet_id":frame["packet_id"]}
    # NARROW S1: an UNMARKED reference, or a CARRIED claim this ingest cannot
    # verify, is refused before anything is dispatched or written. Any other
    # failure (a clock-flagged or clock-sampled reference) is consumed but
    # lends no epoch, so a route that needs one refuses HB_EPOCH_NOT_SUPPLIED.
    epoch,failure=carried_frame_epoch(frame)
    # Every carrier epoch passes the shared digit and anchor check, whatever
    # the frame's clock flag: a malformed or absent epoch is refused too.
    reference=frame.get("heartbeat_reference")
    epoch_failure=supplied_epoch_failure(reference.get("epoch") if isinstance(reference,dict) else None)
    if epoch_failure is not None:
        failure=epoch_failure
    if failure is not None and failure[0]==CARRIED_NOT_ACCEPTED and epoch_failure is None:
        # Not a finding of forgery: this destination does not accept CARRIED
        # crossings, so the sender's hop re-sends with the SUPPLIED epoch.
        return {"status":"FAIL_CLOSED","packet_id":packet["packet_id"],
                "disposition":"FAIL_CLOSED","failure_code":CARRIED_NOT_ACCEPTED,
                "failed_predicate":"DESTINATION_ACCEPTS_CARRIED_CROSSINGS","detail":failure[1],
                "required_evidence_or_repair":"re-send with the SUPPLIED epoch",
                "retry_entrypoint":"the sender's hop: "+str(packet.get("origin",{}).get("org"))+" egress, re-sent with a SUPPLIED epoch",
                "owning_existing_goal":HB_EPOCH_OWNING_EXISTING_GOAL,
                "next_attempt":"the sender re-sends the crossing with a SUPPLIED epoch; nothing was dispatched or written",
                "derived_from_clock":False,"consequence_committed":False}
    if failure is not None and (failure[0] in INGEST_REFUSED_FRAME_CODES or epoch_failure is not None):
        code,detail=failure
        return {"status":"FAIL_CLOSED","packet_id":packet["packet_id"],
                "disposition":"FAIL_CLOSED","failure_code":code,"failed_predicate":HB_EPOCH_PREDICATE,
                "detail":"the frame carries no supplied epoch: "+detail,
                "required_evidence_or_repair":("the frame's heartbeat_reference carries a supplied epoch: "
                                               "derived_from_clock false, no sampled_unix_ns"),
                "retry_entrypoint":"org-kernel/kernel.py::ingest_frame","owning_existing_goal":HB_EPOCH_OWNING_EXISTING_GOAL,
                "next_attempt":"the sender republishes the frame with a supplied epoch; nothing was dispatched or written",
                "derived_from_clock":False,"consequence_committed":False}
    try:
        result=dispatch(root,packet,mesh_root=mesh_root,hb_epoch=epoch)
    except BoundaryFailClosed as refused:
        return {"status":"FAIL_CLOSED","packet_id":packet["packet_id"],**refused.refusal}
    return {"status":"CONSUMED","packet":packet,"execution_result":result}

__all__=["hb_reference","derive_channel","carrier_frame","recover_packet","dispatch","persist_outbox","ingest_frame",
        "capability_ingress","CAPABILITY_INGRESS_ROLE","RESPONDED_REQUEST_CLASSES",
        "HB_EPOCH_NOT_SUPPLIED","HB_EPOCH_INVALID","supplied_epoch_failure",
        "SuppliedEpochRefused","writer_epoch_refusal","supplied_hb_reference",
        "BoundaryFailClosed","carried_frame_epoch"]


# --- Federation mesh v1.1 additions ---
FEDERATION_ROOT_ENV="STEGVERSE_ORG_FEDERATION_ROOT"

def federation_root(env:dict[str,str]|None=None)->Path:
    values=os.environ if env is None else env
    override=values.get(FEDERATION_ROOT_ENV)
    if override:
        return Path(override).expanduser().resolve()
    base=Path(values.get("XDG_STATE_HOME",str(Path.home()/".local"/"state")))
    return (base/"stegverse"/"org-federation").resolve()

def publish_frame(frame:dict[str,Any], *, root:Path|None=None)->Path:
    mesh=(root or federation_root()).resolve()
    frames=mesh/"frames.d"
    frames.mkdir(parents=True,exist_ok=True)
    frame_id=hashlib.sha256((frame["packet_id"]+"|"+frame["frame_sha256"]).encode()).hexdigest()
    path=frames/(frame_id+".json")
    if path.exists():
        existing=json.loads(path.read_text())
        if existing!=frame:
            raise ValueError("federation_frame_write_once_collision")
        return path
    path.write_text(json.dumps(frame,indent=2,sort_keys=True)+"\n")
    return path

#: The largest frames.d file a scan reads. A larger one is refused by name unread.
FRAME_FILE_MAX_BYTES=4*1024*1024

def scan_addressed_frames(organization:str, *, root:Path|None=None, seen:set[str]|None=None)->list[dict[str,Any]]:
    mesh=(root or federation_root()).resolve()
    frames=mesh/"frames.d"
    if not frames.exists():
        return []
    consumed=seen or set()
    out=[]
    for path in sorted(frames.glob("*.json")):
        if path.name in consumed:
            continue
        # A file that cannot be read, is not UTF-8, exceeds the cap or is not
        # a JSON object cannot be addressed or ingested. It is offered with its
        # error, so a consumer refuses it by name instead of the whole scan
        # raising every cycle.
        try:
            if path.stat().st_size>FRAME_FILE_MAX_BYTES:
                raise ValueError("frame_file_exceeds_"+str(FRAME_FILE_MAX_BYTES)+"_bytes")
            frame=json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(frame,dict):
                raise ValueError("frame_not_a_json_object")
            if not isinstance(frame.get("destination_org"),str):
                raise TypeError("frame_destination_org_not_a_string")
        except (ValueError,TypeError,UnicodeDecodeError,OSError) as error:
            out.append({"path":str(path),"frame":None,"error":error})
            continue
        if frame.get("destination_org")==organization:
            out.append({"path":str(path),"frame":frame})
    return out

def ingest_scanned(repo_root:Path, item:dict[str,Any], *, mesh_root:Path|None=None)->dict[str,Any]:
    """Ingest one scanned item; an unreadable file is a six-field FRAME_INGEST_FAILED."""
    if item.get("error") is not None:
        return frame_ingest_refusal(item.get("frame"),item["error"])
    return ingest_frame(repo_root,item["frame"],mesh_root=mesh_root)

def build_packet(*, origin_org:str, origin_service:str, destination_org:str, destination_service:str,
                 payload:dict[str,Any], standing:dict[str,Any], transition_reference:str="federation.v1",
                 authority_effect:str="NONE", packet_id:str|None=None)->dict[str,Any]:
    """Build an ingress packet. `standing` is required and has no default.

    Every ingress class the contract covers requires canonical node standing, so
    a standing-less packet is not a packet this boundary can construct. A default
    here would be a caller-editable claim, and the contract holds that a
    caller-editable classification does not establish identity.
    """
    pid=packet_id or "pkt-"+hashlib.sha256(canon({
        "origin_org":origin_org,"origin_service":origin_service,"destination_org":destination_org,
        "destination_service":destination_service,"payload":payload,"transition_reference":transition_reference
    })).hexdigest()[:24]
    return {
      "schema_version":PACKET_SCHEMA,
      "packet_id":pid,
      "direction":"INGRESS",
      "origin":{"org":origin_org,"service":origin_service},
      "destination":{"org":destination_org,"service":destination_service},
      "carrier":{"kind":"HB_DERIVED","reference":"org-federation"},
      "intr_profile":"stegverse.intr.org-boundary.v1",
      "transition":{"reference":transition_reference,"authority_effect":authority_effect,"conditions":[]},
      "payload":payload,
      "standing":standing,
      "evidence":{"ingress_receipt":None,"dispatch_receipt":None,"consumption_receipt":None,"egress_receipt":None,"reconstruction_reference":None}
    }

def publish_packet(packet:dict[str,Any], *, root:Path|None=None, now_ns:int|None=None,
                   epoch:int|None=None)->dict[str,Any]:
    frame=carrier_frame(packet,now_ns=now_ns,epoch=epoch)
    path=publish_frame(frame,root=root)
    return {"packet":packet,"frame":frame,"path":str(path)}

def consume_addressed_frames(repo_root:Path, *, mesh_root:Path|None=None, seen:set[str]|None=None)->list[dict[str,Any]]:
    registry=load_registry(repo_root)
    organization=registry["organization"]
    results=[]
    for item in scan_addressed_frames(organization,root=mesh_root,seen=seen):
        result=ingest_scanned(repo_root,item,mesh_root=mesh_root)
        results.append({"path":item["path"],"result":result})
    return results


# --- Ecosystem-wide communication v1.2 additions ---
def organization_slug(organization:str)->str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in organization).strip("-")

def build_ecosystem_packets(*, origin_org:str, origin_service:str, organizations:list[str], standing:dict[str,Any],
                            message_class:str, subject:str, body:dict[str,Any],
                            requested_action:str|None=None, transition_reference:str="ecosystem.communication.v1",
                            authority_effect:str="NONE", communication_id:str|None=None)->dict[str,Any]:
    ordered=sorted(dict.fromkeys(organizations))
    if not ordered:
        raise ValueError("organizations_required")
    comm_id=communication_id or "ecosystem-"+hashlib.sha256(canon({
        "origin_org":origin_org,"origin_service":origin_service,"organizations":ordered,
        "message_class":message_class,"subject":subject,"body":body,
        "requested_action":requested_action,"transition_reference":transition_reference
    })).hexdigest()[:24]
    packets=[]
    for org in ordered:
        service=organization_slug(org)+".org-control"
        payload={
          "communication_id":comm_id,
          "message_class":message_class,
          "subject":subject,
          "body":body,
          "requested_action":requested_action,
          "audience":"ECOSYSTEM",
          "target_organization":org,
          "target_count":len(ordered)
        }
        packet=build_packet(
          origin_org=origin_org,
          origin_service=origin_service,
          destination_org=org,
          destination_service=service,
          payload=payload,
          standing=standing,
          transition_reference=transition_reference,
          authority_effect=authority_effect,
          packet_id=comm_id+":"+organization_slug(org)
        )
        packets.append(packet)
    return {"communication_id":comm_id,"organization_count":len(ordered),"packets":packets}

def publish_ecosystem_message(*, origin_org:str, origin_service:str, organizations:list[str],
                              standing:dict[str,Any], message_class:str, subject:str, body:dict[str,Any],
                              requested_action:str|None=None, transition_reference:str="ecosystem.communication.v1",
                              authority_effect:str="NONE", communication_id:str|None=None,
                              root:Path|None=None, now_ns:int|None=None, epoch:int|None=None)->dict[str,Any]:
    built=build_ecosystem_packets(
      origin_org=origin_org,origin_service=origin_service,organizations=organizations,standing=standing,
      message_class=message_class,subject=subject,body=body,requested_action=requested_action,
      transition_reference=transition_reference,authority_effect=authority_effect,
      communication_id=communication_id
    )
    publications=[publish_packet(packet,root=root,now_ns=now_ns,epoch=epoch) for packet in built["packets"]]
    return {"communication_id":built["communication_id"],"organization_count":built["organization_count"],
            "published_count":len(publications),"publications":publications}

def aggregate_ecosystem_results(communication_id:str, results_by_org:dict[str,list[dict[str,Any]]])->dict[str,Any]:
    rows=[]
    for org,items in sorted(results_by_org.items()):
        matched=[]
        for item in items:
            result=item.get("result") or {}
            packet=result.get("packet") or {}
            payload=packet.get("payload") or {}
            if payload.get("communication_id")==communication_id:
                matched.append(item)
        status="CONSUMED" if any((x.get("result") or {}).get("status")=="CONSUMED" for x in matched) else "NOT_OBSERVED"
        terminal=None
        for x in matched:
            er=(x.get("result") or {}).get("execution_result") or {}
            terminal=(er.get("reconstruction") or {}).get("terminal_receipt_id") or terminal
        rows.append({"organization":org,"status":status,"terminal_receipt_id":terminal})
    consumed=sum(1 for row in rows if row["status"]=="CONSUMED")
    return {"communication_id":communication_id,"organization_count":len(rows),
            "consumed_count":consumed,"pending_count":len(rows)-consumed,
            "complete":consumed==len(rows) and len(rows)>0,"organizations":rows}


# --- Ecosystem control/response v1.3 additions ---
def load_federation_directory(root:Path)->dict[str,Any]:
    path=root/"org-boundary/registry/federation.json"
    value=json.loads(path.read_text())
    if value.get("denominator")!=len(value.get("organizations") or []):
        raise ValueError("federation_directory_denominator_mismatch")
    return value

def resident_status(root:Path, registry:dict[str,Any]|None=None, *, hb_epoch:Any=None)->dict[str,Any]:
    """This organization's status. No clock is read: the heartbeat reference is
    the supplied epoch's, or null when none is supplied."""
    reg=registry or load_registry(root)
    activation_path=root/"resident-runtime/activation-manifest.json"
    activation=json.loads(activation_path.read_text()) if activation_path.exists() else {}
    kernel=(activation.get("kernel") or {})
    return {
      "organization":reg["organization"],
      "kernel_version":kernel.get("version"),
      "activation_state":activation.get("state"),
      "registered_service_count":len(reg.get("services") or []),
      "registered_services":[s.get("service_id") for s in reg.get("services") or []],
      "org_control_service":organization_slug(reg["organization"])+".org-control",
      "heartbeat_reference":(hb_reference(epoch=int(str(hb_epoch)))
                             if supplied_epoch_failure(hb_epoch) is None else None),
      "runtime_observation_claimed":False
    }

WORK_INTAKE_RETRY_ENTRYPOINT="org-kernel/kernel.py::persist_work_request (the request frame's supplied heartbeat epoch)"

def persist_work_request(root:Path, packet:dict[str,Any], *, hb_epoch:Any=None)->dict[str,Any]:
    """Queue a work request. Without a supplied epoch it is refused and nothing is written."""
    refusal=writer_epoch_refusal(hb_epoch,retry_entrypoint=WORK_INTAKE_RETRY_ENTRYPOINT)
    if refusal is not None:
        return {**refusal,"state":"FAIL_CLOSED","intake_ref":None,"execution_authority_inferred":False}
    payload=packet.get("payload") or {}
    communication_id=payload.get("communication_id")
    inbox=root/"resident-runtime/control/inbox"
    inbox.mkdir(parents=True,exist_ok=True)
    name=hashlib.sha256((packet["packet_id"]+"|"+str(communication_id)).encode()).hexdigest()+".json"
    path=inbox/name
    record={
      "schema_version":"stegverse.ecosystem-work-intake.v1",
      "communication_id":communication_id,
      "packet_id":packet["packet_id"],
      "origin":packet["origin"],
      "destination":packet["destination"],
      "requested_action":payload.get("requested_action"),
      "body":payload.get("body"),
      "transition":packet["transition"],
      "state":"QUEUED_FOR_LOCAL_ADMISSION_EVALUATION",
      "execution_authority_inferred":False,
      "execution_authority_constraint":"CONSTRAINT_VARIABLE",
      "time_constraint":"CONSTRAINT_VARIABLE",
      "hb_reference":hb_reference(epoch=int(str(hb_epoch)))
    }
    if path.exists():
        if json.loads(path.read_text())!=record:
            raise ValueError("work_intake_write_once_collision")
    else:
        path.write_text(json.dumps(record,indent=2,sort_keys=True)+"\n")
    return {"state":record["state"],"intake_ref":str(path),"execution_authority_inferred":False}

def handle_control_message(root:Path, packet:dict[str,Any], registry:dict[str,Any], *,
                           hb_epoch:Any=None)->dict[str,Any]:
    payload=packet.get("payload") or {}
    message_class=payload.get("message_class")
    result={
      "message_received":True,
      "message_class":message_class,
      "communication_id":payload.get("communication_id"),
      "requested_action":payload.get("requested_action"),
      "execution_authority_inferred":False,
      "execution_authority_effect":packet["transition"]["authority_effect"]
    }
    if message_class=="ecosystem.monitor.request":
        result["monitor_status"]=resident_status(root,registry,hb_epoch=hb_epoch)
    elif message_class=="ecosystem.work.request":
        result["work_intake"]=persist_work_request(root,packet,hb_epoch=hb_epoch)
    elif message_class=="ecosystem.communication":
        result["communication_acknowledged"]=True
    elif message_class in {"ecosystem.monitor.response","ecosystem.work.ack","ecosystem.communication.ack"}:
        result["response_acknowledged"]=True
    return result

RESPONDED_REQUEST_CLASSES=frozenset({
    "ecosystem.monitor.request","ecosystem.work.request","ecosystem.communication"})

def response_message_class(request_class:str|None)->str:
    return {
      "ecosystem.monitor.request":"ecosystem.monitor.response",
      "ecosystem.work.request":"ecosystem.work.ack",
      "ecosystem.communication":"ecosystem.communication.ack"
    }.get(request_class or "","ecosystem.communication.ack")

def build_control_response(request_packet:dict[str,Any], execution_result:dict[str,Any])->dict[str,Any]:
    req_payload=request_packet.get("payload") or {}
    origin_org=request_packet["origin"]["org"]
    local_org=request_packet["destination"]["org"]
    cls=response_message_class(req_payload.get("message_class"))
    payload={
      "communication_id":req_payload.get("communication_id"),
      "message_class":cls,
      "subject":"response:"+str(req_payload.get("subject") or ""),
      "body":{
        "request_packet_id":request_packet["packet_id"],
        "responding_organization":local_org,
        "application_result":execution_result.get("application_result"),
        "receipt_terminal":(execution_result.get("reconstruction") or {}).get("terminal_receipt_id")
      },
      "requested_action":None,
      "audience":"ORIGIN",
      "target_organization":origin_org,
      "target_count":1
    }
    return build_packet(
      origin_org=local_org,
      origin_service=organization_slug(local_org)+".org-control",
      destination_org=origin_org,
      destination_service=organization_slug(origin_org)+".org-control",
      payload=payload,
      standing=carried_standing(request_packet),
      transition_reference=str((request_packet.get("transition") or {}).get("reference") or "ecosystem.communication.v1")+".response",
      authority_effect="NONE",
      packet_id=str(req_payload.get("communication_id"))+":response:"+organization_slug(local_org)
    )

COMMUNICATION_ID_COLLISION="COMMUNICATION_ID_COLLISION"

def response_packet_id(request_packet:dict[str,Any])->str:
    """The id of the response build_control_response makes for this request."""
    payload=request_packet.get("payload") or {}
    return str(payload.get("communication_id"))+":response:"+organization_slug(request_packet["destination"]["org"])

def answered_request(frame:dict[str,Any])->str|None:
    """The request packet id a published response frame answers, or None."""
    try:
        body=(recover_packet(frame).get("payload") or {}).get("body") or {}
    except Exception:
        return None
    return body.get("request_packet_id")

def published_frame_for(packet_id:str, *, root:Path|None=None, answering:str|None=None,
                        origin_org:str|None=None)->dict[str,Any]|None:
    """The frame already published on the mesh for this packet id, if any.

    With `answering`, only a response that answers that request id matches;
    a response under the same id that answers another request is returned
    with `answers_another_request` set. With `origin_org`, only a frame whose
    recovered packet originates there counts: a frame from another origin
    squatting the id is skipped.
    """
    frames=(root or federation_root()).resolve()/"frames.d"
    if not frames.is_dir():
        return None
    for path in sorted(frames.glob("*.json")):
        try:
            frame=json.loads(path.read_text(encoding="utf-8"))
        except (ValueError,OSError):
            continue
        if isinstance(frame,dict) and frame.get("packet_id")==packet_id:
            if origin_org is not None and _recovered_origin(frame)!=origin_org:
                continue
            found={"frame":frame,"path":str(path)}
            if answering is not None:
                found["answers_another_request"]=answered_request(frame)!=answering
            return found
    return None

def _recovered_origin(frame:dict[str,Any])->str|None:
    try:
        return recover_packet(frame)["origin"]["org"]
    except Exception:
        return None

def communication_collision_refusal(request_packet:dict[str,Any], answered:str|None)->dict[str,Any]:
    """The six-field refusal of a second, different request under a communication id already answered."""
    return {"status":"FAIL_CLOSED","packet_id":request_packet.get("packet_id"),
            "disposition":"FAIL_CLOSED","failure_code":COMMUNICATION_ID_COLLISION,
            "failed_predicate":"ONE_COMMUNICATION_ID_BINDS_ONE_REQUEST",
            "detail":("communication_id "+str((request_packet.get("payload") or {}).get("communication_id"))+
                      " is already answered for request "+str(answered)),
            "required_evidence_or_repair":"the sender uses a new communication_id for a different request",
            "retry_entrypoint":"the sender's hop: "+str((request_packet.get("origin") or {}).get("org"))+" egress",
            "owning_existing_goal":HB_EPOCH_OWNING_EXISTING_GOAL,
            "next_attempt":"the request is refused; nothing was dispatched, published or written",
            "derived_from_clock":False,"consequence_committed":False}

def request_collision(frame:Any, *, root:Path|None=None)->dict[str,Any]|None:
    """The collision refusal for a request whose response id already answers another request, or None."""
    try:
        packet=recover_packet(frame)
    except Exception:
        return None
    if (packet.get("payload") or {}).get("message_class") not in RESPONDED_REQUEST_CLASSES:
        return None
    existing=published_frame_for(response_packet_id(packet),root=root,answering=packet["packet_id"],
                                 origin_org=packet["destination"]["org"])
    if existing is None or not existing["answers_another_request"]:
        return None
    return communication_collision_refusal(packet,answered_request(existing["frame"]))

def publish_response_once(response:dict[str,Any], *, root:Path|None=None, epoch:int|None=None)->dict[str,Any]:
    """Publish a response once per request. A frame retried after a fault that
    followed publication reuses the response already published for that same
    request; a response under the same id for another request is a collision
    (refused before dispatch by `request_collision`) and is never reused."""
    request_id=(response.get("payload") or {}).get("body",{}).get("request_packet_id")
    existing=published_frame_for(response["packet_id"],root=root,answering=request_id,
                                 origin_org=response["origin"]["org"])
    if existing is not None:
        if existing["answers_another_request"]:
            raise ValueError("communication_id_collision")
        return {"packet":response,**existing,"already_published":True}
    return publish_packet(response,root=root,epoch=epoch)

RESPONSE_RETRY_ENTRYPOINT="org-kernel/kernel.py::consume_and_respond (a request frame carrying a supplied heartbeat epoch)"

def response_epoch_refusal(failure:tuple[str,str])->dict[str,Any]:
    """The six-field refusal to answer a request frame that lends no epoch. No response is published."""
    code,detail=failure
    return {"disposition":"FAIL_CLOSED","failure_code":code,"failed_predicate":HB_EPOCH_PREDICATE,
            "detail":"the request frame carries no supplied epoch: "+detail,
            "required_evidence_or_repair":"the request frame's heartbeat_reference carries a supplied epoch (derived_from_clock false)",
            "retry_entrypoint":RESPONSE_RETRY_ENTRYPOINT,"owning_existing_goal":HB_EPOCH_OWNING_EXISTING_GOAL,
            "next_attempt":"the requester resends with a supplied epoch; no response frame was published",
            "derived_from_clock":False,"consequence_committed":False}

def consume_and_respond(repo_root:Path, *, mesh_root:Path|None=None,
                        seen:set[str]|None=None)->list[dict[str,Any]]:
    """Consume addressed frames and answer the requests among them.

    A response frame carries the epoch its request frame carried as supplied.
    A request whose frame carries none gets no response: its refusal is
    returned in `response_refusal`, nothing is published, and no clock is read.
    """
    registry=load_registry(repo_root)
    organization=registry["organization"]
    durable_seen=federation_seen_frame_names(repo_root)
    effective_seen=set(seen or set())|durable_seen
    out=[]
    for item in scan_addressed_frames(organization,root=mesh_root,seen=effective_seen):
        # A second, different request under a communication id already
        # answered is refused before it is dispatched.
        collision=request_collision(item.get("frame"),root=mesh_root) if item.get("error") is None else None
        result=collision if collision is not None else ingest_scanned(repo_root,item)
        response_publication=None; response_refusal=None; marker=None
        # The guard is total for this frame's remaining steps too: an OSError
        # is this boundary's own I/O and leaves the frame pending (no marker);
        # any other error is terminal for the frame. The loop always continues.
        try:
            packet=result.get("packet") or {}
            message_class=(packet.get("payload") or {}).get("message_class")
            if result.get("status")=="CONSUMED" and message_class in {
                "ecosystem.monitor.request","ecosystem.work.request","ecosystem.communication"}:
                epoch,failure=carried_frame_epoch(item["frame"])
                if epoch is None:
                    response_refusal=response_epoch_refusal(failure)
                else:
                    response=build_control_response(packet,result["execution_result"])
                    response_publication=publish_response_once(response,root=mesh_root,epoch=epoch)
            # A refused frame writes no receipt. It is quarantined: a terminal
            # seen marker, so it is not re-refused every cycle ahead of valid
            # frames. A frame pending on this boundary's own I/O gets no marker.
            if result.get("status")=="CONSUMED":
                marker=mark_federation_frame_seen(repo_root,item["path"],item["frame"],result)
            elif result.get("failure_code")!=FRAME_DISPATCH_IO_FAILED:
                marker=mark_federation_frame_quarantined(repo_root,item["path"],item["frame"],result)
        except Exception as error:
            if is_own_state_fault(error):
                result=dispatch_io_refusal(item.get("frame"),error)
                out.append({"path":item["path"],"result":result,"response_publication":response_publication,
                            "response_refusal":response_refusal,"seen_marker":None})
                continue
            result=frame_ingest_refusal(item.get("frame"),error)
            try:
                marker=mark_federation_frame_quarantined(repo_root,item["path"],item.get("frame"),result)
            except OSError:
                marker=None
        out.append({"path":item["path"],"result":result,"response_publication":response_publication,
                    "response_refusal":response_refusal,"seen_marker":str(marker) if marker else None})
    return out

def collect_ecosystem_responses(origin_org:str, communication_id:str, *, mesh_root:Path|None=None)->dict[str,Any]:
    responses=[]; refused=[]
    for item in scan_addressed_frames(origin_org,root=mesh_root):
        # A frame that does not recover is refused with six fields and skipped;
        # it never aborts the collection of the frames after it.
        try:
            if item.get("error") is not None:
                raise item["error"]
            packet=recover_packet(item["frame"])
        except Exception as error:
            refused.append({"path":item["path"],**frame_ingest_refusal(item["frame"],error)})
            continue
        payload=packet.get("payload") or {}
        if payload.get("communication_id")!=communication_id:
            continue
        if payload.get("message_class") not in {
            "ecosystem.monitor.response","ecosystem.work.ack","ecosystem.communication.ack"}:
            continue
        body=payload.get("body") or {}
        responses.append({
          "organization":body.get("responding_organization") or packet["origin"]["org"],
          "message_class":payload.get("message_class"),
          "request_packet_id":body.get("request_packet_id"),
          "application_result":body.get("application_result"),
          "receipt_terminal":body.get("receipt_terminal"),
          "response_packet_id":packet["packet_id"],
          "frame_sha256":item["frame"].get("frame_sha256")
        })
    dedup={}
    for row in responses:
        dedup[row["organization"]]=row
    rows=[dedup[k] for k in sorted(dedup)]
    return {
      "communication_id":communication_id,
      "response_count":len(rows),
      "organizations":rows,
      "refused_frames":refused
    }

def publish_ecosystem_from_directory(repo_root:Path, *, standing:dict[str,Any], message_class:str, subject:str, body:dict[str,Any],
                                     requested_action:str|None=None, authority_effect:str="NONE",
                                     communication_id:str|None=None, mesh_root:Path|None=None,
                                     now_ns:int|None=None, epoch:int|None=None)->dict[str,Any]:
    registry=load_registry(repo_root)
    directory=load_federation_directory(repo_root)
    organizations=[row["organization"] for row in directory["organizations"]]
    origin=registry["organization"]
    return publish_ecosystem_message(
      origin_org=origin,
      origin_service=organization_slug(origin)+".org-control",
      organizations=organizations,
      standing=standing,
      message_class=message_class,
      subject=subject,
      body=body,
      requested_action=requested_action,
      authority_effect=authority_effect,
      communication_id=communication_id,
      root=mesh_root,
      now_ns=now_ns,
      epoch=epoch
    )


# --- Federation replay/dedup v1.3.1 additions ---
def federation_seen_frame_names(repo_root:Path)->set[str]:
    seen_dir=repo_root/"resident-runtime/federation/seen.d"
    if not seen_dir.exists():
        return set()
    names=set()
    for path in seen_dir.glob("*.json"):
        try:
            value=json.loads(path.read_text())
            if isinstance(value.get("frame_name"),str):
                names.add(value["frame_name"])
        except Exception:
            continue
    return names

def mark_federation_frame_seen(repo_root:Path, frame_path:str, frame:dict[str,Any], result:dict[str,Any])->Path:
    seen_dir=repo_root/"resident-runtime/federation/seen.d"
    seen_dir.mkdir(parents=True,exist_ok=True)
    frame_name=Path(frame_path).name
    marker={
      "schema_version":"stegverse.federation-frame-consumption.v1",
      "frame_name":frame_name,
      "frame_sha256":frame.get("frame_sha256"),
      "packet_id":frame.get("packet_id"),
      "destination_org":frame.get("destination_org"),
      "status":result.get("status"),
      "authority_effect":"NONE_CARRIER_ONLY"
    }
    marker_path=seen_dir/(hashlib.sha256(frame_name.encode()).hexdigest()+".json")
    if marker_path.exists():
        if json.loads(marker_path.read_text())!=marker:
            raise ValueError("federation_seen_marker_collision")
    else:
        marker_path.write_text(json.dumps(marker,indent=2,sort_keys=True)+"\n")
    return marker_path


def mark_federation_frame_quarantined(repo_root:Path, frame_path:str, frame:dict[str,Any], result:dict[str,Any])->Path:
    """Record a refused frame as seen, terminally. Not a receipt; no clock is read.

    The marker is six-field FRAME_REFUSED_QUARANTINED and keeps the
    refusal's own code, so a later cycle skips the frame instead of refusing
    it again.
    """
    seen_dir=repo_root/"resident-runtime/federation/seen.d"
    seen_dir.mkdir(parents=True,exist_ok=True)
    frame_name=Path(frame_path).name
    frame=frame if isinstance(frame,dict) else {}
    marker={
      "schema_version":"stegverse.federation-frame-quarantine.v1",
      "frame_name":frame_name,
      "frame_sha256":frame.get("frame_sha256"),
      "packet_id":frame.get("packet_id"),
      "destination_org":frame.get("destination_org"),
      "status":"REFUSED",
      "terminal":True,
      "disposition":"FAIL_CLOSED",
      "failure_code":"FRAME_REFUSED_QUARANTINED",
      "failed_predicate":result.get("failed_predicate"),
      "detail":"refused at ingest: "+str(result.get("failure_code"))+": "+str(result.get("detail")),
      "refused_failure_code":result.get("failure_code"),
      "required_evidence_or_repair":result.get("required_evidence_or_repair"),
      "retry_entrypoint":result.get("retry_entrypoint"),
      "owning_existing_goal":result.get("owning_existing_goal"),
      "next_attempt":"quarantined and not retried; the sender publishes a new frame with a supplied epoch",
      "derived_from_clock":False,
      "consequence_committed":False,
      "authority_effect":"NONE_CARRIER_ONLY"
    }
    marker_path=seen_dir/(hashlib.sha256(frame_name.encode()).hexdigest()+".json")
    if marker_path.exists():
        if json.loads(marker_path.read_text())!=marker:
            raise ValueError("federation_seen_marker_collision")
    else:
        marker_path.write_text(json.dumps(marker,indent=2,sort_keys=True)+"\n")
    return marker_path
