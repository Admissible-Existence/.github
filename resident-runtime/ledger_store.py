#!/usr/bin/env python3
"""Posix ledger locator for repository and organization receipts.

A root is a directory. ``HEAD.json`` names the latest receipt. Receipt bytes
live under ``receipts/``. This store does not decide a disposition. Authority
and time stay constraint variables wherever a caller records them.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

HEAD_KEY = "HEAD.json"


def receipt_key(digest: str) -> str:
    return "receipts/" + str(digest).split(":", 1)[-1] + ".json"


def open_store(location: str | Path) -> "PosixLedgerStore":
    return PosixLedgerStore(location)


class PosixLedgerStore:
    def __init__(self, location: str | Path) -> None:
        self.root = Path(location)

    def get(self, key: str) -> Any:
        path = self.root / key
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def put(self, key: str, value: Any) -> None:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if existing == value:
                return
            # Receipt bytes are write-once. The head names the latest receipt
            # and moves when a new receipt is appended.
            if key != HEAD_KEY:
                raise ValueError("ledger_receipt_collision")
        path.write_text(rendered, encoding="utf-8")
