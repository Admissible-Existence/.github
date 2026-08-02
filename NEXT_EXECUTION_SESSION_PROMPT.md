# Next Execution Session Prompt

**Status:** ACTIVE  
**Updated:** 2026-08-02

```text
Continue `AEX-FORMALISM-PUBLICATION-ACTIVATION-001` using the connected GitHub account directly.

Treat live repository state, Git history, committed receipts, workflow runs, jobs, logs, artifacts, immutable blobs, deployment observations, and current handoffs as authoritative over previous chat claims.

Read first, in order:

1. Admissible-Existence/.github/FORMALISM_MIRROR_HANDOFF.md
2. Admissible-Existence/.github/NEXT_EXECUTION_SESSION_PROMPT.md
3. Admissible-Existence/.github/HANDOFF_COMPLETENESS_STANDARD.md
4. Admissible-Existence/RTG/docs/RTG_MIRROR_HANDOFF.md
5. Admissible-Existence/RTG/review/volume-I-integrated-v0.9.0/machine-execution/task-registry.json
6. Admissible-Existence/RTG/review/volume-I-integrated-v0.9.0/machine-execution/lane-3-observation.json
7. Admissible-Existence/RTG/review/volume-I-integrated-v0.9.0/machine-execution/lane-4-observation.json
8. Admissible-Existence/RTG/review/volume-I-integrated-v0.9.0/machine-execution/lane-5-observation.json
9. Admissible-Existence/RTG/review/volume-I-integrated-v0.9.0/machine-execution/readiness-observation.json
10. Admissible-Existence/RTG/review/volume-I-integrated-v0.9.0/machine-execution/evidence-closure-ledger.json
11. Admissible-Existence/RTG/review/volume-I-integrated-v0.9.0/machine-execution/predecessor-lineage-application-receipt.json
12. Admissible-Existence/RTG/.github/workflows/render-rtg-volume-i.yml
13. Admissible-Existence/RTG/tools/render_rtg_volume_i.sh
14. Admissible-Existence/RTG/tools/advance_evidence_closure.py
15. Admissible-Existence/RTG/.github/workflows/advance-evidence-closure.yml
16. Admissible-Existence/RTG/tools/advance_formalism_lanes.py
17. Admissible-Existence/RTG/tools/converge_formalism_publication.py
18. StegVerse-Labs/Site/docs/SITE_MIRROR_HANDOFF.md before any Site mutation.

Current verified state:

- RTG manuscript is deposited and hash-bound.
- Statement inventory contains 131 records.
- Lane 4 is `BOUNDED_LINEAGE_APPLIED`.
- Application receipt records 131 resolved, 121 predecessor-present, 10 new, 0 unresolved.
- Run 30736323253: lineage application PASS; validator defect exposed.
- Run 30736411157: lineage application PASS; validator PASS; stale archive-recovery path exposed in lane executor.
- `tools/advance_formalism_lanes.py` repair commit: dc201d9a1247f78054f220c1b157da7032eb9281.
- Lane-3 hosted render generation 2 trigger commit: f58de3d33052241c00b107cae1dc8042b73ed06a.
- At the previous handoff update, `review/volume-I-integrated-v0.9.0/render-attempt-receipt.json` was absent and no terminal render result was claimed.
- Lane-5 executor commit: 86c8581cfd04d7cb441baa87278ff445b4042a3b.
- Lane-5 workflow commit: c018751335e136b63c40b0f6f75e947c7be5c445.
- At the previous handoff update, neither `evidence-closure-execution-receipt.json` nor `evidence-closure-attempt.json` was present; no hosted lane-5 result was claimed.
- Site review-only projection is active; no canonical publication, release, or AE authority is granted.
- There are no external or manual tasks.

Execute in this order:

1. Fetch `Admissible-Existence/RTG/review/volume-I-integrated-v0.9.0/render-attempt-receipt.json`.
2. If present, inspect its run ID; fetch jobs, step results, complete logs, and artifacts. Record DOCX/PDF/render-receipt hashes, artifact ID, digest, size, and expiry. If failed, repair only the first log-proven defect. If successful, trigger and verify a second byte-identical hosted render.
3. Fetch `.../machine-execution/evidence-closure-execution-receipt.json` and `evidence-closure-attempt.json`.
4. If an attempt exists, inspect its run, jobs, steps, and logs. Repair only the first proven defect. Require 13/13 evidence classes to be `RECOVERED_HASH_BOUND` or `CLOSED_BOUNDED_WITH_SCOPE`; require 48 theorem review packets; preserve proof correctness as REVIEW_REQUIRED unless independently reviewed.
5. Recompute lanes and readiness through `tools/advance_formalism_lanes.py` and `tools/converge_formalism_publication.py` only after the relevant receipts pass.
6. Verify the StegVerse projection consumes the new RTG state through `StegVerse-Labs/Site/scripts/check_rtg_formalism_projection.py`, subject to Site orchestration admission.
7. Keep Publisher, validator, Factory, admissibility-wiki, stegguardian-wiki, tags, releases, and canonical publication fail-closed until central acceptance permits them.
8. Update RTG and central handoffs after meaningful state changes; update this prompt before ending.

Do not treat a workflow trigger as success. Do not infer deployment or publication from repository completion. Do not create external tasks. Every unresolved task must remain assigned to a repository-native workflow, named component, authority boundary, or machine-observable blocked state.

End substantive responses with: DO NOT ARCHIVE THIS SESSION — ACTIVE WORK REMAINS, unless every program goal and propagation requirement is directly verified complete.
```
