#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "triform-relational-admissibility-manifest.json"
SCHEMA = ROOT / "schemas" / "triform-formalism-manifest.schema.json"
REQUIRED_FORMS = ("prose", "mathematics", "code")
REQUIRED_PRINCIPLE_FIELDS = (
    "principle_id",
    "title",
    "normative",
    "prose_binding",
    "mathematical_binding",
    "code_binding",
    "assumptions",
    "invariants",
    "unknown_class_relevance",
    "witnesses",
    "counterexamples",
    "proof_status",
    "falsification_conditions",
    "equivalence_status",
)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require(condition: bool, findings: list[str], code: str) -> None:
    if not condition:
        findings.append(code)


def binding_path(binding: str) -> str:
    return binding.split("#", 1)[0]


def main() -> int:
    findings: list[str] = []

    require(MANIFEST.exists(), findings, "manifest:missing")
    require(SCHEMA.exists(), findings, "schema:missing")
    if findings:
        print(json.dumps({"valid": False, "findings": findings}, indent=2))
        return 1

    manifest = load_json(MANIFEST)
    schema = load_json(SCHEMA)

    require(manifest.get("schema_version") == "1.0.0", findings, "manifest:invalid_schema_version")
    require(manifest.get("authority_effect") == "NONE_VALIDATION_ONLY", findings, "manifest:authority_effect_must_be_none_validation_only")
    require(isinstance(schema, dict) and schema.get("title") == "Tri-Form Formalism Manifest", findings, "schema:unexpected_title")

    forms = manifest.get("forms", {})
    for form in REQUIRED_FORMS:
        entry = forms.get(form)
        require(isinstance(entry, dict), findings, f"forms:{form}:missing")
        if not isinstance(entry, dict):
            continue
        paths = entry.get("paths")
        require(isinstance(paths, list) and len(paths) > 0, findings, f"forms:{form}:paths_missing")
        if isinstance(paths, list):
            for raw in paths:
                require(isinstance(raw, str) and raw != "", findings, f"forms:{form}:invalid_path")
                if isinstance(raw, str) and raw:
                    require((ROOT / raw).exists(), findings, f"forms:{form}:path_missing:{raw}")

    principles = manifest.get("principles")
    require(isinstance(principles, list) and len(principles) > 0, findings, "principles:missing")
    seen: set[str] = set()
    if isinstance(principles, list):
        for index, principle in enumerate(principles):
            prefix = f"principles:{index}"
            require(isinstance(principle, dict), findings, f"{prefix}:not_object")
            if not isinstance(principle, dict):
                continue
            for field in REQUIRED_PRINCIPLE_FIELDS:
                require(field in principle, findings, f"{prefix}:missing:{field}")
            pid = principle.get("principle_id")
            require(isinstance(pid, str) and pid != "", findings, f"{prefix}:invalid_principle_id")
            if isinstance(pid, str) and pid:
                require(pid not in seen, findings, f"principles:duplicate_id:{pid}")
                seen.add(pid)

            for field in ("prose_binding", "mathematical_binding", "code_binding"):
                raw = principle.get(field)
                require(isinstance(raw, str) and raw != "", findings, f"{prefix}:invalid:{field}")
                if isinstance(raw, str) and raw:
                    path = binding_path(raw)
                    require((ROOT / path).exists(), findings, f"{prefix}:binding_path_missing:{field}:{path}")

            for field in ("assumptions", "invariants", "witnesses", "counterexamples", "falsification_conditions"):
                require(isinstance(principle.get(field), list), findings, f"{prefix}:invalid_list:{field}")

            if principle.get("normative") is True:
                require(bool(principle.get("assumptions")), findings, f"{prefix}:normative_assumptions_empty")
                require(bool(principle.get("invariants")), findings, f"{prefix}:normative_invariants_empty")
                require(bool(principle.get("witnesses")), findings, f"{prefix}:normative_witnesses_empty")
                require(bool(principle.get("falsification_conditions")), findings, f"{prefix}:normative_falsification_empty")
                require(principle.get("equivalence_status") in {"BOUND_CANDIDATE", "TRIFORM_BOUND"}, findings, f"{prefix}:normative_not_bound_candidate")

            for witness in principle.get("witnesses", []) if isinstance(principle.get("witnesses"), list) else []:
                if isinstance(witness, str) and witness:
                    require((ROOT / binding_path(witness)).exists(), findings, f"{prefix}:witness_missing:{witness}")

    expected_axioms = {f"A{i}" for i in range(1, 10)}
    require(expected_axioms.issubset(seen), findings, "pilot:missing_A1_A9")

    # Structural validation alone cannot award TRIFORM_BOUND.
    if manifest.get("maturity") == "TRIFORM_BOUND":
        require(all(p.get("equivalence_status") == "TRIFORM_BOUND" for p in principles), findings, "maturity:triform_bound_without_all_principles_bound")

    valid = not findings
    result = {
        "schema": "admissible-existence.triform-validation/v1",
        "formalism_id": manifest.get("formalism_id"),
        "valid": valid,
        "principle_count": len(principles) if isinstance(principles, list) else 0,
        "principle_ids": sorted(seen),
        "maturity": manifest.get("maturity"),
        "authority_effect": "NONE_VALIDATION_ONLY",
        "findings": findings,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
