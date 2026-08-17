#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMALISM = ROOT / "data" / "relational-admissibility-formalism.json"
DOC = ROOT / "docs" / "MINIMUM_ADMISSIBLE_TRANSITION_SET.md"
CLAIM = ROOT / "data" / "relational-admissibility-minimum-set-claim.json"
MINIMUM = {"DENY", "REVIEW", "FAIL_CLOSED"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    for path in (FORMALISM, DOC, CLAIM):
        require(path.is_file(), f"missing required file: {path.relative_to(ROOT)}")

    formalism = json.loads(FORMALISM.read_text(encoding="utf-8"))
    claim = json.loads(CLAIM.read_text(encoding="utf-8"))
    text = DOC.read_text(encoding="utf-8")

    declared = set(formalism.get("minimum_required_admissible_transition_classes") or [])
    require(MINIMUM <= declared, "formalism omits a mandatory minimum admissible transition class")
    require(formalism.get("resolution_classes_are_extensible") is True, "minimum set must remain extensible")
    requirements = formalism.get("conformance_requirements") or {}
    require(requirements.get("minimum_admissible_transition_set_required") is True, "minimum set must be a conformance requirement")

    claim_set = set(claim.get("minimum_required_admissible_transition_classes") or [])
    require(MINIMUM <= claim_set, "claim omits mandatory minimum set")
    require(claim.get("additional_classes_allowed") is True, "claim must preserve extension classes")

    for value in MINIMUM:
        require(value in text, f"human formalism omits {value}")
    require("minimum set, not an exhaustive set" in text, "human formalism must state non-exhaustiveness")
    require("DENY != no transition" in text, "DENY null-transition compression forbidden")
    require("REVIEW != no transition" in text, "REVIEW null-transition compression forbidden")
    require("FAIL_CLOSED != no transition" in text, "FAIL_CLOSED null-transition compression forbidden")
    require(formalism.get("admissibility_resolver") == "Admissible-Existence/AE", "AE must remain resolver")
    require(formalism.get("credential_authority_for_stegverse_runtime") == "TV/TVC", "TV/TVC credential boundary required")
    require(formalism.get("github_token_runtime_authority") == "NONE", "GitHub token runtime authority must be NONE")

    print(json.dumps({
        "schema": "admissible-existence.minimum-admissible-transition-set-validation/v1",
        "valid": True,
        "minimum_required_admissible_transition_classes": sorted(MINIMUM),
        "additional_classes_allowed": True,
        "admissibility_resolver": "Admissible-Existence/AE",
        "authority_effect": "NONE_VALIDATION_ONLY"
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
