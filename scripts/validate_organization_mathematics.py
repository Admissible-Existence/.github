#!/usr/bin/env python3
"""Validate the Admissible-Existence organization mathematics registry."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "organization-mathematics-registry.yaml"
RECEIPT = ROOT / "reports" / "organization-mathematics-validation.json"

EXPECTED = {
    "Admissible-Existence/.github", "Admissible-Existence/AE", "Admissible-Existence/Existence",
    "Admissible-Existence/RTG", "Admissible-Existence/GTG", "Admissible-Existence/TT",
    "Admissible-Existence/STCM", "Admissible-Existence/ET",
    "Admissible-Existence/learning-transition-governance", "Admissible-Existence/BC",
    "Admissible-Existence/CHF", "Admissible-Existence/RE", "Admissible-Existence/RE-Reduction",
    "Admissible-Existence/DC", "Admissible-Existence/Triad", "Admissible-Existence/GCAT-BCAT",
    "Admissible-Existence/ECAT-ICAT", "Admissible-Existence/IICT", "Admissible-Existence/CTA",
    "Admissible-Existence/HPS", "Admissible-Existence/FI", "Admissible-Existence/DaCo",
    "Admissible-Existence/IW", "Admissible-Existence/standing-proof-formalism",
    "Admissible-Existence/core-lite", "Admissible-Existence/validator",
    "Admissible-Existence/tracker", "Admissible-Existence/telemetry",
    "Admissible-Existence/ae-validation-factory", "Admissible-Existence/ae-validation-research",
    "Admissible-Existence/validation-profile-registry", "Admissible-Existence/SOL",
}
ROLES = {"source", "support", "coordination", "empty"}
MATH_STATUSES = {"UNASSESSED", "THESIS", "DEFINED", "FORMALIZED", "PROOF_CANDIDATE", "PROVED", "SIMULATED", "VALIDATED"}
PROOF_STATUSES = {"NONE", "CANDIDATE", "REVIEW_REQUIRED", "ACCEPTED", "REJECTED", "SUPERSEDED"}


def main() -> int:
    raw = REGISTRY.read_bytes()
    data = yaml.safe_load(raw)
    rows = data.get("repositories", [])
    findings: list[dict[str, object]] = []
    names = [row.get("repository") for row in rows]

    if len(rows) != 32:
        findings.append({"code": "REPOSITORY_COUNT_MISMATCH", "actual": len(rows), "expected": 32})
    if len(names) != len(set(names)):
        findings.append({"code": "DUPLICATE_REPOSITORY"})
    missing = sorted(EXPECTED - set(names))
    extra = sorted(set(names) - EXPECTED)
    if missing:
        findings.append({"code": "MISSING_REPOSITORIES", "repositories": missing})
    if extra:
        findings.append({"code": "UNEXPECTED_REPOSITORIES", "repositories": extra})

    proof_candidates: list[str] = []
    formalized: list[str] = []
    unsupported: list[str] = []
    empty: list[str] = []

    for row in rows:
        repo = row.get("repository", "<missing>")
        required = ["repository", "role", "layer", "intended_mathematics", "mathematics_status", "support_status", "proof_candidate_status", "touched"]
        absent = [key for key in required if key not in row]
        if absent:
            findings.append({"code": "MISSING_FIELDS", "repository": repo, "fields": absent})
            continue
        if row["role"] not in ROLES:
            findings.append({"code": "INVALID_ROLE", "repository": repo, "value": row["role"]})
        if row["mathematics_status"] not in MATH_STATUSES:
            findings.append({"code": "INVALID_MATHEMATICS_STATUS", "repository": repo, "value": row["mathematics_status"]})
        if row["proof_candidate_status"] not in PROOF_STATUSES:
            findings.append({"code": "INVALID_PROOF_STATUS", "repository": repo, "value": row["proof_candidate_status"]})
        if not isinstance(row["intended_mathematics"], list) or not row["intended_mathematics"]:
            findings.append({"code": "MISSING_INTENDED_MATHEMATICS", "repository": repo})
        if row["proof_candidate_status"] != "NONE":
            proof_candidates.append(repo)
        if row["mathematics_status"] in {"FORMALIZED", "PROOF_CANDIDATE", "PROVED", "SIMULATED", "VALIDATED"}:
            formalized.append(repo)
        if row["mathematics_status"] == "UNASSESSED":
            unsupported.append(repo)
        if row["role"] == "empty":
            empty.append(repo)

    receipt = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "registry": str(REGISTRY.relative_to(ROOT)),
        "registry_sha256": hashlib.sha256(raw).hexdigest(),
        "repository_count": len(rows),
        "formalized_or_stronger": sorted(formalized),
        "proof_candidate_repositories": sorted(proof_candidates),
        "unassessed_repositories": sorted(unsupported),
        "empty_repositories": sorted(empty),
        "findings": findings,
        "valid": not findings,
        "authority": {
            "creates_source_mathematical_authority": False,
            "creates_proof_acceptance": False,
            "creates_release_authority": False,
        },
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"valid": receipt["valid"], "repositories": len(rows), "proof_candidate_repositories": proof_candidates}, sort_keys=True))
    return 0 if receipt["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
