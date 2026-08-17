from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_relational_admissibility_formalism.py"
SPEC = importlib.util.spec_from_file_location("relational_admissibility_validator", MODULE_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class RelationalAdmissibilityFormalismTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixtures = validator.load(validator.FIXTURES)
        self.by_id = {case["case_id"]: case["transition"] for case in self.fixtures["cases"]}

    def test_repository_contract_is_valid(self) -> None:
        result = validator.validate_repository()
        self.assertTrue(result["valid"], result["findings"])
        self.assertEqual(result["axiom_count"], 9)
        self.assertEqual(result["fixture_count"], 6)
        self.assertEqual(result["admissibility_resolver"], "Admissible-Existence/AE")
        self.assertEqual(result["credential_authority_for_stegverse_runtime"], "TV/TVC")
        self.assertEqual(result["github_token_runtime_authority"], "NONE")

    def test_valid_deny_is_not_null_transition(self) -> None:
        transition = self.by_id["DENY_IS_REAL_SUCCESSOR_TRANSITION"]
        self.assertTrue(transition["resolution"]["resolution_valid"])
        self.assertFalse(transition["resolution"]["requested_effect_authorized"])
        self.assertFalse(transition["resolution"]["requested_effect_realized"])
        self.assertNotEqual(
            transition["predecessor_state"]["state_hash"],
            transition["successor_state"]["state_hash"],
        )
        self.assertEqual([], validator.validate_transition("DENY_IS_REAL_SUCCESSOR_TRANSITION", transition))

    def test_confirmation_changes_total_state_without_object_change(self) -> None:
        transition = self.by_id["CONFIRMATION_CHANGES_TOTAL_STATE_WITHOUT_OBJECT_CHANGE"]
        self.assertEqual(
            transition["predecessor_state"]["component_states"],
            transition["successor_state"]["component_states"],
        )
        self.assertNotEqual(
            transition["predecessor_state"]["state_hash"],
            transition["successor_state"]["state_hash"],
        )
        self.assertTrue(any(r["state"] == "CONFIRMED_INVARIANT" for r in transition["relations"]))

    def test_rejects_allow_only_validity_compression(self) -> None:
        transition = copy.deepcopy(self.by_id["DENY_IS_REAL_SUCCESSOR_TRANSITION"])
        transition["resolution"]["resolution_valid"] = False
        findings = validator.validate_transition("DENY_IS_REAL_SUCCESSOR_TRANSITION", transition)
        self.assertIn("DENY_IS_REAL_SUCCESSOR_TRANSITION:resolution_must_be_valid", findings)

    def test_rejects_null_successor_for_non_allow(self) -> None:
        transition = copy.deepcopy(self.by_id["FAIL_CLOSED_RECORDS_EVIDENCE_GAP"])
        transition["successor_state"]["state_id"] = transition["predecessor_state"]["state_id"]
        transition["successor_state"]["state_hash"] = transition["predecessor_state"]["state_hash"]
        findings = validator.validate_transition("FAIL_CLOSED_RECORDS_EVIDENCE_GAP", transition)
        self.assertIn("FAIL_CLOSED_RECORDS_EVIDENCE_GAP:successor_state_hash_must_change", findings)
        self.assertIn("FAIL_CLOSED_RECORDS_EVIDENCE_GAP:successor_state_id_must_change", findings)

    def test_rejects_confirmation_as_no_state_change(self) -> None:
        transition = copy.deepcopy(self.by_id["CONFIRMATION_CHANGES_TOTAL_STATE_WITHOUT_OBJECT_CHANGE"])
        transition["successor_state"]["state_hash"] = transition["predecessor_state"]["state_hash"]
        findings = validator.validate_transition("CONFIRMATION_CHANGES_TOTAL_STATE_WITHOUT_OBJECT_CHANGE", transition)
        self.assertIn(
            "CONFIRMATION_CHANGES_TOTAL_STATE_WITHOUT_OBJECT_CHANGE:confirmation_must_change_total_state_hash",
            findings,
        )

    def test_rejects_periodic_heartbeat_as_primitive_observation_trigger(self) -> None:
        transition = copy.deepcopy(self.by_id["ALLOW_REALIZES_REQUESTED_EFFECT"])
        transition["observation_trigger"] = "PERIODIC_HEARTBEAT"
        findings = validator.validate_transition("ALLOW_REALIZES_REQUESTED_EFFECT", transition)
        self.assertIn("ALLOW_REALIZES_REQUESTED_EFFECT:invalid_observation_trigger", findings)
        self.assertIn(
            "ALLOW_REALIZES_REQUESTED_EFFECT:periodic_heartbeat_may_not_be_primitive_trigger",
            findings,
        )

    def test_composition_can_require_different_resolution(self) -> None:
        transition = self.by_id["COMPOSITION_CHANGES_RELATIONAL_RESOLUTION"]
        self.assertEqual(transition["resolution"]["classification"], "REVIEW")
        self.assertGreaterEqual(len(transition["affected_components"]), 3)
        self.assertEqual([], validator.validate_transition("COMPOSITION_CHANGES_RELATIONAL_RESOLUTION", transition))

    def test_authority_boundary_cannot_be_widened(self) -> None:
        transition = copy.deepcopy(self.by_id["ALLOW_REALIZES_REQUESTED_EFFECT"])
        transition["github_token_runtime_authority"] = "GITHUB_TOKEN"
        findings = validator.validate_transition("ALLOW_REALIZES_REQUESTED_EFFECT", transition)
        self.assertIn("ALLOW_REALIZES_REQUESTED_EFFECT:github_token_runtime_authority_must_be_NONE", findings)


if __name__ == "__main__":
    unittest.main()
