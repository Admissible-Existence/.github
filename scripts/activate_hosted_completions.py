#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKERS_PATH = ROOT / "data" / "formalism-worker-registry.json"
REMEDIATION_PATH = ROOT / "data" / "cross-repository-remediation-registry.json"
REPORT_PATH = ROOT / "reports" / "hosted-completion-activation-latest.json"
SOURCE_STATE = "implementation_complete_hosted_validation_blocked"
TARGET_STATE = "validated_complete_notify_only"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def bump_minor(version: str) -> str:
    major, minor, _patch = (int(part) for part in version.split("."))
    return f"{major}.{minor + 1}.0"


def evidence_files() -> list[Path]:
    return sorted((ROOT / "data").glob("*-hosted-completion-evidence.json"))


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
        elif state == TARGET_STATE:
            counts["validated_complete_notify_only"] += 1
        elif state == "source_complete_integration_pending":
            counts["source_complete_integration_pending"] += 1
        elif state == SOURCE_STATE:
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
        "handoff": evidence["handoff"],
        "handoff_commit": evidence["handoff_commit"],
        "validation_run": evidence["validation_run"],
        "validation_job": evidence["validation_job"],
        "validation_conclusion": evidence["validation_conclusion"],
        "workflow": evidence["workflow"],
        "validated_checks": evidence["validated_checks"],
        "artifact_policy": evidence.get("artifact_policy", "unspecified"),
        "artifact_id": evidence.get("artifact_id"),
        "artifact_digest": evidence.get("artifact_digest"),
        "receipt": evidence.get("receipt"),
        "receipt_commit": evidence.get("receipt_commit"),
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
        row = by_repo.get(repo)
        if not row or row.get("worker_state") != SOURCE_STATE:
            continue
        if evidence.get("complete") is not True:
            raise SystemExit(f"{repo}: hosted completion evidence must be complete")
        if evidence.get("validation_conclusion") != "success":
            raise SystemExit(f"{repo}: hosted validation conclusion is not success")
        if not isinstance(evidence.get("validation_run"), int) or not isinstance(evidence.get("validation_job"), int):
            raise SystemExit(f"{repo}: hosted run/job IDs are required")
        if not evidence.get("validated_checks"):
            raise SystemExit(f"{repo}: validated checks are required")
        for required in ("handoff", "handoff_commit", "workflow"):
            if not evidence.get(required):
                raise SystemExit(f"{repo}: missing {required}")
        boundaries = evidence.get("boundaries", {})
        forbidden_true = [key for key, value in boundaries.items() if value is True]
        if forbidden_true:
            raise SystemExit(f"{repo}: completion evidence creates forbidden authority: {forbidden_true}")
        artifact_policy = evidence.get("artifact_policy")
        if artifact_policy == "required" and (not evidence.get("artifact_id") or not evidence.get("artifact_digest")):
            raise SystemExit(f"{repo}: required artifact evidence is missing")
        if artifact_policy not in {"required", "none_by_workflow_design"}:
            raise SystemExit(f"{repo}: artifact policy must be required or none_by_workflow_design")

        row["worker_state"] = TARGET_STATE
        row["completion_evidence"] = compact_evidence(path, evidence)
        changes.append(repo)
        completed[repo] = {
            "repository": repo,
            "state": "COMPLETE_NOTIFY_ONLY",
            "source_handoff": f"{repo}@main:{evidence['handoff']}",
            "handoff_commit": evidence["handoff_commit"],
            "validation_run": evidence["validation_run"],
            "validation_job": evidence["validation_job"],
            "validation_conclusion": "success",
            "workflow": evidence["workflow"],
            "artifact_policy": artifact_policy,
            "artifact_id": evidence.get("artifact_id"),
            "artifact_digest": evidence.get("artifact_digest"),
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
        "schema_version": "admissible_existence.hosted_completion_activation.v1",
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
