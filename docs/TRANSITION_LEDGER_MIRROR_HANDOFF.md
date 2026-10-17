# Transition Ledger Mirror Handoff

Repository: `Admissible-Existence/.github`

Every durable transition owned by this repository is recorded first in this repository's transition ledger. Repository replay/reconstruction must terminate here without organization- or ecosystem-level replay.

- Contract: `.stegverse/transition-ledger/contract.json`
- Emitter: `.stegverse/transition-ledger/emit.py`
- Designated location: subtree `repository-ledger/Admissible-Existence/.github` of `refs/stegverse/organization-ledger` in this repository (`contract.json` `repository_ledger_location`)
- Machine-local fallback, when no root is supplied: `$XDG_STATE_HOME/stegverse/repo-ledgers/Admissible-Existence/.github`

Receipts are append-only and hash-linked. Only evidence required to reconstruct organization-level state propagates upward to `Admissible-Existence/.github`; the org ledger never replaces this repo ledger.

Authority and time are constraint variables. A disposition is transition evidence only. Internal inference without a durable repo-owned state transition is not recorded merely because it occurred.
