# Handoff Completeness Standard

**Status:** ACTIVE — mandatory continuity standard

**Last updated:** 2026-07-30

## Purpose

A repository handoff must allow a new execution session to continue correctly without access to the originating chat. A handoff is incomplete when it records only status or percentages but omits the history, evidence, goals, ownership boundaries, blockers, or next executable actions needed to proceed.

## Required content

Every active repository or program handoff must contain, directly or through explicit linked records:

1. **Authority and scope**
   - repository, worker, and task identifiers;
   - local authority and explicit non-authority boundaries;
   - the singular coordination authority controlling cross-repository percentages and routing.

2. **Relevant history**
   - material prior decisions and corrections;
   - resolved misconceptions or rejected assumptions;
   - supersession relationships;
   - completed tasks that constrain later work.

3. **Current verified state**
   - exact paths and repository roles;
   - verified files, schemas, fixtures, tools, workflows, and artifacts;
   - commit SHAs, hashes, run IDs, job IDs, artifact IDs, and conclusions when available;
   - facts distinguished from inference and unresolved claims.

4. **Current goal and end goal**
   - the immediate repository goal;
   - its place in the governing program sequence;
   - the final intended state, including validation, publication, custody, or destination receipts.

5. **Ownership and dependency boundaries**
   - what the repository owns;
   - what adjacent repositories own;
   - required upstream and downstream contracts;
   - publication, execution, and certification prohibitions.

6. **Active work and executable order**
   - completed steps;
   - remaining steps in priority order;
   - the highest-value currently unblocked action;
   - safe parallel work and unsafe competing work.

7. **Blockers and admission conditions**
   - genuine external blockers;
   - missing evidence;
   - conditions required before release, canonicalization, Site mutation, or archive readiness.

8. **Completion accounting**
   - task completion percentage;
   - developed-files percentage;
   - goal-activation percentage;
   - archive-transfer state and source-session dependency.

9. **Continuation prompt linkage**
   - a direct link to `Admissible-Existence/.github/NEXT_EXECUTION_SESSION_PROMPT.md`;
   - the exact additional handoffs the next session must read for the active task.

## Evidence rules

- No status may be upgraded from an unobserved workflow, missing file, inferred filename, or unverified public route.
- A hosted workflow trigger is not a successful validation result until a terminal conclusion and relevant job steps are observed.
- A generated or downloaded manuscript is not repository-canonical until deposited, crosswalked, validated, accepted, and recorded.
- A repository-local completion claim cannot change program-wide percentages unless accepted by the Repository Coordination Authority.
- Workflow artifacts are not permanent custody unless deposited into the target repository or Master-Records under the applicable contract.
- Site publication may not bypass the current Site handoff and orchestrator admission.

## Session-close rule

Before ending substantive work, the executing session must:

1. update affected local handoffs;
2. update the central formalism handoff;
3. update the archive-transfer registry when applicable;
4. update the reusable next-session prompt;
5. verify that the next prompt names the exact documentation paths needed for continuation;
6. include the complete paste-ready prompt at the end of the user-facing response.

## Failure posture

When a required fact cannot be verified, record it as unresolved and identify the exact evidence needed. Never fill continuity gaps with plausible narrative.
