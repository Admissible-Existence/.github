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
import hashlib
import datetime as datetime_module
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
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
                self.assertEqual(cycle.main(["--hb-epoch", "4096"]), 0)

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
                self.assertEqual(cycle.main(["--hb-epoch", "4096"]), 0)
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
        # The cycle record is stamped at the supplied epoch, not from the clock.
        self.assertEqual(cycles[0]["heartbeat_reference"]["epoch"], 4096)
        self.assertIs(cycles[0]["heartbeat_reference"]["derived_from_clock"], False)
        self.assertNotIn("sampled_unix_ns", cycles[0]["heartbeat_reference"])
        self.assertEqual(len(acks), 1)
        # The request frame is a clock sample, so it lends no epoch: the ack
        # carries no clock value, and no response is published.
        self.assertIs(acks[0]["derived_from_clock"], False)
        self.assertIsNone(acks[0]["observed_at"])
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
        # A source must be on its repository ledger (COMMITTED_REQUEST_DIGEST_UNVERIFIED).
        emit = _load("probe_source_emit", ROOT / ".stegverse" / "transition-ledger" / "emit.py")
        source = emit.append("probe:source", "PROBE", "sha256:" + "0" * 64, "sha256:" + "1" * 64, {},
                             hb_epoch="4096")
        record = self.aggregate.append(source, "REPO_STATE_PROPAGATION", "sha256:" + "0" * 64,
                                       "sha256:" + "1" * 64, {}, hb_epoch="4096")
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

    def reframed(self, service, payload, packet_id, reference):
        """A frame whose heartbeat reference is replaced, re-hashed so it recovers."""
        frame = self.K.carrier_frame(self.packet(self.K, service, payload, packet_id), epoch=4096)
        body = {key: value for key, value in frame.items() if key != "frame_sha256"}
        body["heartbeat_reference"] = reference
        return {**body, "frame_sha256": self.K.sha(body)}

    def reframe(self, service, payload, packet_id, reference):
        self.K.publish_frame(self.reframed(service, payload, packet_id, reference), root=self.mesh)

    def test_an_unmarked_frame_is_refused_before_any_write_for_every_role(self):
        unflagged = {key: value for key, value in self.K.hb_reference(epoch=4096).items()
                     if key != "derived_from_clock"}
        references = (("unflagged", unflagged, "HB_EPOCH_PROVENANCE_UNMARKED"),)
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
                    self.assert_quarantined(item, code)
                    self.assertIsNone(item["response_publication"])
        self.assert_only_quarantine_markers_written(before)

    def test_a_fabricated_carried_head_is_refused(self):
        forged = {**self.K.hb_reference(epoch=4096), "source": "ORGANIZATION_LEDGER_HEAD",
                  "head_receipt_sha": "sha256:" + "f" * 64}
        self.reframe("admissible-existence.intr-destination", {
            "message_class": "ecosystem.communication", "communication_id": "forged", "subject": "probe",
            "body": {"schema": "stegverse.org-intr-destination-diagnostic/v1", "probe": "diagnostic-crossing"}},
            "forged", forged)
        frame = json.loads(next((self.mesh / "frames.d").glob("*.json")).read_text())
        before = snapshot(self.work)
        # The kernel's own ingest and the addressed-frame scan write nothing.
        with fixed_clock(self.K) as clock:
            direct = self.K.ingest_frame(self.repo, frame, mesh_root=self.mesh)
            scanned = self.K.consume_addressed_frames(self.repo, mesh_root=self.mesh)
        self.assertEqual(clock.reads, 0)
        assert_six_fields(self, direct, "CARRIED_NOT_ACCEPTED_BY_DESTINATION")
        assert_six_fields(self, scanned[0]["result"], "CARRIED_NOT_ACCEPTED_BY_DESTINATION")
        self.assertEqual(written(self.work, before), [])
        # The gateway cycle refuses and acknowledges BLOCKED, writing nothing.
        cycle = _load("probe_forged_cycle", self.repo / "resident-runtime" / "federation_cycle.py")
        acks = []

        def gateway(method, path, *, body=None, headers=None):
            if method == "GET":
                return {"state": "FRAME_AVAILABLE", "frame": frame}
            acks.append(body)
            return {"state": "BLOCKED"}

        with mock.patch.object(cycle.GW, "_json_request", gateway):
            gateway_result = cycle.GW.resident_gateway_cycle(self.repo)
        self.assertEqual(gateway_result["state"], "BLOCKED")
        self.assertEqual(gateway_result["responses_emitted"], 0)
        self.assertEqual(written(self.work, before), [])
        # consume_and_respond writes only the quarantine marker.
        item = self.consume()["forged"]
        assert_six_fields(self, item["result"], "CARRIED_NOT_ACCEPTED_BY_DESTINATION")
        self.assert_quarantined(item, "CARRIED_NOT_ACCEPTED_BY_DESTINATION")
        self.assert_only_quarantine_markers_written(before)
        self.assertFalse((self.repo / "resident-runtime" / "control" / "inbox").exists())
        self.assertFalse((self.work / "repo-ledger").exists())
        self.assertFalse((self.work / "org-ledger").exists())

    def assert_quarantined(self, item, code):
        marker = json.loads(Path(item["seen_marker"]).read_text())
        self.assertEqual(marker["status"], "REFUSED")
        self.assertIs(marker["terminal"], True)
        assert_six_fields(self, marker, "FRAME_REFUSED_QUARANTINED")
        self.assertEqual(marker["refused_failure_code"], code)
        found, _unmarked = [], []
        scan(marker, "marker", found, _unmarked)
        self.assertEqual(found, [])

    def assert_only_quarantine_markers_written(self, before):
        for path in written(self.work, before):
            self.assertEqual(json.loads(path.read_text())["schema_version"],
                             "stegverse.federation-frame-quarantine.v1", path)

    @staticmethod
    def frame_name(frame):
        return hashlib.sha256((frame["packet_id"] + "|" + frame["frame_sha256"]).encode()).hexdigest()

    def test_a_refused_frame_in_a_mixed_batch_is_quarantined_and_does_not_block_valid_frames(self):
        service = "admissible-existence.org-control"
        unflagged = {key: value for key, value in self.K.hb_reference(epoch=4096).items()
                     if key != "derived_from_clock"}
        self.mixed_batch(service, unflagged, "HB_EPOCH_PROVENANCE_UNMARKED")

    def test_a_forged_carried_frame_in_a_mixed_batch_is_quarantined_and_does_not_block_valid_frames(self):
        forged = {**self.K.hb_reference(epoch=4096), "source": "ORGANIZATION_LEDGER_HEAD",
                  "head_receipt_sha": "sha256:" + "f" * 64}
        self.mixed_batch("admissible-existence.org-control", forged, "CARRIED_NOT_ACCEPTED_BY_DESTINATION", tag="forged")

    def test_a_clock_flagged_frame_is_consumed_lending_no_epoch(self):
        # NARROW S1: a clock-flagged or clock-sampled frame is consumed, lends
        # no epoch, and every route that needs one refuses NOT_SUPPLIED.
        unflagged = {key: value for key, value in self.K.hb_reference(epoch=4096).items()
                     if key != "derived_from_clock"}
        references = (("flagged", {**self.K.hb_reference(epoch=4096), "derived_from_clock": True}),
                      ("sampled", self.K.hb_reference(now_ns=INSTANT_NS)),
                      ("false-sampled", {**self.K.hb_reference(epoch=4096), "sampled_unix_ns": INSTANT_NS}),
                      ("unflagged-sampled", {**unflagged, "sampled_unix_ns": INSTANT_NS}))
        intr = {"message_class": "ecosystem.communication", "communication_id": "x", "subject": "probe",
                "body": {"schema": "stegverse.org-intr-destination-diagnostic/v1", "probe": "diagnostic-crossing"}}
        for name, reference in references:
            self.reframe("admissible-existence.org-control", control("ecosystem.work.request", name),
                         "work-" + name, reference)
            self.reframe("admissible-existence.intr-destination", {**intr, "communication_id": "intr-" + name},
                         "intr-" + name, reference)
        results = self.consume()
        for name, _reference in references:
            with self.subTest(frame=name):
                work = results["work-" + name]
                self.assertEqual(work["result"]["status"], "CONSUMED")
                application = work["result"]["execution_result"]["application_result"]
                assert_six_fields(self, application["work_intake"], "HB_EPOCH_NOT_SUPPLIED")
                assert_six_fields(self, work["response_refusal"], "HB_EPOCH_INVALID")
                self.assertIsNone(work["response_publication"])
                operation = results["intr-" + name]["result"]["execution_result"]["application_result"][
                    "receiving_operation_result"]
                assert_six_fields(self, operation, "HB_EPOCH_NOT_SUPPLIED")
        self.assertFalse((self.repo / "resident-runtime" / "control" / "inbox").exists())
        self.assertFalse((self.work / "repo-ledger").exists())
        self.assertFalse((self.work / "org-ledger").exists())
        self.assertEqual(self.frames_to(PEER), [])
        self.assertEqual(self.consume(), {})

    def mixed_batch(self, service, reference, code, tag="unflagged"):
        for refused_first in (True, False):
            with self.subTest(refused_first=refused_first):
                # Pick packet ids whose frame files sort in the order under test.
                for index in range(1000):
                    valid_id = "valid-%s-%d-%s" % (tag, index, refused_first)
                    refused_id = "refused-%s-%d-%s" % (tag, index, refused_first)
                    valid = self.K.carrier_frame(self.packet(
                        self.K, service, control("ecosystem.communication", valid_id), valid_id), epoch=4096)
                    refused = self.reframed(service, control("ecosystem.communication", refused_id),
                                            refused_id, reference)
                    if (self.frame_name(refused) < self.frame_name(valid)) == refused_first:
                        break
                self.K.publish_frame(valid, root=self.mesh)
                self.K.publish_frame(refused, root=self.mesh)
                names = sorted(path.stem for path in (self.mesh / "frames.d").glob("*.json"))
                self.assertEqual(names.index(self.frame_name(refused)) < names.index(self.frame_name(valid)),
                                 refused_first)
                first = self.consume()
                self.assertEqual(first[valid_id]["result"]["status"], "CONSUMED")
                self.assertIsNotNone(first[valid_id]["response_publication"])
                assert_six_fields(self, first[refused_id]["result"], code)
                self.assert_quarantined(first[refused_id], code)
                # The next cycle neither re-refuses nor re-consumes either frame.
                again = self.consume()
                self.assertNotIn(valid_id, again)
                self.assertNotIn(refused_id, again)

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
        self.assert_quarantined(item, "ENDPOINT_ADAPTER_NOT_INSTALLED")
        self.assertNotIn("no-adapter", self.consume())

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


class FrameIngestErrorTests(_Workspace):
    """B-P36o. An error ingesting one frame is a six-field refusal; the cycle continues."""

    INTR = {"message_class": "ecosystem.communication", "subject": "probe",
            "body": {"schema": "stegverse.org-intr-destination-diagnostic/v1", "probe": "diagnostic-crossing"}}

    def setUp(self):
        super().setUp()
        self.K = _load("probe_ingest_error_kernel", self.repo / "org-kernel" / "kernel.py")

    def frame(self, packet_id, service="admissible-existence.intr-destination", payload=None):
        payload = payload if payload is not None else {**self.INTR, "communication_id": packet_id}
        return self.K.carrier_frame(self.packet(self.K, service, payload, packet_id), epoch=4096)

    def rehash(self, frame, **changes):
        body = {key: value for key, value in frame.items() if key != "frame_sha256"}
        body.update(changes)
        return {**body, "frame_sha256": self.K.sha(body)}

    def bad_frames(self):
        reference = self.K.hb_reference(epoch=4096)
        tampered = self.frame("bad-frame-sha")
        return {
            "bad-generation": ("HB_REFERENCE_INVALID", self.rehash(
                self.frame("bad-generation"), heartbeat_reference={**reference, "generation": 4097})),
            "bad-heartbeat-id": ("HB_REFERENCE_INVALID", self.rehash(
                self.frame("bad-heartbeat-id"), heartbeat_reference={**reference, "heartbeat_id": "HB:4097"})),
            "bad-frame-sha": ("FRAME_INTEGRITY_INVALID", {**tampered, "frame_sha256": "sha256:" + "0" * 64}),
            "bad-packet-sha": ("FRAME_INTEGRITY_INVALID", self.rehash(
                self.frame("bad-packet-sha"), packet_sha256="sha256:" + "0" * 64)),
            "bad-adapter": ("FRAME_INGEST_FAILED", self.frame("bad-adapter", payload={"manifest": {"probe": True}})),
        }

    @staticmethod
    def name(frame):
        return hashlib.sha256((frame["packet_id"] + "|" + frame["frame_sha256"]).encode()).hexdigest()

    def test_bad_frames_before_a_valid_frame_are_refused_and_the_valid_frame_is_ledgered(self):
        bad = self.bad_frames()
        last = max(self.name(frame) for _code, frame in bad.values())
        for index in range(1000):
            valid = self.frame("valid-after-bad-%d" % index)
            if self.name(valid) > last:
                break
        for _code, frame in bad.values():
            self.K.publish_frame(frame, root=self.mesh)
        self.K.publish_frame(valid, root=self.mesh)
        with fixed_clock(self.K) as clock:
            first = self.K.consume_and_respond(self.repo, mesh_root=self.mesh)
            again = self.K.consume_and_respond(self.repo, mesh_root=self.mesh)
        self.assertEqual(clock.reads, 0)
        self.assertEqual(again, [])
        by_id = {item["result"].get("packet_id") or item["result"]["packet"]["packet_id"]: item for item in first}
        self.assertEqual(len(by_id), len(bad) + 1)
        for packet_id, (code, _frame) in bad.items():
            with self.subTest(frame=packet_id):
                item = by_id[packet_id]
                assert_six_fields(self, item["result"], code)
                marker = json.loads(Path(item["seen_marker"]).read_text())
                self.assertEqual(marker["failure_code"], "FRAME_REFUSED_QUARANTINED")
                self.assertEqual(marker["refused_failure_code"], code)
        self.assertEqual(by_id[valid["packet_id"]]["result"]["status"], "CONSUMED")
        receipts = [json.loads(path.read_text()) for path in (self.work / "org-ledger").rglob("*.json")
                    if json.loads(path.read_text()).get("schema") == "stegverse.organization-transition-receipt/v1"]
        self.assertEqual([receipt["repo_transition_id"] for receipt in receipts],
                         ["ORGANIZATION_INTR_DESTINATION_INGRESS:" + valid["packet_id"]])

    def test_the_gateway_cycle_blocks_a_bad_frame_without_aborting(self):
        cycle = _load("probe_ingest_error_cycle", self.repo / "resident-runtime" / "federation_cycle.py")
        for packet_id, (code, frame) in self.bad_frames().items():
            with self.subTest(frame=packet_id):
                acks = []

                def gateway(method, path, *, body=None, headers=None):
                    if method == "GET":
                        return {"state": "FRAME_AVAILABLE", "frame": frame}
                    acks.append(body)
                    return {"state": "BLOCKED"}

                before = snapshot(self.work)
                with fixed_clock(cycle.K, cycle.GW) as clock, mock.patch.object(cycle.GW, "_json_request", gateway):
                    result = cycle.GW.resident_gateway_cycle(self.repo)
                self.assertEqual(clock.reads, 0)
                self.assertEqual(result["state"], "BLOCKED")
                assert_six_fields(self, result["ingest_refusal"], code)
                self.assertEqual(len(acks), 1)
                self.assertEqual(written(self.work, before), [])


class CarrierEpochUniformityTests(_Workspace):
    """Uniformity (08:27Z): every carrier epoch passes the digit/anchor check, whatever its clock flag."""

    def test_a_clock_frame_with_a_malformed_or_absent_epoch_is_refused_and_quarantined(self):
        K = _load("probe_uniform_kernel", self.repo / "org-kernel" / "kernel.py")
        flagged = {**K.hb_reference(epoch=4096), "derived_from_clock": True}
        sampled = K.hb_reference(now_ns=INSTANT_NS)
        cases = {
            "flagged-abc": ({**flagged, "epoch": "abc"}, "HB_EPOCH_INVALID"),
            "flagged-5": ({**flagged, "epoch": 5}, "HB_EPOCH_INVALID"),
            "flagged-none": ({key: value for key, value in flagged.items() if key != "epoch"}, "HB_EPOCH_NOT_SUPPLIED"),
            "sampled-abc": ({**sampled, "epoch": "abc"}, "HB_EPOCH_INVALID"),
            "sampled-5": ({**sampled, "epoch": 5}, "HB_EPOCH_INVALID"),
        }
        service = "admissible-existence.org-control"
        frames = {}
        for packet_id, (reference, _code) in cases.items():
            frame = K.carrier_frame(self.packet(K, service, control("ecosystem.communication", packet_id), packet_id),
                                    epoch=4096)
            body = {key: value for key, value in frame.items() if key != "frame_sha256"}
            body["heartbeat_reference"] = reference
            frames[packet_id] = {**body, "frame_sha256": K.sha(body)}
            K.publish_frame(frames[packet_id], root=self.mesh)
        K.publish_packet(self.packet(K, service, control("ecosystem.communication", "valid"), "valid"),
                         root=self.mesh, epoch=4096)
        with fixed_clock(K) as clock:
            first = K.consume_and_respond(self.repo, mesh_root=self.mesh)
            again = K.consume_and_respond(self.repo, mesh_root=self.mesh)
        self.assertEqual(clock.reads, 0)
        self.assertEqual(again, [])
        by_id = {item["result"].get("packet_id") or item["result"]["packet"]["packet_id"]: item for item in first}
        self.assertEqual(by_id["valid"]["result"]["status"], "CONSUMED")
        for packet_id, (_reference, code) in cases.items():
            with self.subTest(frame=packet_id):
                assert_six_fields(self, by_id[packet_id]["result"], code)
                marker = json.loads(Path(by_id[packet_id]["seen_marker"]).read_text())
                self.assertEqual(marker["refused_failure_code"], code)
        # The gateway route refuses the same frames, BLOCKED.
        cycle = _load("probe_uniform_cycle", self.repo / "resident-runtime" / "federation_cycle.py")
        for packet_id, (_reference, code) in cases.items():
            with self.subTest(gateway=packet_id):
                frame = frames[packet_id]

                def gateway(method, path, *, body=None, headers=None):
                    return {"state": "FRAME_AVAILABLE", "frame": frame} if method == "GET" else {"state": "BLOCKED"}

                with fixed_clock(cycle.K, cycle.GW) as clock, mock.patch.object(cycle.GW, "_json_request", gateway):
                    result = cycle.GW.resident_gateway_cycle(self.repo)
                self.assertEqual(clock.reads, 0)
                self.assertEqual(result["state"], "BLOCKED")
                assert_six_fields(self, result["ingest_refusal"], code)


class CollectorIntegrityTests(_Workspace):
    """A tampered frame in the collector is refused and skipped, not raised."""

    def test_a_tampered_frame_does_not_abort_collection(self):
        K = _load("probe_collect_kernel", self.repo / "org-kernel" / "kernel.py")
        response = K.build_packet(origin_org=PEER, origin_service="p", destination_org=THIS,
                                  destination_service="admissible-existence.org-control",
                                  payload={"communication_id": "collect", "message_class": "ecosystem.communication.ack",
                                           "body": {"responding_organization": PEER}},
                                  standing=STANDING, packet_id="collect:response")
        frame = K.carrier_frame(response, epoch=4096)
        K.publish_frame({**frame, "frame_sha256": "sha256:" + "0" * 64}, root=self.mesh)
        K.publish_frame(frame, root=self.mesh)
        with fixed_clock(K) as clock:
            collected = K.collect_ecosystem_responses(THIS, "collect", mesh_root=self.mesh)
        self.assertEqual(clock.reads, 0)
        self.assertEqual(collected["response_count"], 1)
        refused, = collected["refused_frames"]
        assert_six_fields(self, refused, "FRAME_INTEGRITY_INVALID")


REQUEST_GATE = "python scripts/read_committed_request.py"
SELF_CLOSURE_PACKET = ".stegverse/intr-destination/self-closure-packet.json"
SELF_CLOSURE_READER = ("self_closure_packet.py --packet .stegverse/intr-destination/self-closure-packet.json"
                       " --require-hb-epoch")


def _triggers(workflow):
    return workflow.split("\non:", 1)[1].split("\npermissions:", 1)[0]


def _gate_argv(workflow):
    """The committed-request gate's argv, read from the workflow (folded or one line)."""
    import shlex
    lines = workflow.splitlines()
    first = next(index for index, line in enumerate(lines) if REQUEST_GATE in line)
    parts = [lines[first][lines[first].index(REQUEST_GATE):].strip()]
    for line in lines[first + 1:]:
        if not line.strip().startswith("--"):
            break
        parts.append(line.strip())
    return shlex.split(" ".join(parts))


def _run_gate(workflow, request_text, work):
    """Run the workflow's own gate against `request_text` in place of its committed request."""
    argv = _gate_argv(workflow)
    request = Path(work) / "request.json"
    request.write_text(request_text)
    argv[argv.index("--request") + 1] = str(request)
    env = {key: value for key, value in os.environ.items() if key != "GITHUB_OUTPUT"}
    return subprocess.run([sys.executable, *argv[1:]], cwd=ROOT, capture_output=True, text=True, env=env)


