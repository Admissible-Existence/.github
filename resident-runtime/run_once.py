#!/usr/bin/env python3
import argparse, importlib.util, json, subprocess, sys, tempfile
from pathlib import Path
from org_boundary_runtime import build_egress, validate_org_crossing
_ROOT=Path(__file__).resolve().parents[1]
_spec=importlib.util.spec_from_file_location("org_kernel_run_once",_ROOT/"org-kernel"/"kernel.py"); K=importlib.util.module_from_spec(_spec); _spec.loader.exec_module(K)
_rspec=importlib.util.spec_from_file_location("committed_request_run_once",_ROOT/"scripts"/"read_committed_request.py"); REQUEST=importlib.util.module_from_spec(_rspec); _rspec.loader.exec_module(REQUEST)
def process_boundary_record(completed):
 """The processor's six-field record, or one for an exit it did not explain."""
 try:
  record=json.loads(completed.stdout.strip().splitlines()[-1])
  if isinstance(record,dict) and record.get("failure_code"): return json.dumps(record,sort_keys=True)
 except (*K.JSON_DECODE_ERRORS,IndexError): pass
 return json.dumps({"disposition":"FAIL_CLOSED","failure_code":"PROCESS_BOUNDARY_FAILED","failed_predicate":"PROCESS_BOUNDARY_EXITS_0_65_OR_75",
                    "detail":("exit "+str(completed.returncode)+": "+completed.stderr[-400:]),"required_evidence_or_repair":"org-boundary/runtime/process_boundary.py runs to a recorded outcome",
                    "retry_entrypoint":"resident-runtime/run_once.py (same arguments)","owning_existing_goal":K.HB_EPOCH_OWNING_EXISTING_GOAL,
                    "next_attempt":"nothing was written by this run","terminal":True,"derived_from_clock":False,"consequence_committed":False},sort_keys=True)
def main(argv=None):
 ap=argparse.ArgumentParser(allow_abbrev=False); ap.add_argument("--ingress",required=True); ap.add_argument("--egress",required=True); ap.add_argument("--hb-epoch",default=None); a=ap.parse_args(argv)
 # The egress carrier references the supplied epoch; an absent or invalid one is refused before anything runs.
 refusal=K.writer_epoch_refusal(a.hb_epoch,retry_entrypoint="resident-runtime/run_once.py --hb-epoch")
 if refusal is not None: print(json.dumps(refusal,sort_keys=True)); return 1
 # A run started from a committed request records its digest (B-P40).
 request,refused=REQUEST.recorded()
 if refused is not None: print(json.dumps(refused,sort_keys=True)); return 1
 recorded={"committed_request":request} if request is not None else {}
 # Bad input is the caller's: terminal six fields, read before anything runs or is written.
 try:
  ingress=K.read_json_input(a.ingress,argument="--ingress",retry_entrypoint="resident-runtime/run_once.py --ingress")
  try: validate_org_crossing(ingress,"INGRESS")
  except (ValueError,KeyError,TypeError) as exc: raise K.CliInputRefused(K.cli_input_refusal("--ingress",type(exc).__name__+": "+str(exc),expect=dict,retry_entrypoint="resident-runtime/run_once.py --ingress")) from None
 except K.CliInputRefused as exc: print(json.dumps(exc.refusal,sort_keys=True)); return 1
 with tempfile.TemporaryDirectory() as td:
  p=Path(td)/"execution.json"; completed=subprocess.run(["python3","org-boundary/runtime/process_boundary.py","--envelope",a.ingress,"--out",str(p)],capture_output=True,text=True,check=False)
  if completed.returncode!=0:
   # The processor's six-field record passes through with its exit status:
   # 75 is its own write fault (non-terminal, retry), 65 the input's (terminal).
   print(process_boundary_record(completed)); return completed.returncode if completed.returncode in (K.PROCESS_BOUNDARY_EXIT_WRITE_FAULT,K.PROCESS_BOUNDARY_EXIT_INPUT_FAULT) else 1
  result=json.loads(p.read_text())
 egress=build_egress(ingress,result,epoch=int(str(a.hb_epoch))); validate_org_crossing(egress,"EGRESS")
 try: Path(a.egress).parent.mkdir(parents=True,exist_ok=True); Path(a.egress).write_text(json.dumps(egress,indent=2,sort_keys=True)+"\n")
 except OSError as exc:
  # This run's own write: six fields, non-terminal, never a traceback.
  print(json.dumps(K.writer_cli_refusal(exc,failure_code="RUN_ONCE_WRITE_FAILED",retry_entrypoint="resident-runtime/run_once.py (same arguments)"),sort_keys=True)); return K.PROCESS_BOUNDARY_EXIT_WRITE_FAULT
 print(json.dumps({"status":"PASS","packet_id":ingress["packet_id"],"egress_packet_id":egress["packet_id"],"consumed":result["consumed"],"reconstruction":result["reconstruction"]["status"],**recorded},sort_keys=True))
 return 0
if __name__=="__main__": raise SystemExit(main())
