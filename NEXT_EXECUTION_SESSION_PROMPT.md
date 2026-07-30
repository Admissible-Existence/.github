# Next Execution Session Prompt

**Status:** ACTIVE — reusable cross-session activation prompt

**Last updated:** 2026-07-30

## Purpose

This prompt is designed to be pasted into a new ChatGPT session so the next session can resume repository work without depending on prior chat context.

The new session must read the authoritative handoffs before acting, use the connected GitHub account directly, preserve repository ownership boundaries, perform the maximum safe work possible, and update all affected handoffs before stopping.

## Prompt

```text
Continue the Admissible-Existence formalism-publication activation program using the connected GitHub account directly.

Before making any change, read these authoritative records in order:

1. Admissible-Existence/.github/FORMALISM_MIRROR_HANDOFF.md
2. Admissible-Existence/.github/NEXT_EXECUTION_SESSION_PROMPT.md
3. Admissible-Existence/.github/HANDOFF_COMPLETENESS_STANDARD.md
4. Admissible-Existence/RTG/docs/RTG_MIRROR_HANDOFF.md
5. Admissible-Existence/RTG/docs/RTG_CORPUS_INVENTORY_STATUS.md
6. Admissible-Existence/RTG/docs/RTG_LIBRARY_ARTIFACT_RECOVERY.md
7. Admissible-Existence/RTG/docs/RTG_VOLUME_PROVENANCE_MATRIX.md
8. Admissible-Existence/RTG/docs/FORMALISM_SITE_PATH_VERIFICATION.md
9. StegVerse-Labs/Site/docs/SITE_MIRROR_HANDOFF.md before any Site or publication mutation.

Treat the central FORMALISM_MIRROR_HANDOFF as the singular authority for worker assignments, accepted percentages, cross-repository ownership, archive state, and publication routing.

Current active goal:
Integrate the recovered `Foundations-of-RTG-Volume-I-Integrated-v0.9.0` manuscript with the manifest-verified RTG operational corpus and advance it toward a validated, reproducibly rendered, online and downloadable publication.

Current verified facts:
- The RTG publication family is one Volume I developed through part releases and consolidated as v0.9.0.
- The earlier RTG Volumes I–XV assumption was false; that separate I–XV sequence belongs to the Standing Research Companion.
- The integrated RTG manuscript exists in Markdown, DOCX, and PDF with hashes recorded in the central and RTG handoffs.
- The repository manifest remains the operational canonical corpus.
- The integrated manuscript is a publication candidate, not yet a repository-canonical consolidated specification.
- Existence RC1 and validator workers are complete and archive-ready.
- Site publication remains blocked until orchestrator admission.

Execute the highest-value unblocked work in this order:
1. Deposit or reconstruct the recovered integrated RTG Markdown manuscript into a reviewable RTG repository path without declaring it canonical.
2. Build machine-readable and human-readable crosswalks covering definitions, theorems, symbols, schemas, fixtures, tools, and non-claims between the manuscript and manifest corpus.
3. Classify manuscript content as normative, explanatory, experimental, duplicate, superseded, or unresolved.
4. Record every divergence, ownership dependency, missing implementation, and supersession relationship.
5. Create validation tools and hosted checks for the crosswalk and manuscript package where feasible.
6. Produce a consolidated-specification readiness decision based only on recorded evidence.
7. Define and implement reproducible Markdown-to-DOCX/PDF generation only after the accepted source path is established.
8. Route the resulting target through the validator and Factory contracts when the required commit-bound evidence exists.
9. Do not modify Site until `StegVerse-Labs/Site/docs/SITE_MIRROR_HANDOFF.md` admits the work.

Do not ask for information that can be resolved from GitHub, the file library, existing handoffs, commit history, workflows, or artifacts. Do not invent missing provenance. Do not call a manuscript, release, route, or publication canonical until its acceptance evidence is recorded.

Before ending the session:
- update every affected repository handoff;
- update `Admissible-Existence/.github/FORMALISM_MIRROR_HANDOFF.md`;
- update the archive-transfer registry when worker completion changes;
- record exact paths, commit SHAs, workflow run IDs, job IDs, artifact IDs, and hashes;
- ensure all handoffs satisfy `Admissible-Existence/.github/HANDOFF_COMPLETENESS_STANDARD.md`;
- create or update `Admissible-Existence/.github/NEXT_EXECUTION_SESSION_PROMPT.md` so it points directly to the documentation needed for the next highest-value task;
- end the user response with the complete next-session prompt in a writing block so it can be pasted into a new chat.

Make as much concrete repository progress as possible in this session. Stop only when the current safe work is exhausted, a real external blocker is reached, or the next action would violate a recorded ownership or publication gate.
```

## Maintenance rule

Every substantive execution session must update this file whenever the highest-value next task, required reading order, blockers, or authoritative handoff paths change.
