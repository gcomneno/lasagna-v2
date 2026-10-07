# Public API stability and deprecation contract

Issue: #17 — `api: freeze public API stability and deprecation policy`

Status:

```text
PUBLIC API CONTRACT = FROZEN
PYTHON API SURFACE = EXPLICIT
CLI SURFACE = EXPLICIT
DEPRECATION POLICY = FROZEN
PRODUCTION-READINESS GATE 11 = PASS
```

This contract applies to the current Lasagna 0.3.x production-qualification
baseline.

It defines which Python and CLI interfaces callers may rely on and which
repository symbols remain implementation details.

It does not define wire-version lifetime or future V3 migration policy. Those
remain release/versioning work under issue #18.


## Encoder numeric-domain contract

Production encoding accepts finite real-valued samples and finite encoder
controls within the following domain:

```text
samples               finite Python int/float values
dt                    finite and > 0
C_Q                   finite and >= 0
Q_MIN                 finite and > 0
mse_threshold         finite and >= 0
fixed segment_length  positive integer
adaptive min length   positive integer
adaptive max length   positive integer and >= min length
quantized residual    signed int32:
                      -2147483648 .. 2147483647
```

`TimeSeries` remains a lightweight data container. Construction itself does not
reject unsupported numeric values; validation occurs when a public encoder is
called.

`encode_timeseries()`, `encode_timeseries_v1()` and `encode_timeseries_v2()`
apply the same production numeric-domain validation before segmentation.

Unsupported numeric inputs, arithmetic overflow, non-finite intermediate
statistics, invalid quantization state, metadata representability failures and
out-of-range quantized residuals fail with `ValueError`.

Exact exception messages are diagnostic rather than API-stable.

`C_Q=0` is valid when `Q_MIN > 0`; this selects the positive quantization floor.

V2 preserves the frozen binary32 metadata representation. Its serialized real
segment fields must remain finite and its rounded quantization step must remain
strictly positive. Non-Q metadata may underflow to signed zero. A positive
binary32 subnormal `Q` is valid; a `Q` that rounds to zero is rejected.

Every newly encoded residual is restricted to signed int32 regardless of
residual representation. This applies to raw, varint, zero-run and automatic
V2 selection, and prevents out-of-domain ZigZag values from being emitted.

The stricter encoder contract does not change historical decode compatibility.
Existing V1 artifacts retain their legacy decoder semantics, including numeric
cases that new encoders no longer produce.

## Public Python surface

The supported Python API is exactly the package export surface:

```python
from lasagna2 import (
    TimeSeries,
    encode_timeseries,
    encode_timeseries_v1,
    encode_timeseries_v2,
    decode_timeseries,
)
```

Equivalent contract:

```text
lasagna2.__all__ =
    TimeSeries
    encode_timeseries
    encode_timeseries_v1
    decode_timeseries
    encode_timeseries_v2
```

Ordering in `__all__` is not a compatibility guarantee.

Presence and importability of these names are guaranteed unless they complete
the deprecation process defined below.

## TimeSeries contract

Public constructor:

```python
TimeSeries(
    values: List[float],
    dt: float = 1.0,
    t0: str = "1970-01-01T00:00:00Z",
    unit: str = "unknown",
)
```

Public attributes:

```text
values
dt
t0
unit
```

The current object is a dataclass.

The compatibility guarantee covers:

```text
constructor parameter names
constructor parameter order
constructor defaults
public attribute names
```

It does not promise that every future implementation detail of the dataclass
mechanism itself will remain observable.

## encode_timeseries()

Stable signature:

```python
encode_timeseries(
    ts: TimeSeries,
    segment_length: int = 64,
    predictor: str = "linear",
    C_Q: float = 0.125,
    Q_MIN: float = 1e-6,
    segment_mode: str = "fixed",
    min_segment_length: int = 32,
    max_segment_length: int = 128,
    mse_threshold: float = 0.5,
    residual_coding: str = "raw",
) -> bytes
```

Current semantic default:

```text
wire output = V2
```

The return type is:

```text
bytes
```

Changing the implicit wire-format default is an API compatibility change even
when the function signature remains unchanged.

Such a change must follow the compatibility/deprecation rules applicable at
the time of the change.

## encode_timeseries_v1()

Stable signature:

```python
encode_timeseries_v1(
    ts: TimeSeries,
    segment_length: int = 64,
    predictor: str = "linear",
    C_Q: float = 0.5,
    Q_MIN: float = 1e-6,
    segment_mode: str = "fixed",
    min_segment_length: int = 32,
    max_segment_length: int = 128,
    mse_threshold: float = 0.5,
    residual_coding: str = "raw",
) -> bytes
```

Return type:

```text
bytes
```

Semantic role:

```text
explicit legacy V1 encoding
```

