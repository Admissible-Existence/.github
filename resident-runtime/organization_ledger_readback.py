#!/usr/bin/env python3
"""Read the organization ledger back and verify it, independently of the writer.

The evidence of an append is a read of the ledger, not the writer's own
report. This opens the location it is given. For the designated ref, that
location is a fresh fetch of ``refs/stegverse/organization-ledger``. It walks
the chain from HEAD and checks, for every organization receipt:

- ``receipt_sha256`` is the digest of its own body;
- ``previous_receipt_sha256`` names the receipt before it, ending at genesis
  (null), so the chain has no gaps and no forks;
- the repository receipt it consumed is retained under ``source-receipts/``
  and verifies against its own body.

Given a closure result, it also checks that the named repository and
organization receipts are in their chains and that both carry the result's
``communication_id``.

The repository chain is the subtree named by ``--repository-namespace``. That
walk reads repository receipts only.

Authority and time are constraint variables. A disposition is transition
evidence only. This module writes nothing.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RETRY = "resident-runtime/organization_ledger_readback.py::main"
GOAL = "ADMISSIBLE-EXISTENCE-ORGANIZATION-LEDGER"
CONSTRAINT = "CONSTRAINT_VARIABLE"
DISPOSITION_ROLE = "TRANSITION_EVIDENCE_ONLY"
CONSTRAINT_FIELDS = {
    "routing_authority_constraint": CONSTRAINT,
    "admission_authority_constraint": CONSTRAINT,
    "execution_authority_constraint": CONSTRAINT,
    "time_constraint": CONSTRAINT,
    "disposition_role": DISPOSITION_ROLE,
}


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ledger_store = _load("ledger_store_readback", "resident-runtime/ledger_store.py")


def canon(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(value) -> str:
    return "sha256:" + hashlib.sha256(canon(value)).hexdigest()


class ReadbackRefused(Exception):
    def __init__(self, failed_predicate, detail):
        super().__init__(failed_predicate + ": " + detail)
        self.failed_predicate = failed_predicate
        self.detail = detail


def self_verifies(document) -> bool:
    if not isinstance(document, dict):
        return False
    body = {key: value for key, value in document.items() if key != "receipt_sha256"}
    return document.get("receipt_sha256") == sha(body)


def _chain(store):
    head = store.get(ledger_store.HEAD_KEY)
    if not isinstance(head, dict) or not head.get("receipt_sha256"):
        raise ReadbackRefused("ORGANIZATION_LEDGER_HEAD_PRESENT", "no HEAD")
    chain, cursor, seen = [], head["receipt_sha256"], set()
    while cursor is not None:
        if cursor in seen:
            raise ReadbackRefused("ORGANIZATION_LEDGER_CHAIN_IS_ACYCLIC", str(cursor))
        seen.add(cursor)
        receipt = store.get(ledger_store.receipt_key(cursor))
        if not isinstance(receipt, dict):
            raise ReadbackRefused("ORGANIZATION_LEDGER_CHAIN_IS_COMPLETE", "missing " + str(cursor))
        if receipt.get("receipt_sha256") != cursor or not self_verifies(receipt):
            raise ReadbackRefused("ORGANIZATION_RECEIPT_VERIFIES_AGAINST_ITS_BODY", str(cursor))
        chain.append(receipt)
        cursor = receipt.get("previous_receipt_sha256")
    chain.reverse()
    return head, chain


def _source_ok(store, receipt) -> None:
    source_digest = receipt.get("source_transition_sha256")
    source = store.get(ledger_store.source_key(source_digest)) if isinstance(source_digest, str) else None
    if source is None or source.get("receipt_sha256") != source_digest or not self_verifies(source):
        raise ReadbackRefused("SOURCE_RECEIPT_RETAINED_AND_VERIFIES", str(source_digest))
    if receipt.get("repo_receipt_sha256") != source_digest:
        raise ReadbackRefused("ORGANIZATION_RECEIPT_PRESERVES_REPOSITORY_RECEIPT", str(source_digest))


def repository_readback(location, namespace):
    locator = ledger_store.parse_locator(location)
    repository_location = str(locator) + ":" + namespace
    store = ledger_store.open_store(repository_location)
    head, chain = _chain(store)
    for receipt in chain:
        if receipt.get("schema") != "stegverse.repo-transition-receipt/v1":
            raise ReadbackRefused("REPOSITORY_CHAIN_READS_REPOSITORY_RECEIPTS_ONLY",
                                  str(receipt.get("schema")))
    return {
        "location": repository_location,
        "namespace": namespace,
        "head_receipt_sha256": head["receipt_sha256"],
        "chain_length": len(chain),
        "genesis_receipt_sha256": chain[0]["receipt_sha256"],
        "chain": [{
            "receipt_sha256": receipt["receipt_sha256"],
            "previous_receipt_sha256": receipt.get("previous_receipt_sha256"),
            "transition_id": receipt.get("transition_id"),
            "transition_class": receipt.get("transition_class"),
            "communication_id": (receipt.get("evidence") or {}).get("communication_id"),
        } for receipt in chain],
        "every_receipt_verifies_against_its_body": True,
        "replay_read_organization_receipts": False,
        "receipts": chain,
    }


def readback(location, closure_result=None, repository_namespace=None):
    store = ledger_store.open_store(ledger_store.parse_locator(location))
    head, chain = _chain(store)
    for receipt in chain:
        if receipt.get("schema") != "stegverse.organization-transition-receipt/v1":
            raise ReadbackRefused("ORGANIZATION_CHAIN_READS_ORGANIZATION_RECEIPTS_ONLY",
                                  str(receipt.get("schema")))
        _source_ok(store, receipt)
    result = {
        "schema": "stegverse.organization-ledger-readback/v1",
        "location": location,
        "disposition": "ALLOW",
        "head_receipt_sha256": head["receipt_sha256"],
        "chain_length": len(chain),
        "genesis_receipt_sha256": chain[0]["receipt_sha256"],
        "chain": [{
            "receipt_sha256": receipt["receipt_sha256"],
            "previous_receipt_sha256": receipt.get("previous_receipt_sha256"),
            "repo_receipt_sha256": receipt.get("repo_receipt_sha256"),
            "repo_transition_id": receipt.get("repo_transition_id"),
            "communication_id": (receipt.get("boundary_evidence") or {}).get("communication_id"),
        } for receipt in chain],
        "every_receipt_verifies_against_its_body": True,
        "every_source_receipt_retained_and_verifies": True,
        "authority_effect": "NONE_READBACK_ONLY",
        **CONSTRAINT_FIELDS,
    }
    repository = None
    if repository_namespace:
        repository = repository_readback(location, repository_namespace)
        published = {key: value for key, value in repository.items() if key != "receipts"}
        result["repository_ledger"] = published
    if closure_result is None:
        return result
    communication_id = closure_result.get("communication_id")
    if not isinstance(communication_id, str) or not communication_id.strip():
        raise ReadbackRefused("CLOSURE_CARRIES_A_COMMUNICATION_ID", repr(communication_id))
    org_digest = closure_result.get("organization_receipt_sha256")
    repo_digest = closure_result.get("repository_receipt_sha256")
    org_receipt = next((receipt for receipt in chain if receipt.get("receipt_sha256") == org_digest), None)
    if org_receipt is None:
        raise ReadbackRefused("CLOSURE_ORGANIZATION_RECEIPT_IS_IN_THE_ORGANIZATION_LEDGER", str(org_digest))
    org_communication = (org_receipt.get("boundary_evidence") or {}).get("communication_id")
    if org_communication != communication_id:
        raise ReadbackRefused("ORGANIZATION_RECEIPT_CARRIES_THE_COMMUNICATION_ID", str(org_communication))
    if closure_result.get("self_closure") is True:
        if (org_receipt.get("boundary_evidence") or {}).get("self_closure") is not True:
            raise ReadbackRefused("ORGANIZATION_RECEIPT_RECORDS_THE_SELF_CLOSURE", str(org_digest))
    if repository is None:
        raise ReadbackRefused("REPOSITORY_LEDGER_NAMESPACE_SUPPLIED", "closure readback reads both chains")
    repo_receipt = next((receipt for receipt in repository["receipts"]
                         if receipt.get("receipt_sha256") == repo_digest), None)
    if repo_receipt is None:
        raise ReadbackRefused("CLOSURE_REPOSITORY_RECEIPT_IS_IN_THE_REPOSITORY_LEDGER", str(repo_digest))
    repo_communication = (repo_receipt.get("evidence") or {}).get("communication_id")
    if repo_communication != communication_id:
        raise ReadbackRefused("REPOSITORY_RECEIPT_CARRIES_THE_COMMUNICATION_ID", str(repo_communication))
    if org_receipt.get("repo_receipt_sha256") != repo_digest:
        raise ReadbackRefused("ORGANIZATION_RECEIPT_CONSUMES_THE_REPOSITORY_RECEIPT", str(repo_digest))
    if closure_result.get("self_closure") is True and (repo_receipt.get("evidence") or {}).get("self_closure") is not True:
        raise ReadbackRefused("REPOSITORY_RECEIPT_RECORDS_THE_SELF_CLOSURE", str(repo_digest))
    result.update({
        "closure_communication_id": communication_id,
        "closure_repository_receipt_sha256": repo_digest,
        "closure_organization_receipt_sha256": org_digest,
        "closure_repository_receipt_in_chain": True,
        "closure_organization_receipt_in_chain": True,
        "closure_receipts_carry_communication_id": True,
    })
    return result


def _refusal(location, exc):
    return {
        "schema": "stegverse.organization-ledger-readback/v1",
        "location": location,
        "disposition": "FAIL_CLOSED",
        "failure_code": "ORGANIZATION_LEDGER_READBACK_FAILED",
        "failed_predicate": getattr(exc, "failed_predicate", "ORGANIZATION_LEDGER_READS_BACK"),
        "required_evidence_or_repair": getattr(exc, "detail", str(exc)),
        "retry_entrypoint": RETRY,
        "owning_existing_goal": GOAL,
        "next_attempt": "fetch the ledger ref again and rerun the readback; nothing is written by it",
        "authority_effect": "NONE_READBACK_ONLY",
        **CONSTRAINT_FIELDS,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--location", required=True, help="ledger locator, for example git+<repo>#<ref>")
    parser.add_argument("--repository-namespace", default=None,
                        help="also read the repository chain kept in this subtree of the same ref")
    parser.add_argument("--closure-result", type=Path, default=None,
                        help="a self-closure result whose receipts and communication_id must be in the chains")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    try:
        # The closure result and the ledger read back are untrusted input; a
        # deeply nested one (RecursionError) is refused like any other.
        closure = json.loads(args.closure_result.read_text(encoding="utf-8")) if args.closure_result else None
        result, code = readback(args.location, closure, args.repository_namespace), 0
    except (ReadbackRefused, ValueError, RuntimeError, FileNotFoundError, OSError,
            RecursionError, MemoryError) as exc:
        result, code = _refusal(args.location, exc), 1
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    sys.exit(main())
