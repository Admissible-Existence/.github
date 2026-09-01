import importlib.util, json, unittest
from pathlib import Path
from unittest.mock import patch

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

class AIDDiscoverySurfaceTest(unittest.TestCase):
    def test_describe_and_attribution(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); aid=base/"AID"; write_aid(aid)
            ingress=base/"in.json"
            ingress.write_text(json.dumps(envelope("DESCRIBE_STEGVERSE_002_ATTRIBUTION")))
            with patch.dict(os.environ,{"ADMISSIBLE_EXISTENCE_AID_ROOT":str(aid)},clear=False):
                result=mod.run(ingress)
            self.assertFalse(result["authority_transfer"])
            self.assertEqual(result["stegverse_002"]["proven_construction_lineage"],"Admissible-Existence/TT")
            self.assertEqual(
              set(result["stegverse_002"]["related_available_not_required_resources"]),
              {"Admissible-Existence/RTG","Admissible-Existence/GTG","Admissible-Existence/AE"}
            )

if __name__=="__main__":
    unittest.main()
