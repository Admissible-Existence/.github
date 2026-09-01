# ORG_BOUNDARY_MIRROR_HANDOFF.md

Status: ACTIVE
Updated: 2026-08-31
Organization: Admissible-Existence
Repository: Admissible-Existence/.github

## Canonical rule
Every Admissible-Existence resident runtime activation surface is owned by and kept in `Admissible-Existence/.github`.

All communication crossing the Admissible-Existence organizational boundary is generated through this repository's Interlock/InTr ingress and egress mechanisms.

Application repositories expose capabilities and endpoint profiles. They do not independently become the organization resident-runtime activation authority.

## HB / InTr
HB or HB-derived carriers provide synchronization/carrier capability only. Carrier presence grants no admission, execution, credential, routing, transition, receiving, publication, custody, or release authority.

InTr governs the packets carried across the organization boundary. Applicable transition elements determine authority effects.

## Responsibilities
Ingress: observe carrier -> validate InTr envelope -> bind provenance and transition context -> resolve destination/profile -> dispatch -> receipt.
Egress: validate result/evidence -> resolve destination org -> generate governed InTr envelope -> emit receipt -> preserve reconstruction linkage.

## Runtime home
- `resident-runtime/`
- `org-boundary/runtime/`
- organization-specific existing resident/runtime machinery referenced by the activation manifest

GitHub Actions may validate or convey evidence but are not sovereign runtime authority.

## Migration rule
Legacy organization-runtime activation surfaces outside `Admissible-Existence/.github` are endpoint/provider implementations or migration sources, not competing organizational activation points.


## AID AI Discovery endpoint

`Admissible-Existence/AID` is the organization AI Discovery SDK endpoint. It expands discovery/creative allowance for intelligent code already constructed within consequential governance and does not create entityhood, standing, authority, admissibility, or execution.

Canonical service:

`admissible-existence.aid`

Cross-organization AID communication remains owned by this `.github` boundary. The endpoint is dispatched only through a registered adapter and fails closed when AID source is not materialized on the resident runtime.

Canonical integration handoff:

`docs/AID_DISCOVERY_INTEGRATION_MIRROR_HANDOFF.md`
