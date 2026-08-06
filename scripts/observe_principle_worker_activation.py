#!/usr/bin/env python3
"""Observe hosted activation evidence for the principle-completeness worker.

The observer reads GitHub Actions metadata only. It never resolves, accepts, logs,
or persists a protected credential. It emits a sanitized machine-readable receipt
that distinguishes absent, running, failed, incomplete-evidence, and complete
hosted worker states.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WORKFLOW_ID = 328874742
REPAIR_COMMIT = "e7be2c5c7aea62cf7b9ef50731208f6883ac1dfc"
REQUIRED_ARTIFACT = "principle-completeness-worker-status"
REQUIRED_REPORTS = {
    "reports/formalism-worker-status-latest.json",
    "reports/formalism-worker-status-latest.md",
}


def request_json(url: str, token: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "admissible-existence-principle-worker-observer",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        raise ValueError("github_response_not_object")
    return value


def classify(repository: str, token: str) -> dict[str, Any]:
    base = f"https://api.github.com/repos/{repository}"
    runs = request_json(f"{base}/actions/workflows/{WORKFLOW_ID}/runs?per_page=20", token)
    candidates = [
        row
        for row in runs.get("workflow_runs", [])
        if isinstance(row, dict) and row.get("head_sha") != "4d7941c7c7c20b4aff88332d1de26fbe669c4620"
    ]
    result: dict[str, Any] = {
        "schema_version": "1.0.0",
        "task_id": "AEX-PC-AUTOMATED-WORKERS-001",
        "workflow_id": WORKFLOW_ID,
        "repair_commit": REPAIR_COMMIT,
        "observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "credentials_recorded": False,
        "protected_values_recorded": False,
    }
    if not candidates:
        result.update(
            state="BLOCKED_NO_POST_REPAIR_RUN",
            next_action="Generate an authorized workflow event or wait for the scheduled trigger.",
        )
        return result

    run = candidates[0]
    result.update(
        run_id=run.get("id"),
        run_attempt=run.get("run_attempt"),
        head_sha=run.get("head_sha"),
        run_status=run.get("status"),
        run_conclusion=run.get("conclusion"),
        run_url=run.get("html_url"),
    )
    if run.get("status") != "completed":
        result.update(state="RETRY_RUN_IN_PROGRESS", next_action="Observe the same run after completion.")
        return result

    artifacts = request_json(f"{base}/actions/runs/{run['id']}/artifacts?per_page=100", token)
    names = sorted(
        artifact.get("name")
        for artifact in artifacts.get("artifacts", [])
        if isinstance(artifact, dict) and isinstance(artifact.get("name"), str)
    )
    result["artifact_names"] = names

    contents = set()
    for path in REQUIRED_REPORTS:
        try:
            request_json(f"{base}/contents/{path}?ref=main", token)
            contents.add(path)
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
    result["persisted_reports"] = sorted(contents)

    if run.get("conclusion") not in {"success", "failure"}:
        result.update(state="FAILED_HOSTED_RUN", next_action="Inspect the run jobs and logs.")
    elif REQUIRED_ARTIFACT not in names:
        result.update(
            state="REVIEW_REQUIRED_MISSING_ARTIFACT",
            next_action="Repair the first failed step before artifact upload.",
        )
    elif contents != REQUIRED_REPORTS:
        result.update(
            state="REVIEW_REQUIRED_REPORTS_NOT_PERSISTED",
            next_action="Repair report persistence and rerun.",
        )
    else:
        result.update(
            state="COMPLETE_READ_ONLY_WORKER_EVIDENCE",
            next_action="Advance to the TV/TVC-governed apply invocation.",
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", "Admissible-Existence/.github"))
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    parser.add_argument("--output", default="reports/principle-worker-activation-observation.json")
    args = parser.parse_args()
    if not args.token:
        print("missing GitHub token", file=sys.stderr)
        return 2
    try:
        result = classify(args.repository, args.token)
    except Exception as exc:
        result = {
            "schema_version": "1.0.0",
            "task_id": "AEX-PC-AUTOMATED-WORKERS-001",
            "workflow_id": WORKFLOW_ID,
            "state": "FAILED_OBSERVER_REQUEST",
            "error": type(exc).__name__,
            "next_action": "Inspect observer logs and restore metadata access.",
            "credentials_recorded": False,
            "protected_values_recorded": False,
            "observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["state"] == "COMPLETE_READ_ONLY_WORKER_EVIDENCE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
