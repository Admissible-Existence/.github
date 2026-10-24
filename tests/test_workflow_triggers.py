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

Workflows this lane did not author are not edited here. Each one that still
carries a non-conforming trigger is listed in OTHER_AUTHOR_ALLOWLIST with its
owner, and is recorded on the owning Goal issue. The allowlist may only shrink:
a new non-conforming trigger anywhere else fails this test.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
NON_CONFORMING = ("workflow_dispatch", "schedule")

#: Other-author workflows that still carry a non-conforming trigger, with the
#: owner who must convert it and the commit that created the workflow. They are
#: not edited by this lane: each was created by its owner, and the only Claude
#: commit on most of them (8e86ed6) pinned action shas without touching triggers.
OTHER_AUTHOR_ALLOWLIST: dict[str, dict[str, object]] = {
    "cross-repository-remediation-router.yml": {"owner": "StegVerse (920617f)", "triggers": ('schedule', 'workflow_dispatch')},
    "formalism-archive-gate.yml": {"owner": "StegVerse (afeff0f)", "triggers": ('workflow_dispatch',)},
    "formalism-coherence-audit.yml": {"owner": "StegVerse (95823fd)", "triggers": ('schedule', 'workflow_dispatch')},
    "heartbeat-response-node.yml": {"owner": "StegVerse (ec643c3)", "triggers": ('schedule', 'workflow_dispatch')},
    "hosted-completion-activator.yml": {"owner": "StegVerse (ef45b16)", "triggers": ('workflow_dispatch',)},
    "intr-destination-capability-validation.yml": {"owner": "Cursor Agent (a07a275)", "triggers": ('workflow_dispatch',)},
    "mathematical-completeness-audit.yml": {"owner": "StegVerse (5826a50)", "triggers": ('schedule', 'workflow_dispatch')},
    "org-runtime-boundary.yml": {"owner": "StegVerse (b990e9b)", "triggers": ('workflow_dispatch',)},
    "organization-ledger-transition.yml": {"owner": "Cursor Agent with StegVerse (5221934)", "triggers": ('workflow_dispatch',)},
    "organization-mathematics-registry.yml": {"owner": "StegVerse (1939898)", "triggers": ('workflow_dispatch',)},
    "principle-completeness-reconciled.yml": {"owner": "StegVerse (aa6a192)", "triggers": ('schedule', 'workflow_dispatch')},
    "principle-completeness-workers.yml": {"owner": "StegVerse (4d7941c)", "triggers": ('schedule', 'workflow_dispatch')},
    "principle-worker-activation-observer.yml": {"owner": "StegVerse (96f97a8)", "triggers": ('schedule', 'workflow_dispatch')},
    "repository-disposition-activator.yml": {"owner": "StegVerse (ef45b16)", "triggers": ('workflow_dispatch',)},
    "support-completion-activator.yml": {"owner": "StegVerse (ef45b16)", "triggers": ('workflow_dispatch',)},
    "validate-principle-worker-blocker-fallback.yml": {"owner": "StegVerse (0d6f1ff)", "triggers": ('workflow_dispatch',)},
    "validate-stcm-chf-inert-witness.yml": {"owner": "StegVerse (6a90de8)", "triggers": ('workflow_dispatch',)},
    "validate-stcm-chf-native-baselines.yml": {"owner": "StegVerse (99bc476)", "triggers": ('workflow_dispatch',)},
    "validate-triform-formalism.yml": {"owner": "StegVerse (bc8f3ba)", "triggers": ('workflow_dispatch',)},
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
            allowed = set(OTHER_AUTHOR_ALLOWLIST.get(path.name, {}).get("triggers", ()))
            if set(found) - allowed:
                offending[path.name] = sorted(set(found) - allowed)
        self.assertEqual(offending, {}, "non-conforming triggers outside the other-author allowlist")

    def test_the_allowlist_only_names_live_other_author_triggers(self):
        for name, entry in OTHER_AUTHOR_ALLOWLIST.items():
            with self.subTest(workflow=name):
                path = WORKFLOWS / name
                self.assertTrue(path.is_file(), name + " is allowlisted but does not exist")
                self.assertTrue(entry.get("owner"), name + " is allowlisted without an owner")
                live = triggers(path) & set(NON_CONFORMING)
                self.assertTrue(set(entry["triggers"]) <= live,
                                name + " allowlists a trigger it no longer has; shrink the allowlist")


if __name__ == "__main__":
    unittest.main()
