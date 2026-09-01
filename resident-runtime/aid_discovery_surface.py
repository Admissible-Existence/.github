#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os
from pathlib import Path

def load(path: Path):
    value=json.loads(path.read_text())
    if not isinstance(value,dict):
        raise RuntimeError("expected object")
    return value

def aid_roots():
    out=[]
    if os.environ.get("ADMISSIBLE_EXISTENCE_AID_ROOT"):
        out.append(Path(os.environ["ADMISSIBLE_EXISTENCE_AID_ROOT"]).expanduser())
    home=Path(os.environ.get("HOME",str(Path.home())))
    out.extend([
        home/".stegverse"/"repos"/"Admissible-Existence"/"AID",
        Path("/var/lib/stegverse/source/Admissible-Existence/AID"),
        Path("/srv/stegverse/repos/Admissible-Existence/AID"),
        Path("/opt/stegverse/repos/Admissible-Existence/AID")
    ])
    return [p.resolve() for p in out]

def resolve_aid():
    required=["data/canonical-source-map.json","data/support-repository-map.json","AID_MIRROR_HANDOFF.md"]
    for root in aid_roots():
        if root.is_dir() and all((root/x).is_file() for x in required):
            return root
    raise RuntimeError("AID source not materialized in organization runtime")

def run(ingress: Path):
    env=load(ingress)
    if (env.get("destination") or {}).get("org")!="Admissible-Existence":
        raise RuntimeError("wrong destination organization")
    if (env.get("destination") or {}).get("service")!="admissible-existence.aid":
        raise RuntimeError("wrong destination service")
    payload=env.get("payload") or {}
    request=payload.get("request") if isinstance(payload.get("request"),dict) else payload
    operation=request.get("operation","DESCRIBE_AID")
    if request.get("authority_transfer",False) is not False:
        raise RuntimeError("authority transfer prohibited")
    root=resolve_aid()
    canonical=load(root/"data/canonical-source-map.json")
    support=load(root/"data/support-repository-map.json")
    result={
        "schema":"admissible-existence.aid-discovery-response/v1",
        "service_id":"admissible-existence.aid",
        "operation":operation,
        "aid_role":"AI_DISCOVERY_SDK",
        "authority_effect":"NONE",
        "authority_transfer":False,
        "runtime_authority_created":False
    }
    if operation=="DESCRIBE_AID":
        result["description"]="AID expands discovery and creative latitude for intelligent code already constructed within consequential governance; it is not a generic autonomy bootstrap."
    elif operation=="DISCOVER_CANONICAL_SOURCES":
        result["canonical_sources"]=canonical["sources"]
    elif operation=="DISCOVER_SUPPORT_RESOURCES":
        result["support_resources"]=support["supports"]
    elif operation=="DESCRIBE_STEGVERSE_002_ATTRIBUTION":
        result["stegverse_002"]={
          "proven_construction_lineage":"Admissible-Existence/TT",
          "tt_commit":"ab60b42934222a2cb5335a5a8194f258a491fc57",
          "related_available_not_required_resources":{
            "Admissible-Existence/RTG":"ca69954cb3dc4ad073c9244e003bc8f0ef3837e2",
            "Admissible-Existence/GTG":"8cdb7bce87bb9f8429c35e9c66cc5dc28a46a225",
            "Admissible-Existence/AE":"53c8eedddc4e54d8fa0660039d65ab9ac63057a1"
          }
        }
    else:
        raise RuntimeError("unsupported AID operation")
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ingress",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    try:
        result=run(a.ingress.resolve())
        code=0
    except Exception as exc:
        result={"schema":"admissible-existence.aid-discovery-response/v1","state":"BLOCKED","reason":str(exc),"authority_effect":"NONE_BLOCKED","authority_transfer":False}
        code=2
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
    raise SystemExit(code)

if __name__=="__main__":
    main()
