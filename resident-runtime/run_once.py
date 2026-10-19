#!/usr/bin/env python3
import argparse, importlib.util, json, subprocess, sys, tempfile
from pathlib import Path
from org_boundary_runtime import build_egress, validate_org_crossing
_ROOT=Path(__file__).resolve().parents[1]
_spec=importlib.util.spec_from_file_location("org_kernel_run_once",_ROOT/"org-kernel"/"kernel.py"); K=importlib.util.module_from_spec(_spec); _spec.loader.exec_module(K)
def main(argv=None):
 ap=argparse.ArgumentParser(allow_abbrev=False); ap.add_argument("--ingress",required=True); ap.add_argument("--egress",required=True); ap.add_argument("--hb-epoch",default=None); a=ap.parse_args(argv)
 # The egress carrier references the supplied epoch; an absent or invalid one is refused before anything runs.
 refusal=K.writer_epoch_refusal(a.hb_epoch,retry_entrypoint="resident-runtime/run_once.py --hb-epoch")
 if refusal is not None: print(json.dumps(refusal,sort_keys=True)); return 1
 # Bad input is the caller's: terminal six fields, read before anything runs or is written.
 try:
  ingress=K.read_json_input(a.ingress,argument="--ingress",retry_entrypoint="resident-runtime/run_once.py --ingress")
  try: validate_org_crossing(ingress,"INGRESS")
  except (ValueError,KeyError,TypeError) as exc: raise K.CliInputRefused(K.cli_input_refusal("--ingress",type(exc).__name__+": "+str(exc),expect=dict,retry_entrypoint="resident-runtime/run_once.py --ingress")) from None
 except K.CliInputRefused as exc: print(json.dumps(exc.refusal,sort_keys=True)); return 1
 with tempfile.TemporaryDirectory() as td:
  p=Path(td)/"execution.json"; subprocess.run(["python3","org-boundary/runtime/process_boundary.py","--envelope",a.ingress,"--out",str(p)],check=True); result=json.loads(p.read_text())
 egress=build_egress(ingress,result,epoch=int(str(a.hb_epoch))); validate_org_crossing(egress,"EGRESS"); Path(a.egress).parent.mkdir(parents=True,exist_ok=True); Path(a.egress).write_text(json.dumps(egress,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"status":"PASS","packet_id":ingress["packet_id"],"egress_packet_id":egress["packet_id"],"consumed":result["consumed"],"reconstruction":result["reconstruction"]["status"]}))
 return 0
if __name__=="__main__": raise SystemExit(main())
