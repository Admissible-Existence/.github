#!/usr/bin/env python3
"""Fail-closed coherence audit for registered Admissible-Existence formalisms."""
from __future__ import annotations

import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "formalism-worker-registry.json"
OUTPUT = ROOT / "reports" / "formalism-coherence-latest.json"
ORG = "Admissible-Existence"
PLACEHOLDER_RE = re.compile(r"\b(TODO|FIXME|TBD|PLACEHOLDER|STUB|PENDING)\b", re.I)
MATH_RE = re.compile(r"(\\begin\{|\\forall|\\exists|\$[^$]+\$|\b(theorem|axiom|lemma|proposition|invariant|equation|proof)\b|:=|⇒|→|∈|≤|≥)", re.I)
LINK_RE = re.compile(r"\[[^\]]+\]\((?!https?://|mailto:|#)([^)]+)\)")
DEFINITION_RE = re.compile(r"^#{1,6}\s+(?:definition\s+)?([A-Za-z0-9][^#]{1,100})$", re.I | re.M)


def api(path: str, token: str) -> Any:
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "aex-formalism-coherence-worker",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def fetch_text(repo: str, path: str, token: str) -> str:
    data = api(f"/repos/{ORG}/{repo}/contents/{path}", token)
    return base64.b64decode(data["content"]).decode("utf-8", errors="replace")


def normalize_link(source: str, target: str) -> str:
    target = target.split("#", 1)[0].split("?", 1)[0]
    if not target:
        return ""
    source_dir = Path(source).parent
    return str((source_dir / target).as_posix()).replace("//", "/")


def audit_repo(repo: str, token: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "repository": f"{ORG}/{repo}",
        "state": "IN_PROGRESS",
        "findings": [],
        "metrics": {},
        "next_task": None,
    }
    try:
        metadata = api(f"/repos/{ORG}/{repo}", token)
        branch = metadata.get("default_branch", "main")
        tree = api(f"/repos/{ORG}/{repo}/git/trees/{branch}?recursive=1", token)
        paths = {item["path"] for item in tree.get("tree", []) if item.get("type") == "blob"}
        markdown = sorted(p for p in paths if p.lower().endswith((".md", ".markdown")))
        handoffs = sorted(p for p in paths if p.endswith("_MIRROR_HANDOFF.md"))
        result["metrics"].update({"branch": branch, "files": len(paths), "markdown_files": len(markdown), "handoffs": len(handoffs)})
        if not handoffs:
            result["findings"].append({"severity": "error", "code": "MISSING_HANDOFF"})

        placeholders = 0
        math_files = 0
        broken_links: list[dict[str, str]] = []
        duplicate_definitions: list[str] = []
        definitions: dict[str, str] = {}
        theorem_signals = 0
        proof_signals = 0

        for path in markdown[:250]:
            text = fetch_text(repo, path, token)
            placeholders += len(PLACEHOLDER_RE.findall(text))
            if MATH_RE.search(text):
                math_files += 1
            theorem_signals += len(re.findall(r"\b(theorem|lemma|proposition)\b", text, re.I))
            proof_signals += len(re.findall(r"\bproof\b", text, re.I))
            for label in DEFINITION_RE.findall(text):
                key = re.sub(r"\s+", " ", label.strip().lower())
                if key in definitions and definitions[key] != path:
                    duplicate_definitions.append(label.strip())
                else:
                    definitions[key] = path
            for target in LINK_RE.findall(text):
                normalized = normalize_link(path, target)
                if normalized and normalized not in paths and not normalized.endswith("/"):
                    broken_links.append({"source": path, "target": target})

        result["metrics"].update({
            "math_signal_files": math_files,
            "placeholder_markers": placeholders,
            "broken_local_links": len(broken_links),
            "duplicate_definition_labels": len(set(duplicate_definitions)),
            "theorem_signals": theorem_signals,
            "proof_signals": proof_signals,
        })
        if not markdown:
            result["findings"].append({"severity": "error", "code": "NO_FORMAL_DOCUMENTATION"})
        if math_files == 0:
            result["findings"].append({"severity": "error", "code": "NO_MATHEMATICAL_SIGNAL"})
        if placeholders:
            result["findings"].append({"severity": "warning", "code": "UNRESOLVED_PLACEHOLDERS", "count": placeholders})
        if broken_links:
            result["findings"].append({"severity": "error", "code": "BROKEN_LOCAL_LINKS", "examples": broken_links[:25]})
        if duplicate_definitions:
            result["findings"].append({"severity": "warning", "code": "POSSIBLE_DEFINITION_COLLISIONS", "labels": sorted(set(duplicate_definitions))[:25]})
        if theorem_signals > proof_signals:
            result["findings"].append({"severity": "warning", "code": "THEOREM_PROOF_CLASSIFICATION_GAP", "theorem_signals": theorem_signals, "proof_signals": proof_signals})

        errors = [f for f in result["findings"] if f["severity"] == "error"]
        warnings = [f for f in result["findings"] if f["severity"] == "warning"]
        result["state"] = "BLOCKED" if errors else ("REVIEW_REQUIRED" if warnings else "COMPLETE")
        if result["state"] != "COMPLETE":
            result["next_task"] = {
                "owner": f"{ORG}/{repo}",
                "target": handoffs[0] if handoffs else f"docs/{repo}_MIRROR_HANDOFF.md",
                "action": "Resolve coherence findings and rerun organization audit",
                "release_condition": "No error findings; all warnings classified or closed",
            }
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
        result["state"] = "BLOCKED"
        result["findings"].append({"severity": "error", "code": "REPOSITORY_INACCESSIBLE_OR_API_FAILURE", "detail": str(exc)})
        result["next_task"] = {
            "owner": f"{ORG}/{repo}",
            "target": "repository access / worker credential",
            "action": "Restore machine-readable access and rerun audit",
            "release_condition": "GitHub API tree and Markdown content are readable",
        }
    return result


def main() -> int:
    token = os.environ.get("STEGVERSE_WORKER_TOKEN") or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("No GitHub token available; fail closed.", file=sys.stderr)
        return 2
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    results = [audit_repo(item["name"], token) for item in registry["repositories"]]
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "goal_id": registry["goal_id"],
        "state_counts": {state: sum(r["state"] == state for r in results) for state in ["COMPLETE", "REVIEW_REQUIRED", "BLOCKED", "FAILED"]},
        "repositories": results,
        "publication_authorized": False,
        "publication_rule": "This audit detects coherence gaps; it does not independently authorize publication.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary["state_counts"], sort_keys=True))
    return 1 if any(r["state"] == "BLOCKED" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
