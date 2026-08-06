#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKERS = ROOT / "data/formalism-worker-registry.json"
ROUTING = ROOT / "data/cross-repository-remediation-registry.json"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def classify(entry: dict) -> tuple[str, str]:
    role = entry["role"]
    state = entry["worker_state"]
    if role == "coordination":
        return "CONTROL_PLANE", "Maintain coordination records and observe execution."
    if state == "validated_complete_notify_only":
        return "COMPLETE_NOTIFY_ONLY", "Preserve completion evidence; notify only for separately admitted propagation or regression."
    if state == "source_complete_integration_pending":
        return "INTEGRATION_NOTIFY_ONLY", "Preserve completed source evidence and continue only the named integration or destination-admission task."
    if state == "machine_owned_observe_only":
        return "OBSERVE_NOTIFY_ONLY", "Observe canonical machine-owned work; do not duplicate implementation."
    if role == "empty":
        return "DISPOSITION_REQUIRED", "Create implementation, deprecation, or migration disposition."
    if role == "source":
        return "DIRECT_SOURCE_UPDATE", "Create or validate source formalism, mathematics, proof-candidate, evidence, and handoff artifacts."
    if role == "support":
        return "DIRECT_SUPPORT_UPDATE", "Create or validate support boundary, coverage map, contract, evidence, and handoff artifacts."
    return "REVIEW_REQUIRED", "Unknown role requires review."


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="reports/cross-repository-remediation-latest.json")
    args = parser.parse_args()
    workers = load(WORKERS)
    routing = load(ROUTING)
    rows = []
    counts: dict[str, int] = {}
    for entry in workers["repositories"]:
        action, next_action = classify(entry)
        counts[action] = counts.get(action, 0) + 1
        rows.append({
            "repository": entry["repository"],
            "role": entry["role"],
            "worker_state": entry["worker_state"],
            "routing_state": action,
            "next_action": next_action,
            "owner": entry["repository"] if action.startswith("DIRECT_") or action in {"DISPOSITION_REQUIRED", "INTEGRATION_NOTIFY_ONLY"} else "Admissible-Existence/.github",
            "completion_evidence": entry.get("completion_evidence"),
        })
    report = {
        "schema_version": "1.2.0",
        "goal_id": routing["goal_id"],
        "parent_goal_id": routing["parent_goal_id"],
        "counts": counts,
        "repositories": rows,
        "immediate_dependencies": routing["immediate_dependencies"],
        "conditional_propagation": routing["conditional_propagation"],
        "propagation_gate": routing["propagation_gate"],
        "complete": all(row["routing_state"] in {"CONTROL_PLANE", "OBSERVE_NOTIFY_ONLY", "COMPLETE_NOTIFY_ONLY"} for row in rows),
    }
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