class HeartbeatWorkflowBindingTests(unittest.TestCase):
    """B-P36n, B-P40 COMMITTED_REQUEST: only a committed request with an epoch applies."""

    def setUp(self):
        self.workflow = (ROOT / ".github" / "workflows" / "heartbeat-response-node.yml").read_text()

    def test_apply_runs_only_with_the_committed_request_epoch(self):
        triggers = _triggers(self.workflow)
        # Only a push committing the request reaches the epoch-requiring entrypoint.
        self.assertNotIn("workflow_dispatch:", triggers)
        self.assertNotIn("schedule:", triggers)
        self.assertNotIn("inputs:", triggers)
        self.assertEqual([line.strip() for line in triggers.splitlines() if line.strip().startswith("- ")],
                         ['- "data/requests/heartbeat-response-node.json"'])
        step = self.workflow.split("- name: Receive and classify canonical heartbeat", 1)[1].split("- name:", 1)[0]
        self.assertIn("HB_EPOCH: ${{ steps.request.outputs.hb_epoch }}", step)
        applies = [line.strip() for line in step.splitlines() if "--apply" in line]
        self.assertEqual(applies, ['python scripts/process_heartbeat_response.py --apply --hb-epoch "$HB_EPOCH"'])
        # The request is gated before anything is invoked.
        self.assertLess(self.workflow.index(REQUEST_GATE), self.workflow.index("--apply"))
        self.assertEqual(_gate_argv(self.workflow)[2:],
                         ["--request", "data/requests/heartbeat-response-node.json"])

    def test_the_fail_closed_step_prints_the_six_fields(self):
        with tempfile.TemporaryDirectory() as work:
            for text, code in (("{}", "HB_EPOCH_NOT_SUPPLIED"), ('{"hb_epoch": "31"}', "HB_EPOCH_INVALID"),
                               ("{not json", "COMMITTED_REQUEST_INVALID")):
                with self.subTest(request=text):
                    completed = _run_gate(self.workflow, text, work)
                    self.assertEqual(completed.returncode, 1)
                    assert_six_fields(self, json.loads(completed.stdout), code)

    def test_every_epoch_requiring_workflow_starts_from_a_committed_request(self):
        entrypoints = ("process_heartbeat_response.py --apply", "intr_destination_ingress.py",
                       "organization_egress_boundary.py", "aggregate_repo_transition.py", "transition-ledger/emit.py",
                       "run_once.py", "federation_cycle.py", "ecosystem_control.py", "dispatch_ledger_writer.py")
        reached = set()
        for path in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
            text = path.read_text()
            runs = [line for line in text.splitlines()
                    if line.strip().startswith("python ") and "py_compile" not in line]
            if not any(entry in line for line in runs for entry in entrypoints):
                continue
            reached.add(path.name)
            with self.subTest(workflow=path.name):
                triggers = _triggers(text)
                for event in ("schedule:", "workflow_dispatch:", "pull_request", "inputs:"):
                    self.assertNotIn(event, triggers)
                paths = [line.strip()[2:].strip("'\"") for line in triggers.splitlines()
                         if line.strip().startswith("- ")]
                self.assertTrue(paths)
                first_run = min(text.index(line) for line in runs if any(entry in line for entry in entrypoints))
                if paths == [SELF_CLOSURE_PACKET]:
                    # Lane B's binding (#162): the committed self-closure packet supplies
                    # the epoch, read before the first epoch-requiring entrypoint runs.
                    self.assertLess(text.index(SELF_CLOSURE_READER), first_run)
                    self.assertIn('--hb-epoch "$HB_EPOCH"', text)
                else:
                    self.assertTrue(all(item.startswith("data/requests/") for item in paths), paths)
                    self.assertLess(text.index(REQUEST_GATE), first_run)
                    self.assertIn("${{ steps.request.outputs.hb_epoch }}", text)
        # organization-ledger-transition.yml was retired on main (19f74d6, Lane B).
        self.assertEqual(reached, {"heartbeat-response-node.yml", "resident-runtime-dispatch.yml",
                                   "ledger-writer-dispatch.yml"})


class ManifestDispatcherTests(unittest.TestCase):
    """B-P36n (lead 08:43Z), B-P40: every manifest entrypoint has an in-tree, committed-request dispatcher."""

    def setUp(self):
        self.manifest = json.loads((ROOT / "resident-runtime" / "activation-manifest.json").read_text())
        self.dispatcher = self.manifest["dispatcher"]
        self.workflow = (ROOT / self.dispatcher["workflow"]).read_text()
        self.step = self.workflow.split("- name: Invoke the declared entrypoint", 1)[1]

    def declared_entrypoints(self):
        return {self.manifest[key] for key in ("entrypoint", "ecosystem_control", "federation_cycle",
                                               "resident_cycle_entrypoint")}

    def test_the_dispatcher_is_declared_with_no_authority(self):
        self.assertEqual(self.dispatcher["trigger"], "COMMITTED_REQUEST")
        self.assertEqual(self.dispatcher["request"], "data/requests/resident-runtime-dispatch.json")
        self.assertEqual(self.dispatcher["authority_effect"], "NONE")
        self.assertEqual(self.dispatcher["hb_epoch"], {"from": "committed_request", "field": "hb_epoch",
                                                       "required": True, "absent": "HB_EPOCH_NOT_SUPPLIED"})
        self.assertIs(self.manifest["github_actions_is_runtime_authority"], False)
        triggers = _triggers(self.workflow)
        for event in ("workflow_dispatch:", "schedule:", "inputs:"):
            self.assertNotIn(event, triggers)
        self.assertIn('- "' + self.dispatcher["request"] + '"', triggers)
        argv = _gate_argv(self.workflow)
        self.assertEqual(argv[argv.index("--request") + 1], self.dispatcher["request"])

    def test_every_declared_entrypoint_is_bound_and_invoked(self):
        bindings = self.dispatcher["entrypoints"]
        self.assertEqual(set(bindings), self.declared_entrypoints())
        self.assertIn("HB_EPOCH: ${{ steps.request.outputs.hb_epoch }}", self.step)
        gate = self.workflow.index(REQUEST_GATE)
        for path, binding in bindings.items():
            with self.subTest(entrypoint=path):
                self.assertIn(binding, ("EPOCH_FREE", "EPOCH_REQUIRED"))
                invocations = [line.strip() for line in self.step.splitlines()
                               if line.strip().startswith("python " + path)]
                self.assertTrue(invocations, path)
                self.assertLess(gate, self.workflow.index("python " + path))
                source = (ROOT / path).read_text()
                if binding == "EPOCH_FREE":
                    self.assertNotIn("hb-epoch", source)
                    self.assertNotIn("hb_epoch", source)
                    self.assertTrue(all("--hb-epoch" not in line for line in invocations))
                else:
                    self.assertTrue(all('--hb-epoch "$HB_EPOCH"' in line for line in invocations))

    def test_the_gate_fails_closed_with_six_fields_before_anything_runs(self):
        with tempfile.TemporaryDirectory() as work:
            for request, code in (({"entrypoint": "federation_cycle"}, "HB_EPOCH_NOT_SUPPLIED"),
                                  ({"entrypoint": "federation_cycle", "hb_epoch": ""}, "HB_EPOCH_INVALID"),
                                  ({"entrypoint": "federation_cycle", "hb_epoch": "abc"}, "HB_EPOCH_INVALID"),
                                  ({"entrypoint": "federation_cycle", "hb_epoch": "31"}, "HB_EPOCH_INVALID"),
                                  ({"entrypoint": "status", "hb_epoch": "4096"}, "COMMITTED_REQUEST_INVALID"),
                                  ({"entrypoint": "run_once", "hb_epoch": "4096", "ingress": "a\nb"},
                                   "COMMITTED_REQUEST_INVALID")):
                with self.subTest(request=request):
                    completed = _run_gate(self.workflow, json.dumps(request), work)
                    self.assertEqual(completed.returncode, 1)
                    assert_six_fields(self, json.loads(completed.stdout), code)
            passed = _run_gate(self.workflow, json.dumps({"entrypoint": "run_once", "hb_epoch": "4096",
                                                          "ingress": "data/ingress.json"}), work)
            self.assertEqual(passed.returncode, 0, passed.stdout)
            self.assertEqual(json.loads(passed.stdout)["hb_epoch"], "4096")


class UnreadableFrameFileTests(_Workspace):
    """F-SCAN: a frames.d file that is not a JSON object is refused by name; the cycle continues."""

    def test_malformed_frame_files_are_quarantined_and_valid_frames_proceed(self):
        K = _load("probe_scan_kernel", self.repo / "org-kernel" / "kernel.py")
        frames = self.mesh / "frames.d"
        frames.mkdir(parents=True)
        (frames / "0000-not-json.json").write_text("{not json")
        (frames / "0001-a-list.json").write_text("[1,2,3]")
        (frames / "0002-not-utf8.json").write_bytes(b'{"destination_org": "\xff\xfe"}')
        (frames / "0003-oversized.json").write_text(json.dumps({"pad": "x" * 60_000}))
        (frames / "0004-a-directory.json").mkdir()
        K.publish_packet(self.packet(K, "admissible-existence.org-control",
                                     control("ecosystem.communication", "after-bad-files"), "after-bad-files"),
                         root=self.mesh, epoch=4096)
        K.FRAME_FILE_MAX_BYTES = 50_000  # well above a frame, below the oversized file
        with fixed_clock(K) as clock:
            first = K.consume_and_respond(self.repo, mesh_root=self.mesh)
            again = K.consume_and_respond(self.repo, mesh_root=self.mesh)
            collected = K.collect_ecosystem_responses(THIS, "after-bad-files", mesh_root=self.mesh)
        self.assertEqual(clock.reads, 0)
        self.assertEqual(again, [])
        by_name = {Path(item["path"]).name: item for item in first}
        bad = ("0000-not-json.json", "0001-a-list.json", "0002-not-utf8.json", "0003-oversized.json",
               "0004-a-directory.json")
        for name in bad:
            with self.subTest(file=name):
                assert_six_fields(self, by_name[name]["result"], "FRAME_INGEST_FAILED")
                marker = json.loads(Path(by_name[name]["seen_marker"]).read_text())
                self.assertEqual(marker["frame_name"], name)
                self.assertEqual(marker["refused_failure_code"], "FRAME_INGEST_FAILED")
        consumed = [item for item in first if item["result"].get("status") == "CONSUMED"]
        self.assertEqual([item["result"]["packet"]["packet_id"] for item in consumed], ["after-bad-files"])
        self.assertEqual(len(collected["refused_frames"]), len(bad))
        self.assertIn("UnicodeDecodeError", by_name["0002-not-utf8.json"]["result"]["detail"])
        self.assertIn("frame_file_exceeds_50000_bytes", by_name["0003-oversized.json"]["result"]["detail"])
        self.assertEqual(by_name["0004-a-directory.json"]["result"]["failed_predicate"], "IsADirectoryError")


class LedgerWriterDispatcherTests(unittest.TestCase):
    """B-P36n: every epoch-requiring writer has an in-tree, gate-first, manifest-bound dispatcher."""

    def setUp(self):
        self.manifest = json.loads((ROOT / "resident-runtime" / "activation-manifest.json").read_text())
        self.binding = self.manifest["dispatcher"]["ledger_writers"]
        self.dispatch = _load("probe_dispatch_ledger_writer", ROOT / self.binding["dispatch_script"])

    def test_the_manifest_binds_every_writer_with_no_authority(self):
        self.assertEqual(self.binding["authority_effect"], "NONE")
        self.assertEqual(self.binding["hb_epoch"]["required"], True)
        self.assertEqual(set(self.binding["entrypoints"]), set(self.dispatch.WRITERS.values()))
        self.assertEqual(set(self.binding["entrypoints"].values()), {"EPOCH_REQUIRED"})
        self.assertEqual(self.binding["trigger"], "COMMITTED_REQUEST")
        self.assertEqual(self.binding["hb_epoch"]["from"], "committed_request")
        workflow = (ROOT / self.binding["workflow"]).read_text()
        triggers = _triggers(workflow)
        for event in ("workflow_dispatch:", "schedule:", "inputs:"):
            self.assertNotIn(event, triggers)
        self.assertIn('- "' + self.binding["request"] + '"', triggers)
        argv = _gate_argv(workflow)
        self.assertEqual(argv[argv.index("--request") + 1], self.binding["request"])
        choice = next(item for item in argv if item.startswith("writer="))
        self.assertEqual(set(choice.split("=", 1)[1].split(",")), set(self.dispatch.WRITERS))
        self.assertLess(workflow.index(REQUEST_GATE), workflow.index("python " + self.binding["dispatch_script"]))
        pending = self.manifest["runtime_dispatcher_pending_substrate"]
        for name in ("failure_code", "failed_predicate", "required_evidence_or_repair",
                     "retry_entrypoint", "owning_existing_goal", "next_attempt"):
            self.assertTrue(pending[name], name)
        self.assertEqual(pending["failure_code"], "RUNTIME_DISPATCHER_PENDING_SUBSTRATE")

    def test_the_gate_refuses_before_any_writer_runs(self):
        for epoch, code in ((None, "HB_EPOCH_NOT_SUPPLIED"), ("", "HB_EPOCH_NOT_SUPPLIED"),
                            ("abc", "HB_EPOCH_INVALID"), ("31", "HB_EPOCH_INVALID")):
            with self.subTest(epoch=epoch):
                with contextlib.redirect_stdout(io.StringIO()) as out, \
                        mock.patch.object(self.dispatch.subprocess, "run",
                                          side_effect=AssertionError("a writer ran")), \
                        self.assertRaises(SystemExit) as exited:
                    self.dispatch.command("repository-ledger-emit", epoch, "--transition-id t")
                self.assertEqual(exited.exception.code, 1)
                assert_six_fields(self, json.loads(out.getvalue()), code)

    def test_a_supplied_epoch_reaches_the_writer(self):
        argv = self.dispatch.command("repository-ledger-emit", "4096", "--transition-id 'a b' --transition-class C")
        self.assertEqual(argv[1:], [".stegverse/transition-ledger/emit.py", "--transition-id", "a b",
                                    "--transition-class", "C", "--hb-epoch", "4096"])
        with self.assertRaises(SystemExit):
            self.dispatch.command("repository-ledger-emit", "4096", "--hb-epoch 5")

    def test_the_dispatched_emit_writes_a_receipt_at_the_supplied_epoch(self):
        import os
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as work:
            env = {**os.environ, "STEGVERSE_REPO_LEDGER_ROOT": str(Path(work) / "repo-ledger")}
            completed = subprocess.run(
                [sys.executable, str(ROOT / self.binding["dispatch_script"]), "--writer", "repository-ledger-emit",
                 "--hb-epoch", "4096", "--arguments",
                 "--transition-id dispatch-probe --transition-class PROBE "
                 "--predecessor-state-sha256 sha256:" + "0" * 64 + " --successor-state-sha256 sha256:" + "1" * 64],
                cwd=ROOT, capture_output=True, text=True, env=env)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            receipt = json.loads(completed.stdout)
            self.assertEqual(receipt["hb_reference"]["epoch"], 4096)
            self.assertIs(receipt["hb_reference"]["derived_from_clock"], False)


class GatewayFetchGuardTests(_Workspace):
    """The gateway refuses a malformed fetch or frame with six fields; nothing escapes."""

    def run_cycle(self, fetched):
        cycle = _load("probe_fetch_guard_cycle", self.repo / "resident-runtime" / "federation_cycle.py")
        GW = cycle.GW
        acks = []

        def gateway(method, path, *, body=None, headers=None):
            if method == "GET":
                if fetched == "RAISE_NOT_JSON":
                    raise GW.FederationGatewayTransportError("gateway response is not JSON")
                return fetched
            acks.append(body)
            return {"state": "BLOCKED"}

        with fixed_clock(cycle.K, GW) as clock, mock.patch.object(GW, "_json_request", gateway):
            result = GW.resident_gateway_cycle(self.repo)
        self.assertEqual(clock.reads, 0)
        return GW, result, acks

    def test_a_malformed_fetch_is_refused(self):
        for fetched in ([1, 2], "text", {"state": "SOMETHING_ELSE"}):
            with self.subTest(fetched=fetched):
                _GW, result, acks = self.run_cycle(fetched)
                assert_six_fields(self, result, "GATEWAY_FETCH_INVALID")
                self.assertEqual(acks, [])

    def test_a_fetch_that_is_not_json_is_refused(self):
        _GW, result, acks = self.run_cycle("RAISE_NOT_JSON")
        assert_six_fields(self, result, "GATEWAY_FETCH_INVALID")
        self.assertEqual(acks, [])

    def test_a_non_object_frame_is_blocked_with_six_fields(self):
        for frame in ([1, 2, 3], "frame", None):
            with self.subTest(frame=frame):
                _GW, result, acks = self.run_cycle({"state": "FRAME_AVAILABLE", "frame": frame})
                self.assertEqual(result["state"], "BLOCKED")
                assert_six_fields(self, result["ingest_refusal"], "FRAME_INGEST_FAILED")
                self.assertEqual(len(acks), 1)
                self.assertIsNone(acks[0]["observed_at"])

    def test_a_tampered_frame_ack_echoes_no_epoch(self):
        K = _load("probe_tamper_ack_kernel", self.repo / "org-kernel" / "kernel.py")
        frame = K.carrier_frame(self.packet(K, "admissible-existence.org-control",
                                            control("ecosystem.communication", "tampered"), "tampered"), epoch=4096)
        _GW, result, acks = self.run_cycle({"state": "FRAME_AVAILABLE",
                                            "frame": {**frame, "frame_sha256": "sha256:" + "0" * 64}})
        assert_six_fields(self, result["ingest_refusal"], "FRAME_INTEGRITY_INVALID")
        self.assertIsNone(acks[0]["observed_at"])


class TotalGuardAndIoTests(_Workspace):
    """F-TYPE and the IO row: the per-frame guard is total; this boundary's own I/O failure is not terminal."""

    INTR = FrameIngestErrorTests.INTR

    def setUp(self):
        super().setUp()
        self.K = _load("probe_total_guard_kernel", self.repo / "org-kernel" / "kernel.py")

    def frame(self, packet_id):
        payload = {**self.INTR, "communication_id": packet_id}
        return self.K.carrier_frame(self.packet(self.K, "admissible-existence.intr-destination", payload, packet_id),
                                    epoch=4096)

    def wrong_typed(self, packet_id, field, value):
        frame = self.frame(packet_id)
        body = {key: item for key, item in frame.items() if key != "frame_sha256"}
        body[field] = value
        return {**body, "frame_sha256": self.K.sha(body)}

    def org_receipts(self):
        root = self.work / "org-ledger"
        return [json.loads(path.read_text()) for path in root.rglob("*.json")
                if json.loads(path.read_text()).get("schema") == "stegverse.organization-transition-receipt/v1"] \
            if root.exists() else []

    def repo_receipts(self):
        root = self.work / "repo-ledger"
        return [json.loads(path.read_text()) for path in root.rglob("*.json")
                if json.loads(path.read_text()).get("schema") == "stegverse.repo-transition-receipt/v1"] \
            if root.exists() else []

    def test_wrong_typed_fields_before_and_after_a_valid_frame_are_quarantined(self):
        bad = {"type-%d" % index: self.wrong_typed("type-%d" % index, field, value)
               for index, (field, value) in enumerate((("packet_base64", 123), ("packet_base64", None),
                                                       ("packet_base64", [1]), ("packet_base64", {"a": 1}),
                                                       ("packet_sha256", 5), ("heartbeat_reference", [4096])))}
        names = sorted(FrameIngestErrorTests.name(frame) for frame in bad.values())
        for index in range(5000):
            valid = self.frame("typed-valid-%d" % index)
            if names[0] < FrameIngestErrorTests.name(valid) < names[-1]:
                break
        for frame in bad.values():
            self.K.publish_frame(frame, root=self.mesh)
        self.K.publish_frame(valid, root=self.mesh)
        with fixed_clock(self.K) as clock:
            first = self.K.consume_and_respond(self.repo, mesh_root=self.mesh)
            again = self.K.consume_and_respond(self.repo, mesh_root=self.mesh)
        self.assertEqual(clock.reads, 0)
        self.assertEqual(again, [])
        by_id = {item["result"].get("packet_id") or item["result"]["packet"]["packet_id"]: item for item in first}
        for packet_id in bad:
            with self.subTest(frame=packet_id):
                result = by_id[packet_id]["result"]
                self.assertIn(result["failure_code"], ("FRAME_INGEST_FAILED", "FRAME_INTEGRITY_INVALID",
                                                       "HB_EPOCH_INVALID", "HB_EPOCH_NOT_SUPPLIED"))
                assert_six_fields(self, result, result["failure_code"])
                self.assertIsNotNone(by_id[packet_id]["seen_marker"])
        self.assertEqual(by_id[valid["packet_id"]]["result"]["status"], "CONSUMED")
        self.assertEqual([receipt["repo_transition_id"] for receipt in self.org_receipts()],
                         ["ORGANIZATION_INTR_DESTINATION_INGRESS:" + valid["packet_id"]])
        attribute = by_id["type-0"]["result"]
        self.assertEqual((attribute["failure_code"], attribute["failed_predicate"]),
                         ("FRAME_INGEST_FAILED", "AttributeError"))

    def test_the_gateway_blocks_a_wrong_typed_frame(self):
        cycle = _load("probe_total_guard_cycle", self.repo / "resident-runtime" / "federation_cycle.py")
        frame = self.wrong_typed("gateway-typed", "packet_base64", 123)
        acks = []

        def gateway(method, path, *, body=None, headers=None):
            if method == "GET":
                return {"state": "FRAME_AVAILABLE", "frame": frame}
            acks.append(body)
            return {"state": "BLOCKED"}

        with fixed_clock(cycle.K, cycle.GW) as clock, mock.patch.object(cycle.GW, "_json_request", gateway):
            result = cycle.GW.resident_gateway_cycle(self.repo)
        self.assertEqual(clock.reads, 0)
        self.assertEqual(result["state"], "BLOCKED")
        assert_six_fields(self, result["ingest_refusal"], "FRAME_INGEST_FAILED")
        self.assertEqual(len(acks), 1)

    def test_an_io_failure_on_the_ledger_write_leaves_the_frame_pending_and_consumes_it_once(self):
        import os as os_module
        valid = self.frame("io-pending")
        self.K.publish_frame(valid, root=self.mesh)
        real_replace = os_module.replace
        org_root = str(self.work / "org-ledger")

        def failing_replace(source, destination, *args, **kwargs):
            if str(destination).startswith(org_root):
                raise OSError(28, "No space left on device")
            return real_replace(source, destination, *args, **kwargs)

        with mock.patch("os.replace", side_effect=failing_replace):
            first = self.K.consume_and_respond(self.repo, mesh_root=self.mesh)
        item, = first
        assert_six_fields(self, item["result"], "FRAME_DISPATCH_IO_FAILED")
        self.assertEqual(item["result"]["failed_predicate"], "OSError")
        self.assertIsNone(item["seen_marker"])
        self.assertEqual(self.org_receipts(), [])
        # Pending, not quarantined: the next cycle consumes it exactly once.
        second = self.K.consume_and_respond(self.repo, mesh_root=self.mesh)
        self.assertEqual([entry["result"]["status"] for entry in second], ["CONSUMED"])
        self.assertEqual(len(self.repo_receipts()), 1)
        self.assertEqual(len(self.org_receipts()), 1)
        self.assertEqual(self.K.consume_and_respond(self.repo, mesh_root=self.mesh), [])

    def test_the_gateway_does_not_acknowledge_a_frame_pending_on_its_own_io(self):
        cycle = _load("probe_io_cycle", self.repo / "resident-runtime" / "federation_cycle.py")
        frame = self.frame("gateway-io")
        acks = []

        def gateway(method, path, *, body=None, headers=None):
            if method == "GET":
                return {"state": "FRAME_AVAILABLE", "frame": frame}
            acks.append(body)
            return {"state": "OK"}

        with mock.patch.object(cycle.GW, "_json_request", gateway), \
                mock.patch.object(cycle.GW.K, "dispatch", side_effect=OSError(5, "I/O error")):
            result = cycle.GW.resident_gateway_cycle(self.repo)
        self.assertEqual(result["state"], "PENDING_IO")
        assert_six_fields(self, result["ingest_refusal"], "FRAME_DISPATCH_IO_FAILED")
        self.assertEqual(acks, [])


