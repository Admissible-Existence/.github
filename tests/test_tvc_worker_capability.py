from __future__ import annotations

import copy
import importlib.util
from datetime import datetime, timezone
from pathlib import Path

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
        "policy_sha256": "a" * 64,
        "issued_at": "2026-08-06T20:00:00Z",
        "expires_at": "2026-08-06T20:15:00Z",
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


def test_accepts_canonical_tvc_receipt(monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_RUN_ID", "123")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    errors = module.validate(receipt(), request(), datetime(2026, 8, 6, 20, 5, tzinfo=timezone.utc))
    assert errors == []


def test_rejects_run_binding_mismatch(monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_RUN_ID", "999")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    errors = module.validate(receipt(), request(), datetime(2026, 8, 6, 20, 5, tzinfo=timezone.utc))
    assert "binding:workflow_run_id" in errors


def test_rejects_tampered_scope() -> None:
    value = receipt()
    value["scope"]["operations"].append("contents:write")
    errors = module.validate(value, request(), datetime(2026, 8, 6, 20, 5, tzinfo=timezone.utc))
    assert "receipt_hash_mismatch" in errors
    assert "scope:operations" in errors


def test_rejects_expired_receipt() -> None:
    errors = module.validate(receipt(), request(), datetime(2026, 8, 6, 20, 15, tzinfo=timezone.utc))
    assert "time:expired" in errors


def test_rejects_disclosure_flags() -> None:
    value = copy.deepcopy(receipt())
    value["credentials_recorded"] = True
    value["receipt_sha256"] = module.canonical_sha256({k: v for k, v in value.items() if k != "receipt_sha256"})
    errors = module.validate(value, request(), datetime(2026, 8, 6, 20, 5, tzinfo=timezone.utc))
    assert "mismatch:credentials_recorded" in errors


def test_receipt_hash_is_canonical_hex() -> None:
    value = receipt()
    assert len(value["receipt_sha256"]) == 64
    assert set(value["receipt_sha256"]).issubset(set("0123456789abcdef"))
