#!/usr/bin/env python3
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "data" / "heartbeat-response-node.json"
RECEIPTS = ROOT / "data" / "heartbeat-response-receipts"
AUTH_KEYS = ("execution", "activation", "publication", "custody", "release")


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


def make_receipts(message, config, observed_at):
    organization = config["organization"]
    digest = canonical_sha256(message)
    common = {
        "schema_version": "1.0.0",
        "exchange_id": message["exchange_id"],
        "node_org": organization,
        "source_org": message["source_org"],
        "destination_org": organization,
        "observed_at": observed_at,
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


def apply(config):
    with urlopen(config["outbox_url"], timeout=20) as response:
        batch = json.load(response)
    message = select_message(batch, config["organization"])
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    prefix = message["exchange_id"].replace("/", "-")
    received_path = RECEIPTS / f"{prefix}.received.json"
    responded_path = RECEIPTS / f"{prefix}.responded.json"
    if received_path.exists() and responded_path.exists():
        print(f"HB_NODE_CURRENT:{config['organization']}:{message['exchange_id']}")
        return
    observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    received, responded = make_receipts(message, config, observed_at)
    received_path.write_text(json.dumps(received, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    responded_path.write_text(json.dumps(responded, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"HB_NODE_RESPONDED:{config['organization']}:{message['exchange_id']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    config = load_json(CONFIG)
    validate_local(config)
    if args.apply:
        apply(config)
        validate_local(config)
    elif args.check:
        print(f"HB_NODE_CHECK_PASS:{config['organization']}")
    else:
        parser.error("choose --apply or --check")


if __name__ == "__main__":
    main()
