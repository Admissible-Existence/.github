# VerFi Exact-Tree Validation Request — 2026-08-23

Goal: `AEX-VERFI-EXTERNAL-FORMALISM-001`

Source of truth: `docs/external-formalisms/VERFI_MIRROR_HANDOFF.md`.

This request exists to force a pull-request execution of the existing `Canonical Formalism Orientation Validation` lane against a tree based on current `main` after the VerFi transition-prerequisite hardening.

Required observations:

- `scripts/validate_verfi_external_formalism.py` passes all ten canonical cases;
- `tests.test_verfi_external_formalism` passes the hardened missing-disclosure and missing-signature regressions;
- the workflow retains `permissions: {}` and `NONE_VALIDATION_ONLY` authority effect;
- no result is promoted to VerFi implementation interoperability, legal admissibility, cognitive-state proof, AE authority, execution authority, publication authority, or release authority.

A successful PR run establishes hosted validation of the proposed tree only. It does not by itself satisfy the stricter exact-current-`main` commit gate; merge/current-main evidence must remain separately bound before that gate is released.
