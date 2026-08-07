#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKERS_PATH = ROOT / "data" / "formalism-worker-registry.json"
REMEDIATION_PATH = ROOT / "data" / "cross-repository-remediation-registry.json"
REPORT_PATH = ROOT / "reports" / "support-completion-activation-latest.json"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def bump_minor(version: str) -> str:
    major, minor, _patch = (int(part) for part in version.split("."))
    return f"{major}.{minor + 1}.0"


def evidence_files() -> list[Path]:
    return sorted((ROOT / "data").glob("*-completion-evidence.json"))


def compact_evidence(path: Path, evidence: dict) -> dict:
    validation = evidence.get("validation", {})
    return {
        "normalized_evidence": str(path.relative_to(ROOT)),
        "handoff": evidence.get("handoff"),
        "handoff_commit": evidence.get("handoff_commit"),
        "issue": evidence.get("issue"),
        "validation_run": validation.get("run_id"),
        "validation_job": validation.get("job_id"),
        "validation_conclusion": validation.get("conclusion"),
        "artifact_id": validation.get("artifact_id"),
        "artifact_digest": validation.get("artifact_digest"),
        "creates_authority": evidence.get("boundaries", {}).get("creates_authority", False),
        "commits_execution": evidence.get("boundaries", {}).get("commits_execution", False),
    }


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


def main() -> int:
    workers = load(WORKERS_PATH)
    remediation = load(REMEDIATION_PATH)
    by_repo = {row["repository"]: row for row in workers["repositories"]}
    completed = {row["repository"]: row for row in remediation.get("completed_repositories", [])}
    changes = []

    for path in evidence_files():
        evidence = load(path)
        repo = evidence.get("repository")
        if evidence.get("role") != "support" or evidence.get("state") != "VALIDATED_COMPLETE_NOTIFY_ONLY":
            continue
        row = by_repo.get(repo)
        if not row or row.get("role") != "support":
            continue
        if evidence.get("boundaries", {}).get("creates_authority") is True:
            raise SystemExit(f"{repo}: completion evidence may not create authority")
        validation = evidence.get("validation", {})
        if validation.get("conclusion") != "success":
            raise SystemExit(f"{repo}: hosted validation conclusion must be success")
        if not evidence.get("handoff") or not evidence.get("handoff_commit"):
            raise SystemExit(f"{repo}: handoff evidence incomplete")

        if row.get("worker_state") != "validated_complete_notify_only":
            row["worker_state"] = "validated_complete_notify_only"
            row["completion_evidence"] = compact_evidence(path, evidence)
            changes.append(repo)

        completed[repo] = {
            "repository": repo,
            "state": "COMPLETE_NOTIFY_ONLY",
            "source_handoff": f"{repo}@main:{evidence['handoff']}",
            "handoff_commit": evidence["handoff_commit"],
            "issue": evidence.get("issue"),
            "hosted_run": validation.get("run_id"),
            "hosted_job": validation.get("job_id"),
            "hosted_conclusion": validation.get("conclusion"),
            "artifact_id": validation.get("artifact_id"),
            "artifact_digest": validation.get("artifact_digest"),
            "normalized_evidence": str(path.relative_to(ROOT)),
        }

    if changes:
        workers["schema_version"] = bump_minor(workers["schema_version"])
        remediation["schema_version"] = bump_minor(remediation["schema_version"])
        remediation["completed_repositories"] = list(completed.values())
        counts = classify_counts(workers)
        remediation["summary"].update(counts)
        workers_text = json.dumps(workers, indent=2, sort_keys=False) + "\n"
        remediation_text = json.dumps(remediation, indent=2, sort_keys=False) + "\n"
        WORKERS_PATH.write_text(workers_text, encoding="utf-8")
        REMEDIATION_PATH.write_text(remediation_text, encoding="utf-8")
    else:
        counts = classify_counts(workers)

    report = {
        "schema_version": "admissible_existence.support_completion_activation.v1",
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
