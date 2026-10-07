# Release, package-version and wire-version policy

Issue: #18 — `release: define project, wire-version and deprecation policy`

Status:

```text
PROJECT VERSION POLICY = FROZEN
WIRE VERSION POLICY = FROZEN
WIRE COMPATIBILITY POLICY = FROZEN
RELEASE POLICY = FROZEN

PRODUCTION-READINESS GATE 1 = PASS
PRODUCTION-READINESS GATE 2 = PASS
PRODUCTION-READINESS GATE 9 = PASS
```

This document defines the relationship between:

```text
Lasagna package/project releases
LSG2 wire-format versions
public compatibility promises
release artifacts
security-fix releases
```

The package version and wire version are independent version domains.

## 1. Version domains

Lasagna has two distinct version numbers.

### Package/project version

The Python distribution uses Semantic Versioning:

```text
MAJOR.MINOR.PATCH
```

Current package version:

```text
0.3.0
```

The package version describes the software release.

It may change because of:

```text
API additions or changes
CLI additions or changes
bug fixes
security fixes
performance work
documentation changes
wire-format support changes
new wire-format implementations
```

### Wire-format version

The serialized LSG2 header contains an independent wire-format version.

Currently supported:

```text
format_version = 1
format_version = 2
```

The wire version identifies one physical and semantic interpretation of the
serialized stream.

Package version and wire version SHALL NOT be inferred from one another.

For example:

```text
package 0.3.0 may read wire V1 and V2
package 0.3.0 emits V2 by default
```

A future package version may support multiple wire versions simultaneously.

## 2. Semantic Versioning policy

Lasagna follows Semantic Versioning for package releases.

Before `1.0.0`:

```text
PATCH
    backward-compatible fixes and maintenance

MINOR
    new functionality and may contain explicitly declared incompatible
    changes because the project remains pre-1.0

MAJOR
    reserved for a deliberate project-level compatibility boundary
```

Pre-1.0 status does not waive the public deprecation contract.

Any incompatibility affecting a supported Python or CLI interface must still
follow `docs/public-api-contract.md`, including its deprecation requirements,
unless the documented emergency exception applies.

Starting with `1.0.0`:

```text
PATCH
    backward-compatible fixes

MINOR
    backward-compatible functionality

MAJOR
    incompatible supported public-interface changes
```

Wire-format version changes do not mechanically require a matching package
MAJOR bump.

## 3. Wire-version immutability

A released wire-format version has exactly one interpretation.

The following must not change incompatibly within an existing wire version:

```text
field order
field widths
endianness
meaning of serialized fields
predictor identifiers
residual coding identifiers
required structural invariants
reserved-field interpretation
```

Current policy:

```text
V1 = immutable compatibility baseline
V2 = immutable frozen L32 format
```

Current byte order:

```text
little-endian
```

Current V2 segment layout:

```text
<IIIfffff>
32 bytes
```

An incompatible physical or semantic change requires a new wire-format version.

Therefore:

```text
V2 incompatible change -> V3 or later
```

A package release SHALL NOT silently reinterpret an existing `format_version`.

## 4. Reserved-field policy

Reserved fields in an existing frozen wire version are not permission to make
an incompatible reinterpretation inside that version.

For V1, historical reserved/padding fields retain their historical semantics.

For V2, any field or value documented as reserved remains reserved unless its
future use can be proven compatible with every already valid V2 decoder and
with the frozen V2 contract.

If compatibility cannot be demonstrated:

```text
new meaning -> new wire version
```

A decoder must not infer an incompatible extension from tolerated bytes,
padding or trailing data.

## 5. Unknown wire versions

Unsupported wire versions fail closed.

Current decoder behavior:

```text
V1 -> supported
V2 -> supported
other value -> ValueError
```

A decoder SHALL NOT guess that an unknown future wire version is compatible
with V1 or V2.

## 6. Default encode version

Current default:

```text
Python encode_timeseries() -> V2
CLI lasagna2 encode        -> V2
```

Explicit legacy encoding remains available through:

```text
encode_timeseries_v1()
lasagna2 encode --format-version 1
```

Explicit V2 encoding remains available through:

```text
encode_timeseries_v2()
lasagna2 encode --format-version 2
```

Changing the default encode version is both:

```text
a public API/CLI compatibility event
and
a release-policy event
```

It must be documented in release notes and migration guidance.

## 7. Decode-support lifetime

Released wire versions receive a stronger compatibility promise than the
current default encoder.

A wire version does not lose decode support merely because a newer wire
version becomes the default.

Before decode support for a released wire version may be removed, all of the
following must be true:

```text
1. a successor wire version is released and production-qualified;

2. the successor has become the default encoder in a published package
   release;

3. the old wire version has been explicitly declared deprecated in a
   published package release while decode support still remains functional;

4. a migration path from the deprecated version to a supported version is
   documented and reproducible;

5. release notes identify the future removal boundary;

6. compatibility fixtures for the deprecated version are retained through the
   deprecation period;

7. removal occurs only in a package release explicitly classified as
   incompatible under the project Semantic Versioning policy.
```

