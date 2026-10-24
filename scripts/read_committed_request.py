#!/usr/bin/env python3
"""Read a committed transition request and gate its supplied epoch (B-P40 COMMITTED_REQUEST).

A writer workflow starts from a push that commits a request file, never from a
manual dispatch or a clock. The request is the writer's only input: it names
the transition and supplies the heartbeat epoch. This reads it once, before
anything is written, and either prints the values the writer needs (and
appends them to $GITHUB_OUTPUT when that is set) or prints a six-field
FAIL_CLOSED refusal and exits 1:

* the file missing, unreadable, not UTF-8, not one JSON object, carrying a
  non-finite number, or a field that is missing, not an identifier, not one of
  its declared choices, or not one line of text: COMMITTED_REQUEST_INVALID
  (terminal);
* no `hb_epoch`: HB_EPOCH_NOT_SUPPLIED;
* an `hb_epoch` the shared rule refuses: HB_EPOCH_INVALID.

The epoch is checked by the kernel's shared supplied-epoch rule
(`kernel.supplied_epoch_failure`), so this gate and the writers cannot
disagree about what an epoch is. No clock is read. The request
file's sha256 is printed so the writer binds it into what it records.

A workflow passes the request on to its writer as STEGVERSE_COMMITTED_REQUEST_PATH
and STEGVERSE_COMMITTED_REQUEST_SHA256; the writer records `recorded()`,
`committed_request {path, sha256, hb_epoch_source: COMMITTED_REQUEST}`, on
everything it writes.
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
DIGEST = re.compile(r"[0-9a-f]{64}")
REQUEST_PATH_ENV = "STEGVERSE_COMMITTED_REQUEST_PATH"
REQUEST_SHA256_ENV = "STEGVERSE_COMMITTED_REQUEST_SHA256"
#: One line of text: no control character can end a $GITHUB_OUTPUT line.
TEXT = re.compile(r"[^\x00-\x1f\x7f]{0,4096}")


def _shared_rule():
    spec = importlib.util.spec_from_file_location("committed_request_kernel", ROOT / "org-kernel" / "kernel.py")
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


def _field_failure(value: dict, field: str, *, required: bool, choices: tuple[str, ...] = (),
                   text: bool = False) -> str | None:
    if field not in value and not required:
        return None
    item = value.get(field)
    if not isinstance(item, str):
        return field + " is missing or not a string"
    if choices:
        return None if item in choices else field + " is not one of " + ", ".join(choices)
    if text:
        return None if TEXT.fullmatch(item) else field + " is not one line of text (at most 4096 characters)"
    return None if FIELD.fullmatch(item) else field + " is not an identifier ([A-Za-z0-9._:-]{1,128})"


def read(request: Path, required: tuple[str, ...], *, choices: dict[str, tuple[str, ...]] | None = None,
         optional_text: tuple[str, ...] = ()) -> tuple[dict | None, dict | None]:
    """(values, None) for a request that passes, or (None, six-field refusal).

    `required` fields are identifiers; `choices` fields must be one of their
    declared values; `optional_text` fields, when present, are one line of
    text and are output empty when absent.
    """
    choices = choices or {}
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
    checks = [(field, {"required": True}) for field in required]
    checks += [(field, {"required": True, "choices": options}) for field, options in choices.items()]
    checks += [(field, {"required": False, "text": True}) for field in optional_text]
    for field, check in checks:
        failure = _field_failure(value, field, **check)
        if failure is not None:
            return None, refusal("COMMITTED_REQUEST_INVALID", REQUEST_PREDICATE, failure,
                                 "commit " + name + " with a valid " + field, name, terminal=True)
    if "hb_epoch" not in value:
        return None, refusal("HB_EPOCH_NOT_SUPPLIED", EPOCH_PREDICATE,
                             name + " declares no hb_epoch and no clock is read",
                             "commit " + name + " with hb_epoch: ASCII digits >= 32", name, terminal=False)
    failure = _shared_rule()(value["hb_epoch"])
    if failure is not None:
        code, detail = failure
        return None, refusal(code, EPOCH_PREDICATE, detail,
                             "commit " + name + " with hb_epoch: ASCII digits >= 32", name, terminal=False)
    values = {field: value[field] for field in (*required, *choices)}
    values.update({field: value.get(field, "") for field in optional_text})
    values["hb_epoch"] = str(value["hb_epoch"])
    values["request_sha256"] = hashlib.sha256(raw).hexdigest()
    return values, None


def recorded(environ=None) -> tuple[dict | None, dict | None]:
    """(committed_request, None) for a writer to record, (None, None) outside a
    committed-request run, or (None, six-field refusal) for a half-set or
    malformed one, which the writer raises before anything is written."""
    environ = os.environ if environ is None else environ
    path, digest = environ.get(REQUEST_PATH_ENV) or "", environ.get(REQUEST_SHA256_ENV) or ""
    if not path and not digest:
        return None, None
    if not path or TEXT.fullmatch(path) is None or DIGEST.fullmatch(digest) is None:
        return None, refusal("COMMITTED_REQUEST_INVALID", "COMMITTED_REQUEST_DIGEST_IS_RECORDED",
                             REQUEST_PATH_ENV + " and " + REQUEST_SHA256_ENV + " must both be set, to the request's "
                             "path and its lowercase hex sha256",
                             "pass the gate's request path and request_sha256 to the writer", path or "the request",
                             terminal=True)
    return {"path": path, "sha256": digest, "hb_epoch_source": "COMMITTED_REQUEST"}, None


def _carries_committed_request(value) -> bool:
    """Whether `value` has a committed_request key at any depth (iteratively, so
    a deep document cannot exhaust the stack, and once per container, so a
    cyclic in-process value cannot loop)."""
    pending, seen = [value], set()
    while pending:
        item = pending.pop()
        if isinstance(item, (dict, list, tuple)):
            if id(item) in seen:
                continue
            seen.add(id(item))
        if isinstance(item, dict):
            if "committed_request" in item:
                return True
            pending.extend(item.values())
        elif isinstance(item, (list, tuple)):
            pending.extend(item)
    return False


def bind(evidence, argument: str, environ=None) -> tuple[dict | None, dict | None]:
    """(evidence with committed_request set from `recorded()`, None), or (None, refusal).

    Only the run's own request sets committed_request: evidence a caller
    supplies that carries the key at any depth is a forged provenance and is
    refused six-field COMMITTED_REQUEST_INVALID before anything is written.
    """
    if _carries_committed_request(evidence):
        return None, refusal("COMMITTED_REQUEST_INVALID", "COMMITTED_REQUEST_IS_SET_ONLY_FROM_THE_RUN",
                             argument + " carries committed_request; only the run's own committed request sets it",
                             "remove committed_request from " + argument, argument, terminal=True)
    request, refused = recorded(environ)
    if refused is not None:
        return None, refused
    evidence = dict(evidence)
    if request is not None:
        evidence["committed_request"] = request
    return evidence, None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--require", action="append", default=[],
                        help="an identifier field the request must carry, besides hb_epoch")
    parser.add_argument("--choice", action="append", default=[], metavar="FIELD=A,B,...",
                        help="a field the request must carry with one of these values")
    parser.add_argument("--optional-text", action="append", default=[],
                        help="a field the request may carry as one line of text; empty when absent")
    args = parser.parse_args(argv)
    choices = {}
    for item in args.choice:
        field, _, options = item.partition("=")
        if not field or not options:
            parser.error("--choice takes FIELD=A,B,...")
        choices[field] = tuple(options.split(","))
    values, refused = read(args.request, tuple(args.require), choices=choices,
                           optional_text=tuple(args.optional_text))
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
