# Production-readiness criteria

Date: 2026-10-05

Issue:

```text
#12 meta: define production-readiness criteria for Lasagna
```

Status:

```text
TRACKING CONTRACT FROZEN
PROJECT STATUS = EXPERIMENTAL
PRODUCTION READY = NO
```

## Purpose

This document defines the mandatory evidence required before Lasagna may claim
production readiness.

Production readiness SHALL NOT be inferred from:

```text
a successful release
a frozen wire format
passing unit tests
good compression results
successful benchmarks
one or more real-world datasets
```

It requires the complete mandatory gate defined here.

## Status vocabulary

Every criterion SHALL use one of:

```text
PASS
PARTIAL
REQUIRED
BLOCKER
N/A
```

Definitions:

```text
PASS
    Required evidence exists and satisfies the criterion.

PARTIAL
    Relevant evidence exists, but the production criterion is not fully met.

REQUIRED
    Work or evidence is still required.

BLOCKER
    A known deficiency prevents a production-readiness claim.

N/A
    Criterion is explicitly not applicable, with rationale.
```

`PARTIAL` is not equivalent to `PASS`.

Production readiness requires:

```text
every mandatory criterion = PASS
```

No weighted score or aggregate percentage may override a failed mandatory gate.

## Production-readiness definition

Lasagna may describe itself as production-ready only when all mandatory gates
in this document are `PASS` and the evidence is reproducible from the
repository or linked release artifacts.

Until then, public project language SHALL continue to identify Lasagna as:

```text
experimental research software
```

## Current project state

Current package version:

```text
0.3.0
```

Current wire support:

```text
V1 decode compatibility
V2 default encode/decode
```

Current declared project status:

```text
experimental
```

Current production-readiness decision:

```text
NOT READY
```

## Gate 1 — format stability

Mandatory:

```text
YES
```

Required evidence:

```text
wire version semantics frozen
field widths frozen
endianness frozen
decoder behavior documented
reserved-field policy documented
unknown-version behavior fail-closed
golden/frozen compatibility corpus
```

Current evidence:

```text
docs/rate-distortion-design.md
docs/v2-empirical-validation.md
tests/test_core_v2_format.py
tests/test_core_v2_wire.py
tests/test_v1_frozen_compatibility.py
```

Current status:

```text
PARTIAL
```

Rationale:

V2 physical representation and compatibility behavior are frozen and tested,
but production readiness additionally requires a durable versioning and
deprecation policy covering future format evolution.

## Gate 2 — compatibility policy

Mandatory:

```text
YES
```

Required policy:

```text
supported decode versions
default encode version
minimum compatibility lifetime
conditions for dropping decode support
migration policy
behavior for unsupported future versions
```

Current evidence:

```text
README.md
tests/test_v1_frozen_compatibility.py
tests/test_core_v2_wire.py
```

Current status:

```text
PARTIAL
```

Known:

```text
V1 decode retained
V2 default encode
unknown versions fail closed
```

Still required:

```text
formal deprecation policy
support-lifetime policy
migration policy for future V3+
```

## Gate 3 — malformed-input handling

Mandatory:

```text
YES
```

Required evidence:

```text
truncated headers rejected
invalid magic rejected
unsupported versions rejected
invalid segment ranges rejected
invalid residual lengths rejected
invalid codec identifiers rejected
malformed varints rejected
integer/size overflow cases bounded
pathological metadata rejected
```

Current evidence:

```text
tests/test_decode_malicious.py
tests/test_core_v2_wire.py
tests/test_residual_zero_run_codec.py
```

Current status:

```text
PARTIAL
```

Reason:

Targeted malformed-input tests exist, but systematic adversarial coverage is
not yet demonstrated.

## Gate 4 — resource limits

Mandatory:

```text
YES
```

Production decoder/encoder limits SHALL be explicitly documented for at least:

```text
maximum n_points
maximum n_segments
maximum context size
maximum residual block size
maximum total input size, or explicit unbounded policy
maximum memory amplification
maximum temporary allocation
maximum recursion/nesting where applicable
```

Failure behavior SHALL be deterministic.

Current status:

```text
REQUIRED
```