Therefore:

```text
NEW DEFAULT != OLD DECODER REMOVAL
```

Minimum deprecation lead time:

```text
at least one published package release with the deprecated decoder still
available
```

There is no wall-clock expiration.

## 8. Current V1/V2 support commitment

Current production-qualification contract:

```text
V1 decode = SUPPORTED
V2 decode = SUPPORTED

V1 explicit encode = SUPPORTED
V2 explicit encode = SUPPORTED

default encode = V2
```

Neither V1 nor V2 currently has a removal schedule.

V1 being "compatibility-only" means:

```text
new encoder-format development targets newer formats
```

It does not mean:

```text
V1 decode may disappear without deprecation
```

The frozen V1 compatibility corpus remains required evidence while V1 decode
support is claimed.

## 9. Future V3+ migration policy

A future wire version SHALL be introduced as a new version number rather than
an incompatible mutation of V2.

Before a new wire version may become the default encoder, the repository must
provide:

```text
a frozen semantic contract
a frozen physical layout
explicit version identifier
decoder implementation
encoder implementation
unknown-version fail-closed behavior
compatibility tests
deterministic encoding evidence where applicable
migration documentation
release-note declaration
production qualification appropriate to the change
```

A new version may coexist with older supported versions.

The preferred transition sequence is:

```text
design candidate
    ->
freeze semantics
    ->
freeze physical layout
    ->
implement explicit encoder/decoder
    ->
qualify compatibility
    ->
publish explicit opt-in support
    ->
publish default transition
    ->
only later consider old-version deprecation
```

The introduction of V3 does not itself authorize removal of V1 or V2.

## 10. Migration policy

When the default wire version changes, migration guidance must document at
least:

```text
old default
new default
how to request the old format explicitly, if still supported
which package versions can read each format
whether re-encoding is required
known lossy/reconstruction implications
compatibility limitations
```

If an old decoder is ever scheduled for removal, the project must provide a
reproducible migration path before removal.

For a lossy codec, migration documentation must distinguish:

```text
byte-preserving file migration
decode + re-encode migration
```

and must not imply that decode + re-encode is bitwise or numerically lossless
when it is not.

## 11. Release tags

Published release tags are immutable historical identifiers.

Canonical tag form:

```text
vMAJOR.MINOR.PATCH
```

Examples:

```text
v0.1.0
v0.2.2
```

After a tag has been used for a published release, it SHALL NOT be:

```text
moved
deleted and recreated
force-updated
reassigned to different source
```

A release mistake is corrected by publishing a new package version/tag.

Historical tags are evidence and must remain stable.

## 12. Release artifacts

A release is identified by:

```text
immutable Git tag
source tree at that tag
release notes for that version
```

If package artifacts are published in the future, the release artifact set may
also include:

```text
sdist
wheel
checksums
provenance/attestation material
```

Any binary/package artifact represented as an official release artifact must
be built from the tagged source revision.

The repository currently has no automated package-publishing workflow.

Absence of such a workflow is not represented as evidence of automated release
provenance.

If automated publication is later introduced, its trust/provenance contract
must be documented separately.

## 13. Release notes and changelog policy

`RELEASE_NOTES.md` is the canonical human-readable release history.

Every published package release must add a release section identifying, where
applicable:

```text
package version
release date
public API changes
CLI changes
default changes
wire versions readable
default wire version written
new explicit wire encoders
deprecated API or wire behavior
removed API or wire behavior
migration instructions
security-relevant fixes
known compatibility limitations
```

Compatibility-affecting changes must not be hidden under generic maintenance
notes.

## 14. Compatibility declaration

Every published release must make its current wire compatibility explicit.

Minimum declaration:

```text
DECODE:
    supported wire versions

ENCODE DEFAULT:
    default emitted wire version

ENCODE EXPLICIT:
    explicitly selectable wire versions

DEPRECATED:
    any API, CLI or wire support currently in a deprecation period
```

For the current 0.3.0 source baseline:

```text
DECODE:
    V1, V2

ENCODE DEFAULT:
    V2

ENCODE EXPLICIT:
    V1, V2

DEPRECATED:
    none
```

## 15. Security-fix release policy

Security fixes follow the smallest safe release boundary.

A backward-compatible security fix should normally be released as:

```text
PATCH
```

A security fix that requires an incompatible public API or wire behavior may
use the emergency exception from `docs/public-api-contract.md`.

In that case, the release must document:

```text
affected versions
security or integrity reason normal compatibility cannot be preserved
observable compatibility impact
migration or mitigation guidance
whether wire compatibility is affected
```

Security fixes SHALL NOT silently redefine an existing frozen wire version.

If the vulnerability is inherent to a frozen wire design and cannot be fixed
compatibly:

