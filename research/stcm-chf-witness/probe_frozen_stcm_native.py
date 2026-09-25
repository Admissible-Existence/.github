#!/usr/bin/env python3
"""Source-only exact-specimen invocation of ORIGINAL pinned STCM gated_close.

A synthetic fixture carries no independently retained predecessor. The only
BOUND case below constructs an explicitly synthetic prior to test the existing
callable's positive path. No resulting verdict is a real transition receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from pathlib import Path

import yaml

from validate_pinned_native_sources import CONTRACT, check_source, digest
from validate_inert_comparison import check_specimen

HERE = Path(__file__).resolve().parent
FROZEN_BYTES = b'{"synthetic":"source-v0"}\n'
STCM_SUBDIR = "tools/closure-harness"


def _plain(value):
    return getattr(value, "value", value)


def make_inputs(specimen: dict, *, construct_test_prior: bool):
    """Map only fixture-declared values; mark every added test-only field."""
    declared = specimen["transition"]
    prior_digest = declared.get("predecessor_receipt_sha256")
    claimed_id = "FIXTURE_CONSTRUCTED_PRIOR_NOT_AN_AUTHENTIC_RECEIPT"
    transition = {
        "is_genesis": False,
        "claimed_prior_receipt_id": claimed_id,
        "claimed_prior_receipt_hash": prior_digest,
        "prior_receipt": None,
        "sequence_index": 1,
        "result_receipt_id": "FIXTURE_CONSTRUCTED_RESULT_NOT_RETAINED",
    }
    if construct_test_prior:
        # Deliberately synthetic. Never substitute this object for real custody.
        transition["prior_receipt"] = {
            "id": claimed_id, "hash": prior_digest, "sequence_index": 0,
            "closed": True, "superseded_by": None,
        }
    record = {
        "risk_tier": "low", "transition_type": "synthetic_computational_change",
        "incoming_receipts": {
            "completeness_level": 1,
            "complete": True if construct_test_prior else None,
        },
        "result": {
            "resulting_state": specimen["resulting_state"]["sha256"],
            "decision": "ALLOW" if construct_test_prior else None,
        },
    }
    return record, transition


def native_evaluation(stcm_root: Path, specimen: dict, *, construct_test_prior: bool):
    import_path = (stcm_root / STCM_SUBDIR).resolve()
    sys.path.insert(0, str(import_path))
    try:
        # Original, pinned repository code, not a reimplementation.
        gate = importlib.import_module("lineage_gate")
        policy = yaml.safe_load((import_path / "completeness_policy.yaml").read_text())
        record, transition = make_inputs(
            specimen, construct_test_prior=construct_test_prior
        )
        result = gate.gated_close(record, policy, transition)
    finally:
        sys.path.remove(str(import_path))
    return {
        "native_entry": "tools/closure-harness/lineage_gate.py::gated_close",
        "native_lineage_verdict": _plain(result.lineage.verdict),
        "native_lineage_reason": result.lineage.reason_code,
        "native_closure_invoked": result.closure is not None,
        "native_closure_verdict": (
            _plain(result.closure.verdict) if result.closure is not None else None
        ),
        "native_closure_reason": (
            result.closure.reason_code if result.closure is not None else None
        ),
        "native_closed": result.closed,
        "fixture_constructed_prior": construct_test_prior,
        "authentic_predecessor_present": False,
        "source_native_run_class": "INERT_SYNTHETIC_TEST_ONLY",
    }


def compare(stcm_root: Path, specimen: dict, *, construct_test_prior: bool):
    specimen_bytes = json.dumps(
        specimen, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    record = {
        "schema": "admissible-existence.stcm-chf.frozen-specimen-native-probe/v1",
        "authority_effect": "NONE",
        "specimen_id": specimen["specimen_id"],
        "specimen_json_sha256": digest(specimen_bytes),
        "original_source_sha256": digest(FROZEN_BYTES),
        "stcm_source_commit": CONTRACT["stcm"]["commit"],
        "chf_source_commit": CONTRACT["chf"]["commit"],
        "sdk_native_math_manifest_invocation": "NOT_ESTABLISHED",
        "chf_native_same_specimen_result": "NOT_ESTABLISHED",
        "third_party_technical_export": "NOT_RECEIVED",
        "independent_physical_measurement": "NOT_OBSERVED",
        "authentic_resident_execution": "NOT_OBSERVED",
        "master_records_closure": "NOT_OBSERVED",
        "same_specimen_two_native_results": False,
    }
    eligibility = check_specimen(specimen, FROZEN_BYTES)
    record["precheck"] = eligibility
    if eligibility == "DENY_SPECIMEN_MISMATCH":
        record["stcm"] = {"classification": "NOT_INVOKED_AFTER_HASH_DENIAL"}
    elif eligibility == "UNKNOWN_CAUSAL_RELATION":
        record["stcm"] = native_evaluation(
            stcm_root, specimen, construct_test_prior=False
        )
    elif eligibility.startswith("INERT_"):
        record["stcm"] = native_evaluation(
            stcm_root, specimen, construct_test_prior=construct_test_prior
        )
    else:
        record["stcm"] = {
            "classification": "NOT_INVOKED_AFTER_PRECHECK",
            "reason": eligibility,
        }
    record["comparison_disposition"] = (
        "DENY_SOURCE_HASH" if eligibility == "DENY_SPECIMEN_MISMATCH"
        else "UNKNOWN_NO_SHARED_NATIVE_CHF_PROCESSOR"
    )
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stcm-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    stcm_root = args.stcm_root.resolve()
    check_source(stcm_root, CONTRACT["stcm"])
    cases = {}
    for label, name, constructed in [
        ("synthetic_constructed_positive", "positive_synthetic", True),
        ("synthetic_missing_authentic_predecessor", "positive_synthetic", False),
        ("coincident_timestamp_no_causal_proof", "coincident_timestamps_no_causal_proof", False),
        ("incorrect_original_source_bytes", "specimen_digest_mismatch", False),
    ]:
        fixture = json.loads((HERE / "fixtures" / (name + ".json")).read_text())
        cases[label] = compare(
            stcm_root, fixture, construct_test_prior=constructed
        )
    assert cases["synthetic_constructed_positive"]["stcm"]["native_lineage_verdict"] == "BOUND"
    assert cases["synthetic_constructed_positive"]["stcm"]["native_closed"] is True
    assert cases["synthetic_missing_authentic_predecessor"]["stcm"]["native_lineage_verdict"] == "MISSING_PRIOR"
    assert cases["synthetic_missing_authentic_predecessor"]["stcm"]["native_closed"] is False
    assert cases["coincident_timestamp_no_causal_proof"]["stcm"]["native_lineage_verdict"] == "MISSING_PRIOR"
    assert cases["coincident_timestamp_no_causal_proof"]["stcm"]["native_closed"] is False
    assert cases["incorrect_original_source_bytes"]["stcm"]["classification"] == "NOT_INVOKED_AFTER_HASH_DENIAL"
    report = {
        "schema": "admissible-existence.stcm-chf.native-synthetic-one-sided-probe/v1",
        "authority_effect": "NONE",
        "pin_and_blob_validation": "PASS",
        "stcm_native_callable_invoked": True,
        "chf_native_same_specimen_callable": "NOT_ESTABLISHED",
        "dual_native_comparison_validated": False,
        "cases": cases,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "case_count": len(cases),
        "classification": "INERT_STCM_NATIVE_POSITIVE_AND_ADVERSARIAL",
        "chf_same_specimen": "NOT_ESTABLISHED",
        "report": str(args.output),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
