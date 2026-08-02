import importlib.util
import pathlib
import unittest

MODULE_PATH = pathlib.Path(__file__).parents[1] / "scripts" / "dispatch_formalism_tasks.py"
spec = importlib.util.spec_from_file_location("dispatch_formalism_tasks", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.registry = {
            "goal_id": "AEX-FORMALISM-WORKER-PUBLICATION-001",
            "repositories": [{"name": "RTG"}, {"name": "FI"}],
        }
        self.claims = {
            "tasks": [
                {
                    "repository": "Admissible-Existence/RTG",
                    "stage": "mathematical_validation",
                    "claim_state": "MACHINE_OWNED",
                    "completion_state": "PARTIAL",
                    "claimant": "RTG machine lanes",
                    "evidence": ["RTG/docs/RTG_MIRROR_HANDOFF.md"],
                    "next_action": "Observe receipts",
                    "next_action_location": "RTG/review/",
                }
            ]
        }

    def test_emits_all_stages_for_each_repository(self):
        result = module.dispatch(self.registry, self.claims, {})
        self.assertEqual(len(result["tasks"]), 2 * len(module.STAGES))

    def test_preserves_existing_machine_claim(self):
        result = module.dispatch(self.registry, self.claims, {})
        task = next(
            item
            for item in result["tasks"]
            if item["repository"] == "Admissible-Existence/RTG"
            and item["stage"] == "mathematical_validation"
        )
        self.assertEqual(task["claim_state"], "MACHINE_OWNED")
        self.assertEqual(task["next_action"], "Observe receipts")

    def test_missing_worker_is_not_reported_complete(self):
        result = module.dispatch(self.registry, self.claims, {})
        task = next(
            item
            for item in result["tasks"]
            if item["repository"] == "Admissible-Existence/FI"
            and item["stage"] == "publication_readiness"
        )
        self.assertEqual(task["claim_state"], "UNCLAIMED")
        self.assertEqual(task["completion_state"], "MISSING")
        self.assertTrue(task["archival_dependency"])

    def test_blocked_audit_fails_closed(self):
        report = {"repositories": [{"repository": "FI", "status": "BLOCKED", "issues": ["access"]}]}
        result = module.dispatch(self.registry, self.claims, report)
        task = next(
            item
            for item in result["tasks"]
            if item["repository"] == "Admissible-Existence/FI"
            and item["stage"] == "coherence_audit"
        )
        self.assertEqual(task["claim_state"], "BLOCKED")
        self.assertEqual(task["completion_state"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
