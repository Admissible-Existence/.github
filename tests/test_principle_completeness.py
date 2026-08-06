from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_formalism_coherence.py"
spec = importlib.util.spec_from_file_location("audit_formalism_coherence", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class PrincipleCompletenessTests(unittest.TestCase):
    def test_empty_repository_is_empty(self) -> None:
        self.assertEqual(module.classify_role("SOL", 0), "empty")

    def test_known_roles(self) -> None:
        self.assertEqual(module.classify_role("AE", 3), "source")
        self.assertEqual(module.classify_role("validator", 3), "support")
        self.assertEqual(module.classify_role(".github", 3), "coordination")

    def test_scaffold_does_not_pass(self) -> None:
        scores = {name: False for name in module.DIMENSIONS}
        scores["identity"] = True
        scores["purpose"] = True
        self.assertEqual(module.completion_state("source", scores, 0, 0), "BLOCKED")

    def test_formalized_unvalidated(self) -> None:
        scores = {name: False for name in module.DIMENSIONS}
        scores.update({
            "identity": True,
            "purpose": True,
            "theory": True,
            "mathematics": True,
            "formal_status": True,
            "dependencies": True,
            "handoff_binding": True,
        })
        self.assertEqual(
            module.completion_state("source", scores, 0, 0),
            "FORMALIZED_UNVALIDATED",
        )

    def test_all_dimensions_only_create_candidate(self) -> None:
        scores = {name: True for name in module.DIMENSIONS}
        self.assertEqual(
            module.completion_state("source", scores, 0, 0),
            "COMPLETE_CANDIDATE",
        )

    def test_placeholders_block_candidate(self) -> None:
        scores = {name: True for name in module.DIMENSIONS}
        self.assertEqual(module.completion_state("source", scores, 1, 0), "BLOCKED")

    def test_handoff_is_mandatory(self) -> None:
        scores = {name: True for name in module.DIMENSIONS}
        scores["handoff_binding"] = False
        self.assertEqual(module.completion_state("source", scores, 0, 0), "BLOCKED")

    def test_dimension_detection(self) -> None:
        text = """
        Principle ID AEX-P-001. Purpose and canonical statement.
        Theory domain, codomain, assumptions, objects and state space.
        $A := \{x \mid x \ge 0\}$ and validation predicate.
        Theorem with proof status REVIEW_REQUIRED.
        Falsification counterexample and limitations.
        Upstream dependency and downstream successor.
        Whole-repo role in the overall theory and broader picture.
        Cross-repository ecosystem relation Admissible-Existence/AE.
        Executable validator, fixtures, tests, and schema.
        SHA-256 commit blob hash receipt evidence binding.
        Mirror handoff docs/AE_MIRROR_HANDOFF.md.
        """
        scores = module.dimension_scores([text], ["docs/AE_MIRROR_HANDOFF.md"], "source")
        self.assertTrue(all(scores.values()), scores)


if __name__ == "__main__":
    unittest.main()
