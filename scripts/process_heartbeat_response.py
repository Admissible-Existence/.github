#!/usr/bin/env python3
import argparse
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "data" / "heartbeat-response-node.json"
RECEIPTS = ROOT / "data" / "heartbeat-response-receipts"
AUTH_KEYS = ("execution", "activation", "publication", "custody", "release")
EPOCH_RETRY_ENTRYPOINT = "scripts/process_heartbeat_response.py --apply --hb-epoch"

_spec = importlib.util.spec_from_file_location("org_kernel", ROOT / "org-kernel" / "kernel.py")
kernel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kernel)


def canonical_sha256(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_json(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def authority_is_false(value):
    return all(value.get(key) is False for key in AUTH_KEYS)


def select_message(batch, organization):
    matches = [item for item in batch.get("messages", []) if item.get("destination_org") == organization]
    if len(matches) != 1:
        raise ValueError(f"expected one canonical message for {organization}, found {len(matches)}")
    message = matches[0]
    if message.get("stage") != "SENT":
        raise ValueError("canonical inbound message is not SENT")
    if not authority_is_false(message.get("authority", {})):
        raise ValueError("inbound heartbeat attempts to grant authority")
    return message


def make_receipts(message, config, hb):
    """The received/responded pair. `hb` is the supplied epoch's heartbeat
    reference; `observed_at` is its heartbeat id and no clock is read."""
    organization = config["organization"]
    digest = canonical_sha256(message)
    common = {
        "schema_version": "1.0.0",
        "exchange_id": message["exchange_id"],
        "node_org": organization,
        "source_org": message["source_org"],
        "destination_org": organization,
        "hb_reference": hb,
        "observed_at": hb["heartbeat_id"],
        "observed_message_sha256": digest,
        "authority": {key: False for key in AUTH_KEYS},
    }
    received = {
        **common,
        "message_id": f"{message['message_id']}-received",
        "stage": "RECEIVED",
        "detail_class": message["detail_class"],
        "classification": {
            "primary": message["detail_class"],
            "retention": message.get("retention_class", "EPHEMERAL"),
            "action_admitted": False,
            "awareness_updated": True,
        },
    }
    responded = {
        **common,
        "message_id": f"{message['message_id']}-responded",
        "stage": "RESPONDED",
        "detail_class": config.get("response_detail_class", "CAPABILITY"),
        "classification": {
            "primary": config.get("response_detail_class", "CAPABILITY"),
            "supported_detail_classes": config["supported_detail_classes"],
            "node_state": "RESPONSIVE",
            "return_to": message["source_org"],
            "action_admitted": False,
        },
        "parent_receipt_sha256": canonical_sha256(received),
    }
    return received, responded


def validate_local(config):
    if not config.get("organization") or not config.get("outbox_url"):
        raise ValueError("node configuration incomplete")
    if not authority_is_false(config.get("authority", {})):
        raise ValueError("node configuration attempts to grant transport authority")
    if RECEIPTS.exists():
        for path in RECEIPTS.glob("*.json"):
            item = load_json(path)
            if item.get("node_org") != config["organization"]:
                raise ValueError(f"foreign node receipt in {path}")
            if item.get("stage") not in {"RECEIVED", "RESPONDED", "RECOVERED", "REPEAT", "BLOCKED", "FAILED", "REVIEW_REQUIRED"}:
                raise ValueError(f"invalid receipt stage in {path}")
            if not authority_is_false(item.get("authority", {})):
                raise ValueError(f"receipt attempts to grant authority in {path}")


class NodeRefused(RuntimeError):
    """A six-field FAIL_CLOSED of the node, printed by the CLI."""

    def __init__(self, refusal):
        super().__init__(refusal["failure_code"])
        self.refusal = refusal


def _refusal(failure_code, failed_predicate, detail, repair, next_attempt, *, terminal):
    return {"disposition": "FAIL_CLOSED", "failure_code": failure_code, "failed_predicate": failed_predicate,
            "detail": detail, "required_evidence_or_repair": repair, "retry_entrypoint": EPOCH_RETRY_ENTRYPOINT,
            "owning_existing_goal": kernel.HB_EPOCH_OWNING_EXISTING_GOAL, "next_attempt": next_attempt,
            "terminal": terminal, "derived_from_clock": False}


def _write_once(path, document):
    """Write a receipt atomically, or keep an identical one. A different one is never overwritten."""
    rendered = json.dumps(document, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if load_json(path) == document:
            return
        raise NodeRefused(_refusal(
            "HB_RECEIPT_PAIR_PARTIAL_AT_ANOTHER_EPOCH", "ONE_EXCHANGE_BINDS_ONE_RECEIPT_PAIR",
            f"{path.name} is already written with different content",
            "complete the pair with the same epoch and outbox message the written receipt was made from",
            "the written receipt is not mutated; nothing was written for this attempt", terminal=False))
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(rendered, encoding="utf-8")
    os.replace(temporary, path)


def apply(config, hb_epoch=None):
    try:
        with urlopen(config["outbox_url"], timeout=20) as response:
            batch = json.load(response)
    except OSError as exc:
        raise NodeRefused(_refusal(
            "HB_OUTBOX_FETCH_FAILED", "OUTBOX_IS_READABLE", (type(exc).__name__ + ": " + str(exc))[:512],
            "the outbox URL answers", "run again; nothing was written", terminal=False)) from None
    except ValueError as exc:
        batch = exc
    try:
        if isinstance(batch, Exception) or not isinstance(batch, dict):
            raise ValueError("outbox is not a JSON object" if not isinstance(batch, Exception)
                             else type(batch).__name__ + ": " + str(batch))
        message = select_message(batch, config["organization"])
        missing = [key for key in ("exchange_id", "message_id", "source_org", "detail_class")
                   if not isinstance(message.get(key), str)]
        if missing:
            raise ValueError("message lacks string " + ", ".join(missing))
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        # The outbox is this node's input: a malformed one is terminal and nothing is written.
        raise NodeRefused({**_refusal(
            "HB_OUTBOX_INVALID", "OUTBOX_CARRIES_ONE_SENT_MESSAGE_FOR_THIS_NODE", str(exc)[:512],
            "the outbox is a JSON object with one SENT, authority-free message for this organization",
            "nothing was written; the outbox is corrected upstream", terminal=True),
            "consequence_committed": False}) from None
    prefix = message["exchange_id"].replace("/", "-")
    received_path = RECEIPTS / f"{prefix}.received.json"
    responded_path = RECEIPTS / f"{prefix}.responded.json"
    if received_path.exists() and responded_path.exists():
        print(f"HB_NODE_CURRENT:{config['organization']}:{message['exchange_id']}")
        return
    # Receipts are about to be written: they reference the supplied epoch, and
    # an absent or invalid one is refused (SuppliedEpochRefused) before the
    # receipt directory is created. A run with nothing to write needs none.
    hb = kernel.supplied_hb_reference(hb_epoch, retry_entrypoint=EPOCH_RETRY_ENTRYPOINT)
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    received, responded = make_receipts(message, config, hb)
    # A run torn between the two writes completes the pair at the same epoch.
    for path, document in ((received_path, received), (responded_path, responded)):
        _write_once(path, document)
    print(f"HB_NODE_RESPONDED:{config['organization']}:{message['exchange_id']}")


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--hb-epoch", default=None,
                        help="supplied heartbeat epoch (ASCII digits >= 32); never derived from a clock")
    args = parser.parse_args()
    config = load_json(CONFIG)
    validate_local(config)
    if args.apply:
        try:
            apply(config, args.hb_epoch)
        except (kernel.SuppliedEpochRefused, NodeRefused) as refused:
            print(json.dumps(refused.refusal, indent=2, sort_keys=True))
            sys.exit(1)
        except Exception as exc:
            # A torn write is six fields and exit 1, never a traceback.
            refusal = kernel.writer_cli_refusal(exc, failure_code="HB_RESPONSE_WRITE_FAILED",
                                                retry_entrypoint=EPOCH_RETRY_ENTRYPOINT)
            if refusal is None:
                raise
            print(json.dumps(refusal, indent=2, sort_keys=True))
            sys.exit(1)
        validate_local(config)
    elif args.check:
        print(f"HB_NODE_CHECK_PASS:{config['organization']}")
    else:
        parser.error("choose --apply or --check")


if __name__ == "__main__":
    main()
