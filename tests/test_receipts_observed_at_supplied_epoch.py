"""Repository and organization receipts take `observed_at` from the supplied hb_epoch, never the wall clock.

The SV-LLM S1 sandbox verifier (SV-LLM/.github#46) refused this branch's hop
at fbf1fa46 with DENY HOP_RECEIPTS_DEPEND_ON_AN_UNSUPPLIED_INPUT: two runs at
the same supplied epoch wrote different receipts because `observed_at` read
the clock in emit.py and aggregate_repo_transition.py. Here both modules'
clocks advance on every read; the receipts must not change. Temporary ledger
directories only; nothing is published.
"""
import importlib.util
import os
import shutil
import tempfile
import unittest
from datetime import datetime as _real_datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AdvancingClock:
    reads = 0

    @classmethod
    def now(cls, tz=None):
        cls.reads += 1
        return _real_datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=cls.reads)


class SuppliedEpochObservedAtTests(unittest.TestCase):
    def setUp(self):
        self._saved = {key: os.environ.get(key) for key in ("STEGVERSE_REPO_LEDGER_ROOT", "STEGVERSE_ORG_LEDGER_ROOT")}

    def tearDown(self):
        for key, value in self._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def append_once(self, epoch):
        home = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, home, True)
        os.environ["STEGVERSE_REPO_LEDGER_ROOT"] = str(home / "repo")
        os.environ["STEGVERSE_ORG_LEDGER_ROOT"] = str(home / "org")
        emit = load("emit_observed_at", ROOT / ".stegverse/transition-ledger/emit.py")
        aggregate = load("aggregate_observed_at", ROOT / "resident-runtime/aggregate_repo_transition.py")
        emit.datetime = AdvancingClock
        aggregate.datetime = AdvancingClock
        repo = emit.append("OBSERVED-AT:1", "OBSERVED_AT_TEST", "sha256:" + "0" * 64, "sha256:" + "1" * 64,
                           {"case": "observed_at"}, hb_epoch=epoch)
        org = aggregate.append(repo, "ORGANIZATION_STATE_TRANSITION", repo["predecessor_state_sha256"],
                               repo["successor_state_sha256"], {"case": "observed_at"}, hb_epoch=epoch)
        return repo, org

    def test_observed_at_is_the_supplied_epoch_and_reads_no_clock(self):
        before = AdvancingClock.reads
        repo, org = self.append_once(40)
        self.assertEqual(repo["observed_at"], "SUPPLIED_HB_EPOCH:40")
        self.assertEqual(org["observed_at"], "SUPPLIED_HB_EPOCH:40")
        self.assertEqual(AdvancingClock.reads, before)

    def test_the_same_transition_at_the_same_epoch_writes_the_same_receipts_under_an_advancing_clock(self):
        self.assertEqual(self.append_once(41), self.append_once(41))


if __name__ == "__main__":
    unittest.main()
