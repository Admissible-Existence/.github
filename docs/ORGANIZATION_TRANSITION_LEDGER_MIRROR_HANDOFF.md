# Organization Transition Ledger Mirror Handoff

Organization: `Admissible-Existence`

Repository-level transitions remain owned and replayable in their originating repositories. This `.github` layer verifies a repo receipt, records only the organization-level state consequence, and links the exact repo receipt hash.

Contract: `.stegverse/transition-ledger/org-contract.json`  
Rollup: `resident-runtime/aggregate_repo_transition.py`  
Published ref: `refs/stegverse/organization-ledger` in `Admissible-Existence/.github`  
Writer: `.github/workflows/organization-ledger-writer.yml` (push only; the self-closure `organization-ledger-transition.yml` is retired under Rigel's rule, 2026-10-25: no InTr hop inside one organization)

The repository chain is the subtree `repository-ledger/Admissible-Existence/.github` of that same ref. One fast-forward push publishes both. `resident-runtime/organization_ledger_readback.py` reads both back from a fresh fetch.

Organization replay must terminate using verified repo receipts plus this org chain; it must not depend on Master Records ecosystem replay.

Only the organization receipt and evidence required for ecosystem reconstruction propagate to `master-records/.github`. Authority and time are constraint variables. A disposition is transition evidence only.
