# AID Discovery Integration Mirror Handoff

Status: SOURCE INTEGRATION INSTALLED
Organization owner: Admissible-Existence/.github
Endpoint repository: Admissible-Existence/AID
Service: admissible-existence.aid

## Route

External governed caller
-> caller organization .github
-> Admissible-Existence/.github
-> admissible-existence.aid
-> Admissible-Existence/AID materialized source

Responses return through the corresponding organization boundaries.

## Supported operations

- DESCRIBE_AID
- DISCOVER_CANONICAL_SOURCES
- DISCOVER_SUPPORT_RESOURCES
- DESCRIBE_STEGVERSE_002_ATTRIBUTION

## Attribution

StegVerse-002 proven construction provenance is attributed to Admissible-Existence/TT at commit ab60b42934222a2cb5335a5a8194f258a491fc57.

RTG, GTG, and AE are separately represented as pinned AVAILABLE_NOT_REQUIRED formal resources for the frozen self-characterization experiment. Availability is not use, injection, or provenance.

## Support bindings

AID names:
- learning-transition-governance
- validation-profile-registry
- standing-proof-formalism
- ae-validation-factory

AID inherits no authority from those repositories.

## Authority and runtime boundary

AID is an internal endpoint, not organization resident-runtime authority. Admissible-Existence/.github owns cross-org ingress/egress and dispatch.

Source integration does not prove AID is materialized or live on a resident runtime. The endpoint fails closed when AID source cannot be resolved.