The V1-specific `C_Q=0.5` default is part of the current API contract.

Wire-format support lifetime itself is governed separately by the release and
wire-version policy.

## encode_timeseries_v2()

Stable signature:

```python
encode_timeseries_v2(
    ts: TimeSeries,
    segment_length: int = 64,
    predictor: str = "linear",
    C_Q: float = 0.125,
    Q_MIN: float = 1e-6,
    segment_mode: str = "fixed",
    min_segment_length: int = 32,
    max_segment_length: int = 128,
    mse_threshold: float = 0.5,
    residual_coding: str = "raw",
) -> bytes
```

Return type:

```text
bytes
```

Semantic role:

```text
explicit frozen V2 L32 encoding
```

## decode_timeseries()

Stable signature:

```python
decode_timeseries(
    data: bytes,
) -> TimeSeries
```

Current supported behavior:

```text
V1 decode
V2 decode
unknown wire version -> fail closed
```

Return type:

```text
TimeSeries
```

Changes to supported wire-version lifetime are not decided by this API
contract alone and require the release/versioning policy.

## Argument compatibility

For the supported Python API, the following are compatibility-sensitive:

```text
parameter removal
parameter rename
parameter reordering when positional use is possible
new required parameter
default-value change
accepted-value narrowing
semantic reinterpretation of an existing parameter
```

A new optional parameter with a backward-compatible default may be added
without deprecating the existing call shape.

A compatibility-sensitive change must follow the deprecation process unless it
is covered by the emergency exception below.

## Return-type compatibility

The documented return types are stable:

```text
TimeSeries(...)        -> TimeSeries instance
encode_timeseries(...) -> bytes
encode_timeseries_v1() -> bytes
encode_timeseries_v2() -> bytes
decode_timeseries(...) -> TimeSeries
```

Changing one of these return types is a breaking public-API change.

Adding new behavior inside the documented return type is not automatically
breaking, but observable semantics must still respect the relevant codec and
wire contracts.

## Exception compatibility

The public exception contract is intentionally category-based rather than
message-based.

### Python codec validation failures

Malformed or unsupported encoded input and documented codec validation
failures use:

```text
ValueError
```

Callers may rely on the exception class.

Exact exception text is diagnostic and is not a stable compatibility
interface.

### Invalid Python invocation/types

Programming errors outside the documented input contract may raise ordinary
Python exceptions such as:

```text
TypeError
ValueError
```

unless a more specific public guarantee is documented.

The project does not guarantee every accidental internal exception type for
unsupported caller misuse.

### Resource-policy rejection

Configured codec/resource-limit rejection uses:

```text
ValueError
```

Exact message wording is not stable.

### Filesystem failures

CLI and file-oriented helper behavior may propagate normal operating-system
exceptions/errors produced by opening, reading or writing paths.

The API contract does not translate every filesystem error into a
codec-specific exception.

## Explicitly private / internal Python surface

Anything not exported by `lasagna2.__all__` is outside the stable Python API
unless separately documented as public in a future contract.

This includes, without limitation:

```text
SegmentEntry
Motif
classify_segment_pattern()
extract_motifs()

zigzag_encode()
zigzag_decode()

encode_int_list_varint()
decode_int_list_varint()
encode_int_list_zero_run_varint()
decode_int_list_zero_run_varint()

compute_stats()
predict_mean_const()
predict_linear()
predict_random_walk()
quantize_residuals()

segment_series_fixed_length()
segment_series_adaptive()
build_context_json()

binary struct constants
wire constants
resource constants
parser helpers
functions beginning with "_"
lasagna2.core implementation details
lasagna2.cli implementation helpers
```

Their current accessibility from a module does not make them stable public API.

Tests and internal tools may use these symbols without converting them into
public compatibility commitments.

## Public CLI surface

The installed command is:

```text
lasagna2
```

The parser program label currently renders as:

```text
lasagna
```

The supported subcommands are:

```text
encode
decode
info
export-tags
export-motifs
export-profile
```

Removing or renaming one of these commands is a breaking CLI change.

## CLI encode contract

Command:

```text
lasagna2 encode INPUT OUTPUT
```

Required options:

```text
--dt FLOAT
--t0 STRING
--unit STRING
```

Optional arguments and current defaults:

```text
--segment-mode        adaptive
    choices: fixed, adaptive

--segment-length      64

--min-segment-length  32

--max-segment-length  128

--mse-threshold       0.5

--predictor           linear

--residual-coding     varint
    choices: raw, varint, zero-run, auto

--format-version      2
    choices: 1, 2
```

The CLI default differs intentionally from the Python encoder in two places:

```text
Python encode_timeseries():
    segment_mode = fixed
    residual_coding = raw

CLI encode:
    segment_mode = adaptive
    residual_coding = varint
```

