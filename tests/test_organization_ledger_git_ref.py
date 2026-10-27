"""The designated organization ledger ref can hold a diagnostic self-closure.

These cases run against a temporary git repository. The receipts they append
are fixtures of that temporary ref. They are exercised here so a
push of the committed self-closure packet performed the same closure against the published ref until that
carrier was retired (Rigel's rule, 2026-10-25: no InTr hop inside one organization).
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
REF = "refs/stegverse/organization-ledger"
COMMUNICATION_ID = "diagnostic-self-closure-001"
CONSTRAINT = "CONSTRAINT_VARIABLE"
DISPOSITION_ROLE = "TRANSITION_EVIDENCE_ONLY"
CONSTRAINT_FIELDS = (
    "routing_authority_constraint",
    "admission_authority_constraint",
    "execution_authority_constraint",
    "time_constraint",
)


def git(*args, cwd=None):
    completed = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if completed.returncode != 0:
        raise AssertionError(completed.stderr or completed.stdout)
    return completed


class DesignationTests(unittest.TestCase):
    def test_the_org_contract_designates_the_published_ref(self):
        contract = json.loads((ROOT / ".stegverse/transition-ledger/org-contract.json").read_text())
        location = json.loads((ROOT / ".stegverse/transition-ledger/contract.json").read_text())
        location = location["repository_ledger_location"]
        self.assertEqual(contract["organization"], "Admissible-Existence")
        self.assertEqual(contract["organization_ledger_repository"], "Admissible-Existence/.github")
        self.assertEqual(contract["organization_ledger_ref"], REF)
        self.assertEqual(contract["authority_effect"], "NONE_CONTRACT_ONLY")
        self.assertEqual(contract["disposition_role"], DISPOSITION_ROLE)
        self.assertEqual(contract["time_constraint"], CONSTRAINT)
        self.assertEqual(contract["ledger_lock"], "ORGANIZATION_LEDGER_LOCK")
        self.assertNotIn("runtime_reality_authority", contract)
        self.assertEqual(location["repository"], contract["organization_ledger_repository"])
        self.assertEqual(location["ref"], contract["organization_ledger_ref"])
        self.assertIs(location["new_ledger_root"], False)
        self.assertEqual(location["namespace"], "repository-ledger/Admissible-Existence/.github")

    def test_the_packet_push_workflow_appends_pushes_and_reads_the_designated_ref(self):
        # Re-purposed (base id kept) under Rigel's rule (2026-10-25): InTr paths exist only between distinct
        # organizations, so the packet-push self-closure workflow is retired. The designated ref is appended
        # only by the push-only organization-ledger-writer.yml, fast-forward only.
        self.assertFalse((ROOT / ".github/workflows/organization-ledger-transition.yml").exists())
        text = (ROOT / ".github/workflows/organization-ledger-writer.yml").read_text()
        self.assertNotIn("--self-close", text)
        self.assertNotIn("self-closure-packet", text)
        self.assertIn("refs/stegverse/organization-ledger", text)
        self.assertNotIn("--force", text)
        self.assertNotIn("grant", text.lower())

class TemporaryGitSelfClosureTests(unittest.TestCase):
    def setUp(self):
        self._work = tempfile.TemporaryDirectory()
        self.addCleanup(self._work.cleanup)
        root = Path(self._work.name)
        self.repo = root / "checkout"
        self.remote = root / "origin.git"
        self.fresh = root / "readback.git"
        self.repo.mkdir()
        git("init", "-q", self.repo)
        git("init", "-q", "--bare", self.remote)
        git("-C", self.repo, "remote", "add", "origin", self.remote)
        contract = json.loads((ROOT / ".stegverse/transition-ledger/contract.json").read_text())
        self.namespace = contract["repository_ledger_location"]["namespace"]
        self.closure = root / "closure.json"
        self.readback = root / "readback.json"

    def ledger_env(self):
        env = os.environ.copy()
        env["STEGVERSE_ORG_LEDGER_ROOT"] = f"git+{self.repo}#{REF}"
        env["STEGVERSE_REPO_LEDGER_ROOT"] = f"git+{self.repo}#{REF}:{self.namespace}"
        return env

    def run_closure(self, communication_id, *extra):
        return subprocess.run(
            [sys.executable, "resident-runtime/intr_destination_ingress.py",
             "--self-close", "--communication-id", communication_id, "--hb-epoch", "32",
             "--out", str(self.closure), *extra],
            cwd=ROOT, env=self.ledger_env(), capture_output=True, text=True)

    def test_a_self_closure_appends_both_receipts_and_reads_them_back(self):
        first = self.run_closure(COMMUNICATION_ID)
        self.assertEqual(first.returncode, 0, first.stderr or first.stdout)
        result = json.loads(self.closure.read_text())
        self.assertEqual(result["disposition"], "ALLOW")
        self.assertEqual(result["communication_id"], COMMUNICATION_ID)
        self.assertIs(result["self_closure"], True)
        self.assertIs(result["closure_recorded"], True)
        self.assertIs(result["closed"], True)
        for name in CONSTRAINT_FIELDS:
            self.assertEqual(result[name], CONSTRAINT, name)
        self.assertEqual(result["disposition_role"], DISPOSITION_ROLE)
        git("-C", self.repo, "push", "origin", f"{REF}:{REF}")
        second = self.run_closure(COMMUNICATION_ID)
        self.assertEqual(second.returncode, 0, second.stderr or second.stdout)
        replayed = json.loads(self.closure.read_text())
        self.assertIs(replayed["transition_replayed"], True)
        self.assertEqual(replayed["repository_receipt_sha256"], result["repository_receipt_sha256"])
        self.assertEqual(replayed["organization_receipt_sha256"], result["organization_receipt_sha256"])
        git("init", "-q", "--bare", self.fresh)
        git("--git-dir", self.fresh, "fetch", "-q", self.remote, f"+{REF}:{REF}")
        read = subprocess.run(
            [sys.executable, "resident-runtime/organization_ledger_readback.py",
             "--location", f"git+{self.fresh}#{REF}",
             "--repository-namespace", self.namespace,
             "--closure-result", str(self.closure),
             "--out", str(self.readback)],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(read.returncode, 0, read.stderr or read.stdout)
        report = json.loads(self.readback.read_text())
        self.assertEqual(report["disposition"], "ALLOW")
        self.assertEqual(report["chain_length"], 1)
        self.assertEqual(report["repository_ledger"]["chain_length"], 1)
        self.assertEqual(report["closure_communication_id"], COMMUNICATION_ID)
        self.assertIs(report["closure_receipts_carry_communication_id"], True)
        self.assertIs(report["closure_repository_receipt_in_chain"], True)
        self.assertIs(report["closure_organization_receipt_in_chain"], True)
        self.assertEqual(report["repository_ledger"]["chain"][0]["communication_id"], COMMUNICATION_ID)
        self.assertEqual(report["chain"][0]["communication_id"], COMMUNICATION_ID)
        self.assertEqual(report["disposition_role"], DISPOSITION_ROLE)
        self.assertIs(report["repository_ledger"]["replay_read_organization_receipts"], False)

    def test_a_communication_id_that_is_not_an_identifier_appends_nothing(self):
        refused = self.run_closure("../peer")
        self.assertNotEqual(refused.returncode, 0)
        probed = subprocess.run(
            ["git", "-C", self.repo, "rev-parse", "--verify", "--quiet", REF],
            capture_output=True, text=True)
        self.assertNotEqual(probed.returncode, 0)


if __name__ == "__main__":
    unittest.main()