```text
introduce a new wire version
retain safe legacy decode only where defensible
document the security boundary explicitly
```

## 16. Supported runtime and release-blocking CI policy

The current production-qualified runtime matrix is deliberately narrower than
the package installation declaration.

```text
production-qualified Python   = 3.12
production-qualified platform = Ubuntu 24.04
canonical CI workflow         = .github/workflows/ci.yml
release-blocking job          = CI / Lint & Test
```

`pyproject.toml` currently declares:

```text
requires-python = ">=3.10"
```

That declaration means the package may be installed on Python 3.10 or newer.
It does not, by itself, constitute production-qualification evidence for every
such interpreter or operating system.

Therefore:

```text
PACKAGE INSTALLABILITY RANGE != PRODUCTION-QUALIFIED RUNTIME MATRIX
```

A Python/platform combination becomes part of the production-qualified matrix
only after it is explicitly added to this policy and exercised by required CI
for release candidates.

For the current baseline, the canonical CI job runs on:

```text
Ubuntu 24.04
Python 3.12
```

and executes:

```text
pre-commit run --all-files --show-diff-on-failure
pytest -vv
```

The `CI / Lint & Test` result for the exact commit intended for release is
release-blocking.

Before a release may be published, that required CI result must exist and must
have completed successfully.

The following states block release publication:

```text
failure
cancelled
skipped
missing / not run for the release commit
still pending
```

A locally successful test run or pre-commit run is useful development evidence,
but it does not substitute for the required GitHub CI result on the release
commit.

Security, CodeQL, dependency-review, pip-audit and OpenSSF Scorecard workflows
retain their own security and supply-chain contracts. Issue #22 does not
silently redefine every auxiliary workflow as a Gate 14 release blocker.

If the production-qualified runtime matrix or release-blocking CI set changes,
the policy, workflow and regression tests must change together in the same
reviewed change.

## 17. Release checklist

Before publishing a release:

```text
[ ] package version updated
[ ] release notes updated
[ ] compatibility declaration updated
[ ] public API contract reviewed if affected
[ ] wire-format contract reviewed if affected
[ ] migration guidance present for compatibility changes
[ ] local test suite passes
[ ] local pre-commit passes
[ ] required CI / Lint & Test result for the release commit exists and is successful
[ ] security implications reviewed
[ ] release tag points to the intended commit
```

For a release introducing a new wire version:

```text
[ ] wire semantics frozen
[ ] physical layout frozen
[ ] encoder/decoder qualified
[ ] old-version decode behavior verified
[ ] unsupported-version behavior verified
[ ] migration documentation present
```

## 18. Relationship to public API deprecation

Public Python/CLI deprecation is governed by:

```text
docs/public-api-contract.md
```

Wire deprecation is governed by this document.

The policies are deliberately aligned:

```text
no same-release deprecate-and-remove cycle
migration guidance before removal
explicit release-note declaration
emergency exception only for material safety/correctness reasons
```

Wire support has the additional requirement that migration must account for
the persistence of already-created files.

## 19. Current gate assessment

The existing evidence already freezes:

```text
V1 historical compatibility baseline
V2 semantic interpretation
V2 physical L32 layout
little-endian representation
unknown-version fail-closed behavior
V1 frozen compatibility corpus
V2 deterministic wire behavior
```

This policy adds the previously missing durable rules for:

```text
future format evolution
decode-support lifetime
wire deprecation
V3+ migration
package/wire relationship
tag immutability
release artifacts
release notes
compatibility declarations
security-fix releases
```

Therefore:

```text
PRODUCTION_READINESS_GATE_1=PASS
PRODUCTION_READINESS_GATE_2=PASS
PRODUCTION_READINESS_GATE_9=PASS
```

## 20. Policy gates

```text
SEMANTIC_VERSION_POLICY_GATE=PASS
WIRE_VERSION_POLICY_GATE=PASS
PACKAGE_WIRE_SEPARATION_GATE=PASS

WIRE_IMMUTABILITY_GATE=PASS
RESERVED_FIELD_POLICY_GATE=PASS
UNKNOWN_VERSION_GATE=PASS

DECODE_SUPPORT_LIFETIME_GATE=PASS
WIRE_DEPRECATION_GATE=PASS
V1_V2_SUPPORT_GATE=PASS
V3_MIGRATION_GATE=PASS
MIGRATION_POLICY_GATE=PASS

TAG_IMMUTABILITY_GATE=PASS
RELEASE_ARTIFACT_POLICY_GATE=PASS
CHANGELOG_POLICY_GATE=PASS
COMPATIBILITY_DECLARATION_GATE=PASS
SECURITY_FIX_RELEASE_GATE=PASS

PRODUCTION_READINESS_GATE_1=PASS
PRODUCTION_READINESS_GATE_2=PASS
PRODUCTION_READINESS_GATE_9=PASS
```
