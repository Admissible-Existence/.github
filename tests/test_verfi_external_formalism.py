import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_verfi_external_formalism.py"
SPEC = importlib.util.spec_from_file_location("verfi_validator", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class VerFiExternalFormalismTests(unittest.TestCase):
    def base_case(self):
        return {
            "id": "CLEAN_SEQUENCE",
            "presented_hash": "doc:v1",
            "authorized_hash": "doc:v1",
            "disclosure": True,
            "comprehension_evidence": "DISTINGUISHABLE",
            "authorization_valid_at_commit": True,
            "signature": True,
            "evidence_integrity": True,
            "temporal_order_valid": True,
            "minimum_information_satisfied": True,
            "reconstructable": True,
        }

    def test_clean_sequence_is_candidate_allow(self):
        self.assertEqual(MODULE.evaluate(self.base_case()), "ALLOW_CANDIDATE")

    def test_missing_disclosure_cannot_be_allowed(self):
        case = self.base_case()
        case["disclosure"] = False
        self.assertEqual(MODULE.evaluate(case), "DISCLOSURE_NOT_ESTABLISHED")

    def test_signature_cannot_substitute_for_comprehension(self):
        case = self.base_case()
        case["id"] = "COMPREHENSION_MISSING"
        case["comprehension_evidence"] = "ABSENT"
        self.assertEqual(MODULE.evaluate(case), "AUTHORIZATION_INADMISSIBLE")

    def test_missing_signature_cannot_be_allowed(self):
        case = self.base_case()
        case["signature"] = False
        self.assertEqual(MODULE.evaluate(case), "SIGNATURE_NOT_ESTABLISHED")

    def test_disclosure_drift_requires_review(self):
        case = self.base_case()
        case["id"] = "DISCLOSURE_DRIFT"
        case["authorized_hash"] = "doc:v2"
        self.assertEqual(MODULE.evaluate(case), "REVIEW")

    def test_integrity_failure_fails_closed(self):
        case = self.base_case()
        case["id"] = "EVIDENCE_TAMPER"
        case["evidence_integrity"] = False
        case["reconstructable"] = False
        self.assertEqual(MODULE.evaluate(case), "FAIL_CLOSED")

    def test_lapsed_authorization_denies_requested_effect(self):
        case = self.base_case()
        case["id"] = "AUTHORIZATION_LAPSED"
        case["authorization_valid_at_commit"] = False
        self.assertEqual(MODULE.evaluate(case), "DENY")

    def test_over_collection_is_not_silently_allowed(self):
        case = self.base_case()
        case["id"] = "OVER_COLLECTION"
        case["minimum_information_satisfied"] = False
        self.assertEqual(MODULE.evaluate(case), "REVIEW_MINIMIZATION")

    def test_human_machine_lane_is_comparison_only(self):
        case = {"id": "HUMAN_MACHINE_SYMMETRY", "machine_comparison_only": True}
        self.assertEqual(MODULE.evaluate(case), "STRUCTURAL_COMPARISON_ONLY")


if __name__ == "__main__":
    unittest.main()
