#!/usr/bin/env python3
"""Validate the formalism archive-transfer registry.

A record may be ARCHIVE_READY only when it contains a complete assignment,
worker acknowledgment, zero source-session dependency, and the required
confirmation language. Earlier states are also checked for structural validity.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "formalism-archive-transfer-registry.json"

VALID_STATES = (
    "NOT_TRANSFERRED",
    "ASSIGNED",
    "ACKNOWLEDGED",
    "ARCHIVE_READY",
)
REQUIRED_FIELDS = {
    "task_id",
    "worker_id",
    "destination_repository",
    "handoff_path",
    "assigned_task",
    "completion_percent",
    "state",
    "worker_acknowledged",
    "source_session_dependency",
    "confirmation_line",
}


def fail(message: str) -> bool:
    print(f"FAIL {message}", file=sys.stderr)
    return False


def nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_record(record: object, index: int) -> bool:
    if not isinstance(record, dict):
        return fail(f"record {index} is not an object")

    missing = sorted(REQUIRED_FIELDS - set(record))
    if missing:
        return fail(f"record {index} missing fields: {', '.join(missing)}")

    label = str(record.get("task_id", f"record-{index}"))
    ok = True

    for field in (
        "task_id",
        "worker_id",
        "destination_repository",
        "handoff_path",
        "assigned_task",
        "confirmation_line",
    ):
        if not nonempty_string(record.get(field)):
            ok = fail(f"{label}: {field} must be a non-empty string") and ok

    state = record.get("state")
    if state not in VALID_STATES:
        ok = fail(f"{label}: invalid state {state!r}") and ok

    completion = record.get("completion_percent")
    if not isinstance(completion, int) or isinstance(completion, bool) or not 0 <= completion <= 100:
        ok = fail(f"{label}: completion_percent must be an integer from 0 to 100") and ok

    acknowledged = record.get("worker_acknowledged")
    dependency = record.get("source_session_dependency")
    if not isinstance(acknowledged, bool):
        ok = fail(f"{label}: worker_acknowledged must be boolean") and ok
    if not isinstance(dependency, bool):
        ok = fail(f"{label}: source_session_dependency must be boolean") and ok

    state_rank = VALID_STATES.index(state) if state in VALID_STATES else -1
    if state_rank >= VALID_STATES.index("ACKNOWLEDGED") and acknowledged is not True:
        ok = fail(f"{label}: ACKNOWLEDGED or later requires worker acknowledgment") and ok

    if state == "ARCHIVE_READY":
        if dependency is not False:
            ok = fail(f"{label}: ARCHIVE_READY requires source_session_dependency=false") and ok
        confirmation = str(record.get("confirmation_line", ""))
        worker_id = str(record.get("worker_id", ""))
        task_id = str(record.get("task_id", ""))
        required_fragments = (
            "Repository Coordination Authority has registered worker",
            worker_id,
            f"assigned task {task_id}",
            "no longer references the originating session",
            "authoritative source for continuation",
        )
        for fragment in required_fragments:
            if fragment not in confirmation:
                ok = fail(f"{label}: confirmation_line missing required fragment: {fragment}") and ok

    return ok


def main() -> int:
    if not REGISTRY_PATH.exists():
        fail(f"missing registry: {REGISTRY_PATH.relative_to(ROOT)}")
        return 1

    try:
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"could not read registry: {exc}")
        return 1

    ok = True
    if registry.get("valid_states") != list(VALID_STATES):
        ok = fail("registry valid_states does not match canonical order") and ok
    if registry.get("required_transition_order") != list(VALID_STATES):
        ok = fail("required_transition_order does not match canonical order") and ok

    records = registry.get("records")
    if not isinstance(records, list) or not records:
        ok = fail("records must be a non-empty list") and ok
    else:
        task_ids: set[str] = set()
        worker_task_pairs: set[tuple[str, str]] = set()
        for index, record in enumerate(records):
            ok = validate_record(record, index) and ok
            if isinstance(record, dict):
                task_id = str(record.get("task_id", ""))
                worker_id = str(record.get("worker_id", ""))
                if task_id in task_ids:
                    ok = fail(f"duplicate task_id: {task_id}") and ok
                task_ids.add(task_id)
                pair = (worker_id, task_id)
                if pair in worker_task_pairs:
                    ok = fail(f"duplicate worker/task pair: {worker_id}/{task_id}") and ok
                worker_task_pairs.add(pair)

    if ok:
        print(f"PASS formalism archive gate: {len(records)} records validated")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
