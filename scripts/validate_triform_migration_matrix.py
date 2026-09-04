#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "data" / "triform-migration-matrix.json"

def main():
    data = json.loads(MATRIX.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    repos = [e.get("repository") for e in entries]
    findings = []
    if data.get("registry_repository_count") != 32:
        findings.append("registry_repository_count_mismatch")
    if len(entries) != 32:
        findings.append("entry_count_mismatch")
    if len(set(repos)) != len(repos):
        findings.append("duplicate_repository")
    if data.get("next_candidate") != "Admissible-Existence/Existence":
        findings.append("unexpected_next_candidate")
    for entry in entries:
        if not entry.get("triform_state"):
            findings.append(f"missing_triform_state:{entry.get('repository')}")
    valid = not findings
    print(json.dumps({"schema":"admissible-existence.triform-migration-validation/v1","valid":valid,"entry_count":len(entries),"next_candidate":data.get("next_candidate"),"findings":findings,"authority_effect":"NONE_VALIDATION_ONLY"}, indent=2, sort_keys=True))
    raise SystemExit(0 if valid else 1)

if __name__ == "__main__":
    main()
