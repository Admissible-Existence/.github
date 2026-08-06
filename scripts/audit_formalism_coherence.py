#!/usr/bin/env python3
"""Fail-closed principle-completeness audit for Admissible-Existence.

The worker dynamically discovers every non-archived organization repository and
scores durable evidence against the organization principle-completeness standard.
It detects gaps and routes work; it never creates source-formalism authority.
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "principle-completeness-latest.json"
MARKDOWN_OUTPUT = ROOT / "reports" / "principle-completeness-latest.md"
LEGACY_OUTPUT = ROOT / "reports" / "formalism-coherence-latest.json"
ORG = "Admissible-Existence"

DIMENSIONS = (
    "identity",
    "purpose",
    "theory",
    "mathematics",
    "formal_status",
    "falsification",
    "dependencies",
    "whole_repo_role",
    "ecosystem_relationships",
    "executable_correspondence",
    "evidence_binding",
    "handoff_binding",
)
SOURCE_HINTS = {
    "AE", "Existence", "RTG", "GTG", "TT", "STCM", "IW", "BC", "RE",
    "CHF", "DC", "DaCo", "RE-Reduction", "Triad", "GCAT-BCAT",
    "ECAT-ICAT", "learning-transition-governance", "standing-proof-formalism",
    "IICT", "CTA", "HPS", "FI", "SOL", "ET",
}
SUPPORT_HINTS = {
    "core-lite", "validator", "tracker", "telemetry", "ae-validation-factory",
    "ae-validation-research", "validation-profile-registry",
}
COORDINATION_HINTS = {".github"}

PLACEHOLDER_RE = re.compile(r"\b(TODO|FIXME|TBD|PLACEHOLDER|STUB|PENDING|NOT IMPLEMENTED)\b", re.I)
LINK_RE = re.compile(r"\[[^\]]+\]\((?!https?://|mailto:|#)([^)]+)\)")
FQ_REPO_RE = re.compile(r"\bAdmissible-Existence/[A-Za-z0-9_.-]+\b")
PRINCIPLE_RE = re.compile(
    r"^#{1,6}\s+(?:(?:principle|axiom|definition|invariant|theorem|lemma|proposition|postulate|law)\s*[:—-]?\s*)?"
    r"([A-Za-z0-9][^#\n]{1,140})$",
    re.I | re.M,
)
SIGNALS = {
    "identity": re.compile(r"\b(identifier|principle id|stable id|canonical statement|definition)\b", re.I),
    "purpose": re.compile(r"\b(purpose|governing claim|intent|why this exists|objective)\b", re.I),
    "theory": re.compile(r"\b(theory|domain|codomain|assumption|object|state space|semantics)\b", re.I),
    "mathematics": re.compile(r"(\\begin\{|\\forall|\\exists|\$[^$]+\$|:=|⇒|→|∈|≤|≥|\b(equation|metric|function|operator|set)\b)", re.I),
    "formal_status": re.compile(r"\b(axiom|theorem|lemma|proposition|hypothesis|conjecture|proof status|review required|proved|unproved)\b", re.I),
    "falsification": re.compile(r"\b(falsif|counterexample|invalidat|failure condition|limit(?:ation)?s?|non-claim)\b", re.I),
    "dependencies": re.compile(r"\b(dependenc|upstream|downstream|predecessor|successor|requires|composes with)\b", re.I),
    "whole_repo_role": re.compile(r"\b(whole[- ]repo|repository role|broader picture|overall theory|contributes to|unifying)\b", re.I),
    "ecosystem_relationships": re.compile(r"\b(ecosystem|cross[- ]repository|interoperab|relationship map|Admissible-Existence/)\b", re.I),
    "executable_correspondence": re.compile(r"\b(validator|fixture|executable|implementation|algorithm|workflow|test|schema)\b", re.I),
    "evidence_binding": re.compile(r"\b(sha-?256|commit|blob|hash|receipt|evidence binding|digest)\b", re.I),
    "handoff_binding": re.compile(r"\bmirror handoff\b|_MIRROR_HANDOFF\.md", re.I),
}


def api(path: str, token: str) -> Any:
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "aex-principle-completeness-worker",
        },
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.load(response)


def paged(path: str, token: str) -> list[Any]:
    items: list[Any] = []
    page = 1
    separator = "&" if "?" in path else "?"
    while True:
        batch = api(f"{path}{separator}per_page=100&page={page}", token)
        if not isinstance(batch, list):
            raise TypeError(f"Expected list response for {path}")
        items.extend(batch)
        if len(batch) < 100:
            return items
        page += 1


def fetch_text(repo: str, path: str, token: str) -> str:
    encoded = urllib.parse.quote(path, safe="/")
    data = api(f"/repos/{ORG}/{repo}/contents/{encoded}", token)
    return base64.b64decode(data["content"]).decode("utf-8", errors="replace")


def normalize_link(source: str, target: str) -> str:
    target = target.split("#", 1)[0].split("?", 1)[0]
    if not target:
        return ""
    return str((Path(source).parent / target).as_posix()).replace("//", "/")


def classify_role(repo: str, file_count: int) -> str:
    if file_count == 0:
        return "empty"
    if repo in COORDINATION_HINTS:
        return "coordination"
    if repo in SUPPORT_HINTS:
        return "support"
    return "source" if repo in SOURCE_HINTS else "unclassified"


def dimension_scores(texts: Iterable[str], handoffs: list[str], role: str) -> dict[str, bool]:
    combined = "\n".join(texts)
    scores = {name: bool(pattern.search(combined)) for name, pattern in SIGNALS.items()}
    scores["handoff_binding"] = bool(handoffs) and scores["handoff_binding"]
    if role in {"support", "coordination"}:
        # Support repos do not need original theorems, but must define bounded
        # coverage and non-authority. These signals remain mandatory evidence.
        scores["formal_status"] = scores["formal_status"] or bool(
            re.search(r"\b(non-authority|does not create authority|bounded support)\b", combined, re.I)
        )
        scores["mathematics"] = scores["mathematics"] or bool(
            re.search(r"\b(coverage matrix|mapping function|validation predicate|score)\b", combined, re.I)
        )
    return scores


def completion_state(role: str, scores: dict[str, bool], placeholders: int, broken_links: int) -> str:
    if role == "empty":
        return "EMPTY"
    met = sum(scores.values())
    if placeholders or broken_links or not scores["handoff_binding"]:
        return "BLOCKED"
    if met == len(DIMENSIONS):
        return "COMPLETE_CANDIDATE"
    if scores["theory"] and scores["mathematics"]:
        return "FORMALIZED_UNVALIDATED"
    if met >= len(DIMENSIONS) // 2:
        return "REVIEW_REQUIRED"
    return "SCAFFOLD"


def audit_repo(metadata: dict[str, Any], token: str) -> dict[str, Any]:
    repo = metadata["name"]
    result: dict[str, Any] = {
        "repository": f"{ORG}/{repo}",
        "default_branch": metadata.get("default_branch", "main"),
        "role": "unclassified",
        "state": "BLOCKED",
        "score": 0.0,
        "dimensions": {name: False for name in DIMENSIONS},
        "principles": [],
        "findings": [],
        "metrics": {},
        "next_task": None,
    }
    try:
        branch = result["default_branch"]
        tree = api(f"/repos/{ORG}/{repo}/git/trees/{branch}?recursive=1", token)
        blobs = [item for item in tree.get("tree", []) if item.get("type") == "blob"]
        paths = {item["path"] for item in blobs}
        markdown = sorted(p for p in paths if p.lower().endswith((".md", ".markdown")))
        structured = sorted(p for p in paths if p.lower().endswith((".yaml", ".yml", ".json")))
        handoffs = sorted(p for p in paths if p.endswith("_MIRROR_HANDOFF.md"))
        role = classify_role(repo, len(paths))
        result["role"] = role

        texts: list[str] = []
        principle_records: dict[str, dict[str, Any]] = {}
        placeholders = 0
        broken_links: list[dict[str, str]] = []
        ambiguous_repo_refs: set[str] = set()

        for path in markdown[:400]:
            text = fetch_text(repo, path, token)
            texts.append(text)
            placeholders += len(PLACEHOLDER_RE.findall(text))
            for label in PRINCIPLE_RE.findall(text):
                normalized = re.sub(r"\s+", " ", label.strip())
                if normalized.lower() in {"purpose", "status", "scope", "overview", "introduction"}:
                    continue
                principle_records.setdefault(normalized, {"label": normalized, "sources": []})["sources"].append(path)
            for target in LINK_RE.findall(text):
                normalized = normalize_link(path, target)
                if normalized and normalized not in paths and not normalized.endswith("/"):
                    broken_links.append({"source": path, "target": target})
            for short in re.findall(r"(?<![/\w])(AE|RTG|GTG|TT|STCM|IW|BC|RE|CHF|DC|DaCo)(?![/\w])", text):
                if f"{ORG}/{short}" not in text:
                    ambiguous_repo_refs.add(short)

        scores = dimension_scores(texts, handoffs, role)
        state = completion_state(role, scores, placeholders, len(broken_links))
        met = sum(scores.values())
        result["dimensions"] = scores
        result["score"] = round(100.0 * met / len(DIMENSIONS), 2)
        result["state"] = state
        result["principles"] = sorted(principle_records.values(), key=lambda x: x["label"].lower())
        result["metrics"] = {
            "files": len(paths),
            "markdown_files": len(markdown),
            "structured_files": len(structured),
            "handoffs": len(handoffs),
            "principle_candidates": len(principle_records),
            "placeholder_markers": placeholders,
            "broken_local_links": len(broken_links),
            "ambiguous_short_repository_identities": len(ambiguous_repo_refs),
            "dimensions_met": met,
            "dimensions_total": len(DIMENSIONS),
        }

        if not handoffs:
            result["findings"].append({"severity": "error", "code": "MISSING_HANDOFF"})
        if role == "empty":
            result["findings"].append({"severity": "error", "code": "EMPTY_ACTIVE_REPOSITORY"})
        if role == "unclassified":
            result["findings"].append({"severity": "error", "code": "UNCLASSIFIED_REPOSITORY_ROLE"})
        if role == "source" and not principle_records:
            result["findings"].append({"severity": "error", "code": "NO_PRINCIPLE_INVENTORY"})
        for dimension, present in scores.items():
            if not present:
                result["findings"].append({"severity": "error", "code": f"MISSING_{dimension.upper()}"})
        if placeholders:
            result["findings"].append({"severity": "error", "code": "UNRESOLVED_PLACEHOLDERS", "count": placeholders})
        if broken_links:
            result["findings"].append({"severity": "error", "code": "BROKEN_LOCAL_LINKS", "examples": broken_links[:20]})
        if ambiguous_repo_refs:
            result["findings"].append({
                "severity": "warning",
                "code": "AMBIGUOUS_SHORT_REPOSITORY_IDENTITIES",
                "identities": sorted(ambiguous_repo_refs),
            })
        if state == "COMPLETE_CANDIDATE":
            result["findings"].append({
                "severity": "warning",
                "code": "INDEPENDENT_REVIEW_REQUIRED",
                "detail": "Automated signal coverage cannot establish proof correctness or release authority.",
            })

        if state != "COMPLETE_CANDIDATE":
            target = handoffs[-1] if handoffs else f"docs/{repo.upper()}_MIRROR_HANDOFF.md"
            result["next_task"] = {
                "owner": f"{ORG}/{repo}",
                "target": target,
                "action": "Resolve the first listed blocking completeness finding without duplicating active claims",
                "release_condition": "All twelve dimensions are evidenced and independently reviewed",
            }
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError, TypeError) as exc:
        result["findings"].append({"severity": "error", "code": "REPOSITORY_INACCESSIBLE_OR_API_FAILURE", "detail": str(exc)})
        result["next_task"] = {
            "owner": f"{ORG}/{repo}",
            "target": "repository access / worker credential",
            "action": "Restore machine-readable access and rerun audit",
            "release_condition": "Repository tree and evidence are readable",
        }
    return result


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Admissible-Existence Principle Completeness Report",
        "",
        f"Generated: `{summary['generated_at']}`",
        "",
        "Automated coverage is diagnostic only. `COMPLETE_CANDIDATE` still requires independent mathematical and proof review.",
        "",
        "| Repository | Role | State | Score | Principles | First gap |",
        "|---|---|---:|---:|---:|---|",
    ]
    for repo in summary["repositories"]:
        first = repo["findings"][0]["code"] if repo["findings"] else "NONE"
        lines.append(
            f"| `{repo['repository']}` | {repo['role']} | {repo['state']} | "
            f"{repo['score']:.2f}% | {repo['metrics'].get('principle_candidates', 0)} | `{first}` |"
        )
    lines.extend([
        "",
        "## Organization result",
        "",
        f"- Repositories audited: **{summary['repository_count']}**",
        f"- Complete candidates: **{summary['state_counts'].get('COMPLETE_CANDIDATE', 0)}**",
        f"- Proven complete: **0** (independent review is not performed by this worker)",
        f"- Mean diagnostic coverage: **{summary['organization_score']:.2f}%**",
        "- Publication authorized: **false**",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    token = os.environ.get("STEGVERSE_WORKER_TOKEN") or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("No GitHub token available; fail closed.", file=sys.stderr)
        return 2

    repositories = [r for r in paged(f"/orgs/{ORG}/repos?type=all", token) if not r.get("archived")]
    repositories.sort(key=lambda r: r["name"].lower())
    results = [audit_repo(repo, token) for repo in repositories]
    states = sorted({r["state"] for r in results} | {"COMPLETE_CANDIDATE", "BLOCKED", "EMPTY", "SCAFFOLD", "REVIEW_REQUIRED", "FORMALIZED_UNVALIDATED"})
    summary = {
        "schema_version": "2.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "goal_id": "AEX-PRINCIPLE-COMPLETENESS-001",
        "repository_count": len(results),
        "dimension_count": len(DIMENSIONS),
        "state_counts": {state: sum(r["state"] == state for r in results) for state in states},
        "organization_score": round(sum(r["score"] for r in results) / len(results), 2) if results else 0.0,
        "repositories": results,
        "publication_authorized": False,
        "publication_rule": "Diagnostic signal coverage does not establish mathematical correctness, canonicality, or release authority.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    MARKDOWN_OUTPUT.write_text(render_markdown(summary), encoding="utf-8")
    # Preserve the legacy path for existing dispatch consumers while they migrate.
    LEGACY_OUTPUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"repositories": len(results), "states": summary["state_counts"]}, sort_keys=True))
    return 1 if any(r["state"] != "COMPLETE_CANDIDATE" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
