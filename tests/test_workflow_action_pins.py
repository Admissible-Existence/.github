"""Every remote ``uses:`` in ``.github/workflows`` is pinned to a commit sha.

A tag such as ``@v4`` is a mutable reference. Whoever controls the action
repository can move it, and the next run executes whatever it points to.
A 40-hex commit sha cannot be moved. Local ``./`` actions live in this
repository and are reviewed with it, so they are excepted.

Standard library only. The workflow files are scanned as text, so this
guard needs no YAML parser and adds no dependency.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

USES = re.compile(r"""^\s*(?:-\s+)?uses:\s*['"]?([^'"\s#]+)""")
PINNED = re.compile(r"^[^@\s]+@[0-9a-f]{40}$")


def workflow_uses() -> list[tuple[str, int, str]]:
    found = []
    for path in sorted(WORKFLOWS.rglob("*")):
        if path.suffix not in {".yml", ".yaml"} or not path.is_file():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for number, line in enumerate(lines, start=1):
            match = USES.match(line)
            if match:
                found.append((path.relative_to(ROOT).as_posix(), number, match.group(1)))
    return found


def unpinned(uses: list[tuple[str, int, str]]) -> list[tuple[str, int, str]]:
    return [
        (path, number, ref)
        for path, number, ref in uses
        if not ref.startswith("./") and not PINNED.match(ref)
    ]


def failure_message(offenders: list[tuple[str, int, str]]) -> str:
    listed = "\n".join(f"  {path}:{number}: {ref}" for path, number, ref in offenders)
    return "\n".join(
        [
            "failure_code: WORKFLOW_ACTION_NOT_PINNED",
            "failed_predicate: every remote `uses:` in .github/workflows/** "
            "matches <owner>/<repo>[/<path>]@<40-hex commit sha>",
            "required_evidence_or_repair: replace each listed reference with "
            "<action>@<full commit sha> # <tag>, taking the sha from the "
            "action repository's tag, never guessed",
            "retry_entrypoint: python -m unittest tests.test_workflow_action_pins -v",
            "owning_existing_goal: M-P9 workflow action pinning",
            "next_attempt: pin the listed references and rerun the retry_entrypoint",
            "unpinned_references:",
            listed,
        ]
    )


class WorkflowActionPinsTest(unittest.TestCase):
    def test_workflows_are_scanned(self) -> None:
        self.assertTrue(workflow_uses(), "no `uses:` found under .github/workflows")

    def test_every_remote_action_is_pinned_to_a_commit_sha(self) -> None:
        offenders = unpinned(workflow_uses())
        if offenders:
            self.fail(failure_message(offenders))

    def test_guard_rejects_mutable_references(self) -> None:
        sha = "11d5960a326750d5838078e36cf38b85af677262"
        sample = [
            ("w.yml", 1, "actions/checkout@v4"),
            ("w.yml", 2, "actions/checkout@main"),
            ("w.yml", 3, "actions/checkout@" + sha[:7]),
            ("w.yml", 4, "actions/checkout@" + sha.upper()),
            ("w.yml", 5, "docker://alpine:3"),
            ("w.yml", 6, "actions/checkout@" + sha),
            ("w.yml", 7, "org/repo/.github/workflows/x.yml@" + sha),
            ("w.yml", 8, "./.github/actions/local"),
        ]
        self.assertEqual([number for _, number, _ in unpinned(sample)], [1, 2, 3, 4, 5])

    def test_scanner_reads_both_step_forms(self) -> None:
        for line in (
            "      - uses: actions/checkout@v4",
            "        uses: actions/checkout@v4 # v4",
            "        uses: 'actions/checkout@v4'",
        ):
            self.assertEqual(USES.match(line).group(1), "actions/checkout@v4")


if __name__ == "__main__":
    unittest.main()
