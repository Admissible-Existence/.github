from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_canonical_formalism_orientation.py"

spec = importlib.util.spec_from_file_location("orientation_validator", SCRIPT)
validator = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(validator)


class CanonicalFormalismOrientationTests(unittest.TestCase):
    def test_repository_orientation_is_valid(self) -> None:
        self.assertEqual(validator.main(), 0)

    def test_registry_has_only_established_concepts(self) -> None:
        data = json.loads((ROOT / "data" / "canonical-formalism-orientation.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(data["concepts"]), 8)
        self.assertTrue(all(item["maturity"] == "CANONICAL_ESTABLISHED" for item in data["concepts"]))

    def test_frontier_preserves_lower_maturity_classes(self) -> None:
        text = (ROOT / "docs" / "DISCOVERY_FRONTIER.md").read_text(encoding="utf-8")
        self.assertIn("CONSISTENT_INTERPRETATION", text)
        self.assertIn("CANDIDATE_FORMALIZATION", text)
        self.assertIn("OPEN_EMPIRICAL", text)
        self.assertIn("continuity as an observable/reconstructable relationship across states", text)
        self.assertIn("resolution-dependent Reconstruction Singularity boundary", text)
        self.assertIn("composite observer with individuated inputs", text)

    def test_no_authority_widening_or_non_tvtvc_runtime_credential_path(self) -> None:
        data = json.loads((ROOT / "data" / "canonical-formalism-orientation.json").read_text(encoding="utf-8"))
        self.assertFalse(data["creates_source_formalism_authority"])
        self.assertFalse(data["creates_execution_authority"])
        self.assertFalse(data["creates_validation_authority"])
        self.assertFalse(data["creates_credential_authority"])
        self.assertEqual(data["credential_authority_for_stegverse_runtime"], "TV/TVC")
        self.assertEqual(data["github_token_runtime_authority"], "NONE")

    def test_worker_extension_rule_fails_closed_by_contract(self) -> None:
        data = json.loads((ROOT / "data" / "canonical-formalism-orientation.json").read_text(encoding="utf-8"))
        rule = data["worker_rule"]
        self.assertTrue(rule["extension_requires_insufficiency_record"])
        self.assertTrue(rule["challenge_requires_falsifying_evidence"])
        self.assertFalse(rule["orientation_may_widen_authority"])


if __name__ == "__main__":
    unittest.main()
