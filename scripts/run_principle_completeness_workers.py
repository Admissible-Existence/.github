#!/usr/bin/env python3
"""Coordinate repository-local principle-completeness workers.

This controller is deliberately bounded. It does not invent source authority or
accept proofs. It inventories each registered repository, refreshes one durable
repository-local worker issue, records finite claims, and reports completion
against the required source/support artifact contracts.

With --apply, GH_TOKEN must have organization repository and issue access.
Without --apply, the controller performs a read-only dry run and still emits a
machine-readable report.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import os
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "formalism-worker-registry.json"
OUTPUT = ROOT / "reports" / "formalism-worker-status-latest.json"
SUMMARY = ROOT / "reports" / "formalism-worker-status-latest.md"
ISSUE_TITLE = "[AEX-PC-WORKER] Complete repository formalism, mathematics, and proof candidates"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_gh(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *args], text=True, capture_output=True, check=check)


def api_json(endpoint: str) -> Any:
    result = run_gh(["api", endpoint])
    return json.loads(result.stdout)


def list_tree(repository: str) -> list[str]:
    repo = api_json(f"repos/{repository}")
    branch = repo["default_branch"]
    tree = api_json(f"repos/{repository}/git/trees/{branch}?recursive=1")
    return sorted(item["path"] for item in tree.get("tree", []) if item.get("type") == "blob")


def matches_any(paths: list[str], pattern: str) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for path in paths)


def newest_handoff(paths: list[str]) -> str | None:
    candidates = [path for path in paths if fnmatch.fnmatch(path, "*_MIRROR_HANDOFF.md") or fnmatch.fnmatch(path, "docs/*_MIRROR_HANDOFF.md")]
    return sorted(candidates)[-1] if candidates else None


def required_for(role: str, registry: dict[str, Any]) -> list[str]:
    if role == "source":
        return list(registry["required_source_artifacts"])
    if role == "support":
        return list(registry["required_support_artifacts"])
    if role == "empty":
        return ["docs/*_MIRROR_HANDOFF.md", "README.md"]
    return []


def issue_body(repository: str, role: str, missing: list[str], handoff: str | None, generated: str) -> str:
    required_text = "\n".join(f"- [ ] `{item}`" for item in missing) or "- [x] Required artifact paths are present; validate contents and evidence."
    return f"""## Automated worker claim

- Goal: `AEX-PRINCIPLE-COMPLETENESS-001`
- Repository: `{repository}`
- Role: `{role}`
- Branch: default branch plus bounded worker branches
- Claim state: `CLAIMED_FOR_IMPLEMENTATION` or `CLAIMED_FOR_VALIDATION`
- Claimant: `Admissible-Existence/.github/.github/workflows/principle-completeness-workers.yml`
- Refreshed: `{generated}`
- Claim release: all required files are substantive, validators and fixtures pass, proof candidates are separately reviewed, and the repository handoff binds the resulting evidence.
- Collision boundary: read the newest handoff and existing claims before mutation; do not overwrite machine-owned or source-authority lanes.

## Current handoff

`{handoff or 'MISSING_HANDOFF'}`

## Required work

{required_text}

## Completion contract

For source repositories, enumerate every principle, express its theory and mathematics, record assumptions, dependencies, falsification conditions, whole-repository role, ecosystem relationships, and candidate proofs where appropriate. Candidate proofs must remain `REVIEW_REQUIRED` until independently reviewed.

For support repositories, formalize validation/support predicates, source coverage, soundness and completeness limits, executable correspondence, and explicit non-authority.

## Report-back requirement