Existing ad-hoc sanity checks do not constitute a complete resource-limit
contract.

## Gate 5 — fuzzing

Mandatory:

```text
YES
```

Required evidence:

```text
decoder fuzz target
structured wire-format mutation target
residual codec fuzz targets
seed corpus
documented runtime/budget
reproducible crash artifacts
zero unresolved crashes for the qualification run
```

Recommended minimum qualification:

```text
decoder fuzzing across V1 and V2
residual varint fuzzing
zero-run residual fuzzing
header/segment/block corruption fuzzing
```

Current status:

```text
REQUIRED
```

## Gate 6 — corruption behavior

Mandatory:

```text
YES
```

Required definition:

```text
what corruption is detected
what corruption may remain undetected
whether trailing bytes are accepted/rejected
whether local corruption can affect unrelated segments
whether integrity checks exist
what partial-decode corruption semantics are
```

Current evidence:

```text
tests/test_decode_malicious.py
docs/access-architecture.md
docs/multivariate-architecture.md
```

Current status:

```text
PARTIAL
```

Open production question:

```text
checksum / integrity-domain policy
```

A codec may be production-ready without checksums only if that limitation is
explicitly accepted and documented.

## Gate 7 — performance characterization

Mandatory:

```text
YES
```

Required evidence:

```text
encode throughput
decode throughput
peak memory
representative file sizes
multiple signal families
documented hardware/software environment
reproducible benchmark protocol
```

Current evidence:

```text
docs/performance-benchmark-protocol.md
docs/performance-benchmark.md
docs/performance-benchmark-results.csv
docs/performance-benchmark-environment.json
```

Current status:

```text
PASS
```

This gate means performance is characterized, not that Lasagna is necessarily
faster than competing codecs.

## Gate 8 — large-file behavior

Mandatory:

```text
YES
```

Required evidence:

```text
large n_points
large n_segments
large encoded files
memory behavior at scale
integer/offset safety
runtime scaling
failure behavior at configured limits
```

Required scenarios SHOULD include sizes materially larger than ordinary unit
tests.

Current status:

```text
REQUIRED
```

Existing performance characterization is useful evidence but does not by itself
establish production large-file limits and failure behavior.

## Gate 9 — release and versioning policy

Mandatory:

```text
YES
```

Required policy:

```text
semantic project-version policy
wire-version policy
relationship between package version and wire version
release artifact policy
tag immutability
changelog policy
compatibility declarations
security-fix release policy
```

Current evidence:

```text
pyproject.toml
existing release/tag history
V1/V2 wire documentation
```

Current status:

```text
PARTIAL
```

## Gate 10 — security review

Mandatory:

```text
YES
```

Minimum review scope:

```text
untrusted input model
allocation attacks
CPU amplification
malformed varints
oversized metadata
integer/offset overflow
unexpected trailing data
parser differential behavior
dependency/supply-chain posture
CLI filesystem behavior
```

Required evidence:

```text
written threat model
review findings
resolved critical/high findings
accepted residual risks
```

Current CI evidence includes:

```text
.github/workflows/security.yml
.github/workflows/supply-chain.yml
```

Current status:

```text
REQUIRED
```

Security workflows are useful but do not replace a codec/parser security
review.

## Gate 11 — API stability

Mandatory:

```text
YES
```

Required stable public API surface SHALL be explicitly listed.

Current likely public surface includes:

```text
TimeSeries
encode_timeseries()
encode_timeseries_v1()
encode_timeseries_v2()
decode_timeseries()
```

Required policy:

```text
supported public symbols
argument stability
default-value stability
exception contract
return-type stability
deprecation process
CLI compatibility policy
```

Current status:

```text
REQUIRED
```

Existing behavior is documented, but a formal stable-API contract has not yet
been frozen.

## Gate 12 — documentation completeness

Mandatory:

```text
YES
```

Required documentation:

```text
supported input domain
lossy semantics
error/quality controls
wire versions
compatibility
CLI usage
Python API
failure modes
security limitations
resource limits
performance expectations
known non-goals
migration guidance
```

Current evidence:

```text
README.md
docs/
```

Current status:

