"""``intr-destination`` is a universal ingress capability, not a purpose route.

Admissible-Existence advertises it. A peer address is derived as
``organization_slug + "." + "intr-destination"``. A purpose-neutral diagnostic
can be emitted and closed. Peer installation is not proven at resolution.
Closure, when a fabricated far side answers, shows that a boundary ran this
packet. It does not show which organization that boundary belongs to. No
answer stays ``PENDING`` and writes nothing.

Authority and time are constraint variables. A disposition is transition
evidence only. Both ledger roots and the mesh are redirected. Nothing here is
an authentic production receipt or a live peer installation.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROFILE_ID = "intr-destination"
PROFILE_NAME = "InTr:Destination"
OPERATION = "DIAGNOSTIC_CROSSING"
OPERATION_ID = "ORGANIZATION_INTR_DESTINATION_INGRESS"
ADDRESS = "admissible-existence." + PROFILE_ID
PAYLOAD_SCHEMA = "stegverse.org-intr-destination-diagnostic/v1"
THIS = "Admissible-Existence"
PEER = "StegVerse-org"
CONSTRAINT = "CONSTRAINT_VARIABLE"
DISPOSITION_ROLE = "TRANSITION_EVIDENCE_ONLY"
CONSTRAINT_FIELDS = (
    "routing_authority_constraint",
    "admission_authority_constraint",
    "execution_authority_constraint",
    "time_constraint",
)
STANDING = {"mode": "ESTABLISH_GENESIS", "node_ref": "intr-destination-test", "predecessor": None}


def _module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


kernel = _module("kernel", "org-kernel/kernel.py")
capability = _module("capability_ingress", "org-boundary/runtime/capability_ingress.py")
egress = _module("organization_egress_boundary",
                 "resident-runtime/organization_egress_boundary.py")
ingress = _module("intr_destination_ingress", "resident-runtime/intr_destination_ingress.py")
runtime_boundary = _module("runtime_boundary", "org-runtime/runtime_boundary.py")

REGISTRY = json.loads((ROOT / "org-boundary/registry/services.json").read_text(encoding="utf-8"))
BOUNDARY = json.loads((ROOT / "org-runtime/interlock-intr.json").read_text(encoding="utf-8"))
FEDERATION = json.loads((ROOT / "org-boundary/registry/federation.json").read_text(encoding="utf-8"))


def binding(profile_id, document=None):
    matches = [entry for entry in (document or BOUNDARY)["ingress"]["capability_endpoint_bindings"]
               if entry.get("profile_id") == profile_id]
    if len(matches) != 1:
        raise AssertionError(profile_id)
    return matches[0]


def row(service_id):
    return next(item for item in REGISTRY["services"] if item["service_id"] == service_id)


def diagnostic(communication_id="intr-destination-diagnostic-001", schema=PAYLOAD_SCHEMA):
    return {
        "message_class": "ecosystem.communication",
        "communication_id": communication_id,
        "subject": "purpose-neutral mesh diagnostic",
        "body": {"schema": schema, "probe": "diagnostic-crossing"},
    }


def assert_constraints(test, record):
    for name in CONSTRAINT_FIELDS:
        test.assertEqual(record[name], CONSTRAINT, name)
    test.assertEqual(record["disposition_role"], DISPOSITION_ROLE)


EPOCH_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
                "retry_entrypoint", "owning_existing_goal", "next_attempt")


class _NoClock:
    """Stands in for ``datetime`` and ``time`` in the writers. Reading it fails the test."""

    def __init__(self, test):
        self.test = test

    def __getattr__(self, name):
        self.test.fail("a receipt writer or carrier frame read a clock (" + name + ")")


def _clock_holders():
    """Every loaded writer, kernel and boundary module that could read a clock."""
    seen, pending = {}, [kernel, capability, egress, ingress]
    while pending:
        module = pending.pop()
        if id(module) in seen:
            continue
        seen[id(module)] = module
        for name in ("kernel", "repository_ledger", "organization_ledger", "ledger_store"):
            nested = getattr(module, name, None)
            if nested is not None:
                pending.append(nested)
    return list(seen.values())


class no_clock:
    """``datetime`` and ``time`` in every writer, kernel and boundary module raise."""

    def __init__(self, test):
        self.test = test

    def __enter__(self):
        self.saved = []
        for module in _clock_holders():
            for name in ("datetime", "time"):
                if name in vars(module):
                    self.saved.append((module, name, vars(module)[name]))
                    setattr(module, name, _NoClock(self.test))
        self.patches = [mock.patch("time.time", side_effect=self._read),
                        mock.patch("time.time_ns", side_effect=self._read)]
        for patch in self.patches:
            patch.start()

    def _read(self, *args, **kwargs):
        self.test.fail("a receipt writer or carrier frame read the clock (time)")

    def __exit__(self, *exc):
        for patch in self.patches:
            patch.stop()
        for module, name, value in self.saved:
            setattr(module, name, value)


def assert_epoch_refused(test, record, failure_code):
    test.assertEqual(record["disposition"], "FAIL_CLOSED")
    test.assertEqual(record["failure_code"], failure_code)
    test.assertEqual(record["failed_predicate"], "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH")
    test.assertEqual(record["owning_existing_goal"], "INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001")
    for name in EPOCH_FIELDS:
        test.assertTrue(record[name], name)
    test.assertIs(record["derived_from_clock"], False)
    test.assertIs(record["consequence_committed"], False)
    test.assertIs(record["received"], False)
    test.assertIs(record["repository_receipt_observed"], False)
    test.assertIs(record["organization_receipt_observed"], False)


def assert_epoch_not_supplied(test, record):
    assert_epoch_refused(test, record, "HB_EPOCH_NOT_SUPPLIED")


INVALID_EPOCHS = ("33.0", True, 31, "+33", "abc")
REFUSED_EPOCHS = ((None, "HB_EPOCH_NOT_SUPPLIED"),) + tuple(
    (epoch, "HB_EPOCH_INVALID") for epoch in INVALID_EPOCHS)


class DeclarationTests(unittest.TestCase):
    def test_the_overlay_advertises_the_capability_and_sets_no_constraint(self):
        declared = binding(PROFILE_ID)
        self.assertEqual(declared["profile_name"], PROFILE_NAME)
        self.assertEqual(declared["operation"], OPERATION)
        self.assertEqual(declared["payload_schema"], PAYLOAD_SCHEMA)
        self.assertEqual(declared["submission_reader"], capability.COMMUNICATION_READER)
        self.assertEqual(declared["authority_effect"], "NONE_BINDING_ONLY")
        self.assertIs(declared["environment_selected_ingress"], False)
        assert_constraints(self, declared)
        receiving = declared["receiving_operation"]
        self.assertEqual(receiving["operation_id"], OPERATION_ID)
        self.assertEqual(receiving["addressed_service"], ADDRESS)
        self.assertEqual(receiving["addressed_service_boundary_role"], capability.ROLE)
        self.assertIs(receiving["selects_processing_at_the_capability_address"], False)
        self.assertIs(receiving["host_required"], False)
        self.assertIs(receiving["environment_url_required"], False)
        assert_constraints(self, receiving)
        self.assertTrue((ROOT / receiving["operation"]).is_file())

    def test_the_registry_row_is_an_address_and_not_an_admission(self):
        served = row(ADDRESS)
        self.assertEqual(served["boundary_role"], "BOUNDARY_LOCAL_CAPABILITY_INGRESS")
        self.assertEqual(served["capability_profile_id"], PROFILE_ID)
        self.assertEqual(served["admission_authority_constraint"], CONSTRAINT)
        self.assertEqual(served["time_constraint"], CONSTRAINT)
        self.assertEqual(served["disposition_role"], DISPOSITION_ROLE)
        self.assertIs(served["selects_processing_at_this_address"], False)
        self.assertNotIn("endpoint_adapter", served)
        self.assertNotIn("admits_processing", served)
        self.assertIn("ecosystem.communication", served["accepts"])
        self.assertIn(PAYLOAD_SCHEMA, served["accepts"])

    def test_the_served_address_is_named_and_no_peer_address_is(self):
        proven = BOUNDARY["egress"]["peer_capability_resolution"]["proven_on_this_organization"]
        served = {entry["receiving_operation"]["addressed_service"]
                  for entry in BOUNDARY["ingress"]["capability_endpoint_bindings"]}
        self.assertEqual(served, {ADDRESS})
        self.assertEqual(proven, ADDRESS)
        self.assertNotIn("stegverse-org.intr-destination", (proven,))
        report = runtime_boundary.validate()
        self.assertIs(report["valid"], True, report["checks"])
        self.assertIs(report["checks"]["capability_addresses_resolve"], True)
        self.assertIs(report["checks"]["peer_capability_addresses_derive"], True)

    def test_naming_a_proper_subset_of_served_addresses_is_refused(self):
        document = json.loads(json.dumps(BOUNDARY))
        extra = json.loads(json.dumps(binding(PROFILE_ID)))
        extra["profile_id"] = "sdk-manifest-ingress"
        extra["receiving_operation"] = dict(extra["receiving_operation"])
        extra["receiving_operation"]["addressed_service"] = "admissible-existence.sdk-manifest-ingress"
        document["ingress"]["capability_endpoint_bindings"].append(extra)
        document["egress"]["peer_capability_resolution"]["proven_on_this_organization"] = ADDRESS
        self.assertIs(runtime_boundary.peer_capability_addresses_derive(document), False)

    def test_a_peer_address_in_the_proven_field_is_refused(self):
        document = json.loads(json.dumps(BOUNDARY))
        document["egress"]["peer_capability_resolution"]["proven_on_this_organization"] = [
            ADDRESS, "stegverse-org.intr-destination"]
        self.assertIs(runtime_boundary.peer_capability_addresses_derive(document), False)

    def test_a_single_served_address_may_still_be_named_as_a_string(self):
        self.assertIsInstance(
            BOUNDARY["egress"]["peer_capability_resolution"]["proven_on_this_organization"], str)
        self.assertIs(runtime_boundary.peer_capability_addresses_derive(BOUNDARY), True)

    def test_peer_services_are_not_written_into_the_federation_directory(self):
        for entry in FEDERATION["organizations"]:
            for key in ("org_control_service", "addressed_service"):
                self.assertNotIn(PROFILE_ID, str(entry.get(key) or ""))

    def test_no_governance_or_remediation_destination_binding_was_added(self):
        self.assertNotIn("capability_destination_bindings", BOUNDARY["egress"])


class OverlayAuthorityTests(unittest.TestCase):
    def test_resolution_names_the_overlay_and_the_bound_operation(self):
        resolved = capability.resolve(ROOT, row(ADDRESS))
        self.assertEqual(resolved["resolution_source"], "ORGANIZATION_CAPABILITY_OVERLAY")
        self.assertIs(resolved["resolved_from_the_addressed_row_alone"], False)
        self.assertEqual(resolved["receiving_operation_id"], OPERATION_ID)
        self.assertEqual(resolved["capability_operation"], OPERATION)
        self.assertEqual(ingress.OPERATION_ID, OPERATION_ID)

    def test_a_row_the_overlay_does_not_name_resolves_nothing(self):
        with self.assertRaises(SystemExit) as refused:
            capability.resolve(ROOT, {"service_id": "admissible-existence.not-bound-anywhere"})
        self.assertIn("ADDRESS_SERVES_A_CAPABILITY_THE_OVERLAY_BINDS_HERE",
                      str(refused.exception))

    def test_a_module_that_is_not_the_bound_operation_is_refused(self):
        resolved = dict(capability.resolve(ROOT, row(ADDRESS)))
        resolved["receiving_operation_path"] = ROOT / "resident-runtime/organization_egress_boundary.py"
        with self.assertRaises(SystemExit) as refused:
            capability.load_operation(resolved)
        self.assertIn("MODULE_IDENTIFIES_ITSELF_AS_THE_BOUND_OPERATION",
                      str(refused.exception))

    def test_an_operation_outside_this_organization_is_refused(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        (root / "org-runtime").mkdir(parents=True)
        document = json.loads(json.dumps(BOUNDARY))
        receiving = binding(PROFILE_ID, document)["receiving_operation"]
        receiving["operation"] = "../outside.py"
        (root / "org-runtime/interlock-intr.json").write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(SystemExit) as refused:
            capability.resolve(root, row(ADDRESS))
        self.assertIn("RECEIVING_OPERATION_IS_OWNED_INSIDE_THIS_ORGANIZATION",
                      str(refused.exception))

    def test_the_readers_do_not_cross(self):
        manifest_binding = {"operation": "SUBMIT_MANIFEST"}
        with self.assertRaises(SystemExit) as manifest_refused:
            capability.submission_for(manifest_binding, diagnostic())
        self.assertIn("SUBMISSION_CARRIES_A_MANIFEST", str(manifest_refused.exception))
        with self.assertRaises(SystemExit) as diagnostic_refused:
            capability.submission_for(binding(PROFILE_ID), {"manifest": {"probe": True}})
        self.assertIn("SUBMISSION_DECLARES_A_RESPONDED_REQUEST_CLASS",
                      str(diagnostic_refused.exception))

    def test_a_diagnostic_body_under_another_schema_is_refused(self):
        with self.assertRaises(SystemExit) as refused:
            capability.submission_for(
                binding(PROFILE_ID), diagnostic(schema="stegverse.org-governance-decision/v1"))
        self.assertIn("SUBMISSION_BODY_DECLARES_THE_BOUND_PAYLOAD_SCHEMA", str(refused.exception))


class RedirectedLedgers(unittest.TestCase):
    LEDGER_ROOTS = ("STEGVERSE_REPO_LEDGER_ROOT", "STEGVERSE_ORG_LEDGER_ROOT")

    def setUp(self):
        self._work = tempfile.TemporaryDirectory()
        self.addCleanup(self._work.cleanup)
        previous = {name: os.environ.get(name) for name in self.LEDGER_ROOTS}
        for name in self.LEDGER_ROOTS:
            os.environ[name] = str(Path(self._work.name) / name.lower())
        self.mesh = Path(self._work.name) / "mesh"

        def restore():
            for name, value in previous.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value
        self.addCleanup(restore)

    def receipts(self, variable, schema, transition_class=None):
        found = []
        root = Path(os.environ[variable])
        if not root.exists():
            return found
        for path in root.rglob("*.json"):
            record = json.loads(path.read_text(encoding="utf-8"))
            if record.get("schema") != schema:
                continue
            if transition_class is not None and record.get("transition_class") != transition_class:
                continue
            found.append(record)
        return found


class OperationReceiptTests(RedirectedLedgers):
    def test_a_diagnostic_is_acknowledged_at_both_ledger_levels(self):
        result = ingress.receive(diagnostic(), registry=REGISTRY, packet_id="direct-diagnostic",
                                 hb_epoch=32)
        self.assertEqual(result["disposition"], "ALLOW", result.get("detail"))
        self.assertIs(result["received"], True)
        self.assertIs(result["communication_acknowledged"], True)
        self.assertIs(result["repository_receipt_observed"], True)
        self.assertIs(result["organization_receipt_observed"], True)
        self.assertIs(result["organization_receipt_preserves_repository_receipt"], True)
        self.assertEqual(result["authority_effect"], "NONE_DIAGNOSTIC_ACK_ONLY")
        assert_constraints(self, result)
        for flag in ("selects_processing", "purpose_specific_route", "standing_rechecked_here"):
            self.assertIs(result[flag], False, flag)
        repository, = self.receipts("STEGVERSE_REPO_LEDGER_ROOT",
                                    "stegverse.repo-transition-receipt/v1", OPERATION_ID)
        self.assertEqual(repository["evidence"]["profile_id"], PROFILE_ID)
        self.assertEqual(repository["evidence"]["receiving_operation"], OPERATION_ID)
        assert_constraints(self, repository["evidence"])
        organization, = self.receipts("STEGVERSE_ORG_LEDGER_ROOT",
                                      "stegverse.organization-transition-receipt/v1")
        self.assertEqual(organization["repo_receipt_sha256"], repository["receipt_sha256"])

    def test_a_replay_of_the_same_diagnostic_does_not_mint_a_second_pair(self):
        first = ingress.receive(diagnostic(), registry=REGISTRY, packet_id="replayed-diagnostic",
                                hb_epoch=32)
        second = ingress.receive(diagnostic(), registry=REGISTRY, packet_id="replayed-diagnostic",
                                 hb_epoch=32)
        self.assertIs(second["transition_replayed"], True)
        self.assertEqual(first["repository_receipt_sha256"], second["repository_receipt_sha256"])
        self.assertEqual(len(self.receipts("STEGVERSE_REPO_LEDGER_ROOT",
                                           "stegverse.repo-transition-receipt/v1", OPERATION_ID)), 1)

    def test_a_payload_that_is_not_the_diagnostic_is_refused_and_recorded(self):
        result = ingress.receive(
            {"message_class": "ecosystem.work.request", "communication_id": "not-a-diagnostic",
             "body": {"schema": "stegverse.org-governance-decision-request/v1"}},
            registry=REGISTRY, packet_id="refused-diagnostic", hb_epoch=32)
        self.assertEqual(result["disposition"], "DENY")
        self.assertIs(result["communication_acknowledged"], False)
        self.assertIs(result["refusal_recorded"], True)
        self.assertEqual(result["failed_predicate"], "SUBMISSION_DECLARES_A_RESPONDED_REQUEST_CLASS")
        self.assertEqual(result["authority_effect"], "NONE_REFUSAL_ONLY")
        assert_constraints(self, result)
        self.assertEqual(len(self.receipts(
            "STEGVERSE_REPO_LEDGER_ROOT", "stegverse.repo-transition-receipt/v1",
            ingress.REFUSED_CLASS)), 1)
        self.assertEqual(self.receipts(
            "STEGVERSE_REPO_LEDGER_ROOT", "stegverse.repo-transition-receipt/v1", OPERATION_ID), [])


class SuppliedEpochTests(RedirectedLedgers):
    """A receipt carries a supplied epoch. Without one the writer fails closed
    before a store opens, and no clock is read."""

    def roots_untouched(self):
        for name in self.LEDGER_ROOTS:
            self.assertFalse(Path(os.environ[name]).exists(), name)

    def test_the_repository_writer_fails_closed_before_the_store_opens(self):
        writer = ingress.repository_ledger
        with no_clock(self), self.assertRaises(writer.RepoLedgerEpochRefused) as refused:
            writer.append("probe:no-epoch", "PROBE", "sha256:" + "0" * 64,
                          "sha256:" + "1" * 64, {}, "NONE")
        self.assertEqual(refused.exception.refusal, writer.epoch_refusal(None))
        self.assertEqual(refused.exception.refusal["failure_code"], "HB_EPOCH_NOT_SUPPLIED")
        self.assertEqual(refused.exception.refusal["failed_predicate"],
                         "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH")
        self.roots_untouched()

    def test_the_repository_writer_refuses_an_invalid_epoch_before_the_store_opens(self):
        writer = ingress.repository_ledger
        for epoch in INVALID_EPOCHS:
            with self.subTest(epoch=epoch):
                with no_clock(self), self.assertRaises(writer.RepoLedgerEpochRefused) as refused:
                    writer.append("probe:invalid-epoch", "PROBE", "sha256:" + "0" * 64,
                                  "sha256:" + "1" * 64, {}, "NONE", hb_epoch=epoch)
                refusal = refused.exception.refusal
                self.assertEqual(refusal, writer.epoch_refusal(epoch))
                self.assertEqual(refusal["failure_code"], "HB_EPOCH_INVALID")
                for name in EPOCH_FIELDS:
                    self.assertTrue(refusal[name], name)
                self.roots_untouched()

    def test_the_heartbeat_reference_is_not_derived_from_a_clock(self):
        writer = ingress.repository_ledger
        with no_clock(self):
            with self.assertRaises(writer.RepoLedgerEpochRefused):
                writer.hb_reference(None)
            self.assertEqual(writer.hb_reference(32)["epoch"], 32)
            self.assertIs(writer.hb_reference("33")["derived_from_clock"], False)

    def test_a_diagnostic_without_an_epoch_records_nothing(self):
        with no_clock(self):
            result = ingress.receive(diagnostic(), registry=REGISTRY, packet_id="no-epoch")
        assert_epoch_not_supplied(self, result)
        self.assertEqual({name: result[name] for name in ingress.repository_ledger.epoch_refusal(None)},
                         ingress.repository_ledger.epoch_refusal(None))
        assert_constraints(self, result)
        self.roots_untouched()

    def test_a_diagnostic_with_an_invalid_epoch_records_nothing(self):
        for epoch in INVALID_EPOCHS:
            with self.subTest(epoch=epoch):
                with no_clock(self):
                    result = ingress.receive(diagnostic(), registry=REGISTRY,
                                             packet_id="invalid-epoch", hb_epoch=epoch)
                assert_epoch_refused(self, result, "HB_EPOCH_INVALID")
                self.assertIs(result["received"], False)
                self.assertIs(result["repository_receipt_observed"], False)
                self.assertIs(result["organization_receipt_observed"], False)
                assert_constraints(self, result)
                self.roots_untouched()

    def test_an_emission_without_an_epoch_publishes_and_records_nothing(self):
        with no_clock(self), self.assertRaises(egress.repository_ledger.RepoLedgerEpochRefused) as refused:
            egress.emit(PEER, diagnostic("no-epoch-emission"), standing=STANDING,
                        capability=PROFILE_ID, mesh_root=self.mesh)
        self.assertEqual(refused.exception.refusal["failure_code"], "HB_EPOCH_NOT_SUPPLIED")
        self.assertFalse(self.mesh.exists())
        self.roots_untouched()

    def test_an_emission_with_an_invalid_epoch_publishes_and_records_nothing(self):
        for epoch in INVALID_EPOCHS:
            with self.subTest(epoch=epoch):
                with no_clock(self), \
                        self.assertRaises(egress.repository_ledger.RepoLedgerEpochRefused) as refused:
                    egress.emit(PEER, diagnostic("invalid-epoch-emission"), standing=STANDING,
                                capability=PROFILE_ID, mesh_root=self.mesh, hb_epoch=epoch)
                self.assertEqual(refused.exception.refusal["failure_code"], "HB_EPOCH_INVALID")
                self.assertFalse(self.mesh.exists())
                self.roots_untouched()


class OrganizationLedgerAndFrameEpochTests(RedirectedLedgers):
    """The organization writer and the egress frame take the supplied epoch.

    An absent or invalid one is refused six-field FAIL_CLOSED before a
    directory is created, a frame is built or anything is published. The valid
    path reads no clock.
    """

    def roots_untouched(self):
        for name in self.LEDGER_ROOTS:
            self.assertFalse(Path(os.environ[name]).exists(), name)

    def repository_receipt(self, epoch=33):
        with no_clock(self):
            return ingress.repository_ledger.append(
                "probe:org-epoch", "PROBE", "sha256:" + "0" * 64, "sha256:" + "1" * 64,
                {}, "NONE", hb_epoch=epoch)

    def test_the_organization_writer_refuses_before_any_directory_exists(self):
        writer = ingress.organization_ledger
        receipt = self.repository_receipt()
        org_root = Path(os.environ["STEGVERSE_ORG_LEDGER_ROOT"])
        for epoch, code in REFUSED_EPOCHS:
            with self.subTest(epoch=epoch):
                kwargs = {} if epoch is None else {"hb_epoch": epoch}
                with no_clock(self), self.assertRaises(writer.OrgLedgerEpochRefused) as refused:
                    writer.append(receipt, "REPO_STATE_PROPAGATION", "sha256:" + "0" * 64,
                                  "sha256:" + "1" * 64, {}, "NONE", **kwargs)
                refusal = refused.exception.refusal
                self.assertEqual(refusal, writer.epoch_refusal(epoch))
                self.assertEqual(refusal["disposition"], "FAIL_CLOSED")
                self.assertEqual(refusal["failure_code"], code)
                self.assertEqual(refusal["failed_predicate"], "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH")
                for name in EPOCH_FIELDS:
                    self.assertTrue(refusal[name], name)
                self.assertFalse(org_root.exists())

    def test_the_organization_writer_reads_no_clock_on_the_valid_path(self):
        writer = ingress.organization_ledger
        receipt = self.repository_receipt()
        self.assertEqual(receipt["observed_at"], "HB:33")
        with no_clock(self):
            record = writer.append(receipt, "REPO_STATE_PROPAGATION", "sha256:" + "0" * 64,
                                   "sha256:" + "1" * 64, {}, "NONE", hb_epoch="33")
        self.assertEqual(record["hb_reference"]["epoch"], 33)
        self.assertIs(record["hb_reference"]["derived_from_clock"], False)
        self.assertEqual(record["observed_at"], "HB:33")

    def test_an_emission_with_a_refused_epoch_builds_and_publishes_nothing(self):
        def refuse(*args, **kwargs):
            self.fail("a packet was built or published for a refused epoch")
        for epoch, code in REFUSED_EPOCHS:
            with self.subTest(epoch=epoch):
                kwargs = {} if epoch is None else {"hb_epoch": epoch}
                with no_clock(self), mock.patch.object(egress.kernel, "build_packet", refuse), \
                        mock.patch.object(egress.kernel, "publish_packet", refuse), \
                        self.assertRaises(egress.repository_ledger.RepoLedgerEpochRefused) as refused:
                    egress.emit(PEER, diagnostic("refused-epoch-emission"), standing=STANDING,
                                capability=PROFILE_ID, mesh_root=self.mesh, **kwargs)
                self.assertEqual(refused.exception.refusal["failure_code"], code)
                self.assertEqual(refused.exception.refusal["disposition"], "FAIL_CLOSED")
                self.assertFalse(self.mesh.exists())
                self.roots_untouched()

    def test_an_emission_frame_carries_the_supplied_epoch_and_reads_no_clock(self):
        with no_clock(self):
            emitted = egress.emit(PEER, diagnostic("supplied-epoch-emission"), standing=STANDING,
                                  capability=PROFILE_ID, mesh_root=self.mesh, hb_epoch="35")
        self.assertIs(emitted["emitted"], True)
        frame = emitted["emission_record"]
        frames = [json.loads(path.read_text(encoding="utf-8")) for path in self.mesh.rglob("*.json")]
        published = [item for item in frames if item.get("frame_sha256") == emitted["frame_sha256"]]
        self.assertEqual(len(published), 1, frame)
        self.assertEqual(published[0]["heartbeat_reference"]["epoch"], 35)
        self.assertIs(published[0]["heartbeat_reference"]["derived_from_clock"], False)
        for receipt in (self.receipts("STEGVERSE_REPO_LEDGER_ROOT", "stegverse.repo-transition-receipt/v1")
                        + self.receipts("STEGVERSE_ORG_LEDGER_ROOT",
                                        "stegverse.organization-transition-receipt/v1")):
            self.assertEqual(receipt["hb_reference"]["epoch"], 35)
            self.assertEqual(receipt["observed_at"], "HB:35")


class AddressedAndClosedTests(RedirectedLedgers):
    def publish(self, payload, service, packet_id, origin=PEER):
        packet = kernel.build_packet(
            origin_org=origin,
            origin_service=kernel.organization_slug(origin) + "." + PROFILE_ID,
            destination_org=THIS, destination_service=service,
            payload=payload, standing=STANDING,
            transition_reference="intr:transition:" + packet_id,
            authority_effect="NONE", packet_id=packet_id)
        # The mesh is temporary. publish_packet writes the frame and does not
        # append a ledger receipt; the receiving operation records its own.
        kernel.publish_packet(packet, root=self.mesh, now_ns=kernel.HB_ANCHOR_UNIX_NS)
        return packet

    def consume(self):
        return kernel.consume_addressed_frames(ROOT, mesh_root=self.mesh)

    def frames_to(self, organization):
        directory = self.mesh / "frames.d"
        if not directory.is_dir():
            return []
        frames = []
        for path in directory.glob("*.json"):
            frame = json.loads(path.read_text(encoding="utf-8"))
            if frame.get("destination_org") == organization:
                frames.append(frame)
        return frames

    def test_a_peer_frame_at_the_address_fails_closed_without_a_supplied_epoch(self):
        # Capability ingress hands the frame on with no epoch. The receipt
        # writer does not read a clock to fill one in, so nothing is recorded.
        self.publish(diagnostic("addressed-diagnostic"), ADDRESS, "addressed-diagnostic")
        with no_clock(self):
            results = self.consume()
        self.assertEqual(len(results), 1)
        execution = results[0]["result"]["execution_result"]
        self.assertEqual(results[0]["result"]["status"], "CONSUMED")
        self.assertEqual(results[0]["result"]["packet"]["origin"]["org"], PEER)
        self.assertEqual(execution["service_id"], ADDRESS)
        application = execution["application_result"]
        self.assertIs(application["capability_received"], True)
        self.assertEqual(application["receiving_operation_id"], OPERATION_ID)
        operation = application["receiving_operation_result"]
        assert_epoch_not_supplied(self, operation)
        self.assertIs(operation["communication_acknowledged"], False)
        self.assertEqual(self.receipts("STEGVERSE_REPO_LEDGER_ROOT",
                                       "stegverse.repo-transition-receipt/v1"), [])
        self.assertEqual(self.receipts("STEGVERSE_ORG_LEDGER_ROOT",
                                       "stegverse.organization-transition-receipt/v1"), [])

    def test_a_manifest_addressed_to_this_capability_is_not_a_diagnostic(self):
        self.publish({"manifest": {"probe": True}}, ADDRESS, "not-a-diagnostic")
        with self.assertRaises(ValueError) as refused:
            self.consume()
        self.assertIn("SUBMISSION_DECLARES_A_RESPONDED_REQUEST_CLASS", str(refused.exception))
        self.assertEqual(self.receipts(
            "STEGVERSE_REPO_LEDGER_ROOT", "stegverse.repo-transition-receipt/v1", OPERATION_ID), [])

    def test_outbound_resolution_derives_the_peer_address_and_does_not_prove_it_serves(self):
        resolved = egress.resolve_destination(PEER, capability=PROFILE_ID)
        self.assertEqual(resolved["destination_service"],
                         kernel.organization_slug(PEER) + "." + PROFILE_ID)
        self.assertEqual(resolved["destination_service"], "stegverse-org.intr-destination")
        self.assertNotEqual(resolved["destination_service"],
                            resolved["destination_org_control_service"])
        self.assertIs(resolved["peer_serves_this_capability_is_proven_here"], False)
        self.assertIs(resolved["destination_capability_declared_by_the_peer_directory"], False)
        self.assertEqual(egress.peer_capability_service(THIS, PROFILE_ID), ADDRESS)

    def test_an_undeclared_capability_is_still_refused(self):
        with self.assertRaises(egress.EgressRefused) as refused:
            egress.resolve_destination(PEER, capability="not-a-declared-capability")
        self.assertEqual(refused.exception.failed_predicate,
                         "CAPABILITY_IS_DECLARED_IN_THIS_ORGANIZATIONS_OVERLAY")

    def test_an_undeclared_peer_is_still_refused(self):
        with self.assertRaises(egress.EgressRefused) as refused:
            egress.resolve_destination("Not-A-Declared-Peer", capability=PROFILE_ID)
        self.assertEqual(refused.exception.failed_predicate,
                         "DESTINATION_IS_A_DECLARED_PEER_OF_THIS_ORGANIZATION")

    def answer(self, packet):
        """Answer as a boundary does: the kernel's own receipt chain and control response.

        The chain is fabricated in this temporary mesh. It is not an authentic
        receipt and not a live peer installation.
        """
        chain, previous = [], None
        for kind in egress.FAR_SIDE_RECEIPT_KINDS:
            receipt = kernel.receipt(kind, packet["packet_id"], packet["destination"]["service"],
                                     previous, {"payload_hash": kernel.sha(packet["payload"])})
            chain.append(receipt["receipt_id"])
            previous = receipt["receipt_id"]
        response = kernel.build_control_response(
            packet, {"application_result": {
                "schema": ingress.RESULT_SCHEMA, "disposition": "ALLOW",
                "authority_effect": "NONE_DIAGNOSTIC_ACK_ONLY"},
                "reconstruction": {"terminal_receipt_id": chain[-1]}})
        kernel.publish_packet(response, root=self.mesh, now_ns=kernel.HB_ANCHOR_UNIX_NS)
        return chain[-1]

    def test_a_diagnostic_crossing_closes_only_when_the_far_side_answers(self):
        emitted = egress.emit(PEER, diagnostic("closable-diagnostic"), standing=STANDING,
                              capability=PROFILE_ID, mesh_root=self.mesh, hb_epoch=32)
        self.assertEqual(emitted["disposition"], "ALLOW", emitted.get("detail"))
        self.assertIs(emitted["emitted"], True)
        self.assertEqual(emitted["destination_service"], "stegverse-org.intr-destination")
        self.assertIs(emitted["peer_serves_this_capability_is_proven_here"], False)
        self.assertEqual(emitted["emission_record"]["far_side_service_id"],
                         emitted["destination_service"])
        pending = egress.close(PEER, emitted["packet_id"], "closable-diagnostic",
                               mesh_root=self.mesh, hb_epoch=33)
        self.assertEqual(pending["disposition"], "PENDING")
        self.assertIs(pending["closed"], False)
        self.assertIs(pending["closure_recorded"], False)
        self.assertIs(pending["absence_is_not_a_transition"], True)
        self.assertEqual(self.receipts("STEGVERSE_REPO_LEDGER_ROOT",
                                       "stegverse.repo-transition-receipt/v1",
                                       egress.CLOSED_CLASS), [])

        frame, = self.frames_to(PEER)
        packet = kernel.recover_packet(frame)
        self.assertEqual(packet["destination"]["service"], "stegverse-org.intr-destination")
        self.assertEqual(packet["payload"]["message_class"], "ecosystem.communication")
        self.assertEqual(packet["payload"]["communication_id"], "closable-diagnostic")
        terminal = self.answer(packet)
        closed = egress.close(PEER, emitted["packet_id"], "closable-diagnostic",
                              mesh_root=self.mesh, hb_epoch=34)
        self.assertEqual(closed["disposition"], "ALLOW", closed.get("closure_findings"))
        self.assertIs(closed["closed"], True)
        self.assertEqual(closed["far_side_terminal_receipt"], terminal)
        self.assertEqual(closed["communication_id"], "closable-diagnostic")
        self.assertEqual(closed["closure_record"]["response_message_class"],
                         "ecosystem.communication.ack")
        # Closure shows a boundary ran this packet. It does not show which
        # organization that boundary belongs to, and resolution did not claim
        # the peer serves the capability.
        self.assertIs(closed["closure_record"]["reconstruction_proves_the_boundary_ran_this_packet"], True)
        self.assertIs(closed["closure_record"]["reconstruction_proves_who_the_far_side_is"], False)
        self.assertIs(emitted["peer_serves_this_capability_is_proven_here"], False)
        self.assertEqual(len(self.receipts("STEGVERSE_REPO_LEDGER_ROOT",
                                           "stegverse.repo-transition-receipt/v1",
                                           egress.CLOSED_CLASS)), 1)
        self.assertTrue(self.receipts("STEGVERSE_ORG_LEDGER_ROOT",
                                      "stegverse.organization-transition-receipt/v1"))


FIXED_CLOCK = datetime(2026, 10, 19, 12, 0, 0, tzinfo=timezone.utc)


class _FixedDatetime(datetime):
    """``datetime`` whose ``now`` returns one fixed instant."""

    @classmethod
    def now(cls, tz=None):
        return FIXED_CLOCK


class fixed_clock:
    """Every writer, kernel and boundary module reads the same fixed instant."""

    def __enter__(self):
        self.saved = []
        for module in _clock_holders():
            if "datetime" in vars(module):
                self.saved.append((module, vars(module)["datetime"]))
                module.datetime = _FixedDatetime
        return self

    def __exit__(self, *exc):
        for module, value in self.saved:
            module.datetime = value


def clock_reference(writer):
    """The kernel's clock path, as a pre-B-P31 writer or a None default would stamp it."""
    return lambda epoch: writer.kernel.hb_reference()


