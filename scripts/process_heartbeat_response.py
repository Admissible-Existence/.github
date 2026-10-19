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
    received = make_received(message, config, hb)
    return received, make_responded(received, config)


COMMON_FIELDS = ("schema_version", "exchange_id", "node_org", "source_org", "destination_org",
                 "hb_reference", "observed_at", "observed_message_sha256", "authority")


def make_responded(received, config):
    """The responded receipt, from its received receipt alone: the same epoch,
    exchange and observed message. A torn pair is completed from it."""
    common = {key: received[key] for key in COMMON_FIELDS}
    return {
        **common,
        "message_id": received["message_id"][:-len("-received")] + "-responded",
        "stage": "RESPONDED",
        "detail_class": config.get("response_detail_class", "CAPABILITY"),
        "classification": {
            "primary": config.get("response_detail_class", "CAPABILITY"),
            "supported_detail_classes": config["supported_detail_classes"],
            "node_state": "RESPONSIVE",
            "return_to": received["source_org"],
            "action_admitted": False,
        },
        "parent_receipt_sha256": canonical_sha256(received),
    }


def make_received(message, config, hb):
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
    return received


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
            f"re-run with --hb-epoch {_bound_epoch(path)}",
            "the written receipt is not mutated; nothing was written for this attempt", terminal=False))
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(rendered, encoding="utf-8")
    os.replace(temporary, path)


def partial_pairs():
    """Every exchange with one receipt of its pair written and not the other."""
    if not RECEIPTS.exists():
        return []
    halves = {}
    for stage in ("received", "responded"):
        for path in RECEIPTS.glob(f"*.{stage}.json"):
            halves.setdefault(path.name[:-len(f".{stage}.json")], {})[stage] = path
    return sorted((prefix, paths) for prefix, paths in halves.items() if len(paths) == 1)


def _bound_epoch(path):
    try:
        reference = load_json(path).get("hb_reference")
        return reference.get("epoch") if isinstance(reference, dict) else None
    except (OSError, ValueError, AttributeError):
        return None


def _partial_refusal(prefix, paths, detail, *, terminal=False, repair=None):
    """The six-field refusal of a partial pair, naming the epoch it is bound to."""
    written = next(iter(paths.values()))
    epoch = _bound_epoch(written)
    if repair is None:
        repair = (f"run --apply (with any supplied epoch, or --hb-epoch {epoch}); "
                  f"the pair completes at its recorded epoch {epoch}" if epoch is not None else
                  f"complete or retire {written.name}; its epoch cannot be read")
    return _refusal("HB_RECEIPT_PAIR_PARTIAL", "EVERY_EXCHANGE_HAS_A_COMPLETE_RECEIPT_PAIR",
                    f"{prefix}: {detail}", repair,
                    "the written receipt is not mutated; the pair completes at its own recorded epoch",
                    terminal=terminal)


def _restore_received(prefix, paths, message, config):
    """Rebuild a missing received receipt from the outbox message at the epoch
    its responded receipt recorded, only if it hashes to the responded
    receipt's parent; otherwise refuse, naming the bound epoch."""
    responded_path = paths["responded"]
    epoch = _bound_epoch(responded_path)
    current = message["exchange_id"].replace("/", "-") == prefix
    try:
        responded = load_json(responded_path)
        reference = responded.get("hb_reference")
        if not current:
            raise ValueError("the outbox no longer carries this exchange's message")
        failure = kernel.supplied_epoch_failure(
            reference.get("epoch") if isinstance(reference, dict) else None, reference)
        if failure is not None:
            raise ValueError("the responded receipt's epoch is not a supplied one: " + failure[0])
        received = make_received(message, config, reference)
        if canonical_sha256(received) != responded.get("parent_receipt_sha256"):
            raise ValueError("the outbox message does not rebuild the received receipt the responded receipt names")
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise NodeRefused(_partial_refusal(
            prefix, paths, str(exc)[:400], terminal=True,
            repair=f"restore {prefix}.received.json (sha256 {_parent_of(responded_path)}, epoch {epoch}); "
                   "it cannot be rebuilt from the current outbox")) from None
    _write_once(RECEIPTS / f"{prefix}.received.json", received)
    return epoch


def _parent_of(path):
    try:
        return load_json(path).get("parent_receipt_sha256")
    except (OSError, ValueError, AttributeError):
        return None


def resume_partial_pairs(config, message):
    """Roll forward every torn pair at the epoch its written receipt recorded.

    That epoch was supplied and recorded, so completing the same transition at
    it is resumption, not a new stamp; no clock is read and no other epoch is
    used. A pair that cannot be completed here is refused, naming its epoch."""
    resumed = []
    for prefix, paths in partial_pairs():
        received_path = paths.get("received")
        if received_path is None:
            epoch = _restore_received(prefix, paths, message, config)
            resumed.append(prefix)
            print(f"HB_NODE_RESUMED:{config['organization']}:{prefix}:HB:{epoch}")
            continue
        try:
            received = load_json(received_path)
            reference = received.get("hb_reference")
            failure = kernel.supplied_epoch_failure(
                reference.get("epoch") if isinstance(reference, dict) else None, reference)
            if failure is not None:
                raise ValueError("the received receipt's epoch is not a supplied one: " + failure[0])
            if received.get("node_org") != config["organization"] or received.get("stage") != "RECEIVED":
                raise ValueError("the received receipt is not this node's RECEIVED receipt")
            responded = make_responded(received, config)
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            raise NodeRefused(_partial_refusal(prefix, paths, str(exc)[:400], terminal=True)) from None
        _write_once(RECEIPTS / f"{prefix}.responded.json", responded)
        resumed.append(prefix)
        print(f"HB_NODE_RESUMED:{config['organization']}:{prefix}:HB:{reference['epoch']}")
    return resumed


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
    # A pair torn by an earlier run, this exchange's or an earlier one's, is
    # completed at its own recorded epoch first; none is orphaned.
    resume_partial_pairs(config, message)
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
        partial = partial_pairs()
        if partial:
            # A torn pair is not a pass: FAIL_CLOSED, naming each bound epoch.
            prefix, paths = partial[0]
            print(json.dumps({**_partial_refusal(prefix, paths, "one receipt of the pair is written"),
                              "partial_pairs": [name for name, _paths in partial]}, indent=2, sort_keys=True))
            sys.exit(1)
        print(f"HB_NODE_CHECK_PASS:{config['organization']}")
    else:
        parser.error("choose --apply or --check")


if __name__ == "__main__":
    main()
