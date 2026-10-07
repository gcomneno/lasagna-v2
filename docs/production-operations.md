# Production operations guide

Issue: #20 — `docs: complete production operational documentation`

## Status and scope

Lasagna 2 remains experimental until the parent production-readiness tracker
(#12) passes every mandatory gate.

This guide is the production-facing operational entry point for the currently
supported codec surface. It summarizes how to operate that surface and links to
the authoritative contracts and qualification evidence.

It does not replace those authoritative documents.

Current baseline:

```text
package/source baseline = 0.3.0
supported workload       = univariate time series
access model             = whole-file
default encoded format   = LSG2 V2
supported decode formats = V1, V2
```

## Supported input and numeric domain

The supported data model is a univariate `TimeSeries`:

```python
TimeSeries(
    values: List[float],
    dt: float = 1.0,
    t0: str = "1970-01-01T00:00:00Z",
    unit: str = "unknown",
)
```

`TimeSeries` remains a lightweight container. Numeric validation occurs when an
encoder is invoked.

Production encoding supports:

```text
samples               finite real-valued Python int/float values
dt                    finite and > 0
C_Q                   finite and >= 0
Q_MIN                 finite and > 0
mse_threshold         finite and >= 0
fixed segment_length  positive integer
adaptive min/max      positive integers with max >= min
quantized residuals   signed int32
                      [-2147483648, 2147483647]
```

There is no arbitrary application-level magnitude ceiling for finite samples.
Instead, a finite input is rejected with `ValueError` if required statistics,
prediction, quantization, V2 metadata conversion or residual representation
cannot remain inside the supported numeric domain.

`C_Q=0` is supported when `Q_MIN` is positive.

The CLI parses the first comma-separated field of each non-empty,
non-comment line as a float. Lines whose first field cannot be parsed are
skipped. Parsed `NaN`, infinity and overflow-to-infinity values are not skipped:
they reach the shared encoder validation and are rejected before output bytes
are written.

All newly encoded residuals must fit signed int32, regardless of whether the
selected residual representation is raw, varint, zero-run or automatic.

For V2, segment metadata is rounded through the frozen binary32 layout before
the final residuals are calculated. Those post-rounding residuals are checked
against the same signed-int32 contract, so binary32 metadata rounding cannot
bypass the residual bound.

The authoritative encoder contract is
`docs/public-api-contract.md`.

Historical decoder compatibility is intentionally broader than new encoder
acceptance. Existing V1 artifacts are still decoded according to the frozen
legacy semantics; Issue #21 does not redefine historical V1 bytes.

## Dependency and supply-chain policy

The installed Lasagna runtime currently has zero project dependencies.

Build, development, test, benchmark and analysis dependencies are governed
separately by `docs/dependency-policy.md`.

Current policy intentionally permits minimum-version constraints for ordinary
build/dev/tooling dependencies and uses exact pins where a dependency is part
of frozen reproducibility evidence.

`gorillacompression==1.0.2` is the current reproducibility-critical exact pin.

GitHub Actions use immutable full commit SHAs by default. The current
`pypa/gh-action-pip-audit@v1.1.0` tag reference is the single documented
mutable-reference exception and is treated as accepted residual supply-chain
risk, not as an immutable pin.

The project does not currently claim hermetic dependency resolution or
bit-reproducible package builds.

## Runtime and CI qualification

The current production-qualified execution matrix is:

```text
Python   3.12
OS       Ubuntu 24.04
CI       .github/workflows/ci.yml
job      CI / Lint & Test
```

This is intentionally narrower than `requires-python = ">=3.10"` in
`pyproject.toml`.

The packaging declaration defines the interpreter range on which installation
is permitted. It is not evidence that every interpreter or platform in that
range has completed production qualification.

For release publication, the `CI / Lint & Test` result for the exact release
commit must exist and complete successfully. Failed, cancelled, skipped,
pending or missing required CI blocks publication.

Local `pytest` and pre-commit results remain useful development checks but do
not replace the required CI result on the release commit.

The authoritative policy is `docs/release-versioning-policy.md`.

## Lossy semantics

Lasagna is a predictive lossy codec when quantization is active.

The reconstruction pipeline is conceptually:

```text
segment
-> predict
-> compute residual
-> quantize residual
-> encode residual
-> decode
-> reconstruct
```

A successful encode/decode round trip therefore does not imply:

```text
bitwise equality with the original samples
numerical equality with the original samples
archival losslessness
```

Compression results must be interpreted together with reconstruction error.

Lasagna is not claimed to be a universal replacement for lossless compressors
or a universal best compressor for time-series data.

The external production qualification deliberately retains workloads where
Lasagna is worse than the best lossless comparison.

Authoritative evidence:

- `docs/rate-distortion-design.md`
- `docs/external-qualification.md`
- `docs/external-qualification-results.csv`

## Error and quality controls

The codec exposes controls that affect segmentation, prediction and
quantization behavior.

Python API controls include:

```text
segment_length
predictor
C_Q
Q_MIN
segment_mode
min_segment_length
max_segment_length
mse_threshold
residual_coding
```

The CLI exposes:

```text
--segment-mode
--segment-length
--min-segment-length
--max-segment-length
--mse-threshold
--predictor
--residual-coding
--format-version
```

`mse_threshold` is an adaptive-segmentation control. It is not a universal
end-to-end reconstruction-error guarantee.

Likewise, `C_Q` and `Q_MIN` participate in quantization behavior but do not
constitute a general application-level error budget.

Applications with domain-specific accuracy requirements must measure their own
reconstruction metrics using representative data before deployment.

## Wire versions

Current compatibility:

```text
DECODE:
    V1
    V2

ENCODE DEFAULT:
    V2

ENCODE EXPLICIT:
    V1
    V2

DEPRECATED:
    none
```

V1 and V2 are immutable released wire interpretations.

An incompatible change to V2 requires V3 or later.

Unknown wire versions fail closed with `ValueError`; the decoder does not guess
future compatibility.

Authoritative policy:

- `docs/release-versioning-policy.md`

## Compatibility and deprecation

Python API, CLI behavior and wire-format compatibility are governed by separate
but coordinated contracts.

Supported Python symbols, parameters, defaults, CLI commands or documented
behaviors are not removed incompatibly in the same release in which they are
first deprecated, except for the documented emergency cases.

The normal minimum deprecation period includes at least one published package
release with the deprecated behavior still functional.

Authoritative contracts:

- `docs/public-api-contract.md`
- `docs/release-versioning-policy.md`

## Python API

The stable exported Python surface is exactly:

```python
from lasagna2 import (
    TimeSeries,
    encode_timeseries,
    encode_timeseries_v1,
    encode_timeseries_v2,
    decode_timeseries,
)
```

Typical V2-default use:

```python
from lasagna2 import TimeSeries, decode_timeseries, encode_timeseries

ts = TimeSeries(
    values=[0.1 * i for i in range(200)],
    dt=1.0,
    t0="1970-01-01T00:00:00Z",
    unit="arbitrary",
)

encoded = encode_timeseries(ts)
decoded = decode_timeseries(encoded)
```

`encode_timeseries()` emits V2 by default.

`decode_timeseries()` accepts V1 and V2.

Use `encode_timeseries_v1()` only when explicit legacy V1 output is required.

Exact signatures, defaults, return types and exception compatibility are
authoritatively defined in:

- `docs/public-api-contract.md`

## CLI

Installed command:

```text
lasagna2
```

Stable subcommands:

```text
encode
decode
info
export-tags
export-motifs
export-profile
```

Encode with the V2 default:

```bash
lasagna2 encode \
  input.csv \
  output.lsg2 \
  --dt 1 \
  --t0 1970-01-01T00:00:00Z \
  --unit arbitrary
```

Decode V1 or V2:

```bash
lasagna2 decode input.lsg2 output.csv
```

Request legacy V1 output explicitly:

```bash
lasagna2 encode \
  input.csv \
  output-v1.lsg2 \
  --dt 1 \
  --t0 1970-01-01T00:00:00Z \
  --unit arbitrary \
  --format-version 1
```

Inspect a file:

```bash
lasagna2 info input.lsg2 -v
```

The CLI defaults are part of the compatibility-sensitive public surface and
must not be inferred from the Python defaults.

Authoritative CLI contract:

- `docs/public-api-contract.md`

## Failure modes

Public codec validation failures use:

```text
ValueError
```

This includes malformed or unsupported encoded input and documented
resource-policy rejection.

Invalid Python calls outside the documented contract may raise normal Python
exceptions such as `TypeError` or `ValueError`.

CLI argument errors follow `argparse` behavior and terminate with a non-zero
status.

Filesystem operations may surface normal operating-system failures.

Compatibility applies to the documented exception category, not exact diagnostic
message text.

Unknown wire versions fail closed.

## Malformed input and security limitations

Encoded files must be treated as untrusted input.

The decoder performs structural and resource preflight before expensive decode
work, including validation of:

```text
input size
wire magic and version
point and segment counts
context size and nesting
segment-table extent
predictor identifiers
segment extents
residual coding identifiers
residual block sizes
aggregate residual work
payload availability
```

Important residual risks remain:

```text
LSG2 has no intrinsic checksum
LSG2 has no cryptographic authentication
successful metadata inspection is not proof of full decodability
CLI output writes are not an atomic transactional storage protocol
filesystem/symlink policy remains the responsibility of the deployment
```

Do not use `lasagna2 info` as an integrity or authenticity check.

Authoritative threat model and findings:

- `docs/security-review.md`
- `docs/fuzzing-qualification.md`

## Resource limits

Current inclusive implementation limits:

```text
MAX_POINTS                 = 10,000,000
MAX_SEGMENTS               = 1,000,000
MAX_SEGMENT_POINTS         = 10,000,000
MAX_CONTEXT_BYTES          = 65,536
MAX_CONTEXT_DEPTH          = 64
MAX_VARINT_BYTES           = 10
MAX_RESIDUAL_BLOCK_BYTES   = 100,000,000
MAX_INPUT_BYTES            = 176,065,580
UINT32_MAX                 = 4,294,967,295
```

Exceeding codec/resource-policy limits fails deterministically with
`ValueError`.

These are defensive acceptance ceilings, not recommended operating sizes and
not memory guarantees.

Authoritative contract:

- `docs/resource-limits.md`

## Performance expectations

The current implementation is a whole-file Python implementation.

Reproducible qualification has exercised:

```text
empirically qualified point scale   = 2,000,000
empirically qualified segment scale = 100,000

configured point ceiling            = 10,000,000
configured segment ceiling          = 1,000,000
```

Configured ceilings must not be interpreted as routine-performance guarantees.

Observed behavior over the qualified benchmark range is approximately
sample-count scaling rather than evidence of quadratic growth, but encoding is
CPU-heavy at large scales.

Adaptive segmentation is the primary encode hotspot.

Decode is materially faster than encode in the measured workloads.

Large workloads can also have substantial resident-memory overhead beyond the
logical encoded size.

Applications expecting workloads materially beyond the empirically qualified
scale must benchmark their own hardware and operating environment.

Authoritative evidence:

- `docs/performance-benchmark.md`
- `docs/large-file-qualification.md`

## Operational observability

Available inspection surfaces include:

```text
lasagna2 info
lasagna2 info -v
lasagna2 export-tags
lasagna2 export-motifs
lasagna2 export-profile
```

`info` reports wire version, file size, point count, sampling metadata, unit,
segment count and compression information. Verbose mode additionally reports
segment-level/statistical information.

The export commands expose derived segment/tag/motif/profile information for
diagnostic use.

These interfaces reduce the need for manual binary inspection, but they are not
integrity checks.

Production-readiness Gate 18 remains `PARTIAL`: the repository does not yet
claim a complete operational observability contract covering every required
error-taxonomy/actionability/version-reporting expectation.

Therefore:

```text
INSPECTION TOOLING = AVAILABLE
FULL OBSERVABILITY QUALIFICATION = NOT YET COMPLETE
```

## Migration guidance

The v0.3.0 baseline changed the implicit encode default from V1 to V2:

```text
v0.2.2:
    encode_timeseries() -> V1
    lasagna2 encode      -> V1

v0.3.0:
    encode_timeseries() -> V2
    lasagna2 encode      -> V2
```

Decoding remains compatible with both V1 and V2.

If byte-compatible V1 output is required, request it explicitly:

Python:

```python
encoded = encode_timeseries_v1(ts)
```

CLI:

```bash
lasagna2 encode \
  input.csv \
  output-v1.lsg2 \
  --dt 1 \
  --t0 1970-01-01T00:00:00Z \
  --unit arbitrary \
  --format-version 1
```

V1 currently has no removal schedule.

Future wire-version migration must follow:

- `docs/release-versioning-policy.md`

Future Python/CLI migration must follow:

- `docs/public-api-contract.md`

Decode-and-re-encode migration of lossy data must not be described as bitwise or
numerically lossless.

## Known non-goals and unsupported capabilities

The current production-qualification baseline does not claim:

```text
multivariate codec support
streaming encode/decode
random-access decode as a baseline capability
cryptographic authentication
intrinsic corruption checksum
archival losslessness
universal compression superiority
universal throughput guarantees
universal peak-RSS guarantees
full numeric-domain qualification
full operational-observability qualification
```

Multivariate and random-access/streaming capabilities are outside the current
univariate whole-file baseline unless separately advertised and qualified.

## Operator checklist

Before adopting Lasagna for a deployment:

1. Confirm that univariate whole-file processing matches the application.
2. Confirm that lossy reconstruction is acceptable.
3. Measure application-specific reconstruction error on representative data.
4. Confirm that input sizes fit both configured limits and practical deployment
   resources.
5. Treat input files as untrusted and retain ordinary filesystem security
   controls.
6. Do not treat `info` as an integrity check.
7. Pin package/release expectations and supported wire versions explicitly.
8. Use explicit V1 encoding only when legacy byte compatibility is required.
9. Benchmark representative production workloads on deployment hardware.
10. Review unresolved mandatory gates in `docs/production-readiness.md`.

## Authority map

Operational topic | Authoritative source
--- | ---
Production-readiness state | `docs/production-readiness.md`
Python API / CLI compatibility | `docs/public-api-contract.md`
Package / wire / migration policy | `docs/release-versioning-policy.md`
Resource ceilings | `docs/resource-limits.md`
Threat model / accepted security risks | `docs/security-review.md`
Fuzzing qualification | `docs/fuzzing-qualification.md`
Performance behavior | `docs/performance-benchmark.md`
Large-file behavior | `docs/large-file-qualification.md`
Rate-distortion semantics | `docs/rate-distortion-design.md`
External-data qualification | `docs/external-qualification.md`

## Production-readiness boundary

This document completes the operational-documentation requirement.

It does not by itself make Lasagna production-ready.

The controlling rule remains:

```text
Lasagna is production-ready only when every mandatory gate in
docs/production-readiness.md is PASS and the parent tracker #12 satisfies its
final closure audit.
```

Until then, Lasagna continues to identify itself as experimental.
