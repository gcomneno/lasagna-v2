# Production threat model and parser security review

Issue: #16 — `security: perform production threat-model and parser review`

Status:

```text
SECURITY REVIEW = PASS
CRITICAL FINDINGS = 0
HIGH FINDINGS = 0
REQUIRED CODE FINDINGS = RESOLVED
PRODUCTION-READINESS GATE 10 = PASS
```

Audited baseline:

```text
89b3f31163327d9eba32d5c31a56041f59c6145b
```

The audit was performed after completion of:

```text
#13 fuzzing qualification
#14 resource-limit enforcement
#15 large-file qualification
```

The review covers the production whole-file V1/V2 decoder and CLI boundary for
untrusted `.lsg2` input.

## Threat model

### Assets

The security-relevant assets are:

```text
process availability
decoded numeric samples
decoded metadata
operator filesystem contents
build and release integrity
```

### Trust boundaries

Untrusted `.lsg2` bytes cross several boundaries:

```text
file framing
context JSON parsing
segment metadata parsing
residual decoding
allocation and reconstruction
```

CLI arguments independently select input and output filesystem paths.

Build tooling, Python packages and GitHub Actions form a separate supply-chain
trust boundary.

### Attacker capabilities

An attacker controlling only an `.lsg2` stream may supply:

```text
malformed or truncated framing
maximum permitted point/segment declarations
oversized or malformed context metadata
malformed varints
invalid residual framing
numerically corrupted metadata
structurally valid but semantically altered samples
trailing data
```

Control over output paths, dependencies or CI configuration requires additional
capabilities and is not implied by control of file contents.

### Non-goals

The current baseline does not claim:

```text
cryptographic authenticity
detection of every possible corruption
streaming decode
partial-decode implementation
protection against an operator deliberately choosing a destructive output path
```

## Findings

### S01 — malformed context shape/type

Severity:

```text
MEDIUM
```

Disposition:

```text
FIXED
```

Before this review, syntactically valid JSON such as:

```text
[]
null
{"sampling":[]}
{"sampling":{"dt":[]}}
{"sampling":{"dt":null}}
{"sampling":{"dt":<very large integer>}}
```

could escape the malformed-input contract with:

```text
AttributeError
TypeError
OverflowError
```

rather than `ValueError`.

The fix introduces shared context parsing/shape validation for the decoder and
CLI metadata consumers while preserving existing defaults and accepted
float-convertible `dt` values.

V1 and V2 regression tests cover all reproduced cases.

The structured fuzz campaign now includes the same malformed context families.

Canonical post-fix fuzz qualification:

```text
seed = 20261006
iterations per target = 25,000
targets = 3
total cases = 75,000
unexpected crashes = 0
```

### S02 — plain-varint residual suffix bytes

Severity:

```text
LOW
```

Disposition:

```text
DOCUMENT / ACCEPT COMPATIBILITY
```

`decode_int_list_varint()` decodes the declared residual count and tolerates
remaining bytes inside the framed residual payload.

Raw residual decoding instead requires:

```text
byte_len == 4 * seg_len
```

and zero-run varint decoding consumes the payload while enforcing the declared
decoded count.

Tightening ordinary-varint consumption would reject streams accepted by the
historical V1/V2 decoder.

No demonstrated security requirement justifies changing that compatibility
behavior in issue #16.

Residual framing and total input size remain bounded.

### S03 — V1/V2 numeric and structural differential

Severity:

```text
LOW
```

Disposition:

```text
DOCUMENT
```

Legacy V1 semantics are intentionally more permissive than V2.

V1 may accept:

```text
non-finite predictor metadata
non-positive quantization Q
gaps between segments
overlapping segments
non-empty point declarations with no segments
```

V1 gaps leave corresponding output positions zero-filled.

V1 overlaps allow later segments to overwrite previously reconstructed sample
positions.

V2 instead requires:

```text
contiguous complete sample coverage
finite segment metadata
Q > 0
```

Applying the stricter V2 policy retroactively to V1 would materially change
legacy compatibility.

Resource/work amplification remains bounded by the common preflight.

### S04 — metadata inspection is not proof of full decodability

Severity:

```text
LOW
```

Disposition:

```text
DOCUMENT
```

`read_lsg2_metadata_and_segments()` performs common structural/resource
preflight but intentionally does not fully decode residual payloads.

Metadata inspection may therefore succeed for a stream that later fails full
numeric decode.

The inspection interface must not be interpreted as a complete integrity or
decodability check.

### S05 — accepted maximum workloads can exhaust small deployments

Severity:

```text
MEDIUM
```

Disposition:

```text
ACCEPT
```

A structurally valid compressed stream may request work close to the configured
resource ceilings.

The parser enforces logical ceilings but does not promise:

```text
a fixed process RSS ceiling
a request deadline
a concurrent-service capacity
```

Empirical qualification currently covers:

```text
2,000,000 points
100,000 segments
```

with the 2M V2 decode reaching approximately:

```text
541 MiB peak RSS
```

