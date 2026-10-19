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


def assert_six_fields(test, refusal, failure_code):
    test.assertEqual(refusal["disposition"], "FAIL_CLOSED")
    test.assertEqual(refusal["failure_code"], failure_code)
    for name in EPOCH_FIELDS:
        test.assertTrue(refusal[name], name)
    test.assertIs(refusal["derived_from_clock"], False)


class SharedRuleProvenanceTests(unittest.TestCase):
    """F1. A reference that marks no provenance is refused by the shared rule."""

    def test_a_reference_with_no_derived_from_clock_key_is_refused(self):
        code, _detail = kernel.supplied_epoch_failure(4096, {"epoch": 4096})
        self.assertEqual(code, "HB_EPOCH_PROVENANCE_UNMARKED")

    def test_the_ruled_order(self):
        # (1) flag present and not false, (2) sampled_unix_ns present, (3) flag absent.
        cases = (({"epoch": 4096, "derived_from_clock": True, "sampled_unix_ns": 1}, "HB_EPOCH_INVALID"),
                 ({"epoch": 4096, "derived_from_clock": False, "sampled_unix_ns": 1}, "HB_EPOCH_INVALID"),
                 (kernel.hb_reference(now_ns=INSTANT_NS), "HB_EPOCH_INVALID"),
                 ({"epoch": 4096}, "HB_EPOCH_PROVENANCE_UNMARKED"))
        for reference, code in cases:
            with self.subTest(reference=reference):
                self.assertEqual(kernel.supplied_epoch_failure(4096, reference)[0], code)

    def test_marked_references(self):
        self.assertIsNone(kernel.supplied_epoch_failure(4096, kernel.hb_reference(epoch=4096)))
        # CARRIED also marks derived_from_clock false; a provenance alone is not a marker.
        self.assertEqual(kernel.supplied_epoch_failure(4096, {"epoch": 4096, "provenance": "CARRIED:X"})[0],
                         "HB_EPOCH_PROVENANCE_UNMARKED")
        self.assertEqual(kernel.supplied_epoch_failure(4096, {"epoch": 4096, "derived_from_clock": True})[0],
                         "HB_EPOCH_INVALID")

    def test_a_supplied_epoch_is_marked_supplied_and_reads_no_clock(self):
        # SUPPLIED: derived_from_clock false and no sampled_unix_ns.
        packet = kernel.build_packet(origin_org=PEER, origin_service="p", destination_org=THIS,
                                     destination_service="s", payload={}, standing=STANDING)
        with fixed_clock(kernel) as clock:
            references = (kernel.hb_reference(epoch=4096),
                          kernel.carrier_frame(packet, epoch=4096)["heartbeat_reference"])
        self.assertEqual(clock.reads, 0)
        for reference in references:
            self.assertEqual(reference["epoch"], 4096)
            self.assertIs(reference["derived_from_clock"], False)
            self.assertNotIn("sampled_unix_ns", reference)

    def test_a_clock_frame_carries_no_epoch(self):
        packet = kernel.build_packet(origin_org=PEER, origin_service="p", destination_org=THIS,
                                     destination_service="s", payload={}, standing=STANDING)
        self.assertEqual(kernel.carried_frame_epoch(kernel.carrier_frame(packet, epoch=4096)), (4096, None))
        epoch, failure = kernel.carried_frame_epoch(kernel.carrier_frame(packet, now_ns=INSTANT_NS))
        self.assertIsNone(epoch)
        self.assertEqual(failure[0], "HB_EPOCH_INVALID")


