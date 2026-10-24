#!/usr/bin/env python3
"""Read a committed transition request and gate its supplied epoch (B-P40 COMMITTED_REQUEST).

A writer workflow starts from a push that commits a request file, never from a
manual dispatch or a clock. The request is the writer's only input: it names
the transition and supplies the heartbeat epoch. This reads it once, before
anything is written, and either prints the values the writer needs (and
appends them to $GITHUB_OUTPUT when that is set) or prints a six-field
FAIL_CLOSED refusal and exits 1:

* the file missing, unreadable, not UTF-8, not one JSON object, or carrying a
  non-finite number: COMMITTED_REQUEST_INVALID (terminal);
* no `hb_epoch`: HB_EPOCH_NOT_SUPPLIED;
* an `hb_epoch` the shared rule refuses: HB_EPOCH_INVALID.

The epoch is checked by the shared supplied-epoch rule
(`organization_egress_boundary.supplied_epoch_failure`), so this gate and the
writers cannot disagree about what an epoch is. No clock is read. The request
file's sha256 is printed so the writer binds it into what it records.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNING_GOAL = "INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001"
EPOCH_PREDICATE = "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH"
REQUEST_PREDICATE = "COMMITTED_REQUEST_IS_ONE_READABLE_JSON_OBJECT"
FIELD = re.compile(r"[A-Za-z0-9._:-]{1,128}")


def _shared_rule():
    spec = importlib.util.spec_from_file_location(
        "committed_request_egress", ROOT / "resident-runtime" / "organization_egress_boundary.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.supplied_epoch_failure


def _non_finite(token: str) -> float:
    raise ValueError("non-finite number " + token + " is not JSON")


def _finite(token: str) -> float:
    value = float(token)
    if value != value or value in (float("inf"), float("-inf")):
        _non_finite(token)
    return value


def refusal(code: str, predicate: str, detail: str, repair: str, request: str, *, terminal: bool) -> dict:
    return {"disposition": "FAIL_CLOSED", "failure_code": code, "failed_predicate": predicate,
            "detail": detail[:512], "required_evidence_or_repair": repair,
            "retry_entrypoint": "commit a corrected " + request + " to main",
            "owning_existing_goal": OWNING_GOAL,
            "next_attempt": "nothing was written; the next commit of the request runs the writer again",
            "terminal": terminal, "derived_from_clock": False, "consequence_committed": False,
            "authority_effect": "NONE_REFUSAL_ONLY"}


def read(request: Path, required: tuple[str, ...]) -> tuple[dict | None, dict | None]:
    """(values, None) for a request that passes, or (None, six-field refusal)."""
    name = str(request)
    try:
        raw = request.read_bytes()
        value = json.loads(raw.decode("utf-8"), parse_constant=_non_finite, parse_float=_finite)
    except (OSError, UnicodeDecodeError, ValueError, RecursionError, MemoryError) as error:
        return None, refusal("COMMITTED_REQUEST_INVALID", REQUEST_PREDICATE,
                             type(error).__name__ + ": " + str(error),
                             "commit " + name + " as one readable UTF-8 JSON object", name, terminal=True)
    if not isinstance(value, dict):
        return None, refusal("COMMITTED_REQUEST_INVALID", REQUEST_PREDICATE,
                             "top-level " + type(value).__name__ + " is not a JSON object",
                             "commit " + name + " as one readable UTF-8 JSON object", name, terminal=True)
    for field in required:
        if not isinstance(value.get(field), str) or FIELD.fullmatch(value[field]) is None:
            return None, refusal("COMMITTED_REQUEST_INVALID", REQUEST_PREDICATE,
                                 field + " is missing or not an identifier ([A-Za-z0-9._:-]{1,128})",
                                 "commit " + name + " with a string " + field, name, terminal=True)
    if "hb_epoch" not in value:
        return None, refusal("HB_EPOCH_NOT_SUPPLIED", EPOCH_PREDICATE,
                             name + " declares no hb_epoch and no clock is read",
                             "commit " + name + " with hb_epoch: ASCII digits >= 32", name, terminal=False)
    failure = _shared_rule()(value["hb_epoch"])
    if failure is not None:
        code, detail = failure
        return None, refusal(code, EPOCH_PREDICATE, detail,
                             "commit " + name + " with hb_epoch: ASCII digits >= 32", name, terminal=False)
    values = {field: value[field] for field in required}
    values["hb_epoch"] = str(value["hb_epoch"])
    values["request_sha256"] = hashlib.sha256(raw).hexdigest()
    return values, None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--require", action="append", default=[],
                        help="a string field the request must carry, besides hb_epoch")
    args = parser.parse_args(argv)
    values, refused = read(args.request, tuple(args.require))
    if refused is not None:
        print(json.dumps(refused, sort_keys=True))
        return 1
    print(json.dumps(values, sort_keys=True))
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as stream:
            for key, value in sorted(values.items()):
                stream.write(key + "=" + value + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
