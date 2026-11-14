import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("math_audit", Path(__file__).resolve().parents[1] / "scripts/audit_mathematical_completeness.py")
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class NonSourceEvidenceTests(unittest.TestCase):
    def evidence(self, role="support"):
        return {"state": "PASS", "role": role, "role_contract_complete": True,
                "na_rationale": "Support contract, not source mathematics.",
                "receipt": "reports/role-receipt.json", "receipt_blob": "a" * 40,
                "handoff": "docs/SUPPORT_MIRROR_HANDOFF.md", "handoff_commit": "b" * 40,
                "conclusion": "success", "execution_authorized": False}

    def result(self, evidence, role="support"):
        return audit.non_source_audit("Example/support", role, evidence, "validated_complete_notify_only")

    def test_two_flags_do_not_establish_evidence(self):
        self.assertFalse(self.result({"state": "PASS", "role_contract_complete": True})["mathematical_complete"])

    def test_bound_role_contract_controls(self):
        for role in ("support", "coordination", "empty"):
            with self.subTest(role=role):
                result = self.result(self.evidence(role), role)
                self.assertTrue(result["mathematical_complete"])
                self.assertEqual(set(result["semantic"].values()), {"N/A"})
                self.assertFalse(result["proof_candidate_is_proof"])

    def test_each_required_field_is_required(self):
        for key in self.evidence():
            with self.subTest(key=key):
                value = self.evidence()
                del value[key]
                self.assertFalse(self.result(value)["mathematical_complete"])

    def test_invalid_values_reject(self):
        invalid = {"state": [True, "PENDING_EVIDENCE"], "role": ["source", "coordination"],
                   "role_contract_complete": [1, "true", False], "na_rationale": ["", "  ", True],
                   "receipt": ["", " ", True], "receipt_blob": ["latest", "a" * 39, "g" * 40, True],
                   "handoff": ["", " ", True], "handoff_commit": ["main", "b" * 7, "g" * 40, True],
                   "conclusion": ["failure", True], "execution_authorized": [True, 0, "false"]}
        for key, values in invalid.items():
            for value in values:
                with self.subTest(key=key, value=value):
                    evidence = self.evidence()
                    evidence[key] = value
                    self.assertFalse(self.result(evidence)["mathematical_complete"])

    def test_absent_evidence_does_not_inherit_worker_completion(self):
        for evidence in (None, {}):
            result = self.result(evidence)
            self.assertFalse(result["mathematical_complete"])
            self.assertEqual(result["state"], "PENDING_EVIDENCE")

    def test_malformed_non_object_fails_closed(self):
        for evidence in (True, "PASS", ["PASS"]):
            with self.subTest(evidence=evidence):
                self.assertFalse(self.result(evidence)["mathematical_complete"])

    def test_cli_does_not_turn_two_flags_into_org_readiness(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            (directory / "registry.json").write_text(json.dumps({"repositories": [
                {"repository": "Example/support", "role": "support"}]}))
            (directory / "evidence.json").write_text(json.dumps({"repositories": {
                "Example/support": {"state": "PASS", "role_contract_complete": True}}}))
            subprocess.run([sys.executable, str(root / "scripts/audit_mathematical_completeness.py"),
                            "--registry", str(directory / "registry.json"),
                            "--evidence", str(directory / "evidence.json"),
                            "--policy", str(root / "data/mathematical-completeness-policy.json"),
                            "--json-out", str(directory / "out.json"),
                            "--md-out", str(directory / "out.md")], check=True, capture_output=True)
            report = json.loads((directory / "out.json").read_text())
            self.assertFalse(report["ready"])
            self.assertEqual(report["summary"]["non_source_complete"], 0)
            self.assertEqual(report["repositories"][0]["audit"]["state"], "PENDING_EVIDENCE")

    def test_rejected_payload_is_retained_without_mutation(self):
        evidence = self.evidence()
        evidence["handoff_commit"] = "main"
        original = copy.deepcopy(evidence)
        result = self.result(evidence)
        self.assertEqual(evidence, original)
        self.assertIs(result["evidence"], evidence)
        self.assertNotEqual(result["state"], "PASS")
        self.assertIn("handoff_binding", result["gaps"])


if __name__ == "__main__":
    unittest.main()
