from __future__ import annotations

import copy
import importlib.util
import os
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_tvc_worker_capability.py"
spec = importlib.util.spec_from_file_location("tvc_worker_capability", MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def request() -> dict:
    return module.load(ROOT / "data" / "tvc-principle-completeness-capability-request.json")


def receipt() -> dict:
    req = request()
    value = {
        "schema": "tvc.aex_principle_completeness_capability.v1",
        "request_id": req["request_id"],
        "decision": "ALLOW_CAPABILITY_LEASE",
        "request_sha256": module.canonical_sha256(req),
        "policy_sha256": module.EXPECTED_POLICY_SHA256,
        "policy_source": module.EXPECTED_POLICY_SOURCE,
        "issued_at": "2026-08-06T20:00:00Z",
        "expires_at": "2026-08-06T20:05:00Z",
        "revocation_reference": "tvc:aex-pc:123:1",
        "requester": req["requester"],
        "scope": req["requested_scope"],
        "workflow_run_id": "123",
        "workflow_run_attempt": 1,
        "single_use": True,
        "replay_allowed": False,
        "credentials_recorded": False,
        "protected_values_recorded": False,
        "credential_custody": "StegVerse-Labs/TV",
        "grant_authority": "StegVerse-Labs/TVC",
        "execution_authority_expanded": False,
        "source_mathematics_authority_changed": False,
    }
    value["receipt_sha256"] = module.canonical_sha256(value)
    return value


class TVCWorkerCapabilityTests(unittest.TestCase):
    def test_accepts_canonical_tvc_receipt(self) -> None:
        with patch.dict(os.environ, {"GITHUB_RUN_ID": "123", "GITHUB_RUN_ATTEMPT": "1"}, clear=False):
            errors = module.validate(receipt(), request(), datetime(2026, 8, 6, 20, 4, tzinfo=timezone.utc))
        self.assertEqual(errors, [])

    def test_rejects_run_binding_mismatch(self) -> None:
        with patch.dict(os.environ, {"GITHUB_RUN_ID": "999", "GITHUB_RUN_ATTEMPT": "1"}, clear=False):
            errors = module.validate(receipt(), request(), datetime(2026, 8, 6, 20, 4, tzinfo=timezone.utc))
        self.assertIn("binding:workflow_run_id", errors)

    def test_rejects_tampered_scope(self) -> None:
        value = receipt()
        value["scope"]["operations"].append("contents:write")
        errors = module.validate(value, request(), datetime(2026, 8, 6, 20, 4, tzinfo=timezone.utc))
        self.assertIn("receipt_hash_mismatch", errors)
        self.assertIn("scope:operations", errors)

    def test_rejects_expired_receipt(self) -> None:
        errors = module.validate(receipt(), request(), datetime(2026, 8, 6, 20, 5, tzinfo=timezone.utc))
        self.assertIn("time:expired", errors)

    def test_rejects_disclosure_flags(self) -> None:
        value = copy.deepcopy(receipt())
        value["credentials_recorded"] = True
        value["receipt_sha256"] = module.canonical_sha256({key: field for key, field in value.items() if key != "receipt_sha256"})
        errors = module.validate(value, request(), datetime(2026, 8, 6, 20, 4, tzinfo=timezone.utc))
        self.assertIn("mismatch:credentials_recorded", errors)

    def test_rejects_unpinned_policy(self) -> None:
        value = receipt()
        value["policy_sha256"] = "a" * 64
        value["receipt_sha256"] = module.canonical_sha256({key: field for key, field in value.items() if key != "receipt_sha256"})
        errors = module.validate(value, request(), datetime(2026, 8, 6, 20, 4, tzinfo=timezone.utc))
        self.assertIn("mismatch:policy_sha256", errors)

    def test_rejects_policy_source_drift(self) -> None:
        value = receipt()
        value["policy_source"] = {**module.EXPECTED_POLICY_SOURCE, "commit_sha": "0" * 40}
        value["receipt_sha256"] = module.canonical_sha256({key: field for key, field in value.items() if key != "receipt_sha256"})
        errors = module.validate(value, request(), datetime(2026, 8, 6, 20, 4, tzinfo=timezone.utc))
        self.assertIn("policy_source_mismatch", errors)

    def test_receipt_hash_is_canonical_hex(self) -> None:
        value = receipt()
        self.assertEqual(len(value["receipt_sha256"]), 64)
        self.assertTrue(set(value["receipt_sha256"]).issubset(set("0123456789abcdef")))


if __name__ == "__main__":
    unittest.main()
