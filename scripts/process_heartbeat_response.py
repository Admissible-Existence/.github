#!/usr/bin/env python3
import argparse
import hashlib
import importlib.util
import json
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


def apply(config, hb_epoch=None):
    with urlopen(config["outbox_url"], timeout=20) as response:
        batch = json.load(response)
    message = select_message(batch, config["organization"])
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
    received_path.write_text(json.dumps(received, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    responded_path.write_text(json.dumps(responded, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"HB_NODE_RESPONDED:{config['organization']}:{message['exchange_id']}")


def main():
    parser = argparse.ArgumentParser()
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
        except kernel.SuppliedEpochRefused as refused:
            print(json.dumps(refused.refusal, indent=2, sort_keys=True))
            sys.exit(1)
        validate_local(config)
    elif args.check:
        print(f"HB_NODE_CHECK_PASS:{config['organization']}")
    else:
        parser.error("choose --apply or --check")


if __name__ == "__main__":
    main()