class SourceReceiptProvenanceTests(_Workspace):
    """F2. The organization writer refuses a source receipt whose epoch is not a supplied one."""

    def setUp(self):
        super().setUp()
        self.aggregate = _load("probe_aggregate", ROOT / "resident-runtime" / "aggregate_repo_transition.py")

    def source(self, reference):
        body = {"schema": "stegverse.repo-transition-receipt/v1", "repository": THIS + "/.github",
                "transition_id": "probe:source", "transition_class": "PROBE",
                "predecessor_state_sha256": "sha256:" + "0" * 64, "successor_state_sha256": "sha256:" + "1" * 64,
                "evidence": {}, "authority_effect": "NONE", "hb_reference": reference,
                "observed_at": "probe", "previous_receipt_sha256": None}
        return {**body, "receipt_sha256": self.aggregate.sha(body)}

    def append(self, reference):
        return self.aggregate.append(self.source(reference), "REPO_STATE_PROPAGATION", "sha256:" + "0" * 64,
                                     "sha256:" + "1" * 64, {}, hb_epoch="4096")

    def test_a_clock_or_unmarked_source_is_refused_and_nothing_is_written(self):
        clock = kernel.hb_reference(now_ns=INSTANT_NS)
        cases = ((clock, "SOURCE_RECEIPT_IS_CLOCK_PROVENANCE"),
                 ({**kernel.hb_reference(epoch=4096), "derived_from_clock": True}, "SOURCE_RECEIPT_IS_CLOCK_PROVENANCE"),
                 ({"epoch": 4096}, "HB_EPOCH_PROVENANCE_UNMARKED"),
                 (None, "HB_EPOCH_PROVENANCE_UNMARKED"))
        for reference, code in cases:
            with self.subTest(reference=reference):
                with self.assertRaises(self.aggregate.OrgLedgerEpochRefused) as refused:
                    self.append(reference)
                assert_six_fields(self, refused.exception.refusal, code)
                self.assertFalse((self.work / "org-ledger").exists())
        self.assertEqual(refused.exception.refusal["failed_predicate"], self.aggregate.SOURCE_PREDICATE)

    def test_the_clock_refusal_names_the_migration(self):
        with self.assertRaises(self.aggregate.OrgLedgerEpochRefused) as refused:
            self.append(kernel.hb_reference(now_ns=INSTANT_NS))
        self.assertEqual(refused.exception.refusal["required_evidence_or_repair"], self.aggregate.CLOCK_SOURCE_REPAIR)

    def test_a_supplied_source_is_aggregated(self):
        record = self.append(kernel.hb_reference(epoch=4096))
        self.assertEqual(record["hb_reference"]["epoch"], 4096)


