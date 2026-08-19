#!/usr/bin/env python3
"""Validate a TVC grant receipt for the principle-completeness worker.

This validator never reads or emits a protected credential. It validates only the
sanitized TVC decision receipt and exact GitHub workflow bindings.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "data/tvc-principle-completeness-capability-request.json"
EXPECTED_POLICY_SOURCE = {
    "repository": "StegVerse-Labs/TV",
    "path": "policies/aex_cross_repository_runtime_capability_policy.json",
    "commit_sha": "160a69ccc5b8aeb199b7136a02cd9fadc08180a9",
}
EXPECTED_POLICY_SHA256 = "04044ef49a2bf621d508c53d2c704a9ed71cb2163aa986c8fa6368f03d3e7ad5"
ALLOWED_OPERATIONS = {
    "metadata:read",
    "contents:read",
    "issues:read",
    "issues:write",
    "pull_requests:read",
    "actions:read",
}
REQUIRED_DENIALS = {
    "secrets:read",
    "secrets:write",
    "administration:write",
    "repository:delete",
    "releases:write",
    "packages:write",
    "workflows:write",
    "contents:write",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def canonical_sha256(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def parse_time(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp_missing_timezone")
    return parsed.astimezone(dt.timezone.utc)


def validate(receipt: dict[str, Any], request: dict[str, Any], now: dt.datetime | None = None) -> list[str]:
    errors: list[str] = []
    now = now or dt.datetime.now(dt.timezone.utc)

    expected_scalars = {
        "schema": "tvc.aex_principle_completeness_capability.v1",
        "request_id": request["request_id"],
        "decision": "ALLOW_CAPABILITY_LEASE",
        "request_sha256": canonical_sha256(request),
        "policy_sha256": EXPECTED_POLICY_SHA256,
        "credentials_recorded": False,
        "protected_values_recorded": False,
        "credential_custody": "StegVerse-Labs/TV",
        "grant_authority": "StegVerse-Labs/TVC",
        "single_use": True,
        "replay_allowed": False,
        "execution_authority_expanded": False,
        "source_mathematics_authority_changed": False,
    }
    for key, value in expected_scalars.items():
        if receipt.get(key) != value:
            errors.append(f"mismatch:{key}")

    if receipt.get("policy_source") != EXPECTED_POLICY_SOURCE:
        errors.append("policy_source_mismatch")

    supplied_hash = receipt.get("receipt_sha256")
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256", None)
    if not isinstance(supplied_hash, str) or supplied_hash != canonical_sha256(unsigned):
        errors.append("receipt_hash_mismatch")

    if receipt.get("requester") != request.get("requester"):
        errors.append("requester_binding_mismatch")

    scope = receipt.get("scope")
    requested_scope = request.get("requested_scope")
    if not isinstance(scope, dict) or not isinstance(requested_scope, dict):
        errors.append("missing:scope")
    else:
        if scope.get("repository_pattern") != "Admissible-Existence/*":
            errors.append("scope:repository_pattern")
        operations = scope.get("operations")
        if not isinstance(operations, list) or set(operations) != ALLOWED_OPERATIONS:
            errors.append("scope:operations")
        denied = scope.get("explicitly_denied")
        if not isinstance(denied, list) or not REQUIRED_DENIALS.issubset(set(denied)):
            errors.append("scope:required_denials")
        if scope != requested_scope:
            errors.append("scope_binding_mismatch")

    expected_run_id = os.environ.get("GITHUB_RUN_ID")
    expected_attempt = os.environ.get("GITHUB_RUN_ATTEMPT")
    if expected_run_id is not None and str(receipt.get("workflow_run_id")) != expected_run_id:
        errors.append("binding:workflow_run_id")
    if expected_attempt is not None and str(receipt.get("workflow_run_attempt")) != expected_attempt:
        errors.append("binding:workflow_run_attempt")

    try:
        issued = parse_time(str(receipt["issued_at"]))
        expires = parse_time(str(receipt["expires_at"]))
        if issued > now:
            errors.append("time:not_yet_valid")
        if expires <= now:
            errors.append("time:expired")
        if expires <= issued:
            errors.append("time:invalid_window")
        if (expires - issued).total_seconds() > int(request["lease"]["maximum_ttl_seconds"]):
            errors.append("time:ttl_exceeds_request")
    except Exception:
        errors.append("time:invalid")

    if not isinstance(receipt.get("revocation_reference"), str) or not receipt["revocation_reference"]:
        errors.append("missing:revocation_reference")

    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--output", default="reports/tvc-worker-capability-validation.json")
    parser.add_argument("--now", help="Optional deterministic validation time")
    args = parser.parse_args()

    request = load(REQUEST)
    receipt = load(Path(args.receipt))
    now = parse_time(args.now) if args.now else None
    errors = validate(receipt, request, now)
    result = {
        "schema_version": "1.1.0",
        "request_id": request["request_id"],
        "valid": not errors,
        "errors": errors,
        "policy_source": EXPECTED_POLICY_SOURCE,
        "policy_sha256": EXPECTED_POLICY_SHA256,
        "credentials_recorded": False,
        "protected_values_recorded": False,
        "receipt_path": args.receipt,
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
