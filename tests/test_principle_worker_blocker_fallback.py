from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load_controller():
    path = ROOT / "scripts" / "run_principle_completeness_workers.py"
    spec = importlib.util.spec_from_file_location("principle_completeness_workers_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PrincipleWorkerBlockerFallbackTests(unittest.TestCase):
    def test_blocked_repository_is_persisted_and_later_repository_is_processed(self):
        controller = load_controller()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = root / "registry.json"
            output_path = root / "status.json"
            summary_path = root / "status.md"
            registry = {
                "schema_version": "2.0.0",
                "goal_id": "AEX-PRINCIPLE-COMPLETENESS-001",
                "coordination_repository": "Admissible-Existence/.github",
                "required_source_artifacts": ["README.md"],
                "required_support_artifacts": ["README.md"],
                "repositories": [
                    {
                        "repository": "Admissible-Existence/Blocked-A",
                        "role": "source",
                        "worker_state": "active",
                    },
                    {
                        "repository": "Admissible-Existence/Later-B",
                        "role": "source",
                        "worker_state": "active",
                    },
                ],
            }
            registry_path.write_text(json.dumps(registry), encoding="utf-8")

            def fake_tree(repository):
                if repository.endswith("/Blocked-A"):
                    raise RuntimeError("fixture repository visibility failure")
                if repository.endswith("/Later-B"):
                    return ["README.md", "docs/LATER_MIRROR_HANDOFF.md"]
                raise AssertionError(repository)

            with (
                mock.patch.object(controller, "REGISTRY", registry_path),
                mock.patch.object(controller, "OUTPUT", output_path),
                mock.patch.object(controller, "SUMMARY", summary_path),
                mock.patch.object(controller, "list_tree", side_effect=fake_tree),
                mock.patch.object(sys, "argv", ["run_principle_completeness_workers.py"]),
            ):
                rc = controller.main()

            self.assertEqual(rc, 1)
            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(report["fallback_mode"], "PERSIST_BLOCKER_AND_CONTINUE")
            self.assertEqual(report["repository_count"], 2)
            self.assertEqual(report["blocker_count"], 1)

            rows = {row["repository"]: row for row in report["repositories"]}
            blocked = rows["Admissible-Existence/Blocked-A"]
            later = rows["Admissible-Existence/Later-B"]

            self.assertEqual(blocked["completion_state"], "BLOCKED")
            self.assertEqual(blocked["claim_state"], "BLOCKED")
            self.assertEqual(blocked["fallback_mode"], "PERSIST_BLOCKER_AND_CONTINUE")
            self.assertEqual(blocked["findings"][0]["code"], "REPOSITORY_ACCESS_FAILED")
            self.assertEqual(
                blocked["findings"][0]["durable_owner"],
                "Admissible-Existence/.github#4",
            )
            self.assertTrue(blocked["findings"][0]["release_condition"])
            self.assertTrue(blocked["findings"][0]["next_action"])

            self.assertEqual(later["completion_state"], "IMPLEMENTED_UNVALIDATED")
            self.assertEqual(later["claim_state"], "CLAIMED_FOR_VALIDATION")
            self.assertEqual(later["issue"], "DRY_RUN")
            self.assertEqual(later["missing"], [])

            self.assertFalse(report["archive_permitted"])
            self.assertIn(
                "A blocker is durable work state and does not terminate unrelated in-scope work.",
                report["completion_rule"],
            )


if __name__ == "__main__":
    unittest.main()
