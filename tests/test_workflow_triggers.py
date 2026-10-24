"""No workflow is started by a manual dispatch or a clock (B-P40, lead ruling R-DISPATCH).

Every action is a manifest-bound attempted state transition: it starts from a
committed change (push, pull_request) or a completed upstream workflow
(workflow_run), never from a person pressing a button (workflow_dispatch) or a
clock (schedule). The ruling is DERIVED_FROM_INVARIANT_TEXT
(StegVerse-Labs/.github main@149f16e): task-registry-global-invariants.json
:54 actions_by_manifest_required, :58 external_machine_awaiting_allowed false,
:60 always_on_receiver_required false, :120 and :160-161 NO_EXTERNAL_MACHINE_AWAITING
and NO_ALWAYS_ON_RECEIVER as transition predicates. No invariant names
workflow_dispatch or schedule verbatim.

Scope is surface ownership, not authorship (lead ruling R-SCOPE): every
non-conforming trigger in this repository is converted, whoever committed it,
unless it sits on a declared other-lane surface (TVC, InTr hop, KV). Each such
workflow is listed in OTHER_LANE_ALLOWLIST with the lane that owns it and is
handed off on the PR. The allowlist may only shrink: a non-conforming trigger
anywhere else fails this test.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
NON_CONFORMING = ("workflow_dispatch", "schedule")

#: Workflows on a declared other-lane surface that still carry a
#: non-conforming trigger, with the lane that converts it. They are handed off,
#: not edited, by this lane.
OTHER_LANE_ALLOWLIST: dict[str, dict[str, object]] = {
    # TVC: dispatch and workflow_call take a TVC receipt and a TV-resolved
    # runtime capability (data/tvc-principle-completeness-capability-request.json).
    "principle-completeness-workers.yml": {
        "owner": "Grok Lane C (TVC); git blame StegVerse (4d7941c)",
        "triggers": ("schedule", "workflow_dispatch"),
    },
}


def triggers(path: Path) -> set[str]:
    """The event names in a workflow's top-level `on:` block, without a YAML parser."""
    text = path.read_text(encoding="utf-8")
    inline = re.search(r"^(?:on|\"on\"|'on')\s*:\s*(\[.*\]|[A-Za-z_]+)\s*$", text, re.M)
    if inline:
        return set(re.findall(r"[A-Za-z_]+", inline.group(1)))
    block = re.search(r"^(?:on|\"on\"|'on')\s*:\s*\n((?:[ \t]+.*\n|[ \t]*\n)*)", text, re.M)
    if not block:
        return set()
    lines = [line for line in block.group(1).splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if not lines:
        return set()
    indent = min(len(line) - len(line.lstrip()) for line in lines)
    names = set()
    for line in lines:
        if len(line) - len(line.lstrip()) == indent:
            match = re.match(r"\s*-?\s*([A-Za-z_]+)\s*:?", line)
            if match:
                names.add(match.group(1))
    return names


class WorkflowTriggerTests(unittest.TestCase):
    def test_the_trigger_reader_sees_every_form(self):
        cases = {
            "on:\n  push:\n    branches: [main]\n  workflow_dispatch:\n": {"push", "workflow_dispatch"},
            "on: [push, schedule]\n": {"push", "schedule"},
            "on: workflow_dispatch\n": {"workflow_dispatch"},
            "on:\n  schedule:\n    - cron: '0 0 * * *'\n  pull_request:\n": {"schedule", "pull_request"},
        }
        probe = ROOT / "tests" / ".probe-workflow.yml"
        try:
            for text, expected in cases.items():
                with self.subTest(text=text):
                    probe.write_text(text, encoding="utf-8")
                    self.assertEqual(triggers(probe), expected)
        finally:
            probe.unlink(missing_ok=True)

    def test_no_workflow_starts_by_manual_dispatch_or_clock(self):
        offending = {}
        for path in sorted(WORKFLOWS.glob("*.y*ml")):
            found = sorted(triggers(path) & set(NON_CONFORMING))
            allowed = set(OTHER_LANE_ALLOWLIST.get(path.name, {}).get("triggers", ()))
            if set(found) - allowed:
                offending[path.name] = sorted(set(found) - allowed)
        self.assertEqual(offending, {}, "non-conforming triggers outside the other-lane allowlist")

    def test_the_allowlist_only_names_live_other_lane_triggers(self):
        for name, entry in OTHER_LANE_ALLOWLIST.items():
            with self.subTest(workflow=name):
                path = WORKFLOWS / name
                self.assertTrue(path.is_file(), name + " is allowlisted but does not exist")
                self.assertTrue(entry.get("owner"), name + " is allowlisted without an owner")
                live = triggers(path) & set(NON_CONFORMING)
                self.assertTrue(set(entry["triggers"]) <= live,
                                name + " allowlists a trigger it no longer has; shrink the allowlist")


if __name__ == "__main__":
    unittest.main()
