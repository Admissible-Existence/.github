import importlib.util, json, os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("aid_surface",ROOT/"resident-runtime/aid_discovery_surface.py")
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def write_aid(root):
    (root/"data").mkdir(parents=True)
    (root/"AID_MIRROR_HANDOFF.md").write_text("# AID\n")
    (root/"data/canonical-source-map.json").write_text(json.dumps({
      "sources":[
        {"repository":"Admissible-Existence/TT","stegverse_002_construction_lineage":True},
        {"repository":"Admissible-Existence/RTG","stegverse_002_self_characterization_resource":"AVAILABLE_NOT_REQUIRED"},
        {"repository":"Admissible-Existence/GTG","stegverse_002_self_characterization_resource":"AVAILABLE_NOT_REQUIRED"},
        {"repository":"Admissible-Existence/AE","stegverse_002_self_characterization_resource":"AVAILABLE_NOT_REQUIRED"}
      ]
    }))
    (root/"data/support-repository-map.json").write_text(json.dumps({"supports":[
      {"repository":"Admissible-Existence/learning-transition-governance"},
      {"repository":"Admissible-Existence/validation-profile-registry"},
      {"repository":"Admissible-Existence/standing-proof-formalism"},
      {"repository":"Admissible-Existence/ae-validation-factory"}
    ]}))

def envelope(operation):
    return {
      "destination":{"org":"Admissible-Existence","service":"admissible-existence.aid"},
      "payload":{"operation":operation,"authority_transfer":False}
    }

def test_describe_and_attribution(tmp_path,monkeypatch):
    aid=tmp_path/"AID"; write_aid(aid)
    monkeypatch.setenv("ADMISSIBLE_EXISTENCE_AID_ROOT",str(aid))
    ingress=tmp_path/"in.json"
    ingress.write_text(json.dumps(envelope("DESCRIBE_STEGVERSE_002_ATTRIBUTION")))
    result=mod.run(ingress)
    assert result["authority_transfer"] is False
    assert result["stegverse_002"]["proven_construction_lineage"]=="Admissible-Existence/TT"
    assert set(result["stegverse_002"]["related_available_not_required_resources"])=={
      "Admissible-Existence/RTG","Admissible-Existence/GTG","Admissible-Existence/AE"
    }