class CarriedFrameEpochTests(_Workspace):
    """F3, F4, F6, F7. A frame's supplied epoch is carried; without one nothing reads a clock or writes."""

    def setUp(self):
        super().setUp()
        self.K = _load("probe_carried_kernel", self.repo / "org-kernel" / "kernel.py")

    def publish(self, service, payload, packet_id, *, epoch=None):
        packet = self.packet(self.K, service, payload, packet_id)
        if epoch is None:
            self.K.publish_packet(packet, root=self.mesh, now_ns=INSTANT_NS)
        else:
            self.K.publish_packet(packet, root=self.mesh, epoch=epoch)

    def frames_to(self, organization):
        return [json.loads(path.read_text()) for path in sorted((self.mesh / "frames.d").glob("*.json"))
                if json.loads(path.read_text())["destination_org"] == organization]

    def consume(self):
        with fixed_clock(self.K) as clock:
            results = self.K.consume_and_respond(self.repo, mesh_root=self.mesh)
        self.assertEqual(clock.reads, 0)
        return {item["result"].get("packet_id") or item["result"]["packet"]["packet_id"]: item for item in results}

    def test_the_response_carries_the_request_frames_supplied_epoch(self):
        self.publish("admissible-existence.org-control", control("ecosystem.communication", "carry"), "carry",
                     epoch=4096)
        item = self.consume()["carry"]
        self.assertIsNone(item["response_refusal"])
        response, = self.frames_to(PEER)
        self.assertEqual(response["heartbeat_reference"]["epoch"], 4096)
        self.assertIs(response["heartbeat_reference"]["derived_from_clock"], False)

    def reframe(self, service, payload, packet_id, reference):
        """Publish a frame whose heartbeat reference is replaced, re-hashed so it recovers."""
        frame = self.K.carrier_frame(self.packet(self.K, service, payload, packet_id), epoch=4096)
        body = {key: value for key, value in frame.items() if key != "frame_sha256"}
        body["heartbeat_reference"] = reference
        self.K.publish_frame({**body, "frame_sha256": self.K.sha(body)}, root=self.mesh)

    def test_a_frame_without_a_supplied_epoch_is_refused_before_any_write_for_every_role(self):
        unflagged = {key: value for key, value in self.K.hb_reference(epoch=4096).items()
                     if key != "derived_from_clock"}
        references = (("clock", self.K.hb_reference(now_ns=INSTANT_NS), "HB_EPOCH_INVALID"),
                      ("unflagged", unflagged, "HB_EPOCH_PROVENANCE_UNMARKED"),
                      ("unflagged-sampled", {**unflagged, "sampled_unix_ns": INSTANT_NS}, "HB_EPOCH_INVALID"))
        services = (("admissible-existence.org-control", control("ecosystem.communication", "x")),
                    ("admissible-existence.boundary-diagnostic", {"probe": 1}),
                    ("admissible-existence.aid", {"probe": 1}),
                    ("admissible-existence.intr-destination", {"message_class": "ecosystem.communication"}))
        for name, reference, code in references:
            for service, payload in services:
                self.reframe(service, payload, name + ":" + service, reference)
        before = snapshot(self.work)
        results = self.consume()
        self.assertEqual(len(results), len(references) * len(services))
        for name, _reference, code in references:
            for service, _payload in services:
                with self.subTest(frame=name, service=service):
                    item = results[name + ":" + service]
                    assert_six_fields(self, item["result"], code)
                    self.assertIsNone(item["seen_marker"])
                    self.assertIsNone(item["response_publication"])
        self.assertEqual(written(self.work, before), [])

    def test_a_fabricated_carried_head_is_refused(self):
        forged = {**self.K.hb_reference(epoch=4096), "source": "ORGANIZATION_LEDGER_HEAD",
                  "head_receipt_sha": "sha256:" + "f" * 64}
        self.reframe("admissible-existence.intr-destination", {
            "message_class": "ecosystem.communication", "communication_id": "forged", "subject": "probe",
            "body": {"schema": "stegverse.org-intr-destination-diagnostic/v1", "probe": "diagnostic-crossing"}},
            "forged", forged)
        before = snapshot(self.work)
        item = self.consume()["forged"]
        assert_six_fields(self, item["result"], "CARRIED_PROVENANCE_UNVERIFIED")
        self.assertIsNone(item["seen_marker"])
        self.assertEqual(written(self.work, before), [])

    def test_the_capability_ingress_receives_the_frames_supplied_epoch(self):
        self.publish("admissible-existence.intr-destination", {
            "message_class": "ecosystem.communication", "communication_id": "carried-intr", "subject": "probe",
            "body": {"schema": "stegverse.org-intr-destination-diagnostic/v1", "probe": "diagnostic-crossing"}},
            "carried-intr", epoch=4096)
        item = self.consume()["carried-intr"]
        operation = item["result"]["execution_result"]["application_result"]["receiving_operation_result"]
        self.assertEqual(operation["disposition"], "ALLOW", operation.get("detail"))
        receipts = [json.loads(path.read_text()) for path in (self.work / "org-ledger").rglob("*.json")
                    if json.loads(path.read_text()).get("schema") == "stegverse.organization-transition-receipt/v1"]
        self.assertEqual([receipt["hb_reference"]["epoch"] for receipt in receipts], [4096])

    def test_an_uninstalled_adapter_is_a_six_field_refusal(self):
        self.publish("admissible-existence.stcm", {"probe": 1}, "no-adapter", epoch=4096)
        item = self.consume()["no-adapter"]
        assert_six_fields(self, item["result"], "ENDPOINT_ADAPTER_NOT_INSTALLED")
        self.assertIsNone(item["response_publication"])

    def test_monitor_and_work_handlers_read_no_clock_and_write_nothing_without_an_epoch(self):
        registry = self.K.load_registry(self.repo)
        with fixed_clock(self.K) as clock:
            monitor = self.K.handle_control_message(
                self.repo, self.packet(self.K, "admissible-existence.org-control",
                                       control("ecosystem.monitor.request", "monitor"), "monitor"), registry)
            work = self.K.handle_control_message(
                self.repo, self.packet(self.K, "admissible-existence.org-control",
                                       control("ecosystem.work.request", "work"), "work"), registry)
        self.assertEqual(clock.reads, 0)
        self.assertIsNone(monitor["monitor_status"]["heartbeat_reference"])
        assert_six_fields(self, work["work_intake"], "HB_EPOCH_NOT_SUPPLIED")
        self.assertFalse((self.repo / "resident-runtime" / "control" / "inbox").exists())

    def test_monitor_and_work_requests_carry_a_supplied_epoch(self):
        self.publish("admissible-existence.org-control", control("ecosystem.monitor.request", "monitor"), "monitor",
                     epoch=4096)
        self.publish("admissible-existence.org-control", control("ecosystem.work.request", "work"), "work",
                     epoch=4096)
        results = self.consume()
        status = results["monitor"]["result"]["execution_result"]["application_result"]["monitor_status"]
        self.assertEqual(status["heartbeat_reference"]["epoch"], 4096)
        record, = [json.loads(path.read_text())
                   for path in (self.repo / "resident-runtime" / "control" / "inbox").glob("*.json")]
        self.assertEqual(record["hb_reference"]["epoch"], 4096)
        self.assertIs(record["hb_reference"]["derived_from_clock"], False)