Services exposing Lasagna to untrusted workloads must apply deployment-specific
request, concurrency and memory budgets.

### S06 — V2 widening memory amplification

Severity:

```text
INFO
```

Disposition:

```text
ACCEPT
```

V2 currently widens each 32-byte L32 segment entry into the V1-style semantic
representation before reconstruction.

Preflight occurs before widening.

The conservative logical representation allowance documented by the resource
contract is:

```text
MAX_INPUT_BYTES + 32 * MAX_SEGMENTS
= 208,065,580 bytes
```

This excludes Python object and allocator overhead and is not an RSS guarantee.

No resource-limit bypass was found.

Future optimization may remove the widening without changing the frozen V2
wire format.

### S07 — file-level trailing bytes

Severity:

```text
INFO
```

Disposition:

```text
ACCEPT
```

Bytes following the final expected residual block are currently ignored.

This is established compatibility behavior and remains bounded by:

```text
MAX_INPUT_BYTES
```

Trailing bytes:

```text
are not interpreted
are not integrity-protected
are not an approved mechanism for extending frozen V2
```

An embedded V2 extension must not rely on this tolerance.

### S08 — no intrinsic checksum or authentication

Severity:

```text
INFO
```

Disposition:

```text
ACCEPT
```

Structural validation is not an integrity or authenticity mechanism.

A structurally valid byte mutation may decode successfully and alter numeric
output without detection.

Applications requiring authenticity or end-to-end corruption detection must
provide an external integrity/authentication boundary.

No checksum is required to close Gate 10.

Adding embedded integrity metadata would require an explicitly designed format
or container revision.

### S09 — CLI overwrite/symlink/non-atomic output semantics

Severity:

```text
LOW
```

Disposition:

```text
ACCEPT FOR LOCAL CLI
```

CLI output paths are supplied by the operator rather than extracted from
untrusted `.lsg2` metadata.

Current writers may:

```text
overwrite existing files
follow symlinks
leave partial output after a write failure
destroy the source if input and output paths are deliberately made identical
```

These effects require path/invocation control and are not triggered by file
contents alone.

Operators must use trusted output destinations and normal filesystem
permissions.

### S10 — terminal and spreadsheet interpretation of metadata

Severity:

```text
LOW
```

Disposition:

```text
DOCUMENT
```

Untrusted metadata strings may reach terminal output or CSV fields.

CSV quoting does not neutralize spreadsheet formula interpretation, and
terminal control characters can affect presentation.

Consumers opening exported metadata in formula-capable spreadsheet software
must treat cells as untrusted data.

Changing metadata escaping at the codec layer would alter the represented
value and is not required for parser qualification.

### S11 — supply-chain residual risk

Severity:

```text
LOW
```

Disposition:

```text
NONBLOCKING HARDENING
```

The Lasagna runtime has:

```text
zero project runtime dependencies
```

Development and build tooling still relies on the Python packaging ecosystem,
registry resolution and CI Actions.

Most Actions are SHA-pinned and workflow permissions are scoped.

One `pip-audit` Action reference remains tag-based and development/build
dependencies are not completely hash-locked.

This is useful future hardening but is not a parser-security blocker for issue
#16.

## Parser differential summary

The review explicitly identified the following V1/V2 or codec differences.

### Ordinary varint

Both V1 and V2 tolerate suffix bytes within an ordinary-varint residual block
after the declared number of values has decoded.

### Zero-run varint

Zero-run decoding consumes the payload and enforces the declared result count.

### Raw residuals

Raw residual blocks require an exact payload size:

```text
4 * seg_len
```

### V1 segment semantics

V1 preserves historical gap/overlap behavior.

### V2 segment semantics

V2 requires contiguous complete coverage and validates finite L32 metadata and
positive `Q`.

### Context metadata

The shared context parser now provides consistent malformed-shape/type
rejection for both versions.

The review does not introduce a finite-`dt` policy; that remains part of the
supported numeric-domain work.

## Integer and offset safety

No wrapping integer or offset defect was found.

Wire size/count fields are unsigned fixed-width integers.

Internal cursor arithmetic uses Python integers and therefore does not wrap.

Preflight validates buffer extents and resource ceilings before decoder
amplification.

The supported maximum derived external input allowance:

```text
176,065,580 bytes
```

is below:

```text
UINT32_MAX = 4,294,967,295
```

Ordinary varints permit a terminating tenth byte and therefore may represent up
to 70 payload bits.

Continuation beyond the ten-byte token policy fails closed.

Nonminimal varint encodings are accepted compatibility behavior, not integer
overflow.

## Corruption semantics

The production whole-file codec now explicitly defines the following.

Detected corruption includes structural violations such as:

```text
truncation
invalid magic
unsupported wire version
resource-limit violations
malformed context JSON/shape
invalid segment extents
invalid predictor identifiers
invalid residual coding identifiers
duplicate/missing residual blocks
declared residual count mismatch
raw payload size mismatch
residual payload truncation
malformed overlong varints
invalid zero-run lengths/counts
```