```text
PARTIAL
```

The repository has extensive research documentation but production operational
documentation remains incomplete.

## Gate 13 — external dataset validation

Mandatory:

```text
YES
```

Required evidence:

```text
externally sourced datasets
multiple independent domains
documented provenance
documented preprocessing
reproducible acquisition/preparation
compression and reconstruction metrics
known limitations
```

Current evidence:

```text
docs/real-world-validation-protocol.md
docs/real-world-validation.md
docs/real-world-validation.csv
```

Current corpus:

```text
3 externally sourced univariate series
3 domains
```

Current status:

```text
PARTIAL
```

The existing study demonstrates real-world validation capability but is too
small to justify a broad production-readiness claim by itself.

Production qualification SHALL define a larger target corpus before this gate
may become `PASS`.

## Gate 14 — regression and CI reliability

Mandatory:

```text
YES
```

Required evidence:

```text
clean pre-commit baseline
unit tests
wire compatibility tests
malformed-input tests
CI on supported Python versions/platforms
release-blocking failure semantics
```

Current evidence:

```text
.github/workflows/ci.yml
tests/
```

Current status:

```text
PARTIAL
```

The repository has active CI and test coverage, but the supported runtime
matrix and release-blocking policy must be formally frozen.

## Gate 15 — deterministic behavior

Mandatory:

```text
YES
```

Required evidence:

```text
same input/configuration produces byte-identical output
decode is deterministic
auto decisions are deterministic
frozen compatibility artifacts remain byte-identical
```

Current evidence:

```text
tests/test_v1_frozen_compatibility.py
tests/test_core_v2_wire.py
benchmark/research reproducibility gates
```

Current status:

```text
PASS
```

## Gate 16 — dependency policy

Mandatory:

```text
YES
```

Required policy:

```text
runtime dependencies identified
version constraints defined
dependency update policy
supply-chain controls
optional/tooling dependencies separated from runtime
```

Current evidence:

```text
pyproject.toml
.github/workflows/supply-chain.yml
```

Current status:

```text
PARTIAL
```

## Gate 17 — supported numeric domain

Mandatory:

```text
YES
```

Required definition:

```text
finite/non-finite handling
float input assumptions
quantization bounds
metadata representability
residual integer bounds
overflow behavior
extreme magnitude behavior
```

Current evidence:

```text
docs/rate-distortion-design.md
tests/test_core_v2_wire.py
```

Current status:

```text
PARTIAL
```

## Gate 18 — operational observability

Mandatory:

```text
YES
```

A production codec SHOULD expose enough information to diagnose failures
without requiring binary archaeology.

Required definition:

```text
error taxonomy
actionable exception messages
version reporting
metadata inspection
safe file-info command
```

Current evidence:

```text
CLI info/inspection functionality
tests/test_cli_encode_decode_info.py
```

Current status:

```text
PARTIAL
```

## Gate 19 — access behavior

Mandatory:

```text
NO for baseline whole-file codec
YES if random-access/streaming capability is advertised as production
```

Current architecture:

```text
docs/access-architecture.md
```

Current status:

```text
N/A
```

for baseline production qualification.

If random access, partial decode or streaming is advertised as production
functionality, those features require their own implementation and validation
gates.

## Gate 20 — multivariate behavior

Mandatory:

```text
NO for current univariate product scope
```

Current architecture:

```text
docs/multivariate-architecture.md
```

Current status:

```text
N/A
```

Production readiness for univariate Lasagna does not require multivariate
support.

The documentation MUST continue to state that scope explicitly.

## Mandatory blocker summary

Current known non-PASS mandatory gates include:

```text
format stability             PARTIAL
compatibility policy         PARTIAL
malformed-input handling     PARTIAL
resource limits              REQUIRED
fuzzing                      REQUIRED
corruption behavior          PARTIAL
large-file behavior          REQUIRED
release/versioning policy    PARTIAL
security review              REQUIRED
API stability                REQUIRED
documentation completeness   PARTIAL
external dataset validation  PARTIAL
CI/runtime support policy    PARTIAL
dependency policy            PARTIAL
supported numeric domain     PARTIAL
operational observability    PARTIAL
```

