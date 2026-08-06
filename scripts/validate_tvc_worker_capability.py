#!/usr/bin/env python3
"""Validate a TVC grant receipt for the principle-completeness worker.

This validator never reads or emits a protected credential. It validates only the
sanitized TVC decision receipt and current GitHub workflow bindings.
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
ALLOWED_OPERATIONS = {
    "metadata:read",
    "contents:read",
    "issues:read",
    "issues:write",
    "pull_requests:read",
    "actions:read",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def canonical_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def parse_time(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate(receipt: dict[str, Any], request: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected = {
        "schema_version": "1.0.0",
        "request_id": request["request_id"],
        "decision": "ALLOW_CAPABILITY_LEASE",
        "request_hash": canonical_hash(request),
        "credentials_recorded": False,
        "protected_values_recorded": False,
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            errors.append(f"mismatch:{key}")

    scope = receipt.get("scope")
    if not isinstance(scope, dict):
        errors.append("missing:scope")
    else:
        if scope.get("repository_pattern") != "Admissible-Existence/*":
            errors.append("scope:repository_pattern")
        operations = scope.get("operations")
        if not isinstance(operations, list) or not operations:
            errors.append("scope:operations")
        elif not set(operations).issubset(ALLOWED_OPERATIONS):
            errors.append("scope:operation_exceeds_request")

    bindings = receipt.get("bindings")
    expected_bindings = {
        "repository": os.environ.get("GITHUB_REPOSITORY", "Admissible-Existence/.github"),
        "workflow": ".github/workflows/principle-completeness-workers.yml",
        "ref": os.environ.get("GITHUB_REF", "refs/heads/main"),
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
        "workflow_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
    }
    if not isinstance(bindings, dict):
        errors.append("missing:bindings")
    else:
        for key, value in expected_bindings.items():
            if value is not None and str(bindings.get(key)) != str(value):
                errors.append(f"binding:{key}")

    try:
        issued = parse_time(str(receipt["issued_at"]))
        expires = parse_time(str(receipt["expires_at"]))
        now = dt.datetime.now(dt.timezone.utc)
        if issued > now:
            errors.append("time:not_yet_valid")
        if expires <= now:
            errors.append("time:expired")
        if (expires - issued).total_seconds() > int(request["lease"]["maximum_ttl_seconds"]):
            errors.append("time:ttl_exceeds_request")
    except Exception:
        errors.append("time:invalid")

    for key in ("policy_hash", "revocation_reference"):
        if not isinstance(receipt.get(key), str) or not receipt[key]:
            errors.append(f"missing:{key}")
    if isinstance(receipt.get("policy_hash"), str) and not receipt["policy_hash"].startswith("sha256:"):
        errors.append("invalid:policy_hash")

    authority = receipt.get("authority", {})
    if authority.get("credential_custody") != "StegVerse-Labs/TV":
        errors.append("authority:credential_custody")
    if authority.get("grant_authority") != "StegVerse-Labs/TVC":
        errors.append("authority:grant_authority")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--output", default="reports/tvc-worker-capability-validation.json")
    args = parser.parse_args()
    request = load(REQUEST)
    receipt = load(Path(args.receipt))
    errors = validate(receipt, request)
    result = {
        "schema_version": "1.0.0",
        "request_id": request["request_id"],
        "valid": not errors,
        "errors": errors,
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