Update the canonical handoff with commits, validation commands, workflow runs, artifacts, receipts, unresolved blockers, and the next executable action. The organization controller will re-inspect this repository and report status to `Admissible-Existence/.github/reports/formalism-worker-status-latest.json`.
"""


def upsert_issue(repository: str, body: str) -> str:
    query = f'repo:{repository} is:issue in:title "[AEX-PC-WORKER]" state:open'
    search = api_json(f"search/issues?q={query.replace(' ', '+')}")
    items = search.get("items", [])
    if items:
        number = items[0]["number"]
        run_gh(["api", f"repos/{repository}/issues/{number}", "-X", "PATCH", "-f", f"body={body}"])
        return f"{repository}#{number}"
    result = run_gh(["api", f"repos/{repository}/issues", "-X", "POST", "-f", f"title={ISSUE_TITLE}", "-f", f"body={body}"])
    return f"{repository}#{json.loads(result.stdout)['number']}"


def inspect_repository(item: dict[str, Any], registry: dict[str, Any], apply: bool) -> dict[str, Any]:
    repository = item["repository"]
    role = item["role"]
    state = item["worker_state"]
    row: dict[str, Any] = {
        "repository": repository,
        "role": role,
        "configured_worker_state": state,
        "claim_state": "UNCLAIMED",
        "completion_state": "NOT_INSPECTED",
        "handoff": None,
        "required": required_for(role, registry),
        "present": [],
        "missing": [],
        "issue": None,
        "findings": [],
        "next_action": None,
    }
    if repository == registry["coordination_repository"]:
        row.update(claim_state="MACHINE_OWNED", completion_state="CONTROL_PLANE", next_action="Continue organization dispatch and evidence reconciliation")
        return row
    if state == "machine_owned_observe_only":
        row.update(claim_state="MACHINE_OWNED", completion_state="OBSERVE_ONLY", next_action="Observe existing machine receipts and repair only the first proven defect")
        return row
    try:
        paths = list_tree(repository)
    except Exception as exc:  # fail closed
        row.update(claim_state="BLOCKED", completion_state="BLOCKED", next_action="Restore authorized repository visibility")
        row["findings"].append({"code": "REPOSITORY_ACCESS_FAILED", "detail": str(exc)[:500]})
        return row

    row["handoff"] = newest_handoff(paths)
    for pattern in row["required"]:
        if matches_any(paths, pattern):
            row["present"].append(pattern)
        else:
            row["missing"].append(pattern)
    if row["missing"]:
        row["claim_state"] = "CLAIMED_FOR_IMPLEMENTATION"
        row["completion_state"] = "PARTIAL" if paths else "EMPTY"
        row["next_action"] = f"Implement {len(row['missing'])} missing required artifact classes and validate contents"
    else:
        row["claim_state"] = "CLAIMED_FOR_VALIDATION"
        row["completion_state"] = "IMPLEMENTED_UNVALIDATED"
        row["next_action"] = "Validate substantive content, evidence paths, proof status, and hosted receipts"

    body = issue_body(repository, role, row["missing"], row["handoff"], now())
    if apply:
        try:
            row["issue"] = upsert_issue(repository, body)
        except Exception as exc:
            row["claim_state"] = "BLOCKED"
            row["findings"].append({"code": "ISSUE_UPSERT_FAILED", "detail": str(exc)[:500]})
    else:
        row["issue"] = "DRY_RUN"
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if args.apply and not os.environ.get("GH_TOKEN"):
        raise SystemExit("GH_TOKEN is required with --apply")
    rows = [inspect_repository(item, registry, args.apply) for item in registry["repositories"]]
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["completion_state"]] = counts.get(row["completion_state"], 0) + 1
    report = {
        "schema_version": "1.0.0",
        "generated_at": now(),
        "goal_id": registry["goal_id"],
        "controller": "Admissible-Existence/.github/scripts/run_principle_completeness_workers.py",
        "apply_mode": args.apply,
        "repository_count": len(rows),
        "state_counts": counts,
        "repositories": rows,
        "archive_permitted": all(row["completion_state"] in {"COMPLETE_VALIDATED", "CONTROL_PLANE", "OBSERVE_ONLY"} for row in rows),
        "completion_rule": "File presence is insufficient; substantive validation and reviewed proof status are required.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# Principle Completeness Worker Status", "", f"Generated: `{report['generated_at']}`", f"Repositories: **{len(rows)}**", f"Archive permitted: **{str(report['archive_permitted']).lower()}**", "", "| Repository | Claim | State | Missing | Issue |", "|---|---|---|---:|---|"]
    for row in rows:
        lines.append(f"| `{row['repository']}` | {row['claim_state']} | {row['completion_state']} | {len(row['missing'])} | {row['issue'] or ''} |")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"repositories": len(rows), "states": counts, "archive_permitted": report["archive_permitted"]}, sort_keys=True))
    return 0 if report["archive_permitted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
