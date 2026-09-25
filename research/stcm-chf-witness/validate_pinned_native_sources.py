#!/usr/bin/env python3
"""Run two *independent*, pinned native-source baselines on existing ephemeral CI.

Not a shared-specimen test, SDK manifest call, governed execution or physical witness.
Never modifies original repositories or dispatches a WorkerCoordinator claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTRACT = json.loads((HERE / "native-source-validation-contract.json").read_text())


def digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def run(command: list[str], cwd: Path, timeout: int = 180):
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                            timeout=timeout, check=False)
    return {
        "returncode": result.returncode,
        "stdout_sha256": digest(result.stdout.encode("utf-8")),
        "stderr_sha256": digest(result.stderr.encode("utf-8")),
        "stdout_tail": result.stdout[-1200:],
        "stderr_tail": result.stderr[-1200:],
    }


def check_source(root: Path, spec: dict) -> dict:
    if not root.is_dir():
        raise ValueError("pinned checkout absent")
    head = run(["git", "rev-parse", "HEAD"], root)
    if head["returncode"] != 0:
        raise ValueError("source HEAD not readable")
    source_sha = head["stdout_tail"].strip()
    if source_sha != spec["commit"]:
        raise ValueError("source commit differs from exact pinned commit")
    blobs = {}
    for name, required_sha in spec["blob_guards"].items():
        path = (root / name).resolve()
        if not path.is_file() or not path.is_relative_to(root.resolve()):
            raise ValueError("pinned source file absent or escapes checkout: " + name)
        actual = run(["git", "hash-object", name], root)
        if actual["returncode"] != 0 or actual["stdout_tail"].strip() != required_sha:
            raise ValueError("source blob differs from pinned original: " + name)
        blobs[name] = {"git_blob_sha1": required_sha,
                       "sha256_original_bytes": digest(path.read_bytes())}
    return {"repository": spec["repo"], "exact_commit": source_sha,
            "verified_blob_sources": blobs}


def assess_stcm(root: Path, spec: dict) -> dict:
    result = check_source(root, spec)
    native = run([sys.executable, spec["entry"]], root)
    result["native_execution"] = native
    path = root / spec["report"]
    if path.is_file():
        raw = path.read_bytes()
        observed = json.loads(raw)
        result["native_report_sha256"] = digest(raw)
        result["unexpected_count"] = observed.get("total_unexpected")
        result["observed_layers"] = sorted((observed.get("layers") or {}).keys())
    else:
        result["native_report_sha256"] = None
        result["unexpected_count"] = None
        result["observed_layers"] = []
    result["baseline_validation_pass"] = (
        native["returncode"] == 0
        and result["unexpected_count"] == 0
        and {"lineage", "closure"}.issubset(result["observed_layers"])
    )
    return result


def assess_chf(root: Path, spec: dict) -> dict:
    result = check_source(root, spec)
    results = {}
    for path in spec["checks"]:
        if not (root / path).is_file():
            raise ValueError("expected native CHF checker missing: " + path)
        results[path] = run([sys.executable, path], root)
    result["native_checks"] = results
    result["baseline_validation_pass"] = (
        len(results) == 6 and all(r["returncode"] == 0 for r in results.values())
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stcm-root", required=True, type=Path)
    parser.add_argument("--chf-root", type=Path, help="Use only the authorized existing CHF owner source root")
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    report = {
        "schema": "admissible-existence.stcm-chf.pinned-native-source-validation-report/v1",
        "goal_task_id": "STCM-CHF-THERMODYNAMIC-WITNESS-COMPARISON-001",
        "authority_effect": "NONE",
        "classification": "PINNED_NATIVE_SOURCE_BASELINES_ONLY",
        "common_specimen_executed": False,
        "sdk_manifest_execution_observed": False,
        "external_witness_observed": False,
        "physical_heat_measured": False,
        "authenticated_resident_execution_observed": False,
    }
    failures = []
    for kind, root, assessor in (
        ("STCM", args.stcm_root, assess_stcm),
        *((("CHF", args.chf_root, assess_chf),) if args.chf_root else ()),
    ):
        try:
            report[kind] = assessor(root.resolve(), CONTRACT[kind.lower()])
            if not report[kind]["baseline_validation_pass"]:
                failures.append(kind + "_NATIVE_VALIDATION_FAILED")
        except (ValueError, OSError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
            report[kind] = {"baseline_validation_pass": False,
                            "error_class": type(exc).__name__, "reason": str(exc)}
            failures.append(kind + "_SOURCE_OR_EXECUTION_FAILED")
    if args.chf_root is None:
        report["CHF"] = {"baseline_validation_pass": False,
            "classification": "NATIVE_SOURCE_EXECUTION_NOT_OBSERVED",
            "reason": "private CHF source requires its own authorized native repository CI",
            "native_owner": "Admissible-Existence/CHF"}
    report["source_baselines_complete"] = args.chf_root is not None
    report["scoped_validation_pass"] = not failures
    report["failure_classes"] = failures
    report["source_baselines_pass"] = not failures and args.chf_root is not None
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"source_baselines_pass": report["source_baselines_pass"],
                      "scoped_validation_pass": report["scoped_validation_pass"],
                      "failure_classes": failures,
                      "report": str(args.report)}, sort_keys=True))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