Potentially undetected corruption includes:

```text
structurally valid numeric changes
ordinary-varint suffix bytes
accepted file-level trailing bytes
legacy V1 numeric/segment behaviors
```

No intrinsic checksum or authentication exists.

Random-walk corruption may propagate through later samples in the same segment.

V1 overlapping segments may alter shared output positions according to legacy
reconstruction order.

The baseline product is whole-file decode.

Partial-decode corruption isolation remains an architectural contract in
`docs/access-architecture.md`, not a currently advertised production feature.

## Resource and CPU amplification

Allocation and work amplification are bounded by the resource contract:

```text
MAX_POINTS
MAX_SEGMENTS
MAX_SEGMENT_POINTS
MAX_CONTEXT_BYTES
MAX_CONTEXT_DEPTH
MAX_VARINT_BYTES
MAX_RESIDUAL_BLOCK_BYTES
MAX_INPUT_BYTES
```

The bounds are parser safety ceilings, not service-level capacity guarantees.

Large-file qualification must be used when selecting production deployment
budgets.

## CLI filesystem boundary

Decode/info/export input reads use:

```text
open once
fstat the open descriptor
reject reported oversize
read at most MAX_INPUT_BYTES + 1
reject actual oversize
```

This avoids an unbounded whole-file read and avoids a `stat -> reopen` race.

The bounded-read policy does not protect against every special-file behavior;
deployments processing arbitrary filesystem objects should constrain their
input environment.

Output destination policy remains an operator responsibility.

## Supply-chain posture

Runtime:

```text
project dependencies = none
```

Existing CI controls include:

```text
dependency review
CodeQL
pip-audit
OpenSSF Scorecard
harden-runner
scoped workflow permissions
SHA-pinned Actions in most workflow steps
```

These controls reduce risk but do not substitute for parser review.

Future hardening may pin remaining mutable Action references and adopt stronger
dependency locking.

## Accepted residual risks

The following risks are explicitly accepted for the present production
qualification:

```text
file-level trailing-byte tolerance
ordinary-varint residual suffix tolerance
absence of intrinsic checksum/authentication
legacy V1 semantic differences
whole-file memory model
V2 widening memory amplification
local CLI overwrite/symlink semantics
metadata terminal/CSV interpretation responsibility
normal Python/package/CI supply-chain residual risk
```

None is represented as stronger protection than the available evidence
supports.

## Qualification evidence

Primary evidence:

```text
docs/resource-limits.md
docs/fuzzing-qualification.md
docs/fuzzing-qualification-results.json
docs/large-file-qualification.md
tests/test_decode_malicious.py
tests/test_resource_limits.py
tests/test_fuzz_qualification.py
tests/test_large_file_qualification.py
.github/workflows/security.yml
.github/workflows/supply-chain.yml
```

Issue #16 additionally added:

```text
shared context shape/type validation
V1/V2 malformed-context regressions
CLI metadata-context regressions
structured malformed-context fuzz mutations
```

## Gate conclusion

```text
UNTRUSTED_INPUT_MODEL_GATE=PASS
ALLOCATION_ATTACK_GATE=PASS
CPU_AMPLIFICATION_GATE=PASS
MALFORMED_VARINT_GATE=PASS
OVERSIZED_METADATA_GATE=PASS
INTEGER_OFFSET_GATE=PASS
TRAILING_DATA_POLICY_GATE=PASS
PARSER_DIFFERENTIAL_GATE=PASS
SUPPLY_CHAIN_REVIEW_GATE=PASS
CLI_FILESYSTEM_REVIEW_GATE=PASS

CRITICAL_FINDINGS_RESOLVED_GATE=PASS
HIGH_FINDINGS_RESOLVED_GATE=PASS
S01_CONTEXT_VALIDATION_GATE=PASS
RESIDUAL_RISK_DOCUMENTATION_GATE=PASS

PRODUCTION_READINESS_GATE_3=PASS
PRODUCTION_READINESS_GATE_6=PASS
PRODUCTION_READINESS_GATE_10=PASS
```

## Encoder numeric-domain hardening — Issue #21

The production encoder now rejects unsupported numeric input before emitting
LSG2 bytes.

The enforced encoder domain requires finite real samples, finite positive
`dt`, finite `C_Q >= 0`, finite `Q_MIN > 0`, finite
`mse_threshold >= 0`, valid active segment-length controls and signed-int32
quantized residuals.

Arithmetic overflow and non-finite statistics, prediction-error measurements,
quantization intermediates or residual ratios are normalized to `ValueError`.

The signed-int32 residual bound is enforced before every production residual
representation. `zigzag_encode()` independently enforces the same bound, so
direct varint and zero-run helper use cannot silently encode integers outside
the intended ZigZag domain.

V2 also rechecks residuals after segment metadata has been rounded through the
frozen binary32 layout.

This hardening affects encoder acceptance only. Historical V1 decoder behavior
is intentionally preserved for compatibility and remains broader than the set
of values a new encoder is permitted to emit.
