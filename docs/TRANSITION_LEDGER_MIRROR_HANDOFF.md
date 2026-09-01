# Transition Ledger Mirror Handoff

Repository: `Admissible-Existence/.github`

Every durable transition owned by this repository is recorded first in this repository's transition ledger. Repository replay/reconstruction must terminate here without organization- or ecosystem-level replay.

- Contract: `.stegverse/transition-ledger/contract.json`
- Emitter: `.stegverse/transition-ledger/emit.py`
- Default durable root: `$XDG_STATE_HOME/stegverse/repo-ledgers/Admissible-Existence/.github`

Receipts are append-only and hash-linked. Only evidence required to reconstruct organization-level state propagates upward to `Admissible-Existence/.github`; the org ledger never replaces this repo ledger.

Recording creates no execution, standing, admission, credential, publication, or lifecycle authority. Internal inference without a durable repo-owned state transition is not recorded merely because it occurred.
