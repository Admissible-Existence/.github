#!/usr/bin/env python3
"""Derive durable formalism task states without taking mathematical authority.

Inputs:
  data/formalism-worker-registry.json
  data/formalism-task-claims.json
  reports/formalism-coherence-latest.json (optional)

Output:
  reports/formalism-task-state-latest.json

The dispatcher fails closed: inaccessible or missing evidence becomes BLOCKED or
MISSING. It never marks publication readiness or source mathematics complete.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

STAGES = [
    "inventory",
    "formalism_development",
    "mathematical_validation",
    "coherence_audit",
    "peer_review_preparation",
    "publication_readiness",
    "site_publication_verification",
]


def load_json(path: Path, required: bool = True) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(path)
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def coherence_by_repo(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = report.get("repositories", [])
    if not isinstance(rows, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = row.get("repository") or row.get("name")
        if isinstance(name, str):
            result[name.split("/")[-1]] = row
    return result


def claim_map(claims: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for item in claims.get("tasks", []):
        if not isinstance(item, dict):
            continue
        repo = str(item.get("repository", "")).split("/")[-1]
        stage = str(item.get("stage", ""))
        if repo and stage:
            result[(repo, stage)] = item
    return result


def derive_state(repo: dict[str, Any], stage: str, coherence: dict[str, Any], claim: dict[str, Any] | None) -> dict[str, Any]:
    name = str(repo["name"])
    full_repo = f"Admissible-Existence/{name}"
    evidence: list[str] = []
    issues = coherence.get("issues", []) if isinstance(coherence, dict) else []
    status = str(coherence.get("status", "NOT_OBSERVED")) if coherence else "NOT_OBSERVED"

    if claim:
        evidence.extend(str(x) for x in claim.get("evidence", []) if isinstance(x, str))
        claim_state = str(claim.get("claim_state", "UNCLAIMED"))
        completion = str(claim.get("completion_state", "PARTIAL"))
        next_action = str(claim.get("next_action", "Inspect claim state"))
        next_location = claim.get("next_action_location")
        claimant = claim.get("claimant")
        created = claim.get("claim_created_at")
        expires = claim.get("claim_expires_at")
        release = claim.get("release_condition")
        collision = claim.get("collision_boundary")
    elif status in {"BLOCKED", "FAILED", "ERROR"}:
        claim_state = "BLOCKED"
        completion = "BLOCKED"
        next_action = "Resolve coherence audit blocker and rerun the organization audit"
        next_location = "reports/formalism-coherence-latest.json"
        claimant = "formalism-coherence-audit"
        created = None
        expires = None
        release = "A subsequent audit produces an inspectable non-blocked repository result"
        collision = "Do not create completion claims while repository evidence is unavailable"
    elif stage == "coherence_audit" and status in {"PASS", "REVIEW_REQUIRED"}:
        claim_state = "MACHINE_OWNED"
        completion = "COMPLETE_VALIDATED" if status == "PASS" else "PARTIAL"
        next_action = "Review coherence findings and route unresolved items to source-repository workers"
        next_location = "reports/formalism-coherence-latest.json"
        claimant = "formalism-coherence-audit"
        created = None
        expires = None
        release = "Superseded by the next scheduled audit"
        collision = "Audit findings do not alter source mathematics"
    else:
        claim_state = "UNCLAIMED"
        completion = "MISSING"
        next_action = f"Install or assign the {stage} worker without duplicating an active source-repository lane"
        next_location = full_repo
        claimant = None
        created = None
        expires = None
        release = None
        collision = "Check source handoff and claims registry before implementation"

    if issues:
        evidence.append("reports/formalism-coherence-latest.json")

    return {
        "task_id": f"AEX-{name.upper()}-{stage.upper().replace('_', '-')}",
        "originating_goal": "Automated formalism development, coherence verification, peer review readiness, and Site publication",
        "repository": full_repo,
        "branch": "main",
        "stage": stage,
        "claim_state": claim_state,
        "completion_state": completion,
        "claimant": claimant,
        "claim_created_at": created,
        "claim_expires_at": expires,
        "release_condition": release,
        "collision_boundary": collision,
        "evidence": sorted(set(evidence)),
        "next_action": next_action,
        "next_action_location": next_location,
        "archival_dependency": completion not in {"COMPLETE_VALIDATED", "SUPERSEDED", "MERGED"},
    }


def dispatch(registry: dict[str, Any], claims: dict[str, Any], coherence: dict[str, Any]) -> dict[str, Any]:
    repositories = registry.get("repositories", [])
    if not isinstance(repositories, list) or not repositories:
        raise ValueError("worker registry must contain repositories")
    coherence_map = coherence_by_repo(coherence)
    claims_map = claim_map(claims)
    tasks: list[dict[str, Any]] = []
    for repo in repositories:
        if not isinstance(repo, dict) or not isinstance(repo.get("name"), str):
            raise ValueError("each registry repository requires a name")
        name = repo["name"]
        for stage in STAGES:
            tasks.append(derive_state(repo, stage, coherence_map.get(name, {}), claims_map.get((name, stage))))
    return {
        "schema_version": "1.0.0",
        "generated_at": utc_now(),
        "goal_id": str(registry.get("goal_id", "AEX-FORMALISM-WORKER-PUBLICATION-001")),
        "tasks": tasks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="data/formalism-worker-registry.json")
    parser.add_argument("--claims", default="data/formalism-task-claims.json")
    parser.add_argument("--coherence", default="reports/formalism-coherence-latest.json")
    parser.add_argument("--output", default="reports/formalism-task-state-latest.json")
    args = parser.parse_args()

    registry = load_json(Path(args.registry))
    claims = load_json(Path(args.claims))
    coherence = load_json(Path(args.coherence), required=False)
    output = dispatch(registry, claims, coherence)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(output['tasks'])} tasks to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