class EpochProvenanceTests(RedirectedLedgers):
    """B-P36f. A receipt's epoch is never forwarded to the next writer as supplied.

    The organization writer takes the epoch supplied to the ingress or egress
    call, not the one read back from the repository receipt it just wrote or
    replayed. With the epoch absent and the clock fixed, nothing is written.
    """

    def all_receipts(self):
        return (self.receipts("STEGVERSE_REPO_LEDGER_ROOT", "stegverse.repo-transition-receipt/v1")
                + self.receipts("STEGVERSE_ORG_LEDGER_ROOT",
                                "stegverse.organization-transition-receipt/v1"))

    def assert_no_laundered_epoch(self, supplied):
        for receipt in self.all_receipts():
            reference = receipt["hb_reference"]
            if reference.get("derived_from_clock") is False:
                self.assertIn(reference["epoch"], supplied, receipt["receipt_sha256"])

    def test_every_ingress_writes_nothing_without_an_epoch_under_a_fixed_clock(self):
        attempts = {
            "receive": lambda: ingress.receive(diagnostic("absent-receive"), registry=REGISTRY,
                                               packet_id="absent-receive"),
            "self_close": lambda: ingress.self_close("absent-self-close", registry=REGISTRY),
            "emit": lambda: egress.emit(PEER, diagnostic("absent-emit"), standing=STANDING,
                                        capability=PROFILE_ID, mesh_root=self.mesh),
            "close": lambda: egress._record("probe:absent-close", egress.CLOSED_CLASS,
                                            "sha256:" + "0" * 64, "sha256:" + "1" * 64,
                                            {"intended_action": "CLOSE", "disposition": "ALLOW",
                                             "crossed_an_organization_boundary": True}, None),
        }
        for name, attempt in attempts.items():
            with self.subTest(path=name), fixed_clock():
                try:
                    result = attempt()
                except kernel.SuppliedEpochRefused:
                    pass
                except ValueError as exc:
                    self.assertEqual(getattr(exc, "failed_predicate", None),
                                     "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH", str(exc))
                else:
                    self.assertEqual(result["disposition"], "FAIL_CLOSED", name)
                self.assertEqual(self.all_receipts(), [], name)
        # A peer frame through capability ingress carries no supplied epoch.
        packet = kernel.build_packet(
            origin_org=PEER, origin_service=kernel.organization_slug(PEER) + "." + PROFILE_ID,
            destination_org=THIS, destination_service=ADDRESS, payload=diagnostic("absent-frame"),
            standing=STANDING, transition_reference="intr:transition:absent-frame",
            authority_effect="NONE", packet_id="absent-frame")
        kernel.publish_packet(packet, root=self.mesh, now_ns=kernel.HB_ANCHOR_UNIX_NS)
        with fixed_clock():
            results = kernel.consume_addressed_frames(ROOT, mesh_root=self.mesh)
        operation = results[0]["result"]["execution_result"]["application_result"][
            "receiving_operation_result"]
        self.assertEqual(operation["failure_code"], "HB_EPOCH_NOT_SUPPLIED")
        self.assertEqual(self.all_receipts(), [])

    def org_ledger_files(self):
        root = Path(os.environ["STEGVERSE_ORG_LEDGER_ROOT"])
        return sorted(path for path in root.rglob("*") if path.is_file()) if root.exists() else []

    def test_a_replayed_clock_receipt_is_refused_as_a_source_and_writes_nothing(self):
        writer = ingress.repository_ledger
        with fixed_clock() as clock:
            clock_epoch = writer.kernel.hb_reference()["epoch"]
            with mock.patch.object(writer, "hb_reference", clock_reference(writer)), \
                    mock.patch.object(ingress.organization_ledger, "append",
                                      side_effect=RuntimeError("stopped after the repository write")):
                with self.assertRaises(RuntimeError):
                    ingress.receive(diagnostic("replayed-clock"), registry=REGISTRY,
                                    packet_id="replayed-clock", hb_epoch="4096")
        repository, = self.receipts("STEGVERSE_REPO_LEDGER_ROOT",
                                    "stegverse.repo-transition-receipt/v1")
        self.assertEqual(repository["hb_reference"]["epoch"], clock_epoch)
        self.assertNotEqual(clock_epoch, 4096)
        before = self.org_ledger_files()
        with no_clock(self):
            result = ingress.receive(diagnostic("replayed-clock"), registry=REGISTRY,
                                     packet_id="replayed-clock", hb_epoch="4096")
        # F2: the replayed repository receipt's epoch was read from a clock, so
        # it cannot be the source of an organization receipt.
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertEqual(result["failure_code"], "SOURCE_RECEIPT_IS_CLOCK_PROVENANCE")
        self.assertIn("CARRIED:LEGACY_CLOCK_RECEIPT", result["required_evidence_or_repair"])
        for name in EPOCH_FIELDS:
            self.assertTrue(result[name], name)
        self.assertEqual(self.org_ledger_files(), before)
        self.assertEqual(self.receipts("STEGVERSE_ORG_LEDGER_ROOT",
                                       "stegverse.organization-transition-receipt/v1"), [])
        self.assert_no_laundered_epoch({4096})

    def test_a_replayed_clock_emission_is_refused_as_a_source_and_writes_nothing(self):
        writer = egress.repository_ledger
        record = {"intended_action": "EMIT", "disposition": "ALLOW",
                  "crossed_an_organization_boundary": True,
                  "frame_sha256": "sha256:" + "2" * 64, "payload_sha256": "sha256:" + "3" * 64}
        args = ("probe:replayed-emission", egress.EMITTED_CLASS, "sha256:" + "0" * 64,
                "sha256:" + "1" * 64, record)
        with fixed_clock():
            clock_epoch = writer.kernel.hb_reference()["epoch"]
            with mock.patch.object(writer, "hb_reference", clock_reference(writer)), \
                    mock.patch.object(egress.organization_ledger, "append",
                                      side_effect=RuntimeError("stopped after the repository write")):
                with self.assertRaises(RuntimeError):
                    egress._record(*args, "4096")
        repository, = self.receipts("STEGVERSE_REPO_LEDGER_ROOT",
                                    "stegverse.repo-transition-receipt/v1")
        self.assertEqual(repository["hb_reference"]["epoch"], clock_epoch)
        before = self.org_ledger_files()
        with no_clock(self), self.assertRaises(egress.organization_ledger.OrgLedgerEpochRefused) as refused:
            egress._record(*args, "4096")
        self.assertEqual(refused.exception.refusal["failure_code"], "SOURCE_RECEIPT_IS_CLOCK_PROVENANCE")
        for name in EPOCH_FIELDS:
            self.assertTrue(refused.exception.refusal[name], name)
        self.assertEqual(self.org_ledger_files(), before)
        self.assert_no_laundered_epoch({4096})

    def test_the_supplied_4096_reaches_both_receipts_on_every_path(self):
        with no_clock(self):
            received = ingress.receive(diagnostic("supplied-receive"), registry=REGISTRY,
                                       packet_id="supplied-receive", hb_epoch="4096")
            closed = ingress.self_close("supplied-self-close", registry=REGISTRY, hb_epoch="4096")
            emitted = egress.emit(PEER, diagnostic("supplied-emit"), standing=STANDING,
                                  capability=PROFILE_ID, mesh_root=self.mesh, hb_epoch="4096")
        self.assertEqual(received["disposition"], "ALLOW", received.get("detail"))
        self.assertIs(closed["closed"], True)
        self.assertIs(emitted["emitted"], True)
        repository = self.receipts("STEGVERSE_REPO_LEDGER_ROOT", "stegverse.repo-transition-receipt/v1")
        organization = self.receipts("STEGVERSE_ORG_LEDGER_ROOT",
                                     "stegverse.organization-transition-receipt/v1")
        self.assertEqual(len(repository), 3)
        self.assertEqual(len(organization), 3)
        for receipt in repository + organization:
            self.assertEqual(receipt["hb_reference"]["epoch"], 4096)
            self.assertIs(receipt["hb_reference"]["derived_from_clock"], False)
            self.assertEqual(receipt["observed_at"], "HB:4096")


if __name__ == "__main__":
    unittest.main()
