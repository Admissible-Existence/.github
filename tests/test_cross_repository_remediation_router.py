from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "route_cross_repository_remediation.py"
spec = importlib.util.spec_from_file_location("route_cross_repository_remediation", MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_source_routes_to_direct_source_update() -> None:
    action, next_action = module.classify({"role": "source", "worker_state": "required"})
    assert action == "DIRECT_SOURCE_UPDATE"
    assert "formalism" in next_action and "mathematics" in next_action


def test_support_routes_to_direct_support_update() -> None:
    action, next_action = module.classify({"role": "support", "worker_state": "required"})
    assert action == "DIRECT_SUPPORT_UPDATE"
    assert "support boundary" in next_action and "coverage map" in next_action


def test_empty_routes_to_disposition() -> None:
    action, next_action = module.classify({"role": "empty", "worker_state": "disposition_required"})
    assert action == "DISPOSITION_REQUIRED"
    assert "deprecation" in next_action


def test_machine_owned_routes_to_observe_only_before_source_role() -> None:
    action, next_action = module.classify({"role": "source", "worker_state": "machine_owned_observe_only"})
    assert action == "OBSERVE_NOTIFY_ONLY"
    assert "do not duplicate" in next_action


def test_validated_complete_routes_to_notify_only() -> None:
    action, next_action = module.classify({"role": "source", "worker_state": "validated_complete_notify_only"})
    assert action == "COMPLETE_NOTIFY_ONLY"
    assert "Preserve completion evidence" in next_action


def test_coordination_routes_to_control_plane() -> None:
    action, _ = module.classify({"role": "coordination", "worker_state": "active_control_plane"})
    assert action == "CONTROL_PLANE"


def test_unknown_role_fails_to_review_required() -> None:
    action, _ = module.classify({"role": "unknown", "worker_state": "required"})
    assert action == "REVIEW_REQUIRED"
