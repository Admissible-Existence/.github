"""NWI-S1: emit.py hb_reference never returns a clock value.

With no epoch (or an invalid one) it returns the six-field FAIL_CLOSED
HB_EPOCH_NOT_SUPPLIED / HB_EPOCH_INVALID from the vendored shared rule
(supplied_epoch_failure, function segment sha256 726248a5), and append() is
refused before the ledger is opened. Patching the clock changes nothing.
"""
import ast
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
EMIT = ROOT / ".stegverse/transition-ledger/emit.py"
spec = importlib.util.spec_from_file_location("emit_supplied_epoch", EMIT)
emit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(emit)

SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")
MALFORMED = ("+33", " 33", "33 ", "3_3", "31", "0", "", "x", "٣٣", 31, -40, 33.0, True)
STATE = "sha256:" + "b" * 64


def files(root):
    return sorted(str(p) for p in Path(root).rglob("*") if p.is_file()) if Path(root).exists() else []


class EmitHbReference(unittest.TestCase):
    def assertRefused(self, value, code):
        self.assertEqual(value["disposition"], "FAIL_CLOSED")
        self.assertEqual((value["failure_code"], value["failed_predicate"]),
                         (code, "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH"))
        self.assertTrue(all(value.get(field) for field in SIX), value)
        self.assertNotIn("epoch", value)

    def test_the_vendored_rule_is_the_shared_segment(self):
        text = EMIT.read_text()
        [node] = [n for n in ast.parse(text).body if getattr(n, "name", None) == "supplied_epoch_failure"]
        segment = "\n".join(text.splitlines()[node.lineno - 1:node.end_lineno]).rstrip()
        self.assertEqual(hashlib.sha256(segment.encode()).hexdigest(), emit.SHARED_RULE_SHA256)
        self.assertTrue(emit.SHARED_RULE_SHA256.startswith("726248a5"))

    def test_the_module_imports_no_clock(self):
        tree = ast.parse(EMIT.read_text())
        imported = {alias.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))
                    for alias in n.names} | {n.module.split(".")[0] for n in ast.walk(tree)
                                             if isinstance(n, ast.ImportFrom) and n.module}
        self.assertFalse(imported & {"datetime", "time"}, imported)

    def test_no_epoch_is_six_field_not_supplied_never_a_clock_value(self):
        with mock.patch("time.time", side_effect=AssertionError("clock read")), \
                mock.patch("time.time_ns", side_effect=AssertionError("clock read")):
            self.assertRefused(emit.hb_reference(), "HB_EPOCH_NOT_SUPPLIED")
            self.assertRefused(emit.hb_reference(None), "HB_EPOCH_NOT_SUPPLIED")

    def test_a_malformed_or_pre_anchor_epoch_is_six_field_invalid(self):
        for epoch in MALFORMED:
            with self.subTest(epoch=epoch):
                self.assertRefused(emit.hb_reference(epoch), "HB_EPOCH_INVALID")

    def test_patching_the_clock_has_no_effect(self):
        seen = []
        for clock in (1_000.0, 9_999_999_999.0):
            with mock.patch("time.time", return_value=clock), mock.patch("time.time_ns", return_value=int(clock * 1e9)):
                seen.append((emit.hb_reference(4000), emit.hb_reference(None)))
        self.assertEqual(seen[0], seen[1])
        self.assertEqual(seen[0][0]["epoch"], 4000)

    def test_append_without_an_epoch_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.dict(os.environ, {"STEGVERSE_REPO_LEDGER_ROOT": tmp + "/repo"}):
            for epoch, code in ((None, "HB_EPOCH_NOT_SUPPLIED"), ("3_3", "HB_EPOCH_INVALID")):
                with self.subTest(epoch=epoch), self.assertRaises(emit.RepoLedgerEpochRefused) as caught:
                    emit.append("t:1", "T", STATE, STATE, {}, hb_epoch=epoch)
                self.assertEqual(caught.exception.refusal["failure_code"], code)
            self.assertEqual(files(tmp), [])

    def test_the_cli_refuses_six_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "STEGVERSE_REPO_LEDGER_ROOT": tmp + "/repo"}
            for extra, code in (([], "HB_EPOCH_NOT_SUPPLIED"), (["--hb-epoch", "+33"], "HB_EPOCH_INVALID")):
                with self.subTest(extra=extra):
                    run = subprocess.run([sys.executable, "-B", str(EMIT), "--transition-id", "t:1",
                                          "--transition-class", "T", "--predecessor-state-sha256", STATE,
                                          "--successor-state-sha256", STATE, *extra],
                                         capture_output=True, text=True, env=env)
                    self.assertEqual(run.returncode, 1, run.stderr)
                    refusal = json.loads(run.stdout)
                    self.assertEqual(refusal["failure_code"], code)
                    self.assertTrue(all(refusal.get(field) for field in SIX))
            self.assertEqual(files(tmp), [])


if __name__ == "__main__":
    unittest.main()
