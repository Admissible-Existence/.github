#!/usr/bin/env python3
"""Audit every registered Admissible-Existence repository for role-appropriate mathematical completeness.

This auditor intentionally distinguishes source mathematics from support/coordination/disposition roles.
It produces machine-readable and reviewable matrices and never promotes a proof candidate to a proof.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API = "https://api.github.com"


def load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def api_json(path: str, token: str | None) -> Any:
    req = urllib.request.Request(API + path)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "aex-mathematical-completeness-auditor/1.0")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {exc.code} for {path}: {body[:300]}") from exc


def fetch_repo_tree(repo: str, token: str | None) -> tuple[str, dict[str, dict[str, Any]]]:
    meta = api_json(f"/repos/{repo}", token)
    branch = meta["default_branch"]
    tree = api_json(f"/repos/{repo}/git/trees/{urllib.parse.quote(branch, safe='')}?recursive=1", token)
    if tree.get("truncated"):
        raise RuntimeError(f"recursive tree truncated for {repo}; fail closed")
    mapping = {item["path"]: item for item in tree.get("tree", []) if item.get("type") == "blob"}
    return branch, mapping


def fetch_blob_text(repo: str, sha: str, token: str | None) -> str:
    obj = api_json(f"/repos/{repo}/git/blobs/{sha}", token)
    import base64
    return base64.b64decode(obj.get("content", "")).decode("utf-8", errors="replace")


def normalized_text(text: str) -> str:
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def nontrivial(text: str, minimum: int) -> bool:
    compact = normalized_text(text)
    if len(compact) < minimum:
        return False
    lower = compact.lower()
    placeholder_only = all(marker not in lower for marker in ("principle", "proof", "candidate", "theory", "equation", "support", "contract", "falsif", "dependency", "continuity", "standing", "validation"))
    if placeholder_only and any(marker in lower for marker in ("todo", "tbd", "placeholder", "coming soon")):
        return False
    return True


def has_any(text: str, markers: list[str]) -> bool:
    lower = text.lower()
    return any(marker.lower() in lower for marker in markers)


def find_handoff(paths: set[str]) -> str | None:
    candidates = sorted(p for p in paths if p.endswith("_MIRROR_HANDOFF.md"))
    if not candidates:
        return None
    docs = [p for p in candidates if p.startswith("docs/")]
    return (docs or candidates)[0]


def artifact_check(repo: str, path: str, tree: dict[str, dict[str, Any]], token: str | None, minimum: int) -> dict[str, Any]:
    item = tree.get(path)
    if not item:
        return {"path": path, "present": False, "nontrivial": False, "status": "MISSING"}
    text = fetch_blob_text(repo, item["sha"], token)
    return {
        "path": path,
        "present": True,
        "nontrivial": nontrivial(text, minimum),
        "status": "PASS" if nontrivial(text, minimum) else "REVIEW_REQUIRED",
        "blob_sha": item["sha"],
        "text": text,
    }


def strip_text(check: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in check.items() if k != "text"}


def audit_source(repo: str, tree: dict[str, dict[str, Any]], token: str | None, policy: dict[str, Any]) -> dict[str, Any]:
    minimum = policy["semantic_minimums"]["minimum_nonblank_characters"]
    reqs = policy["source_requirements"]["required_artifacts"]
    checks = {p: artifact_check(repo, p, tree, token, minimum) for p in reqs}
    handoff = find_handoff(set(tree))

    registry = checks["formalism/principle-registry.yaml"]
    dep = checks["formalism/dependency-graph.yaml"]
    proof = checks["formalism/proof-candidates.yaml"]
    theory = checks["docs/WHOLE_REPO_THEORY_MAP.md"]
    math = checks["docs/MATHEMATICAL_NOTATION.md"]
    fals = checks["docs/FALSIFICATION_AND_LIMITS.md"]

    semantic = {
        "formal_declaration": registry.get("status") == "PASS" and has_any(registry.get("text", ""), ["principle", "id", "claim"]),
        "dependency_derivation": dep.get("status") == "PASS" and has_any(dep.get("text", ""), ["depend", "edge", "node", "requires"]),
        "whole_repo_theory": theory.get("status") == "PASS" and has_any(theory.get("text", ""), ["theory", "principle", "model", "map"]),
        "mathematical_notation": math.get("status") == "PASS" and has_any(math.get("text", ""), policy["semantic_minimums"]["mathematical_markers"]),
        "mathematical_derivation_evidence": math.get("status") == "PASS" and has_any(math.get("text", ""), policy["semantic_minimums"]["derivation_markers"]),
        "proof_candidate": proof.get("status") == "PASS" and has_any(proof.get("text", ""), policy["semantic_minimums"]["proof_candidate_markers"]),
        "falsification_and_limits": fals.get("status") == "PASS" and has_any(fals.get("text", ""), policy["semantic_minimums"]["falsification_markers"]),
    }
    gaps = [name for name, passed in semantic.items() if not passed]
    if not handoff:
        gaps.append("mirror_handoff")
    return {
        "applicability": "SOURCE_MATHEMATICS_REQUIRED",
        "handoff": handoff,
        "artifacts": {p: strip_text(c) for p, c in checks.items()},
        "semantic": semantic,
        "gaps": gaps,
        "mathematical_complete": not gaps,
        "proof_candidate_is_proof": False,
    }


def audit_non_source(repo: str, role: str, tree: dict[str, dict[str, Any]], token: str | None, policy: dict[str, Any]) -> dict[str, Any]:
    minimum = policy["semantic_minimums"]["minimum_nonblank_characters"]
    paths = set(tree)
    handoff = find_handoff(paths)
    if role == "support":
        spec = policy["support_requirements"]
        applicability = "ROLE_SPECIFIC_SUPPORT; MATHEMATICS_NA"
    elif role == "coordination":
        spec = policy["coordination_requirements"]
        applicability = "CONTROL_PLANE; MATHEMATICS_NA"
    else:
        spec = policy["empty_or_deprecated_requirements"]
        applicability = "DEPRECATED_OR_EMPTY; MATHEMATICS_NA"
    checks = {p: artifact_check(repo, p, tree, token, minimum) for p in spec["required_artifacts"]}
    gaps = [p for p, c in checks.items() if c["status"] != "PASS"]
    if spec.get("required_handoff") and not handoff:
        gaps.append("mirror_handoff")
    return {
        "applicability": applicability,
        "handoff": handoff,
        "na_rationale": spec.get("na_rationale"),
        "artifacts": {p: strip_text(c) for p, c in checks.items()},
        "semantic": {
            "formal_declaration": "N/A",
            "dependency_derivation": "N/A",
            "whole_repo_theory": "N/A",
            "mathematical_notation": "N/A",
            "mathematical_derivation_evidence": "N/A",
            "proof_candidate": "N/A",
            "falsification_and_limits": "N/A",
        },
        "gaps": gaps,
        "mathematical_complete": not gaps,
        "proof_candidate_is_proof": False,
    }


def to_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Admissible-Existence Mathematical Completeness Matrix",
        "",
        f"Goal: `{report['goal_id']}`  ",
        f"Registered repositories: **{report['summary']['registered']}**  ",
        f"Source repositories: **{report['summary']['source']}**  ",
        f"Source mathematically complete: **{report['summary']['source_complete']}/{report['summary']['source']}**  ",
        f"Non-source role contracts complete: **{report['summary']['non_source_complete']}/{report['summary']['non_source']}**  ",
        f"Organization mathematical-completeness ready: **{str(report['ready']).lower()}**",
        "",
        "| Repository | Role | Worker state | Formal | Dependency | Theory | Math notation | Derivation | Proof candidate | Falsification | Result |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in report["repositories"]:
        s = row["audit"]["semantic"]
        def mark(v: Any) -> str:
            if v == "N/A": return "N/A"
            return "PASS" if v else "GAP"
        result = "PASS" if row["audit"]["mathematical_complete"] else "GAP"
        lines.append(
            f"| `{row['repository']}` | {row['role']} | `{row['worker_state']}` | {mark(s['formal_declaration'])} | {mark(s['dependency_derivation'])} | {mark(s['whole_repo_theory'])} | {mark(s['mathematical_notation'])} | {mark(s['mathematical_derivation_evidence'])} | {mark(s['proof_candidate'])} | {mark(s['falsification_and_limits'])} | **{result}** |"
        )
    lines += ["", "## Gaps", ""]
    gap_rows = [r for r in report["repositories"] if r["audit"]["gaps"]]
    if not gap_rows:
        lines.append("None.")
    else:
        for row in gap_rows:
            lines.append(f"- `{row['repository']}`: " + ", ".join(row["audit"]["gaps"]))
    lines += [
        "",
        "## Authority boundary",
        "",
        "A proof candidate is not an accepted proof. Routing completion is not mathematical completeness. Support/control-plane repositories are marked N/A only because their declared role is non-source and their role-specific contracts pass.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default="data/formalism-worker-registry.json")
    ap.add_argument("--policy", default="data/mathematical-completeness-policy.json")
    ap.add_argument("--json-out", default="reports/mathematical-completeness-matrix.json")
    ap.add_argument("--md-out", default="reports/mathematical-completeness-matrix.md")
    args = ap.parse_args()

    registry = load_json(args.registry)
    policy = load_json(args.policy)
    token = os.environ.get("GITHUB_TOKEN")
    rows = []
    for entry in registry["repositories"]:
        repo = entry["repository"]
        role = entry["role"]
        branch, tree = fetch_repo_tree(repo, token)
        if role == "source":
            audit = audit_source(repo, tree, token, policy)
        else:
            audit = audit_non_source(repo, role, tree, token, policy)
        rows.append({
            "repository": repo,
            "role": role,
            "worker_state": entry.get("worker_state"),
            "default_branch": branch,
            "audit": audit,
        })
        print(f"{repo}: {'PASS' if audit['mathematical_complete'] else 'GAP'} ({audit['applicability']})")

    source = [r for r in rows if r["role"] == "source"]
    non_source = [r for r in rows if r["role"] != "source"]
    summary = {
        "registered": len(rows),
        "source": len(source),
        "source_complete": sum(r["audit"]["mathematical_complete"] for r in source),
        "non_source": len(non_source),
        "non_source_complete": sum(r["audit"]["mathematical_complete"] for r in non_source),
        "gap_repositories": sum(bool(r["audit"]["gaps"]) for r in rows),
    }
    report = {
        "schema_version": "1.0.0",
        "goal_id": policy["goal_id"],
        "registry_schema_version": registry.get("schema_version"),
        "policy_schema_version": policy.get("schema_version"),
        "ready": summary["source_complete"] == summary["source"] and summary["non_source_complete"] == summary["non_source"],
        "summary": summary,
        "repositories": rows,
        "authority_boundary": policy["authority_boundary"],
    }
    Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_out).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    Path(args.md_out).write_text(to_markdown(report), encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    print(f"ready={str(report['ready']).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
