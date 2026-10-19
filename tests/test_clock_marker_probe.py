"""Every clock value a route produces is marked as one (B-P36g).

The clock is fixed at one instant and every frame, cycle, gateway, transport
and heartbeat-response route runs against a copy of this repository and a
temporary mesh. Each value derived from that instant (an ISO stamp, the sampled
nanoseconds, the sampled epoch or its heartbeat id) must sit in an object that
carries ``derived_from_clock: true`` or ``sampled_unix_ns``. A receipt writer
whose epoch is supplied reads no clock at all, and one with no epoch writes
nothing.
"""
from __future__ import annotations

import base64
import contextlib
import datetime as datetime_module
import importlib.util
import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
THIS = "Admissible-Existence"
PEER = "StegVerse-org"
STANDING = {"mode": "ESTABLISH_GENESIS", "node_ref": "clock-marker-probe", "predecessor": None}
EPOCH_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
                "retry_entrypoint", "owning_existing_goal", "next_attempt")

_REAL_DATETIME = datetime_module.datetime
INSTANT = _REAL_DATETIME(2026, 10, 19, 12, 0, 0, 123457, tzinfo=datetime_module.timezone.utc)
INSTANT_NS = int(INSTANT.timestamp() * 1_000_000_000)
INSTANT_TEXT = "2026-10-19T12:00:00.123457"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


kernel = _load("clock_probe_kernel", ROOT / "org-kernel" / "kernel.py")
CLOCK_EPOCH = kernel.hb_reference(now_ns=INSTANT_NS)["epoch"]


class fixed_clock:
    """``datetime.now`` and ``time.time``/``time_ns`` return one instant and count their reads.

    Modules loaded inside the block bind the fixed ``datetime``; `modules`
    loaded before it have theirs replaced for the block.
    """

    def __init__(self, *modules):
        self.modules = modules

    def __enter__(self):
        self.reads = 0
        probe = self

        class _Fixed(_REAL_DATETIME):
            @classmethod
            def now(cls, tz=None):
                probe.reads += 1
                return INSTANT if tz is not None else INSTANT.replace(tzinfo=None)

            @classmethod
            def utcnow(cls):
                probe.reads += 1
                return INSTANT.replace(tzinfo=None)

        def _time(*args, **kwargs):
            probe.reads += 1
            return INSTANT_NS / 1_000_000_000

        def _time_ns(*args, **kwargs):
            probe.reads += 1
            return INSTANT_NS

        self.patches = [mock.patch.object(datetime_module, "datetime", _Fixed),
                        mock.patch("time.time", side_effect=_time),
                        mock.patch("time.time_ns", side_effect=_time_ns)]
        self.patches += [mock.patch.object(module, "datetime", _Fixed)
                         for module in self.modules if "datetime" in vars(module)]
        for patch in self.patches:
            patch.start()
        return self

    def __exit__(self, *exc):
        for patch in reversed(self.patches):
            patch.stop()


def _clock_value(value):
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return value in (INSTANT_NS, CLOCK_EPOCH)
    if isinstance(value, str):
        return INSTANT_TEXT in value or value == "HB:" + str(CLOCK_EPOCH)
    return False


def scan(value, where, found, unmarked):
    """Collect every clock value; record the objects that carry one unmarked."""
    if isinstance(value, dict):
        hits = [key for key, item in value.items() if _clock_value(item)]
        if hits:
            found.extend((where, key) for key in hits)
            if value.get("derived_from_clock") is not True and "sampled_unix_ns" not in value:
                unmarked.append((where, sorted(hits)))
        for key, item in value.items():
            scan(item, where + "." + str(key), found, unmarked)
        if isinstance(value.get("packet_base64"), str):
            scan(json.loads(base64.b64decode(value["packet_base64"])), where + ".<packet>", found, unmarked)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            scan(item, where + "[" + str(index) + "]", found, unmarked)


def snapshot(root):
    return {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}


def written(root, before):
    return [path for path in sorted(root.rglob("*"))
            if path.is_file() and path.suffix == ".json" and before.get(path) != path.read_bytes()]


class _Workspace(unittest.TestCase):
    """A copy of this repository, a temporary mesh and redirected ledger roots."""

    ENV = ("STEGVERSE_REPO_LEDGER_ROOT", "STEGVERSE_ORG_LEDGER_ROOT",
           "STEGVERSE_ORG_FEDERATION_ROOT", "STEGVERSE_ORG_FEDERATION_GATEWAY_URL")

    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.work = Path(work.name)
        self.repo = self.work / "repo"
        shutil.copytree(ROOT, self.repo, ignore=shutil.ignore_patterns(".git", "tests", "__pycache__"))
        self.mesh = self.work / "mesh"
        values = {"STEGVERSE_REPO_LEDGER_ROOT": str(self.work / "repo-ledger"),
                  "STEGVERSE_ORG_LEDGER_ROOT": str(self.work / "org-ledger"),
                  "STEGVERSE_ORG_FEDERATION_ROOT": str(self.mesh),
                  "STEGVERSE_ORG_FEDERATION_GATEWAY_URL": None}
        patch = mock.patch.dict(os.environ, {})
        patch.start()
        self.addCleanup(patch.stop)
        for name, value in values.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def packet(self, K, service, payload, packet_id, origin=PEER):
        return K.build_packet(origin_org=origin, origin_service=K.organization_slug(origin) + ".org-control",
                              destination_org=THIS, destination_service=service, payload=payload,
                              standing=STANDING, transition_reference="probe:" + packet_id,
                              authority_effect="NONE", packet_id=packet_id)