class ResidentEntrypointEpochTests(_Workspace):
    """EPOCH_FREE_CLAIM_INACCURATE: each dispatched entrypoint stamps what it writes at the supplied epoch."""

    def test_federation_cycle_refuses_without_an_epoch_and_writes_nothing(self):
        cycle = _load("probe_cycle_refusal", self.repo / "resident-runtime" / "federation_cycle.py")
        latest = self.repo / "resident-runtime" / "federation" / "latest-cycle.json"
        for argv, code in (([], "HB_EPOCH_NOT_SUPPLIED"), (["--hb-epoch", "abc"], "HB_EPOCH_INVALID"),
                           (["--hb-epoch", "31"], "HB_EPOCH_INVALID")):
            with self.subTest(argv=argv):
                with fixed_clock(cycle.K, cycle.GW) as clock, contextlib.redirect_stdout(io.StringIO()) as out:
                    self.assertEqual(cycle.main(argv), 1)
                self.assertEqual(clock.reads, 0)
                assert_six_fields(self, json.loads(out.getvalue()), code)
                self.assertFalse(latest.exists())

    def test_federation_cycle_stamps_its_record_at_the_supplied_epoch_with_no_clock(self):
        cycle = _load("probe_cycle_stamp", self.repo / "resident-runtime" / "federation_cycle.py")
        with fixed_clock(cycle.K, cycle.GW) as clock, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cycle.main(["--hb-epoch", "4096"]), 0)
        self.assertEqual(clock.reads, 0)
        record = json.loads((self.repo / "resident-runtime" / "federation" / "latest-cycle.json").read_text())
        self.assertEqual(record["heartbeat_reference"], kernel.hb_reference(epoch=4096))

    def test_the_gateway_cycle_record_is_stamped_at_the_supplied_epoch(self):
        cycle = _load("probe_cycle_gateway_stamp", self.repo / "resident-runtime" / "federation_cycle.py")
        os.environ["STEGVERSE_ORG_FEDERATION_GATEWAY_URL"] = "https://gateway.invalid"
        with fixed_clock(cycle.K, cycle.GW) as clock, contextlib.redirect_stdout(io.StringIO()), \
                mock.patch.object(cycle.GW, "_json_request", lambda *a, **k: {"state": "NO_FRAME"}):
            self.assertEqual(cycle.main(["--hb-epoch", "4096"]), 0)
        self.assertEqual(clock.reads, 0)
        record = json.loads((self.repo / "resident-runtime" / "federation" / "latest-cycle.json").read_text())
        self.assertEqual(record["heartbeat_reference"], kernel.hb_reference(epoch=4096))

    def test_run_once_stamps_the_egress_carrier_at_the_supplied_epoch(self):
        import subprocess
        import sys
        K = _load("probe_run_once_kernel", self.repo / "org-kernel" / "kernel.py")
        transport = _load("probe_run_once_transport", self.repo / "org-boundary" / "runtime" / "intr_transport.py")
        ingress = transport.build_ingress({"org": PEER, "service": "p"},
                                          {"org": THIS, "service": "admissible-existence.boundary-diagnostic"},
                                          {"probe": 1}, "org-federation", "probe", packet_id="run-once", epoch=4096)
        envelope = self.work / "ingress.json"
        envelope.write_text(json.dumps(ingress))
        egress = self.work / "egress.json"
        base = [sys.executable, "resident-runtime/run_once.py", "--ingress", str(envelope), "--egress", str(egress)]
        refused = subprocess.run(base, cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(refused.returncode, 1)
        assert_six_fields(self, json.loads(refused.stdout), "HB_EPOCH_NOT_SUPPLIED")
        self.assertFalse(egress.exists())
        completed = subprocess.run(base + ["--hb-epoch", "4096"], cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        carrier = json.loads(egress.read_text())["carrier"]
        self.assertEqual((carrier["observed_at"], carrier["derived_from_clock"]), ("HB:4096", False))
        self.assertEqual(ingress["carrier"]["observed_at"], "HB:4096")
        del K

    def test_ecosystem_control_status_refuses_without_an_epoch_and_carries_one(self):
        import subprocess
        import sys
        base = [sys.executable, "resident-runtime/ecosystem_control.py"]
        refused = subprocess.run(base + ["status"], cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(refused.returncode, 1)
        assert_six_fields(self, json.loads(refused.stdout), "HB_EPOCH_NOT_SUPPLIED")
        status = subprocess.run(base + ["--hb-epoch", "4096", "status"], cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertEqual(json.loads(status.stdout)["heartbeat_reference"]["epoch"], 4096)
        abbreviated = subprocess.run(base + ["--hb-ep", "4096", "status"], cwd=self.repo, capture_output=True, text=True)
        self.assertNotEqual(abbreviated.returncode, 0)

    def test_a_wrong_typed_destination_is_quarantined_not_skipped(self):
        K = _load("probe_destination_kernel", self.repo / "org-kernel" / "kernel.py")
        frames = self.mesh / "frames.d"
        frames.mkdir(parents=True)
        (frames / "wrong-destination.json").write_text(json.dumps({"destination_org": 5, "packet_id": "x"}))
        item, = K.consume_and_respond(self.repo, mesh_root=self.mesh)
        assert_six_fields(self, item["result"], "FRAME_INGEST_FAILED")
        self.assertEqual(item["result"]["failed_predicate"], "TypeError")
        self.assertIsNotNone(item["seen_marker"])

    def test_the_ledger_dispatcher_refuses_an_epoch_in_arguments_with_six_fields(self):
        dispatch = _load("probe_dispatch_conflict", ROOT / "scripts" / "dispatch_ledger_writer.py")
        for arguments in ("--hb-epoch 77", "--hb-epoch=77", "--hb-ep 77", "--hb-e 77", "--hb 77"):
            with self.subTest(arguments=arguments):
                with contextlib.redirect_stdout(io.StringIO()) as out, self.assertRaises(SystemExit) as exited:
                    dispatch.command("repository-ledger-emit", "4096", arguments)
                self.assertEqual(exited.exception.code, 1)
                assert_six_fields(self, json.loads(out.getvalue()), "HB_EPOCH_CONFLICT")


class OwnStateWriteFaultTests(_Workspace):
    """F-TRANSIENT-RT: a fault writing this boundary's own ledger leaves the frame pending, then consumed once."""

    LOSSY = """

import os as _probe_os
_probe_append = PosixLedgerStore.append_transaction
def _probe_lossy_append(self, *args, **kwargs):
    lost = _probe_os.environ.get("PROBE_LOSE_CAS")
    if lost and str(self.root).startswith(lost):
        return False
    return _probe_append(self, *args, **kwargs)
PosixLedgerStore.append_transaction = _probe_lossy_append
"""

    def setUp(self):
        super().setUp()
        store = self.repo / "resident-runtime" / "ledger_store.py"
        store.write_text(store.read_text() + self.LOSSY)
        self.K = _load("probe_own_state_kernel", self.repo / "org-kernel" / "kernel.py")

    def receipts(self, ledger, schema):
        root = self.work / ledger
        return [json.loads(path.read_text()) for path in root.rglob("*.json")
                if json.loads(path.read_text()).get("schema") == schema] if root.exists() else []

    def publish(self, packet_id):
        payload = {**FrameIngestErrorTests.INTR, "communication_id": packet_id}
        self.K.publish_packet(self.packet(self.K, "admissible-existence.intr-destination", payload, packet_id),
                              root=self.mesh, epoch=4096)

    def test_a_lost_comparison_on_each_append_leaves_the_frame_pending_then_consumes_it_once(self):
        for ledger in ("repo-ledger", "org-ledger"):
            with self.subTest(lost=ledger):
                packet_id = "lost-" + ledger
                self.publish(packet_id)
                os.environ["PROBE_LOSE_CAS"] = str(self.work / ledger)
                try:
                    with fixed_clock(self.K) as clock:
                        first = self.K.consume_and_respond(self.repo, mesh_root=self.mesh)
                finally:
                    del os.environ["PROBE_LOSE_CAS"]
                self.assertEqual(clock.reads, 0)
                item, = [entry for entry in first if entry["result"].get("packet_id") == packet_id]
                assert_six_fields(self, item["result"], "FRAME_DISPATCH_IO_FAILED")
                self.assertIs(item["result"]["terminal"], False)
                self.assertEqual(item["result"]["failed_predicate"], "LedgerWriteFault")
                self.assertIsNone(item["seen_marker"])
                second = self.K.consume_and_respond(self.repo, mesh_root=self.mesh)
                self.assertEqual([entry["result"]["status"] for entry in second], ["CONSUMED"])
                self.assertEqual(self.K.consume_and_respond(self.repo, mesh_root=self.mesh), [])
        # Exactly once: one receipt per frame at each level, no duplicate or orphan.
        repository = self.receipts("repo-ledger", "stegverse.repo-transition-receipt/v1")
        organization = self.receipts("org-ledger", "stegverse.organization-transition-receipt/v1")
        self.assertEqual(sorted(receipt["transition_id"] for receipt in repository),
                         ["ORGANIZATION_INTR_DESTINATION_INGRESS:lost-org-ledger",
                          "ORGANIZATION_INTR_DESTINATION_INGRESS:lost-repo-ledger"])
        self.assertEqual(len(organization), 2)
        self.assertEqual({receipt["repo_receipt_sha256"] for receipt in organization},
                         {receipt["receipt_sha256"] for receipt in repository})

    def test_own_state_faults_are_classified_before_the_content_guard(self):
        store = _load("probe_fault_store", self.repo / "resident-runtime" / "ledger_store.py")
        self.assertTrue(self.K.is_own_state_fault(store.LedgerWriteFault("ledger_store_collision")))
        self.assertTrue(self.K.is_own_state_fault(OSError(28, "full")))
        self.assertFalse(self.K.is_own_state_fault(ValueError("carrier_frame_hash_mismatch")))
        self.assertFalse(self.K.is_own_state_fault(AttributeError("x")))


class CarriedCrossingsNotAcceptedTests(_Workspace):
    """B-P36m (09:03Z), option (1): this destination declares it accepts no CARRIED crossings."""

    def test_the_manifest_declares_no_carried_crossings(self):
        manifest = json.loads((ROOT / "resident-runtime" / "activation-manifest.json").read_text())
        self.assertIs(manifest["accepts_carried_crossings"], False)

    def test_a_valid_carried_frame_is_not_accepted_and_a_forged_one_gets_its_content_code(self):
        K = _load("probe_carried_kernel_m", self.repo / "org-kernel" / "kernel.py")
        carried = {**K.hb_reference(epoch=4096), "source": "ORGANIZATION_LEDGER_HEAD",
                   "head_receipt_sha": "sha256:" + "a" * 64}
        cases = {
            "valid-carried": (carried, "CARRIED_NOT_ACCEPTED_BY_DESTINATION"),
            "forged-unflagged": ({key: value for key, value in carried.items() if key != "derived_from_clock"},
                                 "HB_EPOCH_PROVENANCE_UNMARKED"),
            "forged-generation": ({**carried, "generation": 77}, "HB_REFERENCE_INVALID"),
            "forged-epoch": ({**carried, "epoch": "abc"}, "HB_EPOCH_INVALID"),
        }
        service = "admissible-existence.org-control"
        for packet_id, (reference, _code) in cases.items():
            frame = K.carrier_frame(self.packet(K, service, control("ecosystem.communication", packet_id), packet_id),
                                    epoch=4096)
            body = {key: value for key, value in frame.items() if key != "frame_sha256"}
            body["heartbeat_reference"] = reference
            K.publish_frame({**body, "frame_sha256": K.sha(body)}, root=self.mesh)
        sampled = K.carrier_frame(self.packet(K, service, control("ecosystem.communication", "forged-sampled"),
                                              "forged-sampled"), epoch=4096)
        body = {key: value for key, value in sampled.items() if key != "frame_sha256"}
        body["heartbeat_reference"] = {**carried, "sampled_unix_ns": INSTANT_NS}
        K.publish_frame({**body, "frame_sha256": K.sha(body)}, root=self.mesh)
        tampered = K.carrier_frame(self.packet(K, service, control("ecosystem.communication", "forged-hash"),
                                               "forged-hash"), epoch=4096)
        body = {key: value for key, value in tampered.items() if key != "frame_sha256"}
        body["heartbeat_reference"] = carried
        K.publish_frame({**body, "frame_sha256": "sha256:" + "0" * 64}, root=self.mesh)
        with fixed_clock(K) as clock:
            results = K.consume_and_respond(self.repo, mesh_root=self.mesh)
        self.assertEqual(clock.reads, 0)
        by_id = {item["result"].get("packet_id") or item["result"]["packet"]["packet_id"]: item["result"]
                 for item in results}
        # A CARRIED claim on a clock-form reference is refused, never consumed as a clock frame.
        for packet_id, (_reference, code) in {**cases, "forged-hash": (None, "FRAME_INTEGRITY_INVALID"),
                                               "forged-sampled": (None, "CARRIED_NOT_ACCEPTED_BY_DESTINATION")}.items():
            with self.subTest(frame=packet_id):
                assert_six_fields(self, by_id[packet_id], code)
                self.assertNotEqual(by_id[packet_id]["failure_code"], "CARRIED_PROVENANCE_UNVERIFIED")
        valid = by_id["valid-carried"]
        self.assertEqual(valid["required_evidence_or_repair"], "re-send with the SUPPLIED epoch")
        self.assertTrue(valid["retry_entrypoint"].startswith("the sender's hop: " + PEER))
        self.assertFalse((self.work / "repo-ledger").exists())


class ResponseOnceTests(_Workspace):
    """RESPONSE_REPUBLISHED_AFTER_POST_PUBLISH_FAULT: one response per request, whatever fault follows it."""

    def setUp(self):
        super().setUp()
        self.K = _load("probe_response_once_kernel", self.repo / "org-kernel" / "kernel.py")

    def request(self, packet_id):
        payload = {**FrameIngestErrorTests.INTR, "communication_id": packet_id}
        return self.K.carrier_frame(self.packet(self.K, "admissible-existence.intr-destination", payload, packet_id),
                                    epoch=4096)

    def responses_to(self, organization):
        directory = self.mesh / "frames.d"
        return [frame for frame in (json.loads(path.read_text()) for path in directory.glob("*.json"))
                if frame.get("destination_org") == organization]

    def test_a_seen_marker_fault_after_publication_does_not_republish(self):
        self.K.publish_frame(self.request("marker-fault"), root=self.mesh)
        real = self.K.mark_federation_frame_seen
        with mock.patch.object(self.K, "mark_federation_frame_seen", side_effect=OSError(28, "full")):
            first = self.K.consume_and_respond(self.repo, mesh_root=self.mesh)
        assert_six_fields(self, first[0]["result"], "FRAME_DISPATCH_IO_FAILED")
        self.assertEqual(len(self.responses_to(PEER)), 1)
        self.assertIs(self.K.mark_federation_frame_seen, real)
        second = self.K.consume_and_respond(self.repo, mesh_root=self.mesh)
        self.assertEqual(second[0]["result"]["status"], "CONSUMED")
        self.assertIs(second[0]["response_publication"]["already_published"], True)
        self.assertEqual(len(self.responses_to(PEER)), 1)
        self.assertEqual(self.K.consume_and_respond(self.repo, mesh_root=self.mesh), [])

    def test_an_ack_fault_after_submission_does_not_resubmit(self):
        cycle = _load("probe_response_once_cycle", self.repo / "resident-runtime" / "federation_cycle.py")
        frame = self.request("ack-fault")
        submitted, failures = [], {"ack": 1}

        def gateway(method, path, *, body=None, headers=None):
            if method == "GET":
                return {"state": "FRAME_AVAILABLE", "frame": frame}
            if path.endswith("/frames"):
                submitted.append(body)
                return {"state": "PENDING"}
            if failures["ack"]:
                failures["ack"] -= 1
                raise OSError(104, "connection reset")
            return {"state": "CONSUMED"}

        with mock.patch.object(cycle.GW, "_json_request", gateway):
            first = cycle.GW.resident_gateway_cycle(self.repo)
            second = cycle.GW.resident_gateway_cycle(self.repo)
        self.assertEqual(first["state"], "PENDING_IO")
        self.assertEqual(second["state"], "CONSUMED")
        self.assertEqual(len(submitted), 1)
        self.assertEqual(second["responses_emitted"], 0)


class ClockFormCarriedClaimTests(_Workspace):
    """CLOCK_FRAME_CARRIED_CLAIM_CONSUMED: a CARRIED claim on a clock-form frame is refused, never consumed."""

    def reframe(self, K, packet_id, reference):
        frame = K.carrier_frame(self.packet(K, "admissible-existence.org-control",
                                            control("ecosystem.communication", packet_id), packet_id), epoch=4096)
        body = {key: value for key, value in frame.items() if key != "frame_sha256"}
        body["heartbeat_reference"] = reference
        return {**body, "frame_sha256": K.sha(body)}

    def kinds(self, K):
        claim = {"source": "ORGANIZATION_LEDGER_HEAD", "head_receipt_sha": "sha256:" + "f" * 64}
        supplied = K.hb_reference(epoch=4096)
        sampled = K.hb_reference(now_ns=INSTANT_NS)
        unflagged = {key: value for key, value in supplied.items() if key != "derived_from_clock"}
        return {
            "c-flag-carried": ({**supplied, "derived_from_clock": True, "sampled_unix_ns": INSTANT_NS, **claim},
                               "CARRIED_NOT_ACCEPTED_BY_DESTINATION"),
            "c-bare-carried": ({**sampled, **claim}, "CARRIED_NOT_ACCEPTED_BY_DESTINATION"),
            "c-flagonly-carried": ({**supplied, "derived_from_clock": True, **claim},
                                   "CARRIED_NOT_ACCEPTED_BY_DESTINATION"),
            "forged-ii": ({**unflagged, "sampled_unix_ns": INSTANT_NS, **claim},
                          "CARRIED_NOT_ACCEPTED_BY_DESTINATION"),
            "c-flag-carried-bad-epoch": ({**supplied, "derived_from_clock": True, "epoch": "abc", **claim},
                                         "HB_EPOCH_INVALID"),
        }

    def test_each_kind_is_refused_and_quarantined(self):
        K = _load("probe_clock_carried_kernel", self.repo / "org-kernel" / "kernel.py")
        kinds = self.kinds(K)
        for packet_id, (reference, _code) in kinds.items():
            K.publish_frame(self.reframe(K, packet_id, reference), root=self.mesh)
        with fixed_clock(K) as clock:
            results = K.consume_and_respond(self.repo, mesh_root=self.mesh)
            again = K.consume_and_respond(self.repo, mesh_root=self.mesh)
        self.assertEqual(clock.reads, 0)
        self.assertEqual(again, [])
        by_id = {item["result"].get("packet_id"): item for item in results}
        for packet_id, (_reference, code) in kinds.items():
            with self.subTest(kind=packet_id):
                assert_six_fields(self, by_id[packet_id]["result"], code)
                marker = json.loads(Path(by_id[packet_id]["seen_marker"]).read_text())
                self.assertEqual(marker["refused_failure_code"], code)
                self.assertIsNone(by_id[packet_id]["response_publication"])

    def test_the_gateway_blocks_each_kind(self):
        cycle = _load("probe_clock_carried_cycle", self.repo / "resident-runtime" / "federation_cycle.py")
        for packet_id, (reference, code) in self.kinds(cycle.GW.K).items():
            with self.subTest(kind=packet_id):
                frame = self.reframe(cycle.GW.K, packet_id, reference)
                acks = []

                def gateway(method, path, *, body=None, headers=None):
                    if method == "GET":
                        return {"state": "FRAME_AVAILABLE", "frame": frame}
                    acks.append(body)
                    return {"state": "BLOCKED"}

                with mock.patch.object(cycle.GW, "_json_request", gateway):
                    result = cycle.GW.resident_gateway_cycle(self.repo)
                self.assertEqual(result["state"], "BLOCKED")
                assert_six_fields(self, result["ingest_refusal"], code)
                self.assertEqual([ack["state"] for ack in acks], ["BLOCKED"])


class TornWriteTests(_Workspace):
    """A fault between a receipt write and the HEAD advance leaves the frame pending and the store recoverable."""

    def test_a_head_write_fault_rolls_forward_to_exactly_one_receipt(self):
        import os as os_module
        K = _load("probe_torn_kernel", self.repo / "org-kernel" / "kernel.py")
        for ledger in ("repo-ledger", "org-ledger"):
            with self.subTest(torn=ledger):
                packet_id = "torn-" + ledger
                payload = {**FrameIngestErrorTests.INTR, "communication_id": packet_id}
                K.publish_packet(self.packet(K, "admissible-existence.intr-destination", payload, packet_id),
                                 root=self.mesh, epoch=4096)
                real_replace = os_module.replace
                head = str(self.work / ledger / "HEAD.json")
                failures = {"left": 1}

                def torn_replace(source, destination, *args, **kwargs):
                    if str(destination) == head and failures["left"]:
                        failures["left"] -= 1
                        raise OSError(5, "I/O error writing HEAD")
                    return real_replace(source, destination, *args, **kwargs)

                head_before = json.loads(Path(head).read_text()) if Path(head).exists() else None
                with mock.patch("os.replace", side_effect=torn_replace):
                    first = K.consume_and_respond(self.repo, mesh_root=self.mesh)
                item, = [entry for entry in first if entry["result"].get("packet_id") == packet_id]
                assert_six_fields(self, item["result"], "FRAME_DISPATCH_IO_FAILED")
                self.assertIsNone(item["seen_marker"])
                # HEAD did not advance past the orphaned receipt.
                head_after = json.loads(Path(head).read_text()) if Path(head).exists() else None
                self.assertEqual(head_after, head_before)
                second = K.consume_and_respond(self.repo, mesh_root=self.mesh)
                self.assertEqual([entry["result"]["status"] for entry in second], ["CONSUMED"])
                self.assertEqual(K.consume_and_respond(self.repo, mesh_root=self.mesh), [])
        for ledger, schema in (("repo-ledger", "stegverse.repo-transition-receipt/v1"),
                               ("org-ledger", "stegverse.organization-transition-receipt/v1")):
            with self.subTest(ledger=ledger):
                root = self.work / ledger
                receipts = [json.loads(path.read_text()) for path in (root / "receipts").rglob("*.json")]
                self.assertTrue(all(receipt["schema"] == schema for receipt in receipts))
                self.assertEqual(len(receipts), 2)
                # HEAD names the newest receipt, and the chain covers every receipt exactly once.
                cursor, chain = json.loads((root / "HEAD.json").read_text())["receipt_sha256"], []
                by_digest = {receipt["receipt_sha256"]: receipt for receipt in receipts}
                while cursor:
                    chain.append(cursor)
                    cursor = by_digest[cursor]["previous_receipt_sha256"]
                self.assertEqual(sorted(chain), sorted(by_digest))


class CommunicationIdCollisionTests(_Workspace):
    """RESPONSE_ID_COLLISION_SILENTLY_SUPPRESSED: a second, different request under one communication id is refused."""

    def setUp(self):
        super().setUp()
        self.K = _load("probe_collision_kernel", self.repo / "org-kernel" / "kernel.py")

    def request(self, K, packet_id, probe):
        payload = {**FrameIngestErrorTests.INTR, "communication_id": "shared-comm",
                   "body": {"schema": "stegverse.org-intr-destination-diagnostic/v1", "probe": probe}}
        return K.carrier_frame(self.packet(K, "admissible-existence.intr-destination", payload, packet_id),
                               epoch=4096)

    def org_receipts(self):
        root = self.work / "org-ledger"
        return [json.loads(path.read_text()) for path in root.rglob("*.json")
                if json.loads(path.read_text()).get("schema") == "stegverse.organization-transition-receipt/v1"] \
            if root.exists() else []

    def test_the_second_request_is_refused_before_dispatch(self):
        for packet_id, probe in (("req-A", "diagnostic-crossing"), ("req-B", "diagnostic-crossing-b")):
            self.K.publish_frame(self.request(self.K, packet_id, probe), root=self.mesh)
        with fixed_clock(self.K) as clock:
            results = self.K.consume_and_respond(self.repo, mesh_root=self.mesh)
            again = self.K.consume_and_respond(self.repo, mesh_root=self.mesh)
        self.assertEqual(clock.reads, 0)
        self.assertEqual(again, [])
        consumed = [item for item in results if item["result"].get("status") == "CONSUMED"]
        refused = [item for item in results if item["result"].get("status") != "CONSUMED"]
        self.assertEqual(len(consumed), 1)
        self.assertEqual(len(refused), 1)
        assert_six_fields(self, refused[0]["result"], "COMMUNICATION_ID_COLLISION")
        self.assertIsNotNone(refused[0]["seen_marker"])
        answered = consumed[0]["result"]["packet"]["packet_id"]
        responses = [frame for frame in (json.loads(path.read_text())
                                         for path in (self.mesh / "frames.d").glob("*.json"))
                     if frame.get("destination_org") == PEER]
        self.assertEqual(len(responses), 1)
        self.assertEqual(self.K.answered_request(responses[0]), answered)
        # The refused request was never dispatched: one organization receipt, for the answered one.
        self.assertEqual([receipt["repo_transition_id"] for receipt in self.org_receipts()],
                         ["ORGANIZATION_INTR_DESTINATION_INGRESS:" + answered])

    def test_the_gateway_refuses_the_second_request_and_submits_once(self):
        cycle = _load("probe_collision_cycle", self.repo / "resident-runtime" / "federation_cycle.py")
        frames = [self.request(cycle.GW.K, "req-A", "diagnostic-crossing"),
                  self.request(cycle.GW.K, "req-B", "diagnostic-crossing-b")]
        submitted, acks, offered = [], [], list(frames)

        def gateway(method, path, *, body=None, headers=None):
            if method == "GET":
                return {"state": "FRAME_AVAILABLE", "frame": offered[0]}
            if path.endswith("/frames"):
                submitted.append(body)
                return {"state": "PENDING"}
            acks.append(body)
            return {"state": body["state"]}

        with mock.patch.object(cycle.GW, "_json_request", gateway):
            first = cycle.GW.resident_gateway_cycle(self.repo)
            offered.pop(0)
            second = cycle.GW.resident_gateway_cycle(self.repo)
        self.assertEqual(first["state"], "CONSUMED")
        self.assertEqual(second["state"], "BLOCKED")
        assert_six_fields(self, second["ingest_refusal"], "COMMUNICATION_ID_COLLISION")
        self.assertEqual(len(submitted), 1)
        self.assertEqual([ack["state"] for ack in acks], ["CONSUMED", "BLOCKED"])

    def test_the_same_request_retried_reuses_its_response(self):
        frame = self.request(self.K, "req-retry", "diagnostic-crossing")
        self.K.publish_frame(frame, root=self.mesh)
        with mock.patch.object(self.K, "mark_federation_frame_seen", side_effect=OSError(28, "full")):
            self.K.consume_and_respond(self.repo, mesh_root=self.mesh)
        retried = self.K.consume_and_respond(self.repo, mesh_root=self.mesh)
        self.assertEqual(retried[0]["result"]["status"], "CONSUMED")
        self.assertIs(retried[0]["response_publication"]["already_published"], True)


class MultiStepWriteFaultGridTests(_Workspace):
    """B-P36q: an OSError at every durable write step leaves the run resumable, and the next run completes once.

    Steps are counted in a clean run: each ledger document and HEAD replace
    (repository receipt and HEAD, organization source copy, receipt and HEAD),
    the response frame and the seen marker, and on the gateway the response
    record, the submission, the submitted mark and the ack.
    """

    INTR = FrameIngestErrorTests.INTR

    def workspace(self, name):
        root = self.work / name
        repo = root / "repo"
        shutil.copytree(self.repo, repo)
        os.environ["STEGVERSE_REPO_LEDGER_ROOT"] = str(root / "repo-ledger")
        os.environ["STEGVERSE_ORG_LEDGER_ROOT"] = str(root / "org-ledger")
        return root, repo

    @staticmethod
    def receipts(root, ledger):
        directory = root / ledger / "receipts"
        return list(directory.rglob("*.json")) if directory.exists() else []

    def request_frame(self, K, packet_id):
        payload = {**self.INTR, "communication_id": packet_id}
        return K.carrier_frame(self.packet(K, "admissible-existence.intr-destination", payload, packet_id),
                               epoch=4096)

    def faulting(self, fail_at):
        """Patch os.replace and Path.write_text to count durable writes and fail the fail_at-th one."""
        import os as os_module
        state = {"count": 0}
        real_replace, real_write = os_module.replace, Path.write_text

        def step():
            state["count"] += 1
            if state["count"] == fail_at:
                raise OSError(5, "injected fault at write step " + str(fail_at))

        def replace(source, destination, *args, **kwargs):
            step()
            return real_replace(source, destination, *args, **kwargs)

        def write_text(path, *args, **kwargs):
            step()
            return real_write(path, *args, **kwargs)

        return state, [mock.patch("os.replace", side_effect=replace),
                       mock.patch.object(Path, "write_text", write_text)]

    def run_local(self, name, fail_at):
        root, repo = self.workspace(name)
        K = _load("probe_grid_kernel_" + name, repo / "org-kernel" / "kernel.py")
        mesh = root / "mesh"
        K.publish_frame(self.request_frame(K, "grid"), root=mesh)
        state, patches = self.faulting(fail_at)
        for patch in patches:
            patch.start()
        try:
            K.consume_and_respond(repo, mesh_root=mesh)
        finally:
            for patch in reversed(patches):
                patch.stop()
        return root, repo, mesh, K, state["count"]

    def test_every_local_write_step(self):
        _root, _repo, _mesh, _K, steps = self.run_local("clean", fail_at=0)
        self.assertGreaterEqual(steps, 7)
        for fail_at in range(1, steps + 1):
            with self.subTest(step=fail_at):
                root, repo, mesh, K, _count = self.run_local("step-%d" % fail_at, fail_at)
                for _cycle in range(2):
                    K.consume_and_respond(repo, mesh_root=mesh)
                self.assertEqual(K.consume_and_respond(repo, mesh_root=mesh), [])
                self.assertEqual(len(self.receipts(root, "repo-ledger")), 1)
                self.assertEqual(len(self.receipts(root, "org-ledger")), 1)
                responses = [frame for frame in (json.loads(path.read_text())
                                                 for path in (mesh / "frames.d").glob("*.json"))
                             if frame.get("destination_org") == PEER]
                self.assertEqual(len(responses), 1)
                markers = list((repo / "resident-runtime" / "federation" / "seen.d").glob("*.json"))
                self.assertEqual(len(markers), 1)
                self.assertEqual(json.loads(markers[0].read_text())["status"], "CONSUMED")

    def test_a_fault_after_each_head_replace(self):
        """F-POST-HEAD: a directory fsync fault after each HEAD replace; the next cycle appends nothing twice."""
        import stat
        for ledger in ("repo-ledger", "org-ledger"):
            with self.subTest(ledger=ledger):
                root, repo = self.workspace("post-head-" + ledger)
                K = _load("probe_post_head_kernel_" + ledger.replace("-", "_"), repo / "org-kernel" / "kernel.py")
                mesh = root / "mesh"
                K.publish_frame(self.request_frame(K, "post-head"), root=mesh)
                head = (root / ledger / "HEAD.json").resolve()
                real_fsync = os.fsync

                def fsync(fd):
                    if stat.S_ISDIR(os.fstat(fd).st_mode) and head.exists() and \
                            os.path.samestat(os.fstat(fd), os.stat(head.parent)):
                        raise OSError(5, "injected directory fsync fault after the HEAD replace")
                    return real_fsync(fd)

                with mock.patch("os.fsync", side_effect=fsync):
                    torn = K.consume_and_respond(repo, mesh_root=mesh)
                refusal = torn[0]["result"]
                assert_six_fields(self, refusal, K.FRAME_DISPATCH_IO_FAILED)
                self.assertIs(refusal["terminal"], False)
                self.assertIs(refusal["partial_write_possible"], True)
                self.assertNotIn("consequence_committed", refusal)
                recorded = json.loads(head.read_text())
                K.consume_and_respond(repo, mesh_root=mesh)
                self.assertEqual(K.consume_and_respond(repo, mesh_root=mesh), [])
                self.assertEqual(json.loads(head.read_text()), recorded)
                self.assertEqual(len(self.receipts(root, "repo-ledger")), 1)
                self.assertEqual(len(self.receipts(root, "org-ledger")), 1)

    def test_every_gateway_step(self):
        # Steps: the response record, the submission, the submitted mark, the ack.
        for fail_at in range(1, 5):
            with self.subTest(step=fail_at):
                root, repo = self.workspace("gateway-%d" % fail_at)
                cycle = _load("probe_grid_cycle_%d" % fail_at, repo / "resident-runtime" / "federation_cycle.py")
                frame = self.request_frame(cycle.GW.K, "gateway-grid")
                submitted, acks, state = [], [], {"count": 0}
                records = repo / "resident-runtime" / "federation" / "responses-submitted.d"
                real_write = Path.write_text

                def step():
                    state["count"] += 1
                    if state["count"] == fail_at:
                        raise OSError(5, "injected fault at gateway step " + str(fail_at))

                def write_text(path, *args, **kwargs):
                    if str(path).startswith(str(records)):
                        step()
                    return real_write(path, *args, **kwargs)

                def gateway(method, path, *, body=None, headers=None):
                    if method == "GET":
                        return {"state": "FRAME_AVAILABLE", "frame": frame}
                    step()
                    if path.endswith("/frames"):
                        submitted.append(body)
                        return {"state": "PENDING"}
                    acks.append(body)
                    return {"state": body["state"]}

                with mock.patch.object(cycle.GW, "_json_request", gateway), \
                        mock.patch.object(Path, "write_text", write_text):
                    results = [cycle.GW.resident_gateway_cycle(repo) for _cycle in range(3)]
                self.assertEqual([result["state"] for result in results].count("PENDING_IO"), 1)
                # One response: every submission is the same bytes, and the ack is CONSUMED once
                # the cycle completes (a retried cycle re-acknowledges, never re-dispatches).
                self.assertEqual(len({body["frame_sha256"] for body in submitted}), 1)
                self.assertLessEqual(len(submitted), 2)
                self.assertTrue(acks and acks[-1]["state"] == "CONSUMED")
                self.assertEqual(len(self.receipts(root, "repo-ledger")), 1)
                self.assertEqual(len(self.receipts(root, "org-ledger")), 1)


class GatewayCycleEpochTests(_Workspace):
    """The gateway cycle answers at the frame's validated epoch, or not at all, and reads no clock."""

    def cycle(self, reference, packet_id):
        cycle = _load("probe_gateway_" + packet_id, self.repo / "resident-runtime" / "federation_cycle.py")
        K, GW = cycle.K, cycle.GW
        frame = K.carrier_frame(self.packet(K, "admissible-existence.org-control",
                                            control("ecosystem.communication", packet_id), packet_id), epoch=4096)
        body = {key: value for key, value in frame.items() if key != "frame_sha256"}
        body["heartbeat_reference"] = reference
        frame = {**body, "frame_sha256": K.sha(body)}
        sent = []

        def gateway(method, path, *, body=None, headers=None):
            if method == "GET":
                return {"state": "FRAME_AVAILABLE", "frame": frame}
            sent.append((path, body))
            return {"state": "PENDING" if path.endswith("/frames") else "OK"}

        before = snapshot(self.work)
        with fixed_clock(K, GW) as clock, mock.patch.object(GW, "_json_request", gateway):
            result = GW.resident_gateway_cycle(self.repo)
        self.assertEqual(clock.reads, 0)
        # Only this boundary's own response-submitted record, nothing else.
        self.assertEqual([path for path in written(self.work, before)
                          if "responses-submitted.d" not in str(path)], [])
        frames = [body for path, body in sent if path.endswith("/frames")]
        acks = [body for path, body in sent if path.endswith("/acknowledgements")]
        self.assertEqual(len(acks), 1)
        self.assertIs(acks[0]["derived_from_clock"], False)
        return K, result, frames, acks[0]

    def test_a_supplied_frame_is_answered_at_its_epoch(self):
        K, result, frames, ack = self.cycle(kernel.hb_reference(epoch=4096), "gateway-supplied")
        self.assertEqual(result["responses_emitted"], 1)
        response, = frames
        reference = response["heartbeat_reference"]
        self.assertEqual(reference["epoch"], 4096)
        self.assertIs(reference["derived_from_clock"], False)
        self.assertNotIn("sampled_unix_ns", reference)
        self.assertEqual(ack["observed_at"], "HB:4096")

    def test_a_clock_frame_gets_no_response(self):
        references = (("flagged", {**kernel.hb_reference(epoch=4096), "derived_from_clock": True}),
                      ("sampled", kernel.hb_reference(now_ns=INSTANT_NS)))
        for name, reference in references:
            with self.subTest(frame=name):
                _K, result, frames, ack = self.cycle(reference, "gateway-" + name)
                self.assertEqual(frames, [])
                self.assertEqual(result["responses_emitted"], 0)
                assert_six_fields(self, result["response_refusal"], "HB_EPOCH_INVALID")
                self.assertIsNone(ack["observed_at"])

    def test_an_unmarked_frame_is_refused_and_blocked(self):
        unflagged = {key: value for key, value in kernel.hb_reference(epoch=4096).items()
                     if key != "derived_from_clock"}
        _K, result, frames, ack = self.cycle(unflagged, "gateway-unmarked")
        self.assertEqual(result["state"], "BLOCKED")
        self.assertEqual(frames, [])
        assert_six_fields(self, result["ingest_refusal"], "HB_EPOCH_PROVENANCE_UNMARKED")


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


class EgressWriteFaultTests(_Workspace):
    """F-MT-TRACE: a write fault during egress emit is six-field EMIT_WRITE_FAILED, never a traceback."""

    PAYLOAD = {"message_class": "ecosystem.communication", "communication_id": "egress-fault", "subject": "probe",
               "body": {"schema": "stegverse.org-intr-destination-diagnostic/v1", "probe": "diagnostic-crossing"}}

    def setUp(self):
        super().setUp()
        self.egress = _load("probe_egress_fault", ROOT / "resident-runtime" / "organization_egress_boundary.py")

    def emit(self, mesh):
        return self.egress.emit(PEER, self.PAYLOAD, standing=STANDING, capability="intr-destination",
                                mesh_root=mesh, hb_epoch="4096")

    def run_with_fault(self, name, fail_at):
        root = self.work / name
        os.environ["STEGVERSE_REPO_LEDGER_ROOT"] = str(root / "repo-ledger")
        os.environ["STEGVERSE_ORG_LEDGER_ROOT"] = str(root / "org-ledger")
        state, patches = MultiStepWriteFaultGridTests.faulting(self, fail_at)
        for patch in patches:
            patch.start()
        try:
            result = self.emit(root / "mesh")
        finally:
            for patch in reversed(patches):
                patch.stop()
        return root, result, state["count"]

    def test_every_emit_write_step(self):
        _root, clean, steps = self.run_with_fault("clean", fail_at=0)
        self.assertIs(clean["emitted"], True)
        self.assertGreaterEqual(steps, 5)
        for fail_at in range(1, steps + 1):
            with self.subTest(step=fail_at):
                root, result, _count = self.run_with_fault("step-" + str(fail_at), fail_at)
                assert_six_fields(self, result, "EMIT_WRITE_FAILED")
                self.assertIs(result["terminal"], False)
                self.assertIs(result["emission_completed"], False)
                self.assertIs(result["partial_write_possible"], True)
                retried = self.emit(root / "mesh")
                self.assertIs(retried["emitted"], True)
                self.assertEqual(retried["packet_id"], clean["packet_id"])
                self.assertEqual(len(list((root / "mesh" / "frames.d").glob("*.json"))), 1)

    def test_the_cli_prints_six_fields_and_exits_non_zero(self):
        payload, standing = self.work / "payload.json", self.work / "standing.json"
        payload.write_text(json.dumps(self.PAYLOAD))
        standing.write_text(json.dumps(STANDING))
        argv = ["organization_egress_boundary.py", "--destination-organization", PEER,
                "--payload", str(payload), "--standing", str(standing), "--capability", "intr-destination",
                "--mesh-root", str(self.mesh), "--hb-epoch", "4096"]
        state, patches = MultiStepWriteFaultGridTests.faulting(self, 1)
        with mock.patch("sys.argv", argv), contextlib.redirect_stdout(io.StringIO()) as out:
            for patch in patches:
                patch.start()
            try:
                code = self.egress.main()
            finally:
                for patch in reversed(patches):
                    patch.stop()
        self.assertEqual(code, 1)
        assert_six_fields(self, json.loads(out.getvalue()), "EMIT_WRITE_FAILED")


class CommunicationIdSquatTests(_Workspace):
    """A frame from another origin under this organization's response id is not a collision."""

    def test_a_squatting_frame_does_not_refuse_the_request(self):
        K = _load("probe_squat_kernel", self.repo / "org-kernel" / "kernel.py")
        squat = K.build_packet(origin_org="StegVerse-Labs", origin_service="stegverse-labs.org-control",
                               destination_org=PEER, destination_service="stegverse-org.org-control",
                               payload={"message_class": "ecosystem.communication.response",
                                        "communication_id": "shared-comm",
                                        "body": {"request_packet_id": "req-other"}},
                               standing=STANDING, transition_reference="probe:squat", authority_effect="NONE",
                               packet_id="shared-comm:response:admissible-existence")
        K.publish_frame(K.carrier_frame(squat, epoch=4096), root=self.mesh)
        request = CommunicationIdCollisionTests.request(self, K, "req-A", "diagnostic-crossing")
        self.assertIsNone(K.request_collision(request, root=self.mesh))
        K.publish_frame(request, root=self.mesh)
        results = K.consume_and_respond(self.repo, mesh_root=self.mesh)
        self.assertEqual([item["result"].get("status") for item in results], ["CONSUMED"])
        ours = [frame for frame in (json.loads(path.read_text()) for path in (self.mesh / "frames.d").glob("*.json"))
                if frame["packet_id"] == "shared-comm:response:admissible-existence" and frame["origin_org"] == THIS]
        self.assertEqual(len(ours), 1)
        self.assertEqual(K.answered_request(ours[0]), "req-A")


TORN_WRITE_SITECUSTOMIZE = """
import json, os, sys
FAULT_AT = int(os.environ.get("PROBE_FAULT_AT", "0"))
MODE = os.environ.get("PROBE_FAULT_MODE", "before")
COUNT = os.environ.get("PROBE_FAULT_COUNT")
if COUNT or FAULT_AT:
    _replace, _state = os.replace, {"n": 0}
    def replace(source, destination, *args, **kwargs):
        _state["n"] += 1
        if _state["n"] == FAULT_AT and MODE == "before":
            raise OSError(5, "injected fault before put " + str(FAULT_AT))
        result = _replace(source, destination, *args, **kwargs)
        if COUNT:
            with open(COUNT, "w") as stream:
                stream.write(str(_state["n"]))
        if _state["n"] == FAULT_AT and MODE == "after":
            raise OSError(5, "injected fault after put " + str(FAULT_AT))
        return result
    os.replace = replace
DIRSYNC_FAIL_AT = int(os.environ.get("PROBE_DIRSYNC_FAIL_AT", "0"))
DIRSYNC_COUNT = os.environ.get("PROBE_DIRSYNC_COUNT")
if DIRSYNC_FAIL_AT or DIRSYNC_COUNT:
    import stat
    _fsync, _syncs = os.fsync, {"n": 0}
    def fsync(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            _syncs["n"] += 1
            if DIRSYNC_COUNT:
                with open(DIRSYNC_COUNT, "w") as stream:
                    stream.write(str(_syncs["n"]))
            if _syncs["n"] == DIRSYNC_FAIL_AT:
                raise OSError(5, "injected directory fsync fault after replace " + str(DIRSYNC_FAIL_AT))
        return _fsync(fd)
    os.fsync = fsync
WRITE_TEXT_FAIL_NAME = os.environ.get("PROBE_WRITE_TEXT_FAIL_NAME")
if WRITE_TEXT_FAIL_NAME:
    import pathlib
    _write_text = pathlib.Path.write_text
    def write_text(self, *args, **kwargs):
        if self.name == WRITE_TEXT_FAIL_NAME:
            raise OSError(28, "injected write fault on " + self.name)
        return _write_text(self, *args, **kwargs)
    pathlib.Path.write_text = write_text
OUTBOX = os.environ.get("PROBE_OUTBOX")
if OUTBOX:
    import contextlib, io, urllib.request
    urllib.request.urlopen = lambda *a, **k: contextlib.nullcontext(io.BytesIO(open(OUTBOX, "rb").read()))
"""


class WriterCliTornWriteTests(_Workspace):
    """F-WRITER-TRACE: every writer CLI, run as a real subprocess and torn before
    and after each put, prints six fields and exits 1 with no traceback; the next
    run completes once, including a tear after HEAD."""

    def setUp(self):
        super().setUp()
        self.site = self.work / "site"
        self.site.mkdir()
        (self.site / "sitecustomize.py").write_text(TORN_WRITE_SITECUSTOMIZE)
        self.outbox = self.work / "outbox.json"
        self.outbox.write_text(json.dumps({"messages": [HeartbeatResponseEpochTests.MESSAGE]}))

    def run_cli(self, argv, env, fault_at=0, mode="before", count=None):
        values = {**os.environ, **env, "PYTHONPATH": str(self.site), "PROBE_FAULT_AT": str(fault_at),
                  "PROBE_FAULT_MODE": mode, "PROBE_OUTBOX": str(self.outbox)}
        values.pop("PROBE_FAULT_COUNT", None)
        if count is not None:
            values["PROBE_FAULT_COUNT"] = str(count)
        return subprocess.run([sys.executable, *argv], cwd=self.repo, env=values,
                              capture_output=True, text=True, timeout=120)

    def ledgers(self, root):
        return {"STEGVERSE_REPO_LEDGER_ROOT": str(root / "repo-ledger"),
                "STEGVERSE_ORG_LEDGER_ROOT": str(root / "org-ledger")}

    @staticmethod
    def receipts(root, ledger):
        directory = root / ledger / "receipts"
        return sorted(directory.rglob("*.json")) if directory.exists() else []

    def emit_args(self):
        return [".stegverse/transition-ledger/emit.py", "--transition-id", "probe:torn",
                "--transition-class", "PROBE", "--predecessor-state-sha256", "sha256:" + "0" * 64,
                "--successor-state-sha256", "sha256:" + "1" * 64, "--evidence-json", '{"probe": "torn"}',
                "--hb-epoch", "4096"]

    def repo_receipt_file(self, root):
        # The source is on the repository ledger the aggregate verifies it against.
        made = self.run_cli(self.emit_args(), self.ledgers(root))
        self.assertEqual(made.returncode, 0, made.stderr)
        path = root / "repo-receipt.json"
        path.write_text(made.stdout)
        return path

    def cases(self):
        return {
            "emit": (lambda root: self.emit_args(), [("repo-ledger", 1)]),
            "aggregate": (lambda root: ["resident-runtime/aggregate_repo_transition.py", "--repo-receipt",
                                        str(self.repo_receipt_file(root)), "--predecessor-org-state-sha256",
                                        "sha256:" + "2" * 64, "--successor-org-state-sha256", "sha256:" + "3" * 64,
                                        "--hb-epoch", "4096"], [("org-ledger", 1)]),
            "self-close": (lambda root: ["resident-runtime/intr_destination_ingress.py", "--self-close",
                                         "--communication-id", "torn-self-close", "--hb-epoch", "4096"],
                           [("repo-ledger", 1), ("org-ledger", 1)]),
            "dispatch-emit": (lambda root: ["scripts/dispatch_ledger_writer.py", "--writer", "repository-ledger-emit",
                                            "--hb-epoch", "4096", "--arguments",
                                            " ".join(self.emit_args()[1:-2]).replace('{"probe": "torn"}', "'{\"probe\": \"torn\"}'")],
                              [("repo-ledger", 1)]),
        }

    def assert_six_field_exit(self, run, label):
        self.assertEqual(run.returncode, 1, label + run.stdout + run.stderr)
        self.assertNotIn("Traceback", run.stderr, label)
        refusal = json.loads(run.stdout)
        self.assertEqual(refusal["disposition"], "FAIL_CLOSED", label)
        for name in EPOCH_FIELDS:
            self.assertTrue(refusal[name], label + name)
        self.assertIs(refusal["terminal"], False, label)

    def test_every_ledger_writer_cli(self):
        for name, (argv_for, expected) in self.cases().items():
            clean = self.work / ("clean-" + name)
            count = self.work / ("count-" + name)
            first = self.run_cli(argv_for(clean), self.ledgers(clean), count=count)
            self.assertEqual(first.returncode, 0, name + first.stderr)
            puts = int(count.read_text())
            self.assertGreaterEqual(puts, 2, name)
            for mode in ("before", "after"):
                for fault_at in range(1, puts + 1):
                    label = "%s %s put %d: " % (name, mode, fault_at)
                    with self.subTest(writer=name, mode=mode, put=fault_at):
                        root = self.work / ("%s-%s-%d" % (name, mode, fault_at))
                        argv = argv_for(root)
                        torn = self.run_cli(argv, self.ledgers(root), fault_at, mode)
                        self.assert_six_field_exit(torn, label)
                        again = self.run_cli(argv, self.ledgers(root))
                        self.assertEqual(again.returncode, 0, label + again.stdout + again.stderr)
                        once = self.run_cli(argv, self.ledgers(root))
                        self.assertEqual(once.returncode, 0, label + once.stdout + once.stderr)
                        for ledger, receipts in expected:
                            self.assertEqual(len(self.receipts(root, ledger)), receipts, label + ledger)

    def test_a_fault_after_the_head_replace_appends_once(self):
        """F-POST-HEAD: a directory fsync fails after HEAD's os.replace; the retry returns the recorded receipt."""
        for name, (argv_for, expected) in self.cases().items():
            if name == "dispatch-emit":
                continue
            with self.subTest(writer=name):
                clean = self.work / ("dirsync-clean-" + name)
                count = self.work / ("dirsync-count-" + name)
                values = {**self.ledgers(clean), "PROBE_DIRSYNC_COUNT": str(count)}
                self.assertEqual(self.run_cli(argv_for(clean), values).returncode, 0, name)
                last = int(count.read_text())
                root = self.work / ("dirsync-" + name)
                argv = argv_for(root)
                torn = self.run_cli(argv, {**self.ledgers(root), "PROBE_DIRSYNC_FAIL_AT": str(last)})
                self.assert_six_field_exit(torn, name + ": ")
                refusal = json.loads(torn.stdout)
                self.assertIs(refusal["partial_write_possible"], True)
                self.assertIn("HEAD included, may be committed", refusal["committed_state"])
                self.assertNotIn("consequence_committed", refusal)
                self.assertNotIn("nothing", refusal["next_attempt"])
                ledger = expected[-1][0]
                head = json.loads((root / ledger / "HEAD.json").read_text())
                again = self.run_cli(argv, self.ledgers(root))
                self.assertEqual(again.returncode, 0, name + again.stdout + again.stderr)
                for directory, receipts in expected:
                    self.assertEqual(len(self.receipts(root, directory)), receipts, name + directory)
                self.assertEqual(json.loads((root / ledger / "HEAD.json").read_text()), head)
                if name != "self-close":
                    self.assertEqual(json.loads(again.stdout)["receipt_sha256"], head["receipt_sha256"])

    def test_a_different_record_under_a_recorded_transition_is_a_six_field_collision(self):
        root = self.work / "collide"
        self.assertEqual(self.run_cli(self.emit_args(), self.ledgers(root)).returncode, 0)
        argv = [item if item != '{"probe": "torn"}' else '{"probe": "other"}' for item in self.emit_args()]
        run = self.run_cli(argv, self.ledgers(root))
        self.assertEqual(run.returncode, 1)
        self.assertNotIn("Traceback", run.stderr)
        refusal = json.loads(run.stdout)
        self.assertEqual(refusal["failure_code"], "LEDGER_RECEIPT_COLLISION")
        self.assertIs(refusal["terminal"], True)

    def test_the_heartbeat_node_cli(self):
        argv = ["scripts/process_heartbeat_response.py", "--apply", "--hb-epoch", "4096"]
        receipts = self.repo / "data" / "heartbeat-response-receipts"
        prefix = HeartbeatResponseEpochTests.MESSAGE["exchange_id"]
        for mode in ("before", "after"):
            for fault_at in (1, 2):
                label = "heartbeat %s put %d: " % (mode, fault_at)
                with self.subTest(mode=mode, put=fault_at):
                    for path in receipts.glob(prefix + ".*"):
                        path.unlink()
                    torn = self.run_cli(argv, {}, fault_at, mode)
                    self.assert_six_field_exit(torn, label)
                    again = self.run_cli(argv, {})
                    self.assertEqual(again.returncode, 0, label + again.stdout + again.stderr)
                    pair = sorted(path.name for path in receipts.glob(prefix + ".*"))
                    self.assertEqual(pair, [prefix + ".received.json", prefix + ".responded.json"], label)
                    received = json.loads((receipts / (prefix + ".received.json")).read_text())
                    responded = json.loads((receipts / (prefix + ".responded.json")).read_text())
                    self.assertEqual(responded["parent_receipt_sha256"],
                                     hashlib.sha256(json.dumps(received, sort_keys=True,
                                                               separators=(",", ":")).encode()).hexdigest())

    def heartbeat(self, epoch, *extra, fault_at=0, mode="before"):
        argv = ["scripts/process_heartbeat_response.py", "--apply"]
        if epoch is not None:
            argv += ["--hb-epoch", str(epoch)]
        return self.run_cli(argv + list(extra), {}, fault_at, mode)

    def check(self):
        return self.run_cli(["scripts/process_heartbeat_response.py", "--check"], {})

    def pair(self, prefix):
        receipts = self.repo / "data" / "heartbeat-response-receipts"
        received = json.loads((receipts / (prefix + ".received.json")).read_text())
        responded = json.loads((receipts / (prefix + ".responded.json")).read_text())
        self.assertEqual(responded["parent_receipt_sha256"],
                         hashlib.sha256(json.dumps(received, sort_keys=True,
                                                   separators=(",", ":")).encode()).hexdigest())
        self.assertEqual(received["hb_reference"], responded["hb_reference"])
        return received, responded

    def test_a_torn_pair_rolls_forward_at_its_recorded_epoch(self):
        """B-P36q: a pair torn at 4096 is completed at 4096 by a run at a fresh epoch; --check flags it until then."""
        receipts = self.repo / "data" / "heartbeat-response-receipts"
        prefix = HeartbeatResponseEpochTests.MESSAGE["exchange_id"]
        written_with = receipts / (prefix + ".received.json")
        self.assert_six_field_exit(self.heartbeat(4096, fault_at=2), "torn: ")
        written = written_with.read_text()
        flagged = self.check()
        self.assertEqual(flagged.returncode, 1, flagged.stdout + flagged.stderr)
        self.assertNotIn("Traceback", flagged.stderr)
        refusal = json.loads(flagged.stdout)
        self.assertEqual(refusal["failure_code"], "HB_RECEIPT_PAIR_PARTIAL")
        self.assertIn("--hb-epoch 4096", refusal["required_evidence_or_repair"])
        self.assertIn("recorded epoch 4096", refusal["required_evidence_or_repair"])
        for name in EPOCH_FIELDS:
            self.assertTrue(refusal[name], name)
        fresh = self.heartbeat(5000)
        self.assertEqual(fresh.returncode, 0, fresh.stdout + fresh.stderr)
        self.assertIn("HB_NODE_RESUMED", fresh.stdout)
        self.assertEqual(written_with.read_text(), written)
        received, responded = self.pair(prefix)
        self.assertEqual(responded["hb_reference"]["epoch"], 4096)
        self.assertEqual(responded["observed_at"], received["observed_at"])
        self.assertEqual(self.check().returncode, 0)

    def test_an_outstanding_pair_is_not_orphaned_when_the_exchange_moves(self):
        receipts = self.repo / "data" / "heartbeat-response-receipts"
        old = HeartbeatResponseEpochTests.MESSAGE["exchange_id"]
        self.assert_six_field_exit(self.heartbeat(4096, fault_at=2), "torn: ")
        moved = {**HeartbeatResponseEpochTests.MESSAGE, "message_id": "msg-next", "exchange_id": "ex-next"}
        self.outbox.write_text(json.dumps({"messages": [moved]}))
        run = self.heartbeat(5000)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        _received, responded = self.pair(old)
        self.assertEqual(responded["hb_reference"]["epoch"], 4096)
        _received, responded = self.pair("ex-next")
        self.assertEqual(responded["hb_reference"]["epoch"], 5000)
        self.assertEqual(self.check().returncode, 0)

    def test_a_responded_half_alone_rolls_forward_or_names_its_bound_epoch(self):
        receipts = self.repo / "data" / "heartbeat-response-receipts"
        prefix = HeartbeatResponseEpochTests.MESSAGE["exchange_id"]
        self.assertEqual(self.heartbeat(4096).returncode, 0)
        received_path = receipts / (prefix + ".received.json")
        original = received_path.read_text()
        received_path.unlink()
        # The outbox still carries the exchange: the received receipt is rebuilt at 4096.
        resumed = self.heartbeat(5000)
        self.assertEqual(resumed.returncode, 0, resumed.stdout + resumed.stderr)
        self.assertEqual(json.loads(received_path.read_text()), json.loads(original))
        self.pair(prefix)
        # Once the outbox has moved on, it cannot be rebuilt: refused, naming the bound epoch.
        received_path.unlink()
        moved = {**HeartbeatResponseEpochTests.MESSAGE, "message_id": "msg-next", "exchange_id": "ex-next"}
        self.outbox.write_text(json.dumps({"messages": [moved]}))
        refused = self.heartbeat(5000)
        self.assertEqual(refused.returncode, 1)
        self.assertNotIn("Traceback", refused.stderr)
        refusal = json.loads(refused.stdout)
        self.assertEqual(refusal["failure_code"], "HB_RECEIPT_PAIR_PARTIAL")
        self.assertIs(refusal["terminal"], True)
        self.assertIn("epoch 4096", refusal["required_evidence_or_repair"])
        for name in EPOCH_FIELDS:
            self.assertTrue(refusal[name], name)
        self.assertFalse(received_path.exists())
        self.assertFalse((receipts / "ex-next.received.json").exists())

    def test_a_torn_pair_is_not_resumed_without_a_supplied_epoch(self):
        """HB_RESUME_WRITES_WITHOUT_SUPPLIED_EPOCH: the run's own epoch is checked before any roll-forward write."""
        receipts = self.repo / "data" / "heartbeat-response-receipts"
        prefix = HeartbeatResponseEpochTests.MESSAGE["exchange_id"]
        self.assert_six_field_exit(self.heartbeat(4096, fault_at=2), "torn: ")
        before = {path.name: path.read_bytes() for path in receipts.glob("*")}
        for epoch, code in ((None, "HB_EPOCH_NOT_SUPPLIED"), ("", "HB_EPOCH_INVALID"),
                            ("abc", "HB_EPOCH_INVALID"), ("31", "HB_EPOCH_INVALID")):
            with self.subTest(epoch=epoch):
                run = self.heartbeat(epoch)
                self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
                self.assertNotIn("Traceback", run.stderr)
                refusal = json.loads(run.stdout)
                self.assertEqual(refusal["failure_code"], code)
                for name in EPOCH_FIELDS:
                    self.assertTrue(refusal[name], name)
                self.assertEqual({path.name: path.read_bytes() for path in receipts.glob("*")}, before)
        self.assertFalse((receipts / (prefix + ".responded.json")).exists())
        self.assertEqual(self.heartbeat(5000).returncode, 0)
        _received, responded = self.pair(prefix)
        self.assertEqual(responded["hb_reference"]["epoch"], 4096)

    def test_a_pair_already_complete_needs_no_epoch(self):
        self.assertEqual(self.heartbeat(4096).returncode, 0)
        current = self.heartbeat(None)
        self.assertEqual(current.returncode, 0, current.stdout + current.stderr)
        self.assertIn("HB_NODE_CURRENT", current.stdout)


class CliInputTraceTests(WriterCliTornWriteTests):
    """F-INPUT-TRACE: a missing or unparsable input on any writer CLI argument is a
    terminal six-field CLI_INPUT_INVALID, exit 1, nothing written, no traceback."""

    DIAGNOSTIC = {"message_class": "ecosystem.communication", "communication_id": "input-probe",
                  "subject": "probe",
                  "body": {"schema": "stegverse.org-intr-destination-diagnostic/v1", "probe": "diagnostic-crossing"}}

    def bad_files(self):
        bad = self.work / "bad"
        bad.mkdir(exist_ok=True)
        (bad / "not-json.json").write_text("{not json")
        (bad / "not-utf8.json").write_bytes(b"\xff\xfe\x00{")
        (bad / "list.json").write_text("[1, 2]")
        (bad / "a-directory").mkdir(exist_ok=True)
        return {"missing": str(bad / "absent.json"), "directory": str(bad / "a-directory"),
                "not-json": str(bad / "not-json.json"), "not-utf8": str(bad / "not-utf8.json"),
                "wrong-type": str(bad / "list.json")}

    def good(self, name, value):
        path = self.work / (name + ".json")
        path.write_text(json.dumps(value))
        return str(path)

    def assert_input_refused(self, run, label, root):
        self.assertEqual(run.returncode, 1, label + run.stdout + run.stderr)
        self.assertNotIn("Traceback", run.stderr, label)
        refusal = json.loads(run.stdout)
        self.assertEqual(refusal["failure_code"], "CLI_INPUT_INVALID", label)
        for name in EPOCH_FIELDS:
            self.assertTrue(refusal[name], label + name)
        self.assertIs(refusal["terminal"], True, label)
        self.assertIs(refusal["consequence_committed"], False, label)
        self.assertEqual(sorted(path.name for path in root.iterdir()) if root.exists() else [], [], label)

    def file_arguments(self):
        payload = self.good("payload", self.DIAGNOSTIC)
        standing = self.good("standing", STANDING)
        registry = str(self.repo / "org-boundary" / "registry" / "services.json")
        ingress = ["resident-runtime/intr_destination_ingress.py", "--hb-epoch", "4096"]
        egress = ["resident-runtime/organization_egress_boundary.py", "--destination-organization", PEER,
                  "--capability", "intr-destination", "--hb-epoch", "4096"]
        return [
            ("aggregate --repo-receipt", ["resident-runtime/aggregate_repo_transition.py",
                                          "--predecessor-org-state-sha256", "sha256:" + "2" * 64,
                                          "--successor-org-state-sha256", "sha256:" + "3" * 64,
                                          "--hb-epoch", "4096"], "--repo-receipt", {}),
            ("ingress --payload", ingress + ["--registry", registry], "--payload", {}),
            ("ingress --registry", ingress + ["--payload", payload], "--registry", {}),
            ("self-close --registry", ingress + ["--self-close", "--communication-id", "input-probe"],
             "--registry", {}),
            ("egress --payload", egress + ["--standing", standing], "--payload", {}),
            ("egress --standing", egress + ["--payload", payload], "--standing", {}),
            ("run_once --ingress", ["resident-runtime/run_once.py", "--egress", "OUT", "--hb-epoch", "4096"],
             "--ingress", {}),
        ]

    def test_every_file_argument(self):
        for label, argv, argument, extra in self.file_arguments():
            for kind, path in self.bad_files().items():
                with self.subTest(argument=label, input=kind):
                    root = self.work / ("input-" + label.replace(" ", "_") + "-" + kind)
                    values = {**self.ledgers(root), "STEGVERSE_ORG_FEDERATION_ROOT": str(root / "mesh")}
                    full = [item if item != "OUT" else str(root / "egress.json") for item in argv]
                    run = self.run_cli(full + [argument, path], values)
                    self.assert_input_refused(run, label + " " + kind + ": ", root)

    def test_every_inline_json_argument(self):
        cases = [
            ("emit --evidence-json", self.emit_args(), "--evidence-json"),
            ("aggregate --boundary-evidence-json",
             ["resident-runtime/aggregate_repo_transition.py", "--predecessor-org-state-sha256", "sha256:" + "2" * 64,
              "--successor-org-state-sha256", "sha256:" + "3" * 64, "--hb-epoch", "4096"],
             "--boundary-evidence-json"),
            ("ecosystem_control --body-json",
             ["resident-runtime/ecosystem_control.py", "--hb-epoch", "4096", "send-message", "--subject", "probe"],
             "--body-json"),
        ]
        for label, argv, argument in cases:
            for kind, text in (("not-json", "{not json"), ("wrong-type", "[1, 2]")):
                with self.subTest(argument=label, input=kind):
                    root = self.work / ("inline-" + label.split()[0] + "-" + kind)
                    values = {**self.ledgers(root), "STEGVERSE_ORG_FEDERATION_ROOT": str(root / "mesh")}
                    full = list(argv)
                    if argument in full:
                        full[full.index(argument) + 1] = text
                    else:
                        full += [argument, text]
                    if label.startswith("aggregate"):
                        full += ["--repo-receipt", str(self.repo_receipt_file(self.work / ("source-" + kind)))]
                    run = self.run_cli(full, values)
                    self.assert_input_refused(run, label + " " + kind + ": ", root)

    def test_a_malformed_communication_id_and_arguments(self):
        root = self.work / "malformed-id"
        run = self.run_cli(["resident-runtime/intr_destination_ingress.py", "--self-close",
                            "--communication-id", "../escape", "--hb-epoch", "4096"], self.ledgers(root))
        self.assert_input_refused(run, "communication id: ", root)
        root = self.work / "malformed-arguments"
        run = self.run_cli(["scripts/dispatch_ledger_writer.py", "--writer", "repository-ledger-emit",
                            "--hb-epoch", "4096", "--arguments", "--transition-id 'unclosed"], self.ledgers(root))
        self.assert_input_refused(run, "dispatcher arguments: ", root)

    def test_a_malformed_outbox(self):
        receipts = self.repo / "data" / "heartbeat-response-receipts"
        before = sorted(path.name for path in receipts.glob("*"))
        for kind, body in (("not-json", "{not json"), ("wrong-type", "[1]"), ("no-message", '{"messages": []}'),
                           ("message-lacks-fields", json.dumps({"messages": [{
                               "destination_org": THIS, "stage": "SENT",
                               "authority": HeartbeatResponseEpochTests.MESSAGE["authority"]}]}))):
            with self.subTest(outbox=kind):
                self.outbox.write_text(body)
                run = self.run_cli(["scripts/process_heartbeat_response.py", "--apply", "--hb-epoch", "4096"], {})
                self.assertEqual(run.returncode, 1, kind + run.stdout + run.stderr)
                self.assertNotIn("Traceback", run.stderr, kind)
                refusal = json.loads(run.stdout)
                self.assertEqual(refusal["failure_code"], "HB_OUTBOX_INVALID")
                for name in EPOCH_FIELDS:
                    self.assertTrue(refusal[name], kind + name)
                self.assertIs(refusal["terminal"], True)
                self.assertEqual(sorted(path.name for path in receipts.glob("*")), before)

    # The torn-write cases are WriterCliTornWriteTests' own; not rerun here.
    test_every_ledger_writer_cli = None
    test_a_fault_after_the_head_replace_appends_once = None
    test_a_different_record_under_a_recorded_transition_is_a_six_field_collision = None
    test_the_heartbeat_node_cli = None
    test_a_torn_pair_rolls_forward_at_its_recorded_epoch = None
    test_an_outstanding_pair_is_not_orphaned_when_the_exchange_moves = None
    test_a_responded_half_alone_rolls_forward_or_names_its_bound_epoch = None
    test_a_pair_already_complete_needs_no_epoch = None
    test_a_torn_pair_is_not_resumed_without_a_supplied_epoch = None


class ProcessBoundaryExitSplitTests(CliInputTraceTests):
    """DC#10's exit-code split, kept by every caller: process_boundary exit 75 (its own
    write faulted) is non-terminal with no marker and the frame is consumed exactly once
    on the next cycle; exit 65 (bad input) is terminal FRAME_INGEST_FAILED, quarantined."""

    def aid_frame(self, K, packet_id):
        packet = K.build_packet(origin_org=PEER, origin_service=K.organization_slug(PEER) + ".org-control",
                                destination_org=THIS, destination_service="admissible-existence.aid",
                                payload={"message_class": "ecosystem.work.request", "communication_id": packet_id,
                                         "request": {"operation": "DESCRIBE_AID"}},
                                standing=STANDING, transition_reference="probe:" + packet_id,
                                authority_effect="NONE", packet_id=packet_id)
        return K.carrier_frame(packet, epoch=4096)

    def markers(self):
        seen = self.repo / "resident-runtime" / "federation" / "seen.d"
        return [json.loads(path.read_text()) for path in seen.glob("*.json")] if seen.exists() else []

    def set_adapter(self, adapter):
        path = self.repo / "org-boundary" / "registry" / "services.json"
        registry = json.loads(path.read_text())
        for service in registry["services"]:
            if service["service_id"] == "admissible-existence.aid":
                service["endpoint_adapter"] = adapter
        path.write_text(json.dumps(registry, indent=2))

    def test_kernel_write_fault_is_pending_and_consumed_once(self):
        K = _load("probe_split_kernel_75", self.repo / "org-kernel" / "kernel.py")
        K.publish_frame(self.aid_frame(K, "split-75"), root=self.mesh)
        fault = {"PYTHONPATH": str(self.site), "PROBE_WRITE_TEXT_FAIL_NAME": "execution.json"}
        with mock.patch.dict(os.environ, fault):
            torn = K.consume_and_respond(self.repo, mesh_root=self.mesh)
        refusal = torn[0]["result"]
        assert_six_fields(self, refusal, K.FRAME_DISPATCH_IO_FAILED)
        self.assertIs(refusal["terminal"], False)
        self.assertIn("PROCESS_BOUNDARY_WRITE_FAULT", refusal["detail"])
        self.assertIsNone(torn[0]["seen_marker"])
        self.assertEqual(self.markers(), [])
        consumed = K.consume_and_respond(self.repo, mesh_root=self.mesh)
        self.assertEqual([item["result"]["status"] for item in consumed], ["CONSUMED"])
        self.assertEqual(K.consume_and_respond(self.repo, mesh_root=self.mesh), [])
        self.assertEqual([marker["status"] for marker in self.markers()], ["CONSUMED"])

    def test_kernel_missing_adapter_result_is_a_write_fault(self):
        (self.repo / "resident-runtime" / "silent_adapter.py").write_text("raise SystemExit(1)\n")
        self.set_adapter("resident-runtime/silent_adapter.py")
        K = _load("probe_split_kernel_silent", self.repo / "org-kernel" / "kernel.py")
        K.publish_frame(self.aid_frame(K, "split-silent"), root=self.mesh)
        torn = K.consume_and_respond(self.repo, mesh_root=self.mesh)
        self.assertEqual(torn[0]["result"]["failure_code"], K.FRAME_DISPATCH_IO_FAILED)
        self.assertIs(torn[0]["result"]["terminal"], False)
        self.assertEqual(self.markers(), [])

    def test_kernel_input_fault_is_terminal_and_quarantined(self):
        self.set_adapter("resident-runtime/absent_adapter.py")
        K = _load("probe_split_kernel_65", self.repo / "org-kernel" / "kernel.py")
        K.publish_frame(self.aid_frame(K, "split-65"), root=self.mesh)
        refused = K.consume_and_respond(self.repo, mesh_root=self.mesh)
        result = refused[0]["result"]
        assert_six_fields(self, result, "FRAME_INGEST_FAILED")
        self.assertIn("exit 65", result["detail"])
        self.assertIn("PROCESS_BOUNDARY_INPUT_FAULT", result["detail"])
        markers = self.markers()
        self.assertEqual([marker["status"] for marker in markers], ["REFUSED"])
        self.assertEqual(markers[0]["refused_failure_code"], "FRAME_INGEST_FAILED")
        self.assertEqual(K.consume_and_respond(self.repo, mesh_root=self.mesh), [])

    def envelope(self, service="admissible-existence.aid"):
        K = _load("probe_split_envelope_kernel", self.repo / "org-kernel" / "kernel.py")
        packet = K.build_packet(origin_org=PEER, origin_service=K.organization_slug(PEER) + ".org-control",
                                destination_org=THIS, destination_service=service,
                                payload={"message_class": "ecosystem.work.request", "communication_id": "split-cli",
                                         "request": {"operation": "DESCRIBE_AID"}},
                                standing=STANDING, transition_reference="probe:split-cli",
                                authority_effect="NONE", packet_id="split-cli")
        return self.good("envelope-" + service, packet)

    def assert_exit(self, run, code, failure_code, terminal, label):
        self.assertEqual(run.returncode, code, label + run.stdout + run.stderr)
        self.assertNotIn("Traceback", run.stderr, label)
        record = json.loads(run.stdout.strip().splitlines()[-1])
        self.assertEqual(record["failure_code"], failure_code, label)
        for name in EPOCH_FIELDS:
            self.assertTrue(record[name], label + name)
        self.assertIs(record["terminal"], terminal, label)

    def test_process_boundary_exit_codes(self):
        processor = "org-boundary/runtime/process_boundary.py"
        out = str(self.work / "pb" / "execution.json")
        for kind, path in self.bad_files().items():
            with self.subTest(envelope=kind):
                run = self.run_cli([processor, "--envelope", path, "--out", out], {})
                self.assert_exit(run, 65, "PROCESS_BOUNDARY_INPUT_FAULT", True, kind + ": ")
        unknown = self.envelope("admissible-existence.no-such-service")
        self.assert_exit(self.run_cli([processor, "--envelope", unknown, "--out", out], {}),
                         65, "PROCESS_BOUNDARY_INPUT_FAULT", True, "unknown service: ")
        blocker = self.work / "a-file"
        blocker.write_text("")
        self.assert_exit(self.run_cli([processor, "--envelope", self.envelope(), "--out", str(blocker / "x.json")], {}),
                         75, "PROCESS_BOUNDARY_WRITE_FAULT", False, "unwritable --out: ")
        self.assertFalse((self.work / "pb").exists())
        clean = self.run_cli([processor, "--envelope", self.envelope(), "--out", out], {})
        self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)
        self.assertEqual(json.loads(clean.stdout)["status"], "PASS")

    def test_run_once_keeps_the_split(self):
        ingress = self.envelope()
        argv = ["resident-runtime/run_once.py", "--ingress", ingress, "--egress", str(self.work / "egress.json"),
                "--hb-epoch", "4096"]
        self.assert_exit(self.run_cli(argv, {"PROBE_WRITE_TEXT_FAIL_NAME": "execution.json"}),
                         75, "PROCESS_BOUNDARY_WRITE_FAULT", False, "process_boundary write fault: ")
        unknown = ["resident-runtime/run_once.py", "--ingress", self.envelope("admissible-existence.no-such-service"),
                   "--egress", str(self.work / "egress.json"), "--hb-epoch", "4096"]
        self.assert_exit(self.run_cli(unknown, {}), 65, "PROCESS_BOUNDARY_INPUT_FAULT", True, "bad input: ")
        self.assert_exit(self.run_cli(argv, {"PROBE_WRITE_TEXT_FAIL_NAME": "egress.json"}),
                         75, "RUN_ONCE_WRITE_FAILED", False, "egress write fault: ")
        self.assertFalse((self.work / "egress.json").exists())
        done = self.run_cli(argv, {})
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertTrue((self.work / "egress.json").exists())

    for _inherited in [name for name in dir(CliInputTraceTests) if name.startswith("test_")]:
        locals()[_inherited] = None
    del _inherited


DEEP_JSON = '{"a":' + "[" * 200000


class DeepJsonTests(ProcessBoundaryExitSplitTests):
    """FRAME_SCAN_RECURSION_ABORTS_CYCLE: a deeply nested document, far under the size
    cap, raises RecursionError (not a ValueError) when decoded. Every untrusted parse
    treats it as the input's fault: the scan quarantines it and the cycle continues."""

    def test_a_deep_frame_file_is_quarantined_and_the_cycle_continues(self):
        K = _load("probe_deep_scan_kernel", self.repo / "org-kernel" / "kernel.py")
        frames = self.mesh / "frames.d"
        frames.mkdir(parents=True)
        deep = frames / "0000-deep.json"
        deep.write_text(DEEP_JSON)
        self.assertLess(deep.stat().st_size, K.FRAME_FILE_MAX_BYTES)
        # A request whose response check scans frames.d (published_frame_for) as well.
        request = CommunicationIdCollisionTests.request(self, K, "deep-neighbour", "diagnostic-crossing")
        K.publish_frame(request, root=self.mesh)
        results = K.consume_and_respond(self.repo, mesh_root=self.mesh)
        by_path = {Path(item["path"]).name: item["result"] for item in results}
        self.assertEqual(by_path["0000-deep.json"]["failure_code"], "FRAME_INGEST_FAILED")
        self.assertIn("RecursionError", by_path["0000-deep.json"]["detail"])
        consumed = [result for name, result in by_path.items() if name != "0000-deep.json"]
        self.assertEqual([result["status"] for result in consumed], ["CONSUMED"])
        self.assertEqual(K.consume_and_respond(self.repo, mesh_root=self.mesh), [])
        statuses = sorted(marker["status"] for marker in self.markers())
        self.assertEqual(statuses, ["CONSUMED", "REFUSED"])

    def test_a_deep_frame_at_a_response_path_is_a_collision_not_an_abort(self):
        K = _load("probe_deep_publish_kernel", self.repo / "org-kernel" / "kernel.py")
        frame = self.aid_frame(K, "deep-squat")
        frame_id = hashlib.sha256((frame["packet_id"] + "|" + frame["frame_sha256"]).encode()).hexdigest()
        (self.mesh / "frames.d").mkdir(parents=True)
        (self.mesh / "frames.d" / (frame_id + ".json")).write_text(DEEP_JSON)
        with self.assertRaises(ValueError) as raised:
            K.publish_frame(frame, root=self.mesh)
        self.assertEqual(str(raised.exception), "federation_frame_write_once_collision")

    def test_deep_cli_inputs(self):
        deep = self.work / "deep.json"
        deep.write_text(DEEP_JSON)
        runs = [
            ("run_once --ingress", ["resident-runtime/run_once.py", "--ingress", str(deep), "--egress",
                                    str(self.work / "deep-egress.json"), "--hb-epoch", "4096"], "CLI_INPUT_INVALID", 1),
            # An inline argument is capped by the OS (128 KiB), so it nests less deeply; still a RecursionError.
            ("emit --evidence-json", self.emit_args()[:-4] + ["--evidence-json", '{"a":' + "[" * 50000, "--hb-epoch", "4096"],
             "CLI_INPUT_INVALID", 1),
            ("process_boundary --envelope", ["org-boundary/runtime/process_boundary.py", "--envelope", str(deep),
                                             "--out", str(self.work / "deep-pb" / "execution.json")],
             "PROCESS_BOUNDARY_INPUT_FAULT", 65),
        ]
        for label, argv, code, rc in runs:
            with self.subTest(cli=label):
                root = self.work / ("deep-" + label.split()[0])
                run = self.run_cli(argv, self.ledgers(root))
                self.assert_exit(run, rc, code, True, label + ": ")
                self.assertFalse(root.exists(), label)

    def test_a_deep_adapter_result_is_an_input_fault(self):
        (self.repo / "resident-runtime" / "deep_adapter.py").write_text(
            "import pathlib, sys\nout = pathlib.Path(sys.argv[sys.argv.index('--out') + 1])\n"
            "out.parent.mkdir(parents=True, exist_ok=True)\nout.write_text(" + repr(DEEP_JSON) + ")\n")
        self.set_adapter("resident-runtime/deep_adapter.py")
        run = self.run_cli(["org-boundary/runtime/process_boundary.py", "--envelope", self.envelope(),
                            "--out", str(self.work / "deep-adapter" / "execution.json")], {})
        self.assert_exit(run, 65, "PROCESS_BOUNDARY_INPUT_FAULT", True, "deep adapter result: ")
        self.assertIn("RecursionError", json.loads(run.stdout)["detail"])

    def test_deep_readback_and_custody_inputs(self):
        deep = self.work / "deep-input.json"
        deep.write_text(DEEP_JSON)
        readback = self.run_cli(["resident-runtime/organization_ledger_readback.py", "--location",
                                 str(self.work / "no-ledger"), "--closure-result", str(deep)], {})
        self.assertEqual(readback.returncode, 1, readback.stdout + readback.stderr)
        self.assertNotIn("Traceback", readback.stderr)
        refusal = json.loads(readback.stdout)
        self.assertEqual(refusal["failure_code"], "ORGANIZATION_LEDGER_READBACK_FAILED")
        for name in EPOCH_FIELDS:
            self.assertTrue(refusal[name], name)
        root = self.work / "deep-custody"
        custody = self.run_cli(["resident-runtime/submit_org_transition_to_master_records.py", "--org-receipt", str(deep),
                                "--predecessor-ecosystem-state-sha256", "sha256:" + "0" * 64,
                                "--successor-ecosystem-state-sha256", "sha256:" + "1" * 64,
                                "--standing", self.good("custody-standing", STANDING)],
                               {"STEGVERSE_ORG_FEDERATION_ROOT": str(root / "mesh")})
        self.assert_exit(custody, 1, "CLI_INPUT_INVALID", True, "custody --org-receipt: ")
        self.assertFalse(root.exists())

    def test_a_deep_outbox(self):
        self.outbox.write_text(DEEP_JSON)
        run = self.run_cli(["scripts/process_heartbeat_response.py", "--apply", "--hb-epoch", "4096"], {})
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        self.assertNotIn("Traceback", run.stderr)
        refusal = json.loads(run.stdout)
        self.assertEqual(refusal["failure_code"], "HB_OUTBOX_INVALID")
        self.assertIs(refusal["terminal"], True)

    for _inherited in [name for name in dir(ProcessBoundaryExitSplitTests) if name.startswith("test_")]:
        locals()[_inherited] = None
    del _inherited


class GatewayDeepFrameTests(_Workspace):
    """A deep or unusable frame inside a readable gateway envelope is refused terminally
    and acknowledged BLOCKED (FRAME_INGEST_FAILED); only an unreadable envelope stays
    non-terminal (GATEWAY_FETCH_INVALID, no acknowledgement)."""

    def cycle(self, body):
        cycle = _load("probe_deep_gateway_cycle", self.repo / "resident-runtime" / "federation_cycle.py")
        GW = cycle.GW
        acks = []

        def urlopen(request, timeout=None):
            if request.get_method() == "GET":
                return contextlib.nullcontext(io.BytesIO(body))
            acks.append(json.loads(request.data))
            return contextlib.nullcontext(io.BytesIO(b'{"state": "BLOCKED"}'))

        with mock.patch.dict(os.environ, {"STEGVERSE_ORG_FEDERATION_GATEWAY_URL": "https://gateway.invalid"}), \
                mock.patch.object(GW, "urlopen", urlopen):
            result = GW.resident_gateway_cycle(self.repo)
        return result, acks

    def test_a_deep_frame_in_a_readable_envelope_is_blocked(self):
        body = ('{"state": "FRAME_AVAILABLE", "frame": ' + "[" * 200000 + "]" * 200000 + "}").encode()
        result, acks = self.cycle(body)
        self.assertEqual(result["state"], "BLOCKED")
        refusal = result["ingest_refusal"]
        assert_six_fields(self, refusal, "FRAME_INGEST_FAILED")
        self.assertIs(refusal["terminal"], True)
        self.assertIn("RecursionError", refusal["detail"])
        self.assertTrue(refusal["frame_raw_sha256"].startswith("sha256:"))
        self.assertEqual([ack["state"] for ack in acks], ["BLOCKED"])
        self.assertIsNone(acks[0]["observed_at"])

    def test_an_unreadable_envelope_stays_non_terminal(self):
        for label, body in (("deep envelope", ("[" * 200000 + "]" * 200000).encode()),
                            ("deep state", ('{"state": ' + "[" * 200000 + "]" * 200000 + "}").encode()),
                            ("truncated deep", ('{"state": "FRAME_AVAILABLE", "frame": ' + "[" * 200000).encode()),
                            ("not json", b"{not json")):
            with self.subTest(envelope=label):
                result, acks = self.cycle(body)
                assert_six_fields(self, result, "GATEWAY_FETCH_INVALID")
                self.assertEqual(acks, [])

    def test_the_blocked_ack_names_the_frame(self):
        frame = ('{"packet_id": "deep-id", "frame_sha256": "sha256:' + "a" * 64 + '", "payload": '
                 + "[" * 200000 + "]" * 200000 + "}")
        result, acks = self.cycle(('{"state": "FRAME_AVAILABLE", "frame": ' + frame + "}").encode())
        self.assertEqual(result["state"], "BLOCKED")
        self.assertEqual(result["packet_id"], "deep-id")
        ack, = acks
        self.assertEqual(ack["packet_id"], "deep-id")
        self.assertEqual(ack["frame_sha256"], "sha256:" + "a" * 64)
        self.assertEqual(ack["frame_raw_sha256"],
                         "sha256:" + hashlib.sha256(frame.encode()).hexdigest())
        self.assertEqual(result["ingest_refusal"]["frame_raw_sha256"], ack["frame_raw_sha256"])

    def test_a_readable_fetch_is_unchanged(self):
        result, acks = self.cycle(b'{"state": "NO_FRAME"}')
        self.assertEqual(result["state"], "NO_FRAME")
        self.assertEqual(acks, [])


class NonFiniteNumberTests(DeepJsonTests):
    """NON_FINITE_NUMBER_WRITTEN_INTO_RECEIPT: NaN, Infinity, -Infinity and an
    overflowing literal (1e999) are not JSON. Every CLI input refuses them as a
    terminal CLI_INPUT_INVALID with nothing written; the receipt writers refuse
    to serialise them; a peer frame carrying one is quarantined."""

    NON_FINITE = ("NaN", "Infinity", "-Infinity", "1e999")

    def test_every_inline_writer_argument(self):
        cases = [
            ("emit --evidence-json", lambda text: self.emit_args()[:-4] + ["--evidence-json", text, "--hb-epoch", "4096"]),
            ("dispatch --evidence-json", lambda text: [
                "scripts/dispatch_ledger_writer.py", "--writer", "repository-ledger-emit", "--hb-epoch", "4096",
                "--arguments", " ".join(self.emit_args()[1:-4]) + " --evidence-json '" + text + "'"]),
            ("aggregate --boundary-evidence-json", lambda text: [
                "resident-runtime/aggregate_repo_transition.py", "--repo-receipt",
                str(self.repo_receipt_file(self.work / ("nan-source-" + str(abs(hash(text)))))),
                "--predecessor-org-state-sha256", "sha256:" + "2" * 64,
                "--successor-org-state-sha256", "sha256:" + "3" * 64, "--hb-epoch", "4096",
                "--boundary-evidence-json", text]),
        ]
        for label, argv_for in cases:
            for constant in self.NON_FINITE:
                with self.subTest(argument=label, value=constant):
                    root = self.work / ("nan-" + label.split()[0] + "-" + constant.strip("-"))
                    run = self.run_cli(argv_for('{"a": ' + constant + '}'), self.ledgers(root))
                    self.assert_input_refused(run, label + " " + constant + ": ", root)

    def test_every_file_argument(self):
        payload = dict(self.DIAGNOSTIC, body={**self.DIAGNOSTIC["body"], "n": "NAN_HERE"})
        text = json.dumps(payload).replace('"NAN_HERE"', "NaN")
        nan_file = self.work / "nan.json"
        nan_file.write_text(text)
        for label, argv, argument, _extra in self.file_arguments():
            with self.subTest(argument=label):
                root = self.work / ("nan-file-" + label.replace(" ", "_"))
                values = {**self.ledgers(root), "STEGVERSE_ORG_FEDERATION_ROOT": str(root / "mesh")}
                full = [item if item != "OUT" else str(root / "egress.json") for item in argv]
                run = self.run_cli(full + [argument, str(nan_file)], values)
                self.assert_input_refused(run, label + ": ", root)
        receipt = json.loads(Path(self.repo_receipt_file(self.work / "nan-receipt-source")).read_text())
        receipt_text = json.dumps(receipt).replace('"probe": "torn"', '"probe": NaN')
        receipt_file = self.work / "nan-receipt.json"
        receipt_file.write_text(receipt_text)
        root = self.work / "nan-aggregate-receipt"
        run = self.run_cli(["resident-runtime/aggregate_repo_transition.py", "--repo-receipt", str(receipt_file),
                            "--predecessor-org-state-sha256", "sha256:" + "2" * 64,
                            "--successor-org-state-sha256", "sha256:" + "3" * 64, "--hb-epoch", "4096"],
                           self.ledgers(root))
        self.assert_input_refused(run, "aggregate --repo-receipt evidence: ", root)

    def test_the_writers_refuse_to_serialise_a_non_finite_number(self):
        writer = _load("probe_nan_writer", self.repo / ".stegverse" / "transition-ledger" / "emit.py")
        root = self.work / "nan-library"
        os.environ.update(self.ledgers(root))
        with self.assertRaises(ValueError):
            writer.append("probe:nan", "PROBE", "sha256:" + "0" * 64, "sha256:" + "1" * 64,
                          {"a": float("nan")}, hb_epoch="4096")
        self.assertEqual(self.receipts(root, "repo-ledger"), [])
        store = _load("probe_nan_store", self.repo / "resident-runtime" / "ledger_store.py")
        with self.assertRaises(ValueError):
            store._document_bytes({"a": float("inf")})

    def test_a_peer_frame_carrying_a_non_finite_number_is_quarantined(self):
        K = _load("probe_nan_frame_kernel", self.repo / "org-kernel" / "kernel.py")
        # This kernel will not serialise NaN, so a hostile peer's frame is built by hand:
        # a valid frame whose packet bytes carry a raw NaN, with every hash recomputed.
        payload = {**FrameIngestErrorTests.INTR, "communication_id": "nan-frame",
                   "body": {"schema": "stegverse.org-intr-destination-diagnostic/v1", "probe": "NAN_HERE"}}
        frame = K.carrier_frame(self.packet(K, "admissible-existence.intr-destination", payload, "nan-frame"),
                                epoch=4096)
        raw = base64.b64decode(frame["packet_base64"]).replace(b'"NAN_HERE"', b"NaN")
        body = {key: value for key, value in frame.items() if key != "frame_sha256"}
        body.update(packet_base64=base64.b64encode(raw).decode("ascii"), packet_sha256=K.sha(raw))
        K.publish_frame({**body, "frame_sha256": K.sha(body)}, root=self.mesh)
        results = K.consume_and_respond(self.repo, mesh_root=self.mesh)
        self.assertEqual(results[0]["result"]["failure_code"], "FRAME_INGEST_FAILED")
        self.assertIn("non-finite", results[0]["result"]["detail"])
        self.assertEqual([marker["status"] for marker in self.markers()], ["REFUSED"])
        self.assertEqual(self.receipts(self.work, "repo-ledger"), [])

    for _inherited in [name for name in dir(DeepJsonTests) if name.startswith("test_")]:
        if _inherited not in ("test_every_file_argument",):
            locals()[_inherited] = None
    del _inherited


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


REQUEST_DIGEST = "ab" * 32


class CommittedRequestRecordedTests(_Workspace):
    """B-P40 clause (b): every record a committed-request run writes carries
    committed_request {path, sha256, hb_epoch_source: COMMITTED_REQUEST}."""

    # organization-ledger-transition.yml (Lane B's) was retired on main (19f74d6).
    WORKFLOWS = {
        "ledger-writer-dispatch.yml": "data/requests/ledger-writer-dispatch.json",
        "resident-runtime-dispatch.yml": "data/requests/resident-runtime-dispatch.json",
        "heartbeat-response-node.yml": "data/requests/heartbeat-response-node.json",
    }

    def request(self, path):
        os.environ["STEGVERSE_COMMITTED_REQUEST_PATH"] = path
        os.environ["STEGVERSE_COMMITTED_REQUEST_SHA256"] = REQUEST_DIGEST
        return {"path": path, "sha256": REQUEST_DIGEST, "hb_epoch_source": "COMMITTED_REQUEST"}

    def run_cli(self, *argv):
        completed = subprocess.run([sys.executable, *argv], cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        return completed.stdout

    def receipts(self):
        found = []
        for root in (self.work / "repo-ledger", self.work / "org-ledger"):
            for path in sorted(root.rglob("*.json")):
                record = json.loads(path.read_text())
                if record.get("schema") in ("stegverse.repo-transition-receipt/v1",
                                            "stegverse.organization-transition-receipt/v1"):
                    found.append((path, record))
        return found

    def test_each_workflow_passes_its_gated_request_to_the_writer(self):
        for name, request in self.WORKFLOWS.items():
            with self.subTest(workflow=name):
                text = (ROOT / ".github" / "workflows" / name).read_text()
                self.assertEqual(text.count("STEGVERSE_COMMITTED_REQUEST_PATH: " + request), 1)
                self.assertEqual(text.count(
                    "STEGVERSE_COMMITTED_REQUEST_SHA256: ${{ steps.request.outputs.request_sha256 }}"), 1)
                argv = _gate_argv(text)
                self.assertEqual(argv[argv.index("--request") + 1], request)
                self.assertLess(text.index(REQUEST_GATE), text.index("STEGVERSE_COMMITTED_REQUEST_PATH"))

    def test_every_ledger_receipt_records_the_committed_request(self):
        # ledger-writer-dispatch: emit and aggregate through the dispatcher,
        # egress and ingress through their own entrypoints.
        recorded = self.request("data/requests/ledger-writer-dispatch.json")
        receipt = json.loads(self.run_cli(
            "scripts/dispatch_ledger_writer.py", "--writer", "repository-ledger-emit", "--hb-epoch", "4096",
            "--arguments", "--transition-id request-probe --transition-class PROBE "
            "--predecessor-state-sha256 sha256:" + "0" * 64 + " --successor-state-sha256 sha256:" + "1" * 64))
        self.assertEqual(receipt["evidence"]["committed_request"], recorded)
        source = self.work / "repo-receipt.json"
        source.write_text(json.dumps(receipt))
        aggregated = json.loads(self.run_cli(
            "scripts/dispatch_ledger_writer.py", "--writer", "organization-ledger-aggregate", "--hb-epoch", "4096",
            "--arguments", "--repo-receipt " + str(source) + " --predecessor-org-state-sha256 sha256:" + "2" * 64
            + " --successor-org-state-sha256 sha256:" + "3" * 64))
        self.assertEqual(aggregated["boundary_evidence"]["committed_request"], recorded)
        egress = _load("probe_request_egress", self.repo / "resident-runtime" / "organization_egress_boundary.py")
        payload = {"message_class": "ecosystem.communication", "communication_id": "request-probe",
                   "subject": "probe",
                   "body": {"schema": "stegverse.org-intr-destination-diagnostic/v1", "probe": "diagnostic-crossing"}}
        self.assertIs(egress.emit(PEER, payload, standing=STANDING, capability="intr-destination",
                                  mesh_root=self.mesh, hb_epoch="4096")["emitted"], True)
        self.run_cli("resident-runtime/intr_destination_ingress.py", "--self-close", "--communication-id",
                     "request-probe", "--hb-epoch", "4096", "--packet-id", "request-probe:request-sha256:"
                     + REQUEST_DIGEST, "--out", str(self.work / "closure.json"))
        receipts = self.receipts()
        self.assertGreaterEqual(len(receipts), 6)
        for path, record in receipts:
            with self.subTest(receipt=path.name):
                evidence = record.get("evidence", record.get("boundary_evidence"))
                self.assertEqual(evidence["committed_request"], recorded)

    def test_the_resident_cycle_records_carry_the_committed_request(self):
        recorded = self.request("data/requests/resident-runtime-dispatch.json")
        cycle = _load("probe_request_cycle", self.repo / "resident-runtime" / "federation_cycle.py")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cycle.main(["--hb-epoch", "4096"]), 0)
        latest = json.loads((self.repo / "resident-runtime" / "federation" / "latest-cycle.json").read_text())
        self.assertEqual(latest["committed_request"], recorded)
        status = json.loads(self.run_cli("resident-runtime/ecosystem_control.py", "--hb-epoch", "4096", "status"))
        self.assertEqual(status["committed_request"], recorded)
        transport = _load("probe_request_transport", self.repo / "org-boundary" / "runtime" / "intr_transport.py")
        ingress = transport.build_ingress({"org": PEER, "service": "p"},
                                          {"org": THIS, "service": "admissible-existence.boundary-diagnostic"},
                                          {"probe": 1}, "org-federation", "probe", packet_id="request-run-once",
                                          epoch=4096)
        envelope = self.work / "ingress.json"
        envelope.write_text(json.dumps(ingress))
        result = json.loads(self.run_cli("resident-runtime/run_once.py", "--ingress", str(envelope), "--egress",
                                         str(self.work / "egress.json"), "--hb-epoch", "4096"))
        self.assertEqual(result["committed_request"], recorded)

    def test_both_heartbeat_receipts_carry_the_committed_request(self):
        recorded = self.request("data/requests/heartbeat-response-node.json")
        node = _load("probe_request_node", self.repo / "scripts" / "process_heartbeat_response.py")
        receipts = self.work / "receipts"
        body = json.dumps({"messages": [HeartbeatResponseEpochTests.MESSAGE]}).encode()
        config = json.loads((self.repo / "data" / "heartbeat-response-node.json").read_text())
        with mock.patch.object(node, "RECEIPTS", receipts), \
                mock.patch.object(node, "urlopen", lambda *a, **k: contextlib.nullcontext(io.BytesIO(body))), \
                contextlib.redirect_stdout(io.StringIO()):
            node.apply(config, "4096")
        written_receipts = sorted(receipts.glob("*.json"))
        self.assertEqual(len(written_receipts), 2)
        for path in written_receipts:
            with self.subTest(receipt=path.name):
                self.assertEqual(json.loads(path.read_text())["committed_request"], recorded)

    FORGED = {"path": "data/requests/forged.json", "sha256": "f" * 64, "hb_epoch_source": "COMMITTED_REQUEST"}
    EMIT_ARGS = ["--transition-class", "PROBE", "--predecessor-state-sha256", "sha256:" + "0" * 64,
                 "--successor-state-sha256", "sha256:" + "1" * 64, "--hb-epoch", "4096"]

    def refused_cli(self, *argv):
        completed = subprocess.run([sys.executable, *argv], cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        assert_six_fields(self, json.loads(completed.stdout), "COMMITTED_REQUEST_INVALID")

    def test_a_caller_supplied_committed_request_is_refused_with_nothing_written(self):
        # A genuine repository receipt, written before the forgeries, for the aggregate to propagate.
        source = self.work / "repo-receipt.json"
        source.write_text(self.run_cli(".stegverse/transition-ledger/emit.py", "--transition-id", "genuine",
                                       *self.EMIT_ARGS))
        emit = _load("probe_forged_emit", self.repo / ".stegverse" / "transition-ledger" / "emit.py")
        aggregate = _load("probe_forged_aggregate", self.repo / "resident-runtime" / "aggregate_repo_transition.py")
        repo_receipt = json.loads(source.read_text())
        for env_present, forged_evidence in ((False, {"committed_request": self.FORGED}),
                                             (True, {"committed_request": self.FORGED}),
                                             (False, {"nested": [{"deeper": {"committed_request": self.FORGED}}]}),
                                             (True, {"nested": [{"deeper": {"committed_request": self.FORGED}}]})):
            forged = json.dumps(forged_evidence)
            with self.subTest(env_present=env_present, evidence=forged):
                if env_present:
                    self.request("data/requests/ledger-writer-dispatch.json")
                else:
                    os.environ.pop("STEGVERSE_COMMITTED_REQUEST_PATH", None)
                    os.environ.pop("STEGVERSE_COMMITTED_REQUEST_SHA256", None)
                before = snapshot(self.work)
                self.refused_cli(".stegverse/transition-ledger/emit.py", "--transition-id", "forged",
                                 *self.EMIT_ARGS, "--evidence-json", forged)
                self.refused_cli("resident-runtime/aggregate_repo_transition.py", "--repo-receipt", str(source),
                                 "--predecessor-org-state-sha256", "sha256:" + "2" * 64,
                                 "--successor-org-state-sha256", "sha256:" + "3" * 64, "--hb-epoch", "4096",
                                 "--boundary-evidence-json", forged)
                with self.assertRaises(emit.RepoLedgerEpochRefused) as refused:
                    emit.append("forged", "PROBE", "sha256:" + "0" * 64, "sha256:" + "1" * 64,
                                forged_evidence, hb_epoch="4096")
                assert_six_fields(self, refused.exception.refusal, "COMMITTED_REQUEST_INVALID")
                with self.assertRaises(aggregate.OrgLedgerEpochRefused) as refused:
                    aggregate.append(repo_receipt, "REPO_STATE_PROPAGATION", "sha256:" + "2" * 64,
                                     "sha256:" + "3" * 64, forged_evidence, hb_epoch="4096")
                assert_six_fields(self, refused.exception.refusal, "COMMITTED_REQUEST_INVALID")
                self.assertEqual(written(self.work, before), [])

    def test_aggregate_refuses_a_source_that_is_off_ledger_or_of_another_request(self):
        emit = _load("probe_unverified_emit", self.repo / ".stegverse" / "transition-ledger" / "emit.py")
        aggregate = _load("probe_unverified_aggregate", self.repo / "resident-runtime" / "aggregate_repo_transition.py")
        states = ("sha256:" + "0" * 64, "sha256:" + "1" * 64)
        # On the ledger, under another committed request.
        os.environ["STEGVERSE_COMMITTED_REQUEST_PATH"] = "data/requests/ledger-writer-dispatch.json"
        os.environ["STEGVERSE_COMMITTED_REQUEST_SHA256"] = "cd" * 32
        other = emit.append("probe:other-request", "PROBE", *states, {}, hb_epoch="4096")
        recorded = self.request("data/requests/ledger-writer-dispatch.json")
        genuine = emit.append("probe:genuine", "PROBE", *states, {}, hb_epoch="4096")
        self.assertEqual(genuine["evidence"]["committed_request"], recorded)

        def rehashed(**changes):
            body = {key: value for key, value in genuine.items() if key != "receipt_sha256"}
            body.update(changes)
            return {**body, "receipt_sha256": emit.sha(body)}

        sources = {
            "off-ledger, forged request": (rehashed(evidence={"committed_request": self.FORGED}),
                                           "SOURCE_RECEIPT_NOT_ON_LEDGER"),
            "off-ledger, this run's request": (rehashed(transition_id="probe:rehashed"),
                                               "SOURCE_RECEIPT_NOT_ON_LEDGER"),
            "on-ledger, another request": (other, "COMMITTED_REQUEST_DIGEST_UNVERIFIED"),
        }
        for label, (source, code) in sources.items():
            with self.subTest(source=label):
                before = snapshot(self.work)
                with self.assertRaises(aggregate.OrgLedgerEpochRefused) as refused:
                    aggregate.append(source, "REPO_STATE_PROPAGATION", "sha256:" + "2" * 64, "sha256:" + "3" * 64,
                                     {}, hb_epoch="4096")
                assert_six_fields(self, refused.exception.refusal, code)
                path = self.work / "source.json"
                path.write_text(json.dumps(source))
                completed = subprocess.run(
                    [sys.executable, "resident-runtime/aggregate_repo_transition.py", "--repo-receipt", str(path),
                     "--predecessor-org-state-sha256", "sha256:" + "2" * 64,
                     "--successor-org-state-sha256", "sha256:" + "3" * 64, "--hb-epoch", "4096"],
                    cwd=self.repo, capture_output=True, text=True)
                self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
                assert_six_fields(self, json.loads(completed.stdout), code)
                self.assertEqual([item for item in written(self.work, before) if item != path], [])
                self.assertFalse((self.work / "org-ledger").exists())
        # The genuine source, on the ledger with this run's request, is aggregated.
        record = aggregate.append(genuine, "REPO_STATE_PROPAGATION", "sha256:" + "2" * 64, "sha256:" + "3" * 64,
                                  {}, hb_epoch="4096")
        self.assertEqual(record["boundary_evidence"]["committed_request"], recorded)

    def test_aggregate_refuses_an_off_ledger_source_without_a_binding(self):
        # OFF_LEDGER_SOURCE_RECEIPT_WITHOUT_BINDING_ACCEPTED: the ledger check is
        # unconditional, outside a committed-request run and without committed_request.
        emit = _load("probe_unbound_emit", self.repo / ".stegverse" / "transition-ledger" / "emit.py")
        aggregate = _load("probe_unbound_aggregate", self.repo / "resident-runtime" / "aggregate_repo_transition.py")
        genuine = emit.append("probe:unbound", "PROBE", "sha256:" + "0" * 64, "sha256:" + "1" * 64, {},
                              hb_epoch="4096")
        self.assertNotIn("committed_request", genuine["evidence"])
        body = {key: value for key, value in genuine.items() if key != "receipt_sha256"}
        body["transition_id"] = "probe:unbound-rehashed"
        source = {**body, "receipt_sha256": emit.sha(body)}
        aggregate.verify_repo(source)  # the hash is self-consistent
        before = snapshot(self.work)
        with self.assertRaises(aggregate.OrgLedgerEpochRefused) as refused:
            aggregate.append(source, "REPO_STATE_PROPAGATION", "sha256:" + "2" * 64, "sha256:" + "3" * 64, {},
                             hb_epoch="4096")
        assert_six_fields(self, refused.exception.refusal, "SOURCE_RECEIPT_NOT_ON_LEDGER")
        self.assertEqual(written(self.work, before), [])
        self.assertFalse((self.work / "org-ledger").exists())
        # The genuine receipt with one byte of its evidence changed and rehashed is not on the ledger either.
        altered = {**body, "transition_id": genuine["transition_id"], "evidence": {"probe": "altered"}}
        with self.assertRaises(aggregate.OrgLedgerEpochRefused) as refused:
            aggregate.append({**altered, "receipt_sha256": emit.sha(altered)}, "REPO_STATE_PROPAGATION",
                             "sha256:" + "2" * 64, "sha256:" + "3" * 64, {}, hb_epoch="4096")
        assert_six_fields(self, refused.exception.refusal, "SOURCE_RECEIPT_NOT_ON_LEDGER")
        self.assertEqual(written(self.work, before), [])

    def mint(self, name, ledger, repository=None):
        """A receipt minted by the real emit into `ledger`, as `repository` (default: this one)."""
        emit = _load("probe_mint_" + name, self.repo / ".stegverse" / "transition-ledger" / "emit.py")
        if repository is not None:
            emit.CONTRACT = {**emit.CONTRACT, "repository": repository}
        with mock.patch.dict(os.environ, {"STEGVERSE_REPO_LEDGER_ROOT": str(ledger)}):
            return emit.append("probe:" + name, "PROBE", "sha256:" + "0" * 64, "sha256:" + "1" * 64, {},
                               hb_epoch="4096")

    def refused_aggregate(self, aggregate, source, code, *, terminal=True):
        before = snapshot(self.work)
        with self.assertRaises(aggregate.OrgLedgerEpochRefused) as refused:
            aggregate.append(source, "REPO_STATE_PROPAGATION", "sha256:" + "2" * 64, "sha256:" + "3" * 64, {},
                             hb_epoch="4096")
        assert_six_fields(self, refused.exception.refusal, code)
        self.assertIs(refused.exception.refusal["terminal"], terminal)
        self.assertEqual(written(self.work, before), [])
        self.assertFalse((self.work / "org-ledger").exists())

    def test_a_receipt_minted_in_another_ledger_is_not_laundered(self):
        # Row 8, SOURCE_LEDGER_OVERRIDE_LAUNDERS_FABRICATED_RECEIPT: the only
        # ledger read is this repository's own emit store; no caller or
        # receipt names another.
        aggregate = _load("probe_launder_aggregate", self.repo / "resident-runtime" / "aggregate_repo_transition.py")
        import inspect
        self.assertEqual(list(inspect.signature(aggregate.source_ledger).parameters), [])
        attacker = self.mint("attacker-ledger", self.work / "attacker-ledger")
        self.refused_aggregate(aggregate, attacker, "SOURCE_RECEIPT_NOT_ON_LEDGER")
        other = self.mint("other-repository", self.work / "repo-ledger", THIS + "/other")
        self.refused_aggregate(aggregate, other, "SOURCE_RECEIPT_NOT_ON_LEDGER")
        # With no supplied root, the receipt's repository never becomes a path,
        # even through a symlink placed where it would resolve.
        state = self.work / "state"
        linked = state / "stegverse" / "repo-ledgers" / THIS / "linked"
        linked.parent.mkdir(parents=True)
        linked.symlink_to(self.work / "symlinked-ledger", target_is_directory=True)
        symlinked = self.mint("symlinked", self.work / "symlinked-ledger", THIS + "/linked")
        os.environ.pop("STEGVERSE_REPO_LEDGER_ROOT")
        os.environ["XDG_STATE_HOME"] = str(state)
        self.refused_aggregate(aggregate, symlinked, "SOURCE_RECEIPT_NOT_ON_LEDGER")

    def test_a_corrupt_stored_receipt_is_refused_not_a_traceback(self):
        # Row 9, SOURCE_LEDGER_WALK_TRACEBACK_ON_CORRUPT_RECEIPT.
        aggregate = _load("probe_corrupt_aggregate", self.repo / "resident-runtime" / "aggregate_repo_transition.py")
        source = self.mint("corrupt", self.work / "repo-ledger")
        stored = self.work / "repo-ledger" / "receipts" / (source["receipt_sha256"].split(":", 1)[1] + ".json")
        original = stored.read_bytes()
        for label, data in (("truncated", original[: len(original) // 2]), ("garbage", b"\xff\x00 not a receipt")):
            with self.subTest(stored=label):
                stored.write_bytes(data)
                self.refused_aggregate(aggregate, source, "SOURCE_RECEIPT_NOT_ON_LEDGER", terminal=True)
        stored.write_bytes(original)
        with mock.patch.object(aggregate.ledger_store.PosixLedgerStore, "get",
                               side_effect=OSError(5, "Input/output error")):
            self.refused_aggregate(aggregate, source, "SOURCE_RECEIPT_NOT_ON_LEDGER", terminal=False)
        self.assertEqual(aggregate.append(source, "REPO_STATE_PROPAGATION", "sha256:" + "2" * 64,
                                          "sha256:" + "3" * 64, {}, hb_epoch="4096")["repo_receipt_sha256"],
                         source["receipt_sha256"])

    def test_egress_refuses_a_malformed_committed_request_before_publishing(self):
        egress = _load("probe_request_egress_refused", self.repo / "resident-runtime" / "organization_egress_boundary.py")
        payload = {"message_class": "ecosystem.communication", "communication_id": "request-refused",
                   "subject": "probe",
                   "body": {"schema": "stegverse.org-intr-destination-diagnostic/v1", "probe": "diagnostic-crossing"}}
        cases = {
            "sha only": {"STEGVERSE_COMMITTED_REQUEST_SHA256": REQUEST_DIGEST},
            "path only": {"STEGVERSE_COMMITTED_REQUEST_PATH": "data/requests/ledger-writer-dispatch.json"},
            "malformed sha": {"STEGVERSE_COMMITTED_REQUEST_PATH": "data/requests/ledger-writer-dispatch.json",
                              "STEGVERSE_COMMITTED_REQUEST_SHA256": "not-a-digest"},
        }
        for label, environ in cases.items():
            with self.subTest(env=label):
                os.environ.pop("STEGVERSE_COMMITTED_REQUEST_PATH", None)
                os.environ.pop("STEGVERSE_COMMITTED_REQUEST_SHA256", None)
                os.environ.update(environ)
                before = snapshot(self.work)
                with self.assertRaises(egress.repository_ledger.RepoLedgerEpochRefused) as refused:
                    egress.emit(PEER, payload, standing=STANDING, capability="intr-destination",
                                mesh_root=self.mesh, hb_epoch="4096")
                assert_six_fields(self, refused.exception.refusal, "COMMITTED_REQUEST_INVALID")
                self.assertEqual(written(self.work, before), [])
                self.assertEqual(list(self.mesh.rglob("*.json")) if self.mesh.exists() else [], [])

    def test_a_malformed_committed_request_is_refused_before_anything_is_written(self):
        os.environ["STEGVERSE_COMMITTED_REQUEST_PATH"] = "data/requests/ledger-writer-dispatch.json"
        os.environ["STEGVERSE_COMMITTED_REQUEST_SHA256"] = "not-a-digest"
        completed = subprocess.run(
            [sys.executable, "scripts/dispatch_ledger_writer.py", "--writer", "repository-ledger-emit",
             "--hb-epoch", "4096", "--arguments", "--transition-id request-probe --transition-class PROBE "
             "--predecessor-state-sha256 sha256:" + "0" * 64 + " --successor-state-sha256 sha256:" + "1" * 64],
            cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        assert_six_fields(self, json.loads(completed.stdout), "COMMITTED_REQUEST_INVALID")
        cycle = _load("probe_request_cycle_refused", self.repo / "resident-runtime" / "federation_cycle.py")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(cycle.main(["--hb-epoch", "4096"]), 1)
        assert_six_fields(self, json.loads(out.getvalue()), "COMMITTED_REQUEST_INVALID")
        self.assertFalse((self.repo / "resident-runtime" / "federation" / "latest-cycle.json").exists())
        self.assertEqual(self.receipts(), [])


class SourceLedgerPairingTests(_Workspace):
    """CALLER_CHOSEN_SOURCE_LEDGER_ACCEPTED (lead 21:13Z, paired-override form): with no
    override the source ledger is the designated one; an override is accepted only as a
    pair with the organization ledger, a POSIX pair only where this checkout tracks no
    file; a lone, mismatched or request override is refused."""

    REF = "refs/stegverse/organization-ledger"
    NAMESPACE = "repository-ledger/Admissible-Existence/.github"

    def setUp(self):
        super().setUp()
        self.aggregate = _load("probe_pairing_aggregate", self.repo / "resident-runtime" / "aggregate_repo_transition.py")
        self.emit = _load("probe_pairing_emit", self.repo / ".stegverse" / "transition-ledger" / "emit.py")

    def git_repository(self, name):
        path = self.work / name
        subprocess.run(["git", "init", "-q", str(path)], check=True)
        return path

    def pair(self, org, repo):
        os.environ["STEGVERSE_ORG_LEDGER_ROOT"] = org
        os.environ["STEGVERSE_REPO_LEDGER_ROOT"] = repo

    def source(self, name="probe:pairing"):
        return self.emit.append(name, "PROBE", "sha256:" + "0" * 64, "sha256:" + "1" * 64, {}, hb_epoch="4096")

    def aggregate_source(self, source):
        return self.aggregate.append(source, "REPO_STATE_PROPAGATION", "sha256:" + "2" * 64, "sha256:" + "3" * 64,
                                     {}, hb_epoch="4096")

    def test_a_git_pair_is_accepted_through_a_symlink(self):
        ledger = self.git_repository("ledger")
        linked = self.work / "linked"
        linked.symlink_to(ledger, target_is_directory=True)
        self.pair(f"git+{ledger}#{self.REF}", f"git+{ledger}#{self.REF}:{self.NAMESPACE}")
        source = self.source()
        os.environ["STEGVERSE_REPO_LEDGER_ROOT"] = f"git+{linked}#{self.REF}:{self.NAMESPACE}"
        self.assertEqual(self.aggregate_source(source)["repo_receipt_sha256"], source["receipt_sha256"])

    def test_an_unpaired_source_ledger_is_refused_with_nothing_written(self):
        ledger = self.git_repository("ledger")
        other = self.git_repository("other")
        to_other = self.work / "to-other"
        to_other.symlink_to(other, target_is_directory=True)
        org = f"git+{ledger}#{self.REF}"
        cases = {
            "mixed git and POSIX": (org, str(self.work / "repo-ledger")),
            "POSIX and git": (str(self.work / "org-ledger"), f"git+{ledger}#{self.REF}:{self.NAMESPACE}"),
            "another repository's namespace": (org, f"git+{ledger}#{self.REF}:repository-ledger/{THIS}/other"),
            "a different ref": (org, f"git+{ledger}#refs/stegverse/other:{self.NAMESPACE}"),
            "another repository": (org, f"git+{other}#{self.REF}:{self.NAMESPACE}"),
            "a symlink to another repository": (org, f"git+{to_other}#{self.REF}:{self.NAMESPACE}"),
            # Both at one non-contract ref: in an attacker repository, and in this checkout.
            "a non-contract ref in another repository": (f"git+{ledger}#refs/stegverse/not-the-contract",
                                                         f"git+{ledger}#refs/stegverse/not-the-contract:{self.NAMESPACE}"),
            "a non-contract ref in this checkout": (f"git+{self.repo}#refs/stegverse/not-the-contract",
                                                    f"git+{self.repo}#refs/stegverse/not-the-contract:{self.NAMESPACE}"),
        }
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        for label, (org_root, repo_root) in cases.items():
            with self.subTest(pair=label):
                # The source is genuinely on the ledger the repository root names.
                self.pair(org_root, repo_root)
                source = self.source("probe:" + label.replace(" ", "-").replace("'", ""))
                before = snapshot(self.work)
                with self.assertRaises(self.aggregate.OrgLedgerEpochRefused) as refused:
                    self.aggregate_source(source)
                assert_six_fields(self, refused.exception.refusal, "CALLER_CHOSEN_SOURCE_LEDGER_REJECTED")
                self.assertEqual(written(self.work, before), [])

    def test_a_lone_repository_ledger_override_is_refused(self):
        source = self.source()
        os.environ.pop("STEGVERSE_ORG_LEDGER_ROOT")
        before = snapshot(self.work)
        with self.assertRaises(self.aggregate.OrgLedgerEpochRefused) as refused:
            self.aggregate_source(source)
        assert_six_fields(self, refused.exception.refusal, "CALLER_CHOSEN_SOURCE_LEDGER_REJECTED")
        self.assertEqual(written(self.work, before), [])

    def test_a_ledger_root_holding_tracked_files_is_not_contract_designated(self):
        # A fake ledger committed in the checkout, then pointed at as a POSIX pair.
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        fake = self.repo / "fake-ledger"
        self.pair(str(fake / "org"), str(fake / "repo"))
        source = self.source()
        identity = ["-c", "user.name=probe", "-c", "user.email=probe@example.invalid"]
        subprocess.run(["git", "-C", str(self.repo), "add", "fake-ledger"], check=True)
        subprocess.run(["git", "-C", str(self.repo), *identity, "commit", "-q", "-m", "fake ledger"], check=True)
        before = snapshot(self.work)
        with self.assertRaises(self.aggregate.OrgLedgerEpochRefused) as refused:
            self.aggregate_source(source)
        assert_six_fields(self, refused.exception.refusal, "LEDGER_ROOT_NOT_CONTRACT_DESIGNATED")
        self.assertEqual(written(self.work, before), [])
        # The same pair, untracked (a runner-temp or workspace root), is accepted.
        subprocess.run(["git", "-C", str(self.repo), *identity, "rm", "-rq", "--cached", "fake-ledger"], check=True)
        subprocess.run(["git", "-C", str(self.repo), *identity, "commit", "-q", "-m", "untrack"], check=True)
        self.assertEqual(self.aggregate_source(source)["repo_receipt_sha256"], source["receipt_sha256"])

    def test_with_no_override_only_the_designated_ledger_is_read(self):
        source = self.source()  # on the workspace's POSIX ledger, not the designated one
        os.environ.pop("STEGVERSE_REPO_LEDGER_ROOT")
        os.environ.pop("STEGVERSE_ORG_LEDGER_ROOT")
        os.environ["XDG_STATE_HOME"] = str(self.work)
        with self.assertRaises(self.aggregate.OrgLedgerEpochRefused) as refused:
            self.aggregate_source(source)
        assert_six_fields(self, refused.exception.refusal, "SOURCE_RECEIPT_NOT_ON_LEDGER")

    def test_a_request_cannot_choose_either_ledger(self):
        workflow = (ROOT / ".github" / "workflows" / "ledger-writer-dispatch.yml").read_text()
        self.assertNotIn("ledger_root }}", workflow)
        for field, value in (("repo_ledger_root", str(self.work / "attacker")),
                             ("org_ledger_root", f"git+{self.work / 'attacker'}#refs/stegverse/not-the-contract")):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as work:
                completed = _run_gate(workflow, json.dumps({"writer": "organization-ledger-aggregate",
                                                            "hb_epoch": "4096", field: value}), work)
                self.assertEqual(completed.returncode, 1)
                assert_six_fields(self, json.loads(completed.stdout), "COMMITTED_REQUEST_INVALID")


class SourceCommittedRequestTests(_Workspace):
    """LWD_AGGREGATE_UNREACHABLE_ONE_WRITER_PER_REQUEST (lead 20:54Z): a request may name
    source_committed_request, the request that produced its source receipt. Each named
    digest must be a version of the request committed on the request path, with a receipt
    bound to it on the ledger (SOURCE_REQUEST_NOT_RESOLVED_TO_COMMITTED_REQUEST)."""

    PATH = "data/requests/ledger-writer-dispatch.json"
    IDENTITY = ["-c", "user.name=probe", "-c", "user.email=probe@example.invalid"]

    def setUp(self):
        super().setUp()
        self.aggregate = _load("probe_chain_aggregate", self.repo / "resident-runtime" / "aggregate_repo_transition.py")
        self.emit = _load("probe_chain_emit", self.repo / ".stegverse" / "transition-ledger" / "emit.py")
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.serial = 0

    def committed(self):
        """Commit a new version of the request and return its sha256."""
        self.serial += 1
        request = self.repo / self.PATH
        request.parent.mkdir(parents=True, exist_ok=True)
        data = json.dumps({"writer": "repository-ledger-emit", "hb_epoch": "4096",
                           "arguments": "--transition-id probe-%d" % self.serial}).encode()
        request.write_bytes(data)
        subprocess.run(["git", "-C", str(self.repo), "add", self.PATH], check=True)
        subprocess.run(["git", "-C", str(self.repo), *self.IDENTITY, "commit", "-q", "-m", "request"], check=True)
        return hashlib.sha256(data).hexdigest()

    def run_as(self, digest, source=None):
        os.environ["STEGVERSE_COMMITTED_REQUEST_PATH"] = self.PATH
        os.environ["STEGVERSE_COMMITTED_REQUEST_SHA256"] = digest
        if source is None:
            os.environ.pop("STEGVERSE_SOURCE_COMMITTED_REQUEST_SHA256", None)
        else:
            os.environ["STEGVERSE_SOURCE_COMMITTED_REQUEST_SHA256"] = source

    def emitted(self, digest, source=None):
        self.run_as(digest, source)
        return self.emit.append("probe:" + digest, "PROBE", "sha256:" + "0" * 64, "sha256:" + "1" * 64, {},
                                hb_epoch="4096")

    def aggregated(self, receipt, digest, source):
        self.run_as(digest, source)
        return self.aggregate.append(receipt, "REPO_STATE_PROPAGATION", "sha256:" + "2" * 64, "sha256:" + "3" * 64,
                                     {}, hb_epoch="4096")

    def refused(self, receipt, digest, source, code):
        before = snapshot(self.work)
        with self.assertRaises(self.aggregate.OrgLedgerEpochRefused) as refused:
            self.aggregated(receipt, digest, source)
        assert_six_fields(self, refused.exception.refusal, code)
        self.assertEqual(written(self.work, before), [])
        self.assertFalse((self.work / "org-ledger").exists())
        return refused.exception.refusal

    def test_a_genuine_two_request_aggregate_records_both_digests(self):
        first, second = self.committed(), self.committed()
        source = self.emitted(first)
        record = self.aggregated(source, second, first)
        self.assertEqual(record["boundary_evidence"]["committed_request"]["sha256"], second)
        self.assertEqual(record["boundary_evidence"]["source_committed_request"], {"path": self.PATH, "sha256": first})

    def test_a_genuine_two_request_aggregate_through_the_ledger_writer_dispatcher(self):
        first, second = self.committed(), self.committed()

        def dispatch(digest, source, writer, arguments):
            env = {**os.environ, "STEGVERSE_COMMITTED_REQUEST_PATH": self.PATH,
                   "STEGVERSE_COMMITTED_REQUEST_SHA256": digest, "STEGVERSE_SOURCE_COMMITTED_REQUEST_SHA256": source}
            completed = subprocess.run([sys.executable, "scripts/dispatch_ledger_writer.py", "--writer", writer,
                                        "--hb-epoch", "4096", "--arguments", arguments],
                                       cwd=self.repo, capture_output=True, text=True, env=env)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            return json.loads(completed.stdout)
        receipt = dispatch(first, "", "repository-ledger-emit",
                           "--transition-id lwd-emit --transition-class PROBE --predecessor-state-sha256 sha256:"
                           + "0" * 64 + " --successor-state-sha256 sha256:" + "1" * 64)
        path = self.work / "lwd-receipt.json"
        path.write_text(json.dumps(receipt))
        record = dispatch(second, first, "organization-ledger-aggregate",
                          "--repo-receipt " + str(path) + " --predecessor-org-state-sha256 sha256:" + "2" * 64
                          + " --successor-org-state-sha256 sha256:" + "3" * 64)
        self.assertEqual(record["boundary_evidence"]["source_committed_request"]["sha256"], first)
        self.assertEqual(record["boundary_evidence"]["committed_request"]["sha256"], second)

    def test_a_bound_but_uncommitted_digest_is_refused(self):
        # SOURCE_REQUEST_NOT_RESOLVED_TO_COMMITTED_REQUEST: a ledger binding alone is not enough.
        second = self.committed()
        uncommitted = "ab" * 32
        source = self.emitted(uncommitted)  # bound on the ledger, never committed on the request path
        refusal = self.refused(source, second, uncommitted, "COMMITTED_REQUEST_DIGEST_UNVERIFIED")
        self.assertIn("not a version of " + self.PATH + " committed", refusal["detail"])
        # A committed request whose chain names an uncommitted, bound one is refused too.
        first = self.committed()
        chained = self.emitted(first, uncommitted)
        self.refused(chained, second, first, "COMMITTED_REQUEST_DIGEST_UNVERIFIED")

    def test_a_wrong_digest_is_refused(self):
        first, second, other = self.committed(), self.committed(), self.committed()
        source = self.emitted(first)
        self.emitted(other)  # another genuine request on the ledger
        self.refused(source, second, other, "COMMITTED_REQUEST_DIGEST_UNVERIFIED")

    def test_a_missing_request_in_the_chain_is_refused(self):
        first, second, unbound = self.committed(), self.committed(), self.committed()
        source = self.emitted(first, unbound)  # names a committed request with no receipt
        self.refused(source, second, first, "COMMITTED_REQUEST_DIGEST_UNVERIFIED")

    def test_a_request_cannot_name_itself(self):
        first, second = self.committed(), self.committed()
        source = self.emitted(first)
        self.refused(source, second, second, "COMMITTED_REQUEST_INVALID")
        with self.assertRaises(self.emit.RepoLedgerEpochRefused) as refused:
            self.emitted(first, first)
        assert_six_fields(self, refused.exception.refusal, "COMMITTED_REQUEST_INVALID")

    def test_a_cyclic_chain_is_refused(self):
        first, second, third = self.committed(), self.committed(), self.committed()
        source = self.emitted(first, third)
        self.emitted(third, first)
        self.refused(source, second, first, "COMMITTED_REQUEST_DIGEST_UNVERIFIED")
        # A chain that returns to the aggregating request itself is a cycle too.
        fourth = self.committed()
        back = self.emitted(fourth, second)
        self.emitted(second)
        self.refused(back, second, fourth, "COMMITTED_REQUEST_DIGEST_UNVERIFIED")

    def test_an_over_deep_chain_is_refused(self):
        digests = [self.committed() for _ in range(self.aggregate.SOURCE_REQUEST_CHAIN_LIMIT + 1)]
        aggregating = self.committed()
        previous = None
        for digest in digests:
            receipt = self.emitted(digest, previous)
            previous = digest
        self.refused(receipt, aggregating, digests[-1], "SOURCE_REQUEST_CHAIN_TOO_DEEP")
        # A shorter chain is accepted.
        shallow_digest = self.committed()
        shallow = self.emitted(shallow_digest, digests[1])
        self.assertEqual(self.aggregated(shallow, aggregating, shallow_digest)["boundary_evidence"]
                         ["source_committed_request"]["sha256"], shallow_digest)


if __name__ == "__main__":
    unittest.main()
