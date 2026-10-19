#!/usr/bin/env python3
"""Dispatch one epoch-requiring ledger writer with the supplied epoch.

The in-tree dispatcher behind .github/workflows/ledger-writer-dispatch.yml,
declared in resident-runtime/activation-manifest.json. The epoch is checked by
the kernel's shared rule before anything is invoked; an absent or invalid one
is the six-field FAIL_CLOSED and nothing runs. The writer then receives it as
--hb-epoch and keeps its own refusal logic. It carries no authority.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RETRY_ENTRYPOINT = "ledger-writer-dispatch.yml workflow_dispatch input hb_epoch"
#: Every epoch-requiring writer the manifest binds to this dispatcher.
WRITERS = {
    "repository-ledger-emit": ".stegverse/transition-ledger/emit.py",
    "organization-ledger-aggregate": "resident-runtime/aggregate_repo_transition.py",
    "organization-egress": "resident-runtime/organization_egress_boundary.py",
    "intr-destination-ingress": "resident-runtime/intr_destination_ingress.py",
}

_spec = importlib.util.spec_from_file_location("kernel", ROOT / "org-kernel" / "kernel.py")
kernel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kernel)


def command(writer: str, hb_epoch: str | None, arguments: str = "") -> list[str]:
    """The writer's argv, or SystemExit carrying the six-field refusal."""
    refusal = kernel.writer_epoch_refusal(hb_epoch or None, retry_entrypoint=RETRY_ENTRYPOINT)
    if refusal is not None:
        print(json.dumps(refusal, sort_keys=True))
        raise SystemExit(1)
    extra = shlex.split(arguments or "")
    if any(item == "--hb-epoch" or item.startswith("--hb-epoch=") or
           (item.startswith("--hb-ep") and "--hb-epoch".startswith(item.split("=", 1)[0])) for item in extra):
        print(json.dumps({
            "disposition": "FAIL_CLOSED", "failure_code": "HB_EPOCH_CONFLICT",
            "failed_predicate": kernel.HB_EPOCH_PREDICATE,
            "detail": "an epoch was passed in arguments as well as the hb_epoch input",
            "required_evidence_or_repair": "supply the epoch only as the hb_epoch input",
            "retry_entrypoint": RETRY_ENTRYPOINT, "owning_existing_goal": kernel.HB_EPOCH_OWNING_EXISTING_GOAL,
            "next_attempt": "dispatch again without --hb-epoch in arguments; no writer was invoked",
            "derived_from_clock": False, "consequence_committed": False}, sort_keys=True))
        raise SystemExit(1)
    return [sys.executable, WRITERS[writer], *extra, "--hb-epoch", str(hb_epoch)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    parser.add_argument("--writer", required=True, choices=sorted(WRITERS))
    parser.add_argument("--hb-epoch", default=None)
    parser.add_argument("--arguments", default="")
    args = parser.parse_args()
    return subprocess.run(command(args.writer, args.hb_epoch, args.arguments), cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
