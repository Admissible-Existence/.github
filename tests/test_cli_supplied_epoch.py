"""Every ``--hb-epoch`` CLI reads the epoch as text and checks it with the kernel's rule.

An ``argparse`` ``type=int`` epoch admits ``"+33"``, ``"３３"`` and ``" 33"``
as 33. Here each CLI takes the text, refuses what the shared rule
(SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH) refuses with the six-field
FAIL_CLOSED, exits non-zero and writes nothing. ``"4096"`` is accepted. Both
ledger roots and the mesh are redirected; nothing here is a production receipt.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EMIT = ROOT / ".stegverse/transition-ledger/emit.py"
AGGREGATE = ROOT / "resident-runtime/aggregate_repo_transition.py"
INGRESS = ROOT / "resident-runtime/intr_destination_ingress.py"
EGRESS = ROOT / "resident-runtime/organization_egress_boundary.py"

EPOCH_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
                "retry_entrypoint", "owning_existing_goal", "next_attempt")
REFUSED = ((None, "HB_EPOCH_NOT_SUPPLIED"),) + tuple(
    (epoch, "HB_EPOCH_INVALID") for epoch in ("+33", "３３", " 33", "True", "abc", "33.7"))
ACCEPTED = "4096"
DIGEST = "sha256:" + "0" * 64


class CliSuppliedEpochTests(unittest.TestCase):
    def setUp(self):
        self._work = tempfile.TemporaryDirectory()
        self.addCleanup(self._work.cleanup)
        self.work = Path(self._work.name)
        self.repo_root = self.work / "repo-ledger"
        self.org_root = self.work / "org-ledger"
        self.mesh = self.work / "mesh"
        self.out = self.work / "out" / "result.json"
        self.env = {**os.environ, "STEGVERSE_REPO_LEDGER_ROOT": str(self.repo_root),
                    "STEGVERSE_ORG_LEDGER_ROOT": str(self.org_root),
                    "XDG_STATE_HOME": str(self.work / "state")}
        self.payload = self.work / "payload.json"
        self.payload.write_text(json.dumps({
            "message_class": "ecosystem.communication", "communication_id": "cli-epoch",
            "subject": "purpose-neutral mesh diagnostic",
            "body": {"schema": "stegverse.org-intr-destination-diagnostic/v1",
                     "probe": "diagnostic-crossing"}}), encoding="utf-8")
        self.standing = self.work / "standing.json"
        self.standing.write_text(json.dumps({"mode": "ESTABLISH_GENESIS", "node_ref": "cli-epoch",
                                             "predecessor": None}), encoding="utf-8")
        self.receipt = self.work / "repo-receipt.json"

    def run_cli(self, script, args, epoch):
        argv = [sys.executable, str(script), *args]
        if epoch is not None:
            argv += ["--hb-epoch=" + epoch]
        return subprocess.run(argv, cwd=self.work, env=self.env, capture_output=True,
                              text=True, encoding="utf-8")

    def written(self):
        return [path for path in (self.repo_root, self.org_root, self.mesh, self.out,
                                  self.work / "state") if path.exists()]

    def repository_receipt(self):
        done = self.run_cli(EMIT, ["--transition-id", "cli:seed", "--transition-class", "PROBE",
                                   "--predecessor-state-sha256", DIGEST,
                                   "--successor-state-sha256", DIGEST], ACCEPTED)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.receipt.write_text(done.stdout, encoding="utf-8")

    def clis(self):
        return {
            "emit": (EMIT, ["--transition-id", "cli:probe", "--transition-class", "PROBE",
                            "--predecessor-state-sha256", DIGEST, "--successor-state-sha256", DIGEST]),
            "aggregate": (AGGREGATE, ["--repo-receipt", str(self.receipt),
                                      "--predecessor-org-state-sha256", DIGEST,
                                      "--successor-org-state-sha256", DIGEST]),
            "ingress": (INGRESS, ["--self-close", "--communication-id", "cli-epoch",
                                  "--out", str(self.out)]),
            "egress": (EGRESS, ["--destination-organization", "StegVerse-org",
                                "--capability", "intr-destination", "--payload", str(self.payload),
                                "--standing", str(self.standing), "--mesh-root", str(self.mesh),
                                "--out", str(self.out)]),
        }

    def test_each_cli_refuses_an_absent_or_invalid_epoch_and_writes_nothing(self):
        # The aggregate CLI reads a real repository receipt, so its refusal is
        # the epoch's and not the receipt's. The seed is written elsewhere.
        seed_env = self.env
        self.env = {**seed_env, "STEGVERSE_REPO_LEDGER_ROOT": str(self.work / "seed")}
        self.repository_receipt()
        self.env = seed_env
        for name, (script, args) in self.clis().items():
            for epoch, code in REFUSED:
                with self.subTest(cli=name, epoch=epoch):
                    done = self.run_cli(script, args, epoch)
                    self.assertNotEqual(done.returncode, 0)
                    refusal = json.loads(done.stdout.strip().splitlines()[-1])
                    self.assertEqual(refusal["disposition"], "FAIL_CLOSED")
                    self.assertEqual(refusal["failure_code"], code)
                    self.assertEqual(refusal["failed_predicate"],
                                     "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH")
                    for field in EPOCH_FIELDS:
                        self.assertTrue(refusal[field], field)
                    self.assertIs(refusal["derived_from_clock"], False)
                    self.assertEqual(self.written(), [])

    def test_each_cli_accepts_4096(self):
        self.repository_receipt()
        self.assertEqual(json.loads(self.receipt.read_text())["hb_reference"]["epoch"], 4096)
        for name, (script, args) in self.clis().items():
            if name == "emit":
                continue
            with self.subTest(cli=name):
                done = self.run_cli(script, args, ACCEPTED)
                self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
                result = json.loads(done.stdout.strip().splitlines()[-1])
                if name == "aggregate":
                    self.assertEqual(result["hb_reference"]["epoch"], 4096)
                    self.assertEqual(result["observed_at"], "HB:4096")
                else:
                    self.assertIn(result["disposition"], {"ALLOW", "PENDING"})


if __name__ == "__main__":
    unittest.main()
