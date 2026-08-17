from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_minimum_admissible_transition_set.py"
SPEC = importlib.util.spec_from_file_location("minimum_set_validator", SCRIPT)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class MinimumAdmissibleTransitionSetTests(unittest.TestCase):
    def test_repository_minimum_set_is_valid(self) -> None:
        self.assertEqual(0, validator.main())

    def test_required_set_is_exact_minimum_not_exhaustive(self) -> None:
        data = json.loads(validator.FORMALISM.read_text(encoding="utf-8"))
        self.assertTrue(validator.MINIMUM <= set(data["minimum_required_admissible_transition_classes"]))
        self.assertTrue(data["resolution_classes_are_extensible"])
        self.assertIn("ALLOW", data["baseline_resolution_examples"])

    def test_missing_deny_is_rejected(self) -> None:
        data = json.loads(validator.FORMALISM.read_text(encoding="utf-8"))
        mutated = copy.deepcopy(data)
        mutated["minimum_required_admissible_transition_classes"] = ["REVIEW", "FAIL_CLOSED"]
        with mock.patch.object(validator, "FORMALISM") as path:
            path.is_file.return_value = True
        self.assertNotEqual(set(mutated["minimum_required_admissible_transition_classes"]), validator.MINIMUM)


if __name__ == "__main__":
    unittest.main()