def control(message_class, communication_id):
    return {"message_class": message_class, "communication_id": communication_id,
            "subject": "probe", "body": {"probe": communication_id}, "requested_action": None}


class ClockMarkerProbeTests(_Workspace):
    def test_every_clock_value_on_every_route_is_marked(self):
        found, unmarked, objects = [], [], []
        before = snapshot(self.work)
        with fixed_clock() as clock:
            cycle = _load("probe_federation_cycle", self.repo / "resident-runtime" / "federation_cycle.py")
            transport = _load("probe_intr_transport", self.repo / "org-boundary" / "runtime" / "intr_transport.py")
            K, GW = cycle.K, cycle.GW

            # Frame-only helpers that take no epoch (WU-B13).
            objects.append(("publish_packet", K.publish_packet(
                self.packet(K, "admissible-existence.boundary-diagnostic", {"probe": 1}, "probe-diag"))))
            objects.append(("publish_ecosystem_message", K.publish_ecosystem_message(
                origin_org=THIS, origin_service="admissible-existence.org-control", organizations=[PEER, THIS],
                standing=STANDING, message_class="ecosystem.communication", subject="probe", body={})))
            objects.append(("resident_status", K.resident_status(self.repo)))
            for message_class in ("ecosystem.monitor.request", "ecosystem.work.request", "ecosystem.communication"):
                K.publish_packet(self.packet(K, "admissible-existence.org-control",
                                             control(message_class, "probe-" + message_class),
                                             "probe-" + message_class))
            K.publish_packet(self.packet(K, "admissible-existence.intr-destination", {
                "message_class": "ecosystem.communication", "communication_id": "probe-intr",
                "subject": "probe", "body": {"schema": "stegverse.org-intr-destination-diagnostic/v1",
                                             "probe": "diagnostic-crossing"}}, "probe-intr"))

            # federation_cycle over the local spool: consume_and_respond and latest-cycle.json.
            with contextlib.redirect_stdout(io.StringIO()):
                cycle.main()

            # federation_cycle through the gateway: carrier frames, the ack and the cycle receipt.
            sent = []
            request = K.carrier_frame(self.packet(K, "admissible-existence.org-control",
                                                  control("ecosystem.monitor.request", "probe-gateway"),
                                                  "probe-gateway"))

            def gateway(method, path, *, body=None, headers=None):
                sent.append(body)
                if method == "GET":
                    return {"state": "FRAME_AVAILABLE", "frame": request}
                return {"state": "CONSUMED" if "acknowledgements" in path else "PENDING"}

            os.environ["STEGVERSE_ORG_FEDERATION_GATEWAY_URL"] = "https://gateway.invalid"
            with mock.patch.object(GW, "_json_request", gateway), contextlib.redirect_stdout(io.StringIO()):
                cycle.main()
            del os.environ["STEGVERSE_ORG_FEDERATION_GATEWAY_URL"]
            objects.extend(("gateway-body", body) for body in sent if body is not None)
            acks = [body for body in sent if (body or {}).get("schema") == "stegverse.org-federation-rendezvous.ack/v1"]

            # The INTR org-boundary transport's carrier stamps.
            crossing = transport.build_ingress({"org": PEER, "service": "x"}, {"org": THIS, "service": "y"},
                                               {"probe": 1}, "org-federation", "probe")
            receipts = [{"receipt_id": "r" + str(index)} for index in range(5)]
            objects.append(("build_ingress", crossing))
            objects.append(("build_egress", transport.build_egress(
                crossing, {"receipts": receipts, "reconstruction": {"terminal_receipt_id": "r4"}})))

        for path in written(self.work, before):
            objects.append((str(path.relative_to(self.work)), json.loads(path.read_text())))
        for where, value in objects:
            scan(value, where, found, unmarked)

        self.assertGreater(clock.reads, 0)
        self.assertTrue(found, "the probe saw no clock value")
        self.assertEqual(unmarked, [])
        cycles = [value for where, value in objects if where.endswith("latest-cycle.json")]
        self.assertEqual(len(cycles), 1)
        self.assertEqual(cycles[0]["heartbeat_reference"]["sampled_unix_ns"], INSTANT_NS)
        self.assertEqual(len(acks), 1)
        self.assertIs(acks[0]["derived_from_clock"], True)
        self.assertIs(crossing["carrier"]["derived_from_clock"], True)

    def test_an_ingest_route_that_writes_nothing_reads_no_clock(self):
        K = _load("probe_ingest_kernel", self.repo / "org-kernel" / "kernel.py")
        routes = (("admissible-existence.boundary-diagnostic", {"probe": 1}, "ingest-diagnostic"),
                  ("admissible-existence.org-control", control("ecosystem.communication", "ingest-comm"),
                   "ingest-comm"))
        for service, payload, packet_id in routes:
            with self.subTest(service=service):
                frame = K.carrier_frame(self.packet(K, service, payload, packet_id), epoch=4096)
                before = snapshot(self.work)
                with fixed_clock(K) as clock:
                    result = K.ingest_frame(self.repo, frame, mesh_root=self.mesh)
                self.assertEqual(result["status"], "CONSUMED")
                self.assertEqual(clock.reads, 0)
                self.assertEqual(written(self.work, before), [])


