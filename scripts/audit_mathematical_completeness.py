#!/usr/bin/env python3
"""Build the organization mathematical-completeness matrix from durable repository-local evidence.

Private sibling repositories cannot be inspected by the .github workflow token. Each repository therefore
self-audits locally and the coordination repo records the inspected receipt/run evidence here. Missing evidence
remains PENDING. A proof candidate is never promoted to proof by this auditor.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any

SOURCE_FIELDS = [
    "formal_declaration",
    "dependency_derivation",
    "whole_repo_theory",
    "mathematical_notation",
    "mathematical_derivation_evidence",
    "proof_candidate",
    "falsification_and_limits",
]


def load(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def source_audit(evidence: dict[str, Any] | None) -> dict[str, Any]:
    if not evidence:
        return {
            "state": "PENDING_EVIDENCE",
            "semantic": {k: False for k in SOURCE_FIELDS},
            "gaps": ["repository_local_self_audit_evidence"],
            "mathematical_complete": False,
            "proof_candidate_is_proof": False,
        }
    semantic = {k: bool(evidence.get(k, False)) for k in SOURCE_FIELDS}
    gaps = [k for k, ok in semantic.items() if not ok]
    if evidence.get("state") != "PASS":
        gaps.append("evidence_state_not_pass")
    if evidence.get("conclusion") != "success":
        gaps.append("hosted_self_audit_not_success")
    if evidence.get("execution_authorized") is not False:
        gaps.append("execution_authority_boundary")
    if not evidence.get("receipt") or not evidence.get("receipt_blob"):
        gaps.append("receipt_binding")
    if not evidence.get("handoff") or not evidence.get("handoff_commit"):
        gaps.append("handoff_binding")
    return {
        "state": evidence.get("state", "PENDING_EVIDENCE"),
        "semantic": semantic,
        "gaps": sorted(set(gaps)),
        "mathematical_complete": not gaps,
        "proof_candidate_is_proof": False,
        "proof_maturity": evidence.get("proof_maturity"),
        "evidence": evidence,
    }


def non_source_audit(repo: str, role: str, evidence: dict[str, Any] | None, worker_state: str | None) -> dict[str, Any]:
    # Mathematics/proof is intentionally non-applicable to non-source roles. The row still requires durable
    # role-completion evidence; until that evidence is recorded in this registry, the row remains pending.
    if evidence and evidence.get("state") == "PASS" and evidence.get("role_contract_complete") is True:
        gaps = []
        state = "PASS"
    else:
        # Existing completed/deprecated routing is not by itself enough to prove the clarified role contract.
        gaps = ["role_specific_completeness_evidence"]
        state = "PENDING_EVIDENCE"
    return {
        "state": state,
        "semantic": {k: "N/A" for k in SOURCE_FIELDS},
        "na_rationale": evidence.get("na_rationale") if evidence else (
            "Non-source repository: mathematics and independent proof candidates are not required; the repository must instead prove its declared support, coordination, observation, integration, or disposition role without creating source authority."
        ),
        "gaps": gaps,
        "mathematical_complete": not gaps,
        "proof_candidate_is_proof": False,
        "worker_state": worker_state,
        "evidence": evidence,
    }


def markdown(report: dict[str, Any]) -> str:
    s = report["summary"]
    lines = [
        "# Admissible-Existence Mathematical Completeness Matrix",
        "",
        f"Goal: `{report['goal_id']}`  ",
        f"Registered: **{s['registered']}**  ",
        f"Source PASS: **{s['source_complete']}/{s['source']}**  ",
        f"Non-source role-contract PASS: **{s['non_source_complete']}/{s['non_source']}**  ",
        f"Pending/GAP repositories: **{s['gap_repositories']}**  ",
        f"Organization ready: **{str(report['ready']).lower()}**",
        "",
        "| Repository | Role | Worker state | Formal | Dependency | Theory | Math | Derivation | Proof candidate | Falsification | Result |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    def mark(value: Any) -> str:
        if value == "N/A": return "N/A"
        return "PASS" if value else "PENDING"
    for row in report["repositories"]:
        sem = row["audit"]["semantic"]
        result = "PASS" if row["audit"]["mathematical_complete"] else row["audit"]["state"]
        lines.append(
            f"| `{row['repository']}` | {row['role']} | `{row.get('worker_state')}` | {mark(sem['formal_declaration'])} | {mark(sem['dependency_derivation'])} | {mark(sem['whole_repo_theory'])} | {mark(sem['mathematical_notation'])} | {mark(sem['mathematical_derivation_evidence'])} | {mark(sem['proof_candidate'])} | {mark(sem['falsification_and_limits'])} | **{result}** |"
        )
    lines += ["", "## Open evidence/gaps", ""]
    for row in report["repositories"]:
        if row["audit"]["gaps"]:
            lines.append(f"- `{row['repository']}`: " + ", ".join(row["audit"]["gaps"]))
    lines += [
        "",
        "## Non-negotiable boundary",
        "",
        "Routing completion is not mathematical completeness. A proof candidate is not an accepted proof. Non-source mathematics is N/A only when the role-specific completeness evidence is itself durable and PASS.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default="data/formalism-worker-registry.json")
    ap.add_argument("--evidence", default="data/mathematical-completeness-evidence-registry.json")
    ap.add_argument("--policy", default="data/mathematical-completeness-policy.json")
    ap.add_argument("--json-out", default="reports/mathematical-completeness-matrix.json")
    ap.add_argument("--md-out", default="reports/mathematical-completeness-matrix.md")
    args = ap.parse_args()

    registry = load(args.registry)
    evidence_registry = load(args.evidence)
    policy = load(args.policy)
    evidence_map = evidence_registry.get("repositories", {})
    rows = []
    for entry in registry["repositories"]:
        repo = entry["repository"]
        role = entry["role"]
        evidence = evidence_map.get(repo)
        audit = source_audit(evidence) if role == "source" else non_source_audit(repo, role, evidence, entry.get("worker_state"))
        rows.append({"repository": repo, "role": role, "worker_state": entry.get("worker_state"), "audit": audit})
        print(f"{repo}: {'PASS' if audit['mathematical_complete'] else audit['state']}")

    source = [r for r in rows if r["role"] == "source"]
    non_source = [r for r in rows if r["role"] != "source"]
    summary = {
        "registered": len(rows),
        "source": len(source),
        "source_complete": sum(r["audit"]["mathematical_complete"] for r in source),
        "non_source": len(non_source),
        "non_source_complete": sum(r["audit"]["mathematical_complete"] for r in non_source),
        "gap_repositories": sum(not r["audit"]["mathematical_complete"] for r in rows),
    }
    ready = summary["source_complete"] == summary["source"] and summary["non_source_complete"] == summary["non_source"]
    report = {
        "schema_version": "2.0.0",
        "goal_id": policy["goal_id"],
        "registry_schema_version": registry.get("schema_version"),
        "evidence_registry_schema_version": evidence_registry.get("schema_version"),
        "policy_schema_version": policy.get("schema_version"),
        "ready": ready,
        "summary": summary,
        "repositories": rows,
        "authority_boundary": policy["authority_boundary"],
    }
    Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_out).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    Path(args.md_out).write_text(markdown(report), encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    print(f"ready={str(ready).lower()}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