Those CLI defaults are independently compatibility-sensitive.

## CLI decode contract

Command:

```text
lasagna2 decode INPUT OUTPUT
```

`INPUT` and `OUTPUT` are required positional arguments.

The decoder auto-detects supported V1/V2 streams.

## CLI info contract

Command:

```text
lasagna2 info INPUT
```

Optional flag:

```text
-v
--verbose
```

Default:

```text
False
```

The command is an inspection interface.

Successful metadata inspection does not constitute an integrity guarantee or
proof that every residual payload will fully decode.

## CLI export contracts

Supported commands:

```text
lasagna2 export-tags INPUT OUTPUT
lasagna2 export-motifs INPUT OUTPUT
lasagna2 export-profile INPUT OUTPUT
```

Both positional arguments are required.

The existing CSV column schemas exercised by compatibility tests are part of
the documented command behavior for the current baseline.

## CLI argument compatibility

The following are compatibility-sensitive:

```text
removing a command
renaming a command
removing an option
renaming an option without retaining an alias
changing a required argument into an incompatible shape
making an optional argument required
changing a default
removing an accepted choice
changing positional argument meaning
changing established output schema incompatibly
```

Adding a new optional flag with a backward-compatible default is normally
compatible.

Adding a new accepted choice is normally compatible unless it changes existing
default behavior.

## CLI failure compatibility

Argument parsing errors follow `argparse` behavior and terminate CLI parsing
with a non-zero status.

The exact help/error wording produced by `argparse` is not frozen.

Codec validation failures and filesystem failures remain operational errors.

The project guarantees meaningful failure, not byte-identical stderr text.

## Deprecation policy

A supported Python symbol, parameter, default, CLI command, option or
documented behavior must not be removed or incompatibly changed without a
deprecation phase, except under the emergency rule below.

Normal process:

```text
1. announce the intended incompatible change in release notes/documentation;
2. retain the existing behavior during the deprecation release;
3. provide a migration path;
4. emit a warning where technically appropriate;
5. keep the deprecated surface through at least one published package release;
6. remove or incompatibly change it only in a later published release.
```

Therefore:

```text
DEPRECATE AND REMOVE IN THE SAME RELEASE = NOT ALLOWED
```

There is no fixed wall-clock deprecation duration.

The minimum lead time is one published release boundary with the deprecated
behavior still available.

### Python warning policy

Where a runtime warning is practical, deprecated Python behavior SHOULD emit:

```python
DeprecationWarning
```

Documentation and release notes remain mandatory even when a runtime warning
is impractical.

### CLI warning policy

Where practical, deprecated CLI commands/options SHOULD remain accepted during
the deprecation phase and emit a migration warning to stderr.

The old spelling/behavior remains functional until the later removal release.

## Emergency exception

A compatibility-preserving deprecation period may be shortened only when
continuing the behavior creates a material:

```text
security vulnerability
data-loss risk
integrity failure
critical correctness defect
```

An emergency incompatible change must:

```text
be explicitly documented
identify why normal deprecation was unsafe
provide the safest available migration guidance
be called out prominently in release notes
```

Convenience, cleanup or implementation preference are not emergency reasons.

## Documentation obligations

Any public API compatibility change must update, as applicable:

```text
docs/public-api-contract.md
README.md
RELEASE_NOTES.md
CONTRIBUTING.md
tests covering the affected contract
```

CLI changes must additionally update relevant CLI examples and parser tests.

## Relationship to wire compatibility

This document governs Python and CLI API compatibility.

It does not by itself decide:

```text
minimum V1 decode lifetime
future V2 support lifetime
conditions for dropping a wire version
V3 migration requirements
package-version / wire-version relationship
release artifact policy
```

Those belong to the release/versioning contract tracked by issue #18.

Therefore completion of issue #17:

```text
Gate 11 -> PASS
Gate 1  -> remains PARTIAL
Gate 2  -> remains PARTIAL
```

## Gates

```text
PUBLIC_PYTHON_SURFACE_GATE=PASS
PYTHON_SIGNATURE_DEFAULT_GATE=PASS
RETURN_TYPE_GATE=PASS
EXCEPTION_POLICY_GATE=PASS
PRIVATE_SYMBOL_BOUNDARY_GATE=PASS

PUBLIC_CLI_SURFACE_GATE=PASS
CLI_ARGUMENT_DEFAULT_GATE=PASS
CLI_FAILURE_POLICY_GATE=PASS

DEPRECATION_PROCESS_GATE=PASS
DEPRECATION_LEAD_TIME_GATE=PASS
EMERGENCY_EXCEPTION_GATE=PASS

WIRE_POLICY_SCOPE_SEPARATION_GATE=PASS

PRODUCTION_READINESS_GATE_11=PASS
```