Therefore:

```text
PRODUCTION_READY_GATE=FAIL
```

This is expected.

Issue #12 exists to make that state explicit.

## Existing strong evidence

The following areas already have substantial evidence:

```text
V1 compatibility
V2 physical-layout validation
deterministic encode behavior
real-world validation framework
external codec comparison
performance characterization
sensitivity characterization
predictor research
residual coding research
entropy coding research
multivariate architecture
random-access/streaming architecture
CI and supply-chain workflows
```

These are inputs to production qualification, not substitutes for it.

## Required subordinate work

Before production readiness can be claimed, subordinate work SHALL exist for at
least:

```text
A. fuzzing qualification
B. resource-limit contract
C. large-file qualification
D. security/threat-model review
E. public API stability/deprecation contract
F. release/versioning policy
G. expanded external dataset qualification
H. production documentation completion
```

Additional subordinate issues MAY be split further if implementation scope
requires it.

## Closure policy for issue #12

Issue #12 SHALL remain open while any mandatory gate is not `PASS`.

It may be closed only when:

```text
1. every mandatory criterion is PASS;
2. every PASS links to reproducible evidence;
3. no unresolved BLOCKER remains;
4. README/project metadata no longer need the experimental disclaimer;
5. a final production-readiness audit confirms the complete gate.
```

Closing subordinate issues is not sufficient by itself.

The final decision SHALL be evidence-driven.

## Release naming policy

Until the complete production gate passes, releases SHALL NOT use wording such
as:

```text
production-ready
stable for archival use
safe for untrusted production workloads
long-term format guarantee
```

unless the specific claim has independently satisfied its relevant gate.

Experimental releases MAY continue.

## Failure policy

Any mandatory regression after production readiness SHALL immediately reopen
the relevant gate.

A later project version cannot inherit `PASS` automatically when it changes:

```text
wire format
decoder parser
predictor semantics
residual coding
resource behavior
public API
security boundary
```

Affected gates require requalification.

## Production-readiness matrix

```text
01 format stability             PARTIAL
02 compatibility policy         PARTIAL
03 malformed-input handling     PARTIAL
04 resource limits              REQUIRED
05 fuzzing                      REQUIRED
06 corruption behavior          PARTIAL
07 performance characterization PASS
08 large-file behavior          REQUIRED
09 release/versioning policy    PARTIAL
10 security review              REQUIRED
11 API stability                REQUIRED
12 documentation completeness   PARTIAL
13 external dataset validation  PARTIAL
14 regression/CI reliability    PARTIAL
15 deterministic behavior       PASS
16 dependency policy            PARTIAL
17 supported numeric domain     PARTIAL
18 operational observability    PARTIAL
19 access behavior              N/A
20 multivariate behavior        N/A
```

Current mandatory PASS count:

```text
2
```

This count is informational only.

It SHALL NOT be used as a readiness percentage.

## Final rule

```text
Lasagna remains experimental
until every mandatory production-readiness gate is PASS.
```

## Issue #12 acceptance mapping

Production readiness explicitly defined:

```text
PASS
```

Required evidence mapped to tests/reports/work items:

```text
PASS
```

Security and malformed-input requirements included:

```text
PASS
```

Compatibility and deprecation requirements documented:

```text
PASS
```

Performance and real-world validation required:

```text
PASS
```

Experimental status retained until all mandatory criteria pass:

```text
PASS
```

Issue #12 may close now:

```text
NO
```

Reason:

```text
tracking/meta issue remains open until subordinate production work completes
```

## Meta gates

```text
PRODUCTION_DEFINITION_GATE=PASS
EVIDENCE_MAPPING_GATE=PASS
SECURITY_REQUIREMENTS_GATE=PASS
COMPATIBILITY_POLICY_REQUIREMENTS_GATE=PASS
PERFORMANCE_REQUIREMENTS_GATE=PASS
REAL_WORLD_VALIDATION_REQUIREMENTS_GATE=PASS
EXPERIMENTAL_STATUS_GATE=PASS

PRODUCTION_READY_GATE=FAIL
ISSUE_12_CLOSE_GATE=BLOCKED
```
