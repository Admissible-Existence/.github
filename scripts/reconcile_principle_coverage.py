#!/usr/bin/env python3
"""Reconcile a partial live audit with the authoritative organization registry.

This script never upgrades a repository to complete. It ensures every repository
known to the organization mathematical registry remains visible even when the
workflow token cannot inspect private repositories.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "organization-mathematics-registry.yaml"
LIVE = ROOT / "reports" / "principle-completeness-latest.json"
OUTPUT = ROOT / "reports" / "principle-completeness-reconciled.json"
SUMMARY = ROOT / "reports" / "principle-completeness-reconciled.md"


def main() -> int:
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    live = json.loads(LIVE.read_text(encoding="utf-8"))

    expected = registry["repositories"]
    live_by_repo = {item["repository"]: item for item in live.get("repositories", [])}
    reconciled: list[dict[str, Any]] = []

    for row in expected:
        repository = row["repository"]
        observed = live_by_repo.get(repository)
        if observed is not None:
            item = dict(observed)
            item["visibility"] = "LIVE_OBSERVED"
            item["registry_maturity"] = row.get("mathematics_maturity", "UNASSESSED")
            item["registry_proof_candidate_status"] = row.get("proof_candidate_status", "NONE")
        else:
            item = {
                "repository": repository,
                "role": row["role"],
                "state": "BLOCKED",
                "score": 0.0,
                "visibility": "REGISTRY_ONLY_NOT_LIVE_OBSERVED",
                "registry_maturity": row.get("mathematics_maturity", "UNASSESSED"),
                "registry_proof_candidate_status": row.get("proof_candidate_status", "NONE"),
                "dimensions": {},
                "principles": [],
                "metrics": {"live_observed": False},
                "findings": [
                    {
                        "severity": "error",
                        "code": "REPOSITORY_NOT_VISIBLE_TO_WORKFLOW_TOKEN",
                        "detail": "Repository is preserved from the authoritative organization registry but was not available to the live audit token.",
                    }
                ],
                "next_task": {
                    "owner": "Admissible-Existence/.github",
                    "target": "organization audit credential or repository-specific validation lane",
                    "action": "Provide machine-readable repository evidence through an authorized lane; do not treat missing visibility as success",
                    "release_condition": "Repository tree, handoff, principle/support registry, validators, and evidence are live-observed or imported with immutable bindings",
                },
            }
        reconciled.append(item)

    expected_names = {row["repository"] for row in expected}
    unexpected = sorted(set(live_by_repo) - expected_names)
    state_counts: dict[str, int] = {}
    for item in reconciled:
        state_counts[item["state"]] = state_counts.get(item["state"], 0) + 1

    result = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "goal_id": "AEX-PRINCIPLE-COMPLETENESS-001",
        "expected_repository_count": len(expected),
        "live_observed_repository_count": len(live_by_repo),
        "reconciled_repository_count": len(reconciled),
        "coverage_complete": len(live_by_repo) == len(expected) and not unexpected,
        "unexpected_live_repositories": unexpected,
        "state_counts": state_counts,
        "repositories": reconciled,
        "publication_authorized": False,
        "release_authorized": False,
        "completion_rule": "Registry-only visibility is BLOCKED and cannot establish completeness.",
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Reconciled Principle Completeness Coverage",
        "",
        f"- Expected repositories: **{result['expected_repository_count']}**",
        f"- Live-observed repositories: **{result['live_observed_repository_count']}**",
        f"- Reconciled repositories: **{result['reconciled_repository_count']}**",
        f"- Full live coverage: **{str(result['coverage_complete']).lower()}**",
        "- Publication authorized: **false**",
        "",
        "| Repository | Visibility | State | Registry maturity | Proof candidate |",
        "|---|---|---|---|---|",
    ]
    for item in reconciled:
        lines.append(
            f"| `{item['repository']}` | {item['visibility']} | {item['state']} | "
            f"{item['registry_maturity']} | {item['registry_proof_candidate_status']} |"
        )
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "expected": result["expected_repository_count"],
        "observed": result["live_observed_repository_count"],
        "reconciled": result["reconciled_repository_count"],
        "coverage_complete": result["coverage_complete"],
    }, sort_keys=True))
    return 0 if result["coverage_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