class EgressCollisionTests(_Workspace):
    """F5. A collision is refused with six fields before the frame is published."""

    def test_a_second_emission_at_another_epoch_publishes_nothing(self):
        egress = _load("probe_egress", ROOT / "resident-runtime" / "organization_egress_boundary.py")
        payload = {"message_class": "ecosystem.communication", "communication_id": "collide", "subject": "probe",
                   "body": {"schema": "stegverse.org-intr-destination-diagnostic/v1", "probe": "diagnostic-crossing"}}
        first = egress.emit(PEER, payload, standing=STANDING, capability="intr-destination",
                            mesh_root=self.mesh, hb_epoch="4096")
        self.assertIs(first["emitted"], True)
        frames = sorted((self.mesh / "frames.d").glob("*.json"))
        before = snapshot(self.work)
        with self.assertRaises(egress.kernel.BoundaryFailClosed) as refused:
            egress.emit(PEER, payload, standing=STANDING, capability="intr-destination",
                        mesh_root=self.mesh, hb_epoch="4097")
        assert_six_fields(self, refused.exception.refusal, "LEDGER_RECEIPT_COLLISION")
        self.assertEqual(sorted((self.mesh / "frames.d").glob("*.json")), frames)
        self.assertEqual(written(self.work, before), [])


class CarriedProvenanceArgumentTests(unittest.TestCase):
    """No writer accepts a caller-supplied provenance or CARRIED source."""

    def test_no_writer_takes_a_provenance_argument(self):
        import inspect
        writers = (_load("probe_emit", ROOT / ".stegverse" / "transition-ledger" / "emit.py").append,
                   _load("probe_aggregate_args", ROOT / "resident-runtime" / "aggregate_repo_transition.py").append)
        for writer in writers:
            names = [name.lower() for name in inspect.signature(writer).parameters]
            self.assertFalse([name for name in names if "provenance" in name or "carried" in name], names)


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
