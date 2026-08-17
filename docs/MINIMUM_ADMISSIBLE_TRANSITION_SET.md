# Minimum Admissible Transition Set

**Task:** `AEX-RELATIONAL-ADMISSIBILITY-MINSET-002`  
**Applies to:** relational-admissibility conformance surfaces  
**Resolver:** `Admissible-Existence/AE`  
**Authority effect:** none

A conforming admissibility surface MUST support, at minimum, the following distinct governed realized transition classes:

```text
DENY
REVIEW
FAIL_CLOSED
```

Formally, if `R` is the supported resolution-class set:

\[
\{DENY, REVIEW, FAIL\_CLOSED\} \subseteq R.
\]

This is a **minimum set, not an exhaustive set**. Additional profile-defined classes MAY be present, including `ALLOW`, provided an extension does not erase, alias, collapse, or reinterpret any member of the minimum set as absence of a transition.

Each minimum-set member is a valid admitted transition class capable of producing a realized successor state. The requested effect need not be authorized or realized for the governed resolution itself to be valid.

Therefore:

```text
resolution_valid != requested_effect_authorized
resolution_valid != requested_effect_realized
DENY != no transition
REVIEW != no transition
FAIL_CLOSED != no transition
```

The minimum-set rule is a conformance requirement. It does not enumerate successor states, create execution authority, or make `.github` an admissibility resolver. Adjacent repositories retain native mathematical ownership and `Admissible-Existence/AE` remains the resolver.

For StegVerse runtime fields, credential authority remains TV/TVC and GitHub-token runtime authority remains NONE. No Render dependency is introduced.
