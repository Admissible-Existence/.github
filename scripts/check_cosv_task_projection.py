#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
idx=json.loads((ROOT/"data/cosv/task-vector-index.json").read_text())
claims=json.loads((ROOT/"data/formalism-task-claims.json").read_text())
worker=json.loads((ROOT/"data/principle-completeness-worker-claim.json").read_text())
observer=json.loads((ROOT/"data/principle-worker-activation-observer-claim.json").read_text())
verfi=json.loads((ROOT/"data/task-states/verfi-external-formalism.json").read_text())
cross=json.loads((ROOT/"data/cross-repository-remediation-registry.json").read_text())

assert idx["profile"]=="task.v1"
assert idx["width"]==14
assert idx["notation"]=="L R U I V G O C M T B E A P"
assert idx["authority_effect"]=="NONE"

rows={x["task_id"]:x for x in idx["tasks"]}
expected={
 "AEX-ORG-COHERENCE-AUDIT":"60000000101000",
 "AEX-PC-AUTOMATED-WORKERS-001":"50000000101000",
 "AEX-MATHEMATICAL-COMPLETENESS-AUDIT-002":"50000000109000",
 "AEX-CROSS-REPOSITORY-REMEDIATION-001":"40000000104000",
 "HB-RESPONSE-ORG-NODE-0001":"50000000100110",
}
assert set(rows)==set(expected)
for task_id, vector in expected.items():
    assert rows[task_id]["vector"]==vector
    p=ROOT/rows[task_id]["vector_ref"]
    assert p.exists(), p
    v=json.loads(p.read_text())
    assert v["identity"]==f"Admissible-Existence/.github:task:{task_id}"
    assert v["profile"]=="task.v1" and v["level"]=="task"
    assert v["vector"]==vector and len(vector)==14
    assert v["authority_effect"]=="NONE"
    assert v["exact_metrics"]["symbol_order"]=="LRUIVGOCMTBEAP"

claim_rows={x["task_id"]:x for x in claims["tasks"]}
assert claim_rows["AEX-ORG-COHERENCE-AUDIT"]["claim_state"]=="BLOCKED"
assert claim_rows["AEX-ORG-COHERENCE-AUDIT"]["claim_expires_at"]>"2026-08-31T16:52:00Z"
assert worker["claim_state"]=="ACTIVE"
assert observer["claim_state"]=="COMPLETE_RELEASED"
assert observer["completion_state"]=="COMPLETE_READ_ONLY_WORKER_EVIDENCE"
assert verfi["claim_state"]=="COMPLETE_RELEASED"
assert verfi["completion"]["percent"]==100
assert cross["state"]=="ACTIVE"

# Expired historical claims are not active under the repository's own semantics.
assert claims["claim_semantics"]["expired_claim_without_renewal_is_active"] is False

cov=idx["coverage"]
assert cov["current_structured_active_tasks_audited"]==5
assert cov["current_structured_active_tasks_projected"]==5
assert cov["current_structured_active_task_gap"]==0
assert cov["repository_active_task_surface_audit_complete"] is True
assert cov["repository_vector_present_claimed"] is True
print("AEX_GITHUB_COSV_PROJECTION_PASS active_tasks=5 projected=5 gap=0")
