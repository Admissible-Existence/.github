#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKERS_PATH = ROOT / "data" / "formalism-worker-registry.json"
REMEDIATION_PATH = ROOT / "data" / "cross-repository-remediation-registry.json"
REPORT_PATH = ROOT / "reports" / "repository-disposition-activation-latest.json"
ALLOWED_STATES = {"DEPRECATED_NOTIFY_ONLY", "MIGRATED_NOTIFY_ONLY"}
ALLOWED_DISPOSITIONS = {"DEPRECATE", "MIGRATE"}


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def bump_minor(version: str) -> str:
    major, minor, _patch = (int(part) for part in version.split("."))
    return f"{major}.{minor + 1}.0"


def evidence_files() -> list[Path]:
    return sorted((ROOT / "data").glob("*-disposition-evidence.json"))


def classify_counts(workers: dict) -> dict[str, int]:
    counts = {
        "control_plane": 0,
        "direct_source_update_remaining": 0,
        "direct_support_update_remaining": 0,
        "disposition_required": 0,
        "machine_owned_observe_only": 0,
        "validated_complete_notify_only": 0,
        "source_complete_integration_pending": 0,
        "implementation_complete_hosted_validation_blocked": 0,
    }
    for row in workers["repositories"]:
        role = row["role"]
        state = row["worker_state"]
        if role == "coordination":
            counts["control_plane"] += 1
        elif state == "validated_complete_notify_only":
            counts["validated_complete_notify_only"] += 1
        elif state == "source_complete_integration_pending":
            counts["source_complete_integration_pending"] += 1
        elif state == "implementation_complete_hosted_validation_blocked":
            counts["implementation_complete_hosted_validation_blocked"] += 1
        elif state == "machine_owned_observe_only":
            counts["machine_owned_observe_only"] += 1
        elif role == "empty":
            counts["disposition_required"] += 1
        elif role == "source":
            counts["direct_source_update_remaining"] += 1
        elif role == "support":
            counts["direct_support_update_remaining"] += 1
    return counts


def compact_evidence(path: Path, evidence: dict) -> dict:
    return {
        "normalized_evidence": str(path.relative_to(ROOT)),
        "disposition": evidence["disposition"],
        "disposition_state": evidence["state"],
        "handoff": evidence["handoff"],
        "handoff_commit": evidence["handoff_commit"],
        "issue": evidence["issue"],
        "receipt": evidence["receipt"],
        "receipt_commit": evidence["receipt_commit"],
        "redirects": evidence.get("redirects", []),
        "unique_artifacts_remaining": evidence.get("unique_artifacts_remaining", 0),
        "creates_authority": False,
        "commits_execution": False,
    }


def main() -> int:
    workers = load(WORKERS_PATH)
    remediation = load(REMEDIATION_PATH)
    by_repo = {row["repository"]: row for row in workers["repositories"]}
    completed = {row["repository"]: row for row in remediation.get("completed_repositories", [])}
    changes: list[str] = []

    for path in evidence_files():
        evidence = load(path)
        repo = evidence.get("repository")
        state = evidence.get("state")
        disposition = evidence.get("disposition")
        if state not in ALLOWED_STATES or disposition not in ALLOWED_DISPOSITIONS:
            continue
        row = by_repo.get(repo)
        if not row or row.get("role") != "empty":
            continue
        if evidence.get("complete") is not True:
            raise SystemExit(f"{repo}: disposition evidence must be complete")
        if evidence.get("unique_artifacts_remaining", 0) != 0:
            raise SystemExit(f"{repo}: unique artifacts remain")
        boundaries = evidence.get("boundaries", {})
        forbidden_true = [key for key, value in boundaries.items() if value is True]
        if forbidden_true:
            raise SystemExit(f"{repo}: disposition evidence creates forbidden authority: {forbidden_true}")
        for required in ("handoff", "handoff_commit", "issue", "receipt", "receipt_commit"):
            if not evidence.get(required):
                raise SystemExit(f"{repo}: missing {required}")
        if disposition == "MIGRATE" and not evidence.get("redirects"):
            raise SystemExit(f"{repo}: migrated disposition requires redirects")

        if row.get("worker_state") != "validated_complete_notify_only":
            row["worker_state"] = "validated_complete_notify_only"
            row["completion_evidence"] = compact_evidence(path, evidence)
            changes.append(repo)

        completed[repo] = {
            "repository": repo,
            "state": "COMPLETE_NOTIFY_ONLY",
            "source_handoff": f"{repo}@main:{evidence['handoff']}",
            "handoff_commit": evidence["handoff_commit"],
            "issue": evidence["issue"],
            "disposition": disposition,
            "receipt": evidence["receipt"],
            "receipt_commit": evidence["receipt_commit"],
            "normalized_evidence": str(path.relative_to(ROOT)),
        }

    counts = classify_counts(workers)
    if changes:
        workers["schema_version"] = bump_minor(workers["schema_version"])
        remediation["schema_version"] = bump_minor(remediation["schema_version"])
        remediation["completed_repositories"] = list(completed.values())
        remediation["summary"].update(counts)
        WORKERS_PATH.write_text(json.dumps(workers, indent=2) + "\n", encoding="utf-8")
        REMEDIATION_PATH.write_text(json.dumps(remediation, indent=2) + "\n", encoding="utf-8")

    report = {
        "schema_version": "admissible_existence.repository_disposition_activation.v1",
        "goal_id": "AEX-CROSS-REPOSITORY-REMEDIATION-001",
        "changes": changes,
        "counts": counts,
        "complete": True,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
