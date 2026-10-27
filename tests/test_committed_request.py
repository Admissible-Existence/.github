"""The committed-request gate (B-P40 COMMITTED_REQUEST) before a writer runs.

A writer workflow's only input is a committed request file. The gate refuses
an unreadable request (COMMITTED_REQUEST_INVALID), an absent epoch
(HB_EPOCH_NOT_SUPPLIED) and an invalid one (HB_EPOCH_INVALID) with six fields
before anything is written, and binds the request's sha256 for a passing one.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")


def _gate():
    spec = importlib.util.spec_from_file_location("committed_request_gate", ROOT / "scripts" / "read_committed_request.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


#: sha256 of resident-runtime/intr_destination_ingress.py on main @92e1c2d. The
#: InTr path is Grok Lane B's (lead ruling 20:06Z): this lane records the
#: committed request through the ledger writers it owns and never edits it.
INTR_INGRESS_MAIN_SHA256 = "40401fda643f336bbb35a8050ef46bcedc97d93d6e603d67c502b3b61c045eba"


class InTrIngressUnchangedTests(unittest.TestCase):
    def test_the_intr_ingress_module_is_byte_identical_to_main(self):
        data = (ROOT / "resident-runtime" / "intr_destination_ingress.py").read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), INTR_INGRESS_MAIN_SHA256)


class CommittedRequestGateTests(unittest.TestCase):
    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.work = Path(work.name)
        self.gate = _gate()

    def request(self, text):
        path = self.work / "request.json"
        path.write_bytes(text.encode("utf-8") if isinstance(text, str) else text)
        return path

    def refused(self, text, code):
        values, refusal = self.gate.read(self.request(text), ("communication_id",))
        self.assertIsNone(values)
        self.assertEqual(refusal["failure_code"], code, refusal)
        self.assertEqual(refusal["disposition"], "FAIL_CLOSED")
        for field in SIX:
            self.assertTrue(refusal[field], field)
        self.assertIs(refusal["derived_from_clock"], False)
        return refusal

    def test_a_supplied_request_passes_with_its_digest(self):
        text = json.dumps({"communication_id": "b-p40-probe", "hb_epoch": "4096"})
        values, refusal = self.gate.read(self.request(text), ("communication_id",))
        self.assertIsNone(refusal)
        self.assertEqual(values, {"communication_id": "b-p40-probe", "hb_epoch": "4096",
                                  "request_sha256": hashlib.sha256(text.encode()).hexdigest()})

    def test_an_absent_epoch_is_not_supplied(self):
        self.refused(json.dumps({"communication_id": "b-p40-probe"}), "HB_EPOCH_NOT_SUPPLIED")
        # null is the shared rule's absent epoch, not an invalid one.
        self.refused(json.dumps({"communication_id": "b-p40-probe", "hb_epoch": None}), "HB_EPOCH_NOT_SUPPLIED")

    def test_an_invalid_epoch_is_invalid(self):
        for epoch in ("31", "abc", "+33", " 33", "", True, 33.0):
            with self.subTest(epoch=epoch):
                self.refused(json.dumps({"communication_id": "b-p40-probe", "hb_epoch": epoch}),
                             "HB_EPOCH_INVALID")

    def test_an_unusable_request_is_terminal(self):
        cases = {
            "not JSON": "{not json",
            "a list": "[1]",
            "NaN": '{"communication_id": "b", "hb_epoch": NaN}',
            "1e999": '{"communication_id": "b", "hb_epoch": "4096", "x": 1e999}',
            "deep": '{"a":' + "[" * 200000,
            "not UTF-8": b"\xff\xfe{",
            "no communication_id": json.dumps({"hb_epoch": "4096"}),
            "an output injection": json.dumps({"communication_id": "x\ninjected=1", "hb_epoch": "4096"}),
        }
        for label, text in cases.items():
            with self.subTest(request=label):
                self.assertIs(self.refused(text, "COMMITTED_REQUEST_INVALID")["terminal"], True)
        values, refusal = self.gate.read(self.work / "absent.json", ("communication_id",))
        self.assertEqual(refusal["failure_code"], "COMMITTED_REQUEST_INVALID")

    def test_choices_and_optional_text_fields(self):
        choices = {"entrypoint": ("federation_cycle", "run_once")}
        text = json.dumps({"entrypoint": "run_once", "hb_epoch": "4096", "ingress": "data/in put.json"})
        values, refusal = self.gate.read(self.request(text), (), choices=choices, optional_text=("ingress", "extra"))
        self.assertIsNone(refusal)
        self.assertEqual((values["entrypoint"], values["ingress"], values["extra"]),
                         ("run_once", "data/in put.json", ""))
        for label, body in {
            "not a choice": {"entrypoint": "status", "hb_epoch": "4096"},
            "no choice": {"hb_epoch": "4096"},
            "a newline in text": {"entrypoint": "run_once", "hb_epoch": "4096", "ingress": "a\nb=1"},
            "text not a string": {"entrypoint": "run_once", "hb_epoch": "4096", "ingress": ["a"]},
        }.items():
            with self.subTest(request=label):
                values, refusal = self.gate.read(self.request(json.dumps(body)), (), choices=choices,
                                                 optional_text=("ingress",))
                self.assertIsNone(values)
                self.assertEqual(refusal["failure_code"], "COMMITTED_REQUEST_INVALID")
                self.assertIs(refusal["terminal"], True)

    def test_a_writer_records_the_request_it_was_passed(self):
        path, digest = "data/requests/ledger-writer-dispatch.json", "ab" * 32
        self.assertEqual(self.gate.recorded({}), (None, None))
        self.assertEqual(self.gate.recorded({self.gate.REQUEST_PATH_ENV: path, self.gate.REQUEST_SHA256_ENV: digest}),
                         ({"path": path, "sha256": digest, "hb_epoch_source": "COMMITTED_REQUEST"}, None))
        for label, environ in {
            "no digest": {self.gate.REQUEST_PATH_ENV: path},
            "no path": {self.gate.REQUEST_SHA256_ENV: digest},
            "uppercase digest": {self.gate.REQUEST_PATH_ENV: path, self.gate.REQUEST_SHA256_ENV: digest.upper()},
            "short digest": {self.gate.REQUEST_PATH_ENV: path, self.gate.REQUEST_SHA256_ENV: "ab"},
        }.items():
            with self.subTest(environ=label):
                values, refusal = self.gate.recorded(environ)
                self.assertIsNone(values)
                self.assertEqual(refusal["failure_code"], "COMMITTED_REQUEST_INVALID")
                for field in SIX:
                    self.assertTrue(refusal[field], field)

    def test_bind_refuses_a_committed_request_at_any_depth(self):
        forged = {"path": "data/requests/forged.json", "sha256": "f" * 64}
        for evidence in ({"committed_request": forged}, {"a": {"committed_request": forged}},
                         {"a": [1, {"b": [{"committed_request": None}]}]}):
            with self.subTest(evidence=evidence):
                values, refusal = self.gate.bind(evidence, "evidence", {})
                self.assertIsNone(values)
                self.assertEqual(refusal["failure_code"], "COMMITTED_REQUEST_INVALID")
        deep = {}
        cursor = deep
        for _ in range(100000):
            cursor["a"] = {}
            cursor = cursor["a"]
        cursor["committed_request"] = forged
        self.assertEqual(self.gate.bind(deep, "evidence", {})[1]["failure_code"], "COMMITTED_REQUEST_INVALID")
        self.assertEqual(self.gate.bind({"a": [1]}, "evidence", {}), ({"a": [1]}, None))
        cyclic = {"a": []}
        cyclic["a"].append(cyclic)
        self.assertIsNone(self.gate.bind(cyclic, "evidence", {})[1])

    def test_the_cli_writes_outputs_only_for_a_passing_request(self):
        output = self.work / "github_output"
        passing = self.request(json.dumps({"communication_id": "b-p40-probe", "hb_epoch": "4096"}))
        saved = os.environ.get("GITHUB_OUTPUT")
        os.environ["GITHUB_OUTPUT"] = str(output)
        try:
            self.assertEqual(self.gate.main(["--request", str(passing), "--require", "communication_id"]), 0)
            lines = output.read_text().splitlines()
            self.assertIn("communication_id=b-p40-probe", lines)
            self.assertIn("hb_epoch=4096", lines)
            output.unlink()
            failing = self.request(json.dumps({"communication_id": "b-p40-probe"}))
            self.assertEqual(self.gate.main(["--request", str(failing), "--require", "communication_id"]), 1)
            self.assertFalse(output.exists())
        finally:
            if saved is None:
                os.environ.pop("GITHUB_OUTPUT", None)
            else:
                os.environ["GITHUB_OUTPUT"] = saved


if __name__ == "__main__":
    unittest.main()
