"""org-kernel/kernel.py heartbeat reference: no clock fallback (NWI-S1).

A missing epoch is a six-field FAIL_CLOSED HB_EPOCH_NOT_SUPPLIED, never a value
read from a clock. The clock-patch tests make every clock return a different
value and require the result to be unchanged.
"""
import ast, datetime as _dt, hashlib, importlib.util, time, unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "org-kernel" / "kernel.py"
SPEC = importlib.util.spec_from_file_location("org_kernel_no_clock", SOURCE)
K = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(K)
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")
PACKET = {"packet_id": "p-1", "payload": {"a": 1}, "origin": {"org": "A"},
          "destination": {"org": "B"}, "intr_profile": "stegverse.intr.org-boundary.v1"}


class _Clock(_dt.datetime):
    @classmethod
    def now(cls, tz=None):
        return _dt.datetime(2099, 1, 1, tzinfo=tz)

    @classmethod
    def utcnow(cls):
        return _dt.datetime(2099, 1, 1)


def clocks_moved():
    return [mock.patch.object(time, "time", return_value=4_102_444_800.0),
            mock.patch.object(time, "time_ns", return_value=4_102_444_800 * 10**9),
            mock.patch.object(time, "monotonic", return_value=9e9),
            mock.patch.object(_dt, "datetime", _Clock)]


class NoClockFallback(unittest.TestCase):
    def refused(self, call, code):
        with self.assertRaises(K.HbEpochRefused) as cm:
            call()
        r = cm.exception.refusal
        self.assertEqual(r["disposition"], "FAIL_CLOSED")
        self.assertEqual(r["failure_code"], code)
        for f in SIX:
            self.assertTrue(isinstance(r.get(f), str) and r[f], f)
        return r

    def test_the_kernel_imports_no_clock(self):
        tree = ast.parse(SOURCE.read_text())
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom):
                names.add((node.module or "").split(".")[0])
        self.assertFalse(names & {"datetime", "time"}, names)
        self.assertNotIn("datetime.now", SOURCE.read_text())

    def test_the_vendored_rule_is_the_shared_segment(self):
        tree = ast.parse(SOURCE.read_text()); lines = SOURCE.read_text().splitlines()
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "supplied_epoch_failure")
        seg = "\n".join(lines[node.lineno - 1:node.end_lineno]).rstrip()
        self.assertEqual(hashlib.sha256(seg.encode()).hexdigest(), K.SHARED_RULE_SHA256)

    def test_a_missing_epoch_is_six_field_fail_closed(self):
        self.refused(lambda: K.hb_reference(), "HB_EPOCH_NOT_SUPPLIED")
        self.refused(lambda: K.hb_reference(None, epoch=None), "HB_EPOCH_NOT_SUPPLIED")
        self.refused(lambda: K.carrier_frame(dict(PACKET)), "HB_EPOCH_NOT_SUPPLIED")
        r = K.hb_epoch_refusal(None)
        self.assertEqual(r["failure_code"], "HB_EPOCH_NOT_SUPPLIED")

    def test_a_missing_epoch_stays_refused_when_every_clock_moves(self):
        patches = clocks_moved()
        for p in patches: p.start()
        try:
            self.refused(lambda: K.hb_reference(), "HB_EPOCH_NOT_SUPPLIED")
            self.refused(lambda: K.carrier_frame(dict(PACKET)), "HB_EPOCH_NOT_SUPPLIED")
        finally:
            for p in reversed(patches): p.stop()

    def test_invalid_epochs_are_refused(self):
        for bad in (31, "31", "x", "", "٣٣", -1, True):
            with self.subTest(bad=bad):
                self.refused(lambda: K.hb_reference(epoch=bad), "HB_EPOCH_INVALID")

    def test_a_supplied_epoch_is_byte_identical_under_moved_clocks(self):
        before = (K.hb_reference(epoch=4000), K.carrier_frame(dict(PACKET), epoch="4000"))
        patches = clocks_moved()
        for p in patches: p.start()
        try:
            after = (K.hb_reference(epoch=4000), K.carrier_frame(dict(PACKET), epoch="4000"))
        finally:
            for p in reversed(patches): p.stop()
        self.assertEqual(K.canon(before), K.canon(after))
        self.assertEqual(before[0]["epoch"], 4000)
        self.assertIs(before[0]["derived_from_clock"], False)
        self.assertNotIn("sampled_unix_ns", before[0])

    def test_an_explicit_sample_is_still_a_supplied_value(self):
        ref = K.hb_reference(K.HB_ANCHOR_UNIX_NS + 3 * K.HB_PERIOD_NS)
        self.assertEqual(ref["epoch"], K.HB_ANCHOR_EPOCH + 3)
        with self.assertRaises(ValueError):
            K.hb_reference(K.HB_ANCHOR_UNIX_NS, epoch=40)

    def test_the_status_read_carries_the_refusal_not_a_clock_reference(self):
        self.assertIn('"heartbeat_reference":hb_epoch_refusal(None)', SOURCE.read_text())


if __name__ == "__main__":
    unittest.main()