class HeartbeatResponseEpochTests(unittest.TestCase):
    MESSAGE = {"message_id": "msg-probe", "exchange_id": "ex-probe", "source_org": "StegVerse-Labs",
               "destination_org": THIS, "stage": "SENT", "detail_class": "AWARENESS",
               "retention_class": "PROJECT",
               "authority": {"execution": False, "activation": False, "publication": False,
                             "custody": False, "release": False}}

    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.receipts = Path(work.name) / "receipts"
        self.node = _load("probe_heartbeat_response", ROOT / "scripts" / "process_heartbeat_response.py")
        self.config = json.loads((ROOT / "data" / "heartbeat-response-node.json").read_text())
        body = json.dumps({"messages": [self.MESSAGE]}).encode()
        for patch in (mock.patch.object(self.node, "RECEIPTS", self.receipts),
                      mock.patch.object(self.node, "urlopen",
                                        lambda *a, **k: contextlib.nullcontext(io.BytesIO(body)))):
            patch.start()
            self.addCleanup(patch.stop)

    def apply(self, hb_epoch):
        with fixed_clock(self.node, self.node.kernel) as clock, \
                contextlib.redirect_stdout(io.StringIO()) as out:
            self.node.apply(self.config, hb_epoch)
        self.assertEqual(clock.reads, 0)
        return out.getvalue()

    def test_new_receipts_without_a_supplied_epoch_are_refused_before_any_write(self):
        cases = [(None, "HB_EPOCH_NOT_SUPPLIED")] + [
            (epoch, "HB_EPOCH_INVALID") for epoch in ("33.0", True, 31, "+33", "abc", " 33", "")]
        for epoch, code in cases:
            with self.subTest(epoch=epoch):
                with self.assertRaises(self.node.kernel.SuppliedEpochRefused) as refused:
                    self.apply(epoch)
                refusal = refused.exception.refusal
                self.assertEqual(refusal["disposition"], "FAIL_CLOSED")
                self.assertEqual(refusal["failure_code"], code)
                for name in EPOCH_FIELDS:
                    self.assertTrue(refusal[name], name)
                self.assertEqual(refusal["retry_entrypoint"], self.node.EPOCH_RETRY_ENTRYPOINT)
                self.assertIs(refusal["derived_from_clock"], False)
                self.assertFalse(self.receipts.exists())

    def test_the_cli_prints_the_six_fields_and_exits_non_zero(self):
        with fixed_clock(self.node, self.node.kernel) as clock, contextlib.redirect_stdout(io.StringIO()) as out, \
                mock.patch("sys.argv", ["process_heartbeat_response.py", "--apply"]), \
                self.assertRaises(SystemExit) as exited:
            self.node.main()
        self.assertEqual(exited.exception.code, 1)
        self.assertEqual(clock.reads, 0)
        refusal = json.loads(out.getvalue())
        self.assertEqual(refusal["failure_code"], "HB_EPOCH_NOT_SUPPLIED")
        for name in EPOCH_FIELDS:
            self.assertTrue(refusal[name], name)
        self.assertFalse(self.receipts.exists())

    def test_a_supplied_epoch_stamps_both_receipts_and_reads_no_clock(self):
        self.assertIn("HB_NODE_RESPONDED", self.apply("4096"))
        written_receipts = sorted(self.receipts.glob("*.json"))
        self.assertEqual(len(written_receipts), 2)
        for path in written_receipts:
            receipt = json.loads(path.read_text())
            self.assertEqual(receipt["observed_at"], "HB:4096")
            self.assertEqual(receipt["hb_reference"]["epoch"], 4096)
            self.assertIs(receipt["hb_reference"]["derived_from_clock"], False)
            found, unmarked = [], []
            scan(receipt, path.name, found, unmarked)
            self.assertEqual(found, [])

    def test_receipts_already_current_need_no_epoch(self):
        self.apply("4096")
        self.assertIn("HB_NODE_CURRENT", self.apply(None))


if __name__ == "__main__":
    unittest.main()
