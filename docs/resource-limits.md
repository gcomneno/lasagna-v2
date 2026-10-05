# Resource-limit contract

Issue: #14 — `security: define and enforce codec resource limits`

Status:

```text
RESOURCE LIMIT CONTRACT = IMPLEMENTED
WIRE FORMAT = UNCHANGED
V1 COMPATIBILITY SEMANTICS = RETAINED
V2 FROZEN L32 SEMANTICS = RETAINED
```

## Purpose

Lasagna accepts complete in-memory LSG2 streams. Production use therefore
requires explicit bounds before attacker-controlled declarations can amplify
CPU work or memory allocation.

These limits are implementation acceptance limits. They do not change the
serialized V1 or V2 field widths.

All limits are inclusive.

Exceeding a limit fails deterministically with `ValueError`.

## Limits

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

`MAX_POINTS` and `MAX_SEGMENTS` preserve the historical decoder ceilings.

`MAX_SEGMENT_POINTS == MAX_POINTS` permits the largest supported series to
remain a single segment.

`MAX_CONTEXT_BYTES` and `MAX_CONTEXT_DEPTH` are conservative production
policies for metadata that is normally tiny.

The frozen V1 compatibility corpus has a maximum observed context size of
70 bytes.

`MAX_VARINT_BYTES == 10` names and preserves the existing decoder token-length
behavior.

`MAX_RESIDUAL_BLOCK_BYTES` is derived from the worst permitted per-sample
varint storage:

```text
10 bytes/sample × 10,000,000 samples = 100,000,000 bytes
```

The external input ceiling is derived using the larger V1 segment layout:

```text
28-byte file header
+ 65,536-byte context
+ (64-byte segment entry + 12-byte residual block header) × 1,000,000
+ 10-byte residual allowance × 10,000,000
+ 16-byte residual-section header
= 176,065,580 bytes
```

## Structural preflight

Before V1 residual decoding or V2 L32-to-V1 widening, Lasagna validates:

```text
input size
header availability
magic and supported version
n_points
n_segments
context size
context nesting depth
complete segment-table extent
segment predictor identifiers
segment extents
per-segment sample count
aggregate segment sample count
residual coding identifier
complete residual-block headers
unique residual block per segment
residual seg_len == validated segment length
aggregate residual sample count
per-block byte length
raw block byte_len == 4 * seg_len
residual payload availability
```

V2 retains its existing contiguous full-coverage requirement.

V1 does not gain a V2-style continuity requirement. Historical V1 overlap/gap
semantics remain distinct, but aggregate segment work is bounded by
`MAX_POINTS`.

Trailing bytes remain tolerated because rejecting them would be a separate
compatibility decision.

## Arithmetic

Python integer arithmetic does not wrap, so Lasagna does not emulate
fixed-width checked addition for internal cursors.

Instead, it validates resource products and computed offsets against:

```text
actual buffer length
resource-policy limits
wire representability where a value is serialized
```

`UINT32_MAX` is a wire representability boundary, not an internal Python cursor
limit.

## Context parsing

Context size and nesting depth are checked before `json.loads()`.

The nesting scan is iterative and ignores brackets/braces inside JSON strings,
including escaped quotes.

This bounds parser nesting without depending on the interpreter recursion
limit.

## CLI file reads

The CLI remains a whole-file implementation.

For decode/info/export operations it now:

```text
open once
fstat the open descriptor
reject reported size > MAX_INPUT_BYTES
read at most MAX_INPUT_BYTES + 1
reject returned size > MAX_INPUT_BYTES
```

This prevents an unbounded `Path.read_bytes()` allocation and avoids the
`stat → reopen` race.

Streaming is outside issue #14 and remains governed by
`docs/access-architecture.md`.

## Encoder policy

V1, V2 and the default encoder share the same point and segment ceilings.

Encoder-side checks prevent creation of streams that the production decoder
would reject.

Context serialization is bounded.

Varint emission cannot exceed the decoder's existing ten-byte token limit.

Residual payloads and final encoded size are checked against the same production
resource contract.

This may reject pathological inputs that older encoders could emit even though
the historical decoder would later reject them.

That is an intentional production-safety restriction, not a wire-format
revision.

## Memory interpretation

The contract bounds logical collection sizes:

```text
decoded output samples      <= MAX_POINTS
aggregate residual samples  <= MAX_POINTS
segment bookkeeping         <= MAX_SEGMENTS
single sample temporary     <= MAX_SEGMENT_POINTS
```

For V2, the current widening implementation may grow the logical representation
by 32 bytes per segment:

```text
MAX_INPUT_BYTES + 32 * MAX_SEGMENTS
= 208,065,580 bytes
```

This is not an RSS guarantee.

Python object overhead, allocator behavior and temporary codec payloads may
increase peak resident memory substantially.

Measured large-file/RSS qualification remains separate work under #15 and
parent tracker #12.

## Compatibility boundary

Issue #14 does not change:

```text
V1 field layout
V2 L32 field layout
V1/V2 predictor semantics
V2 metadata rounding
reserved/padding interpretation
ten-byte varint decode behavior
trailing-byte tolerance
```

Malformed streams that previously reached accidental `IndexError`,
`struct.error` or very large residual loops are now rejected earlier with
`ValueError`.

## Gates

```text
RESOURCE_CONSTANTS_GATE=PASS
EARLY_PREFLIGHT_GATE=PASS
V1_RESOURCE_PARITY_GATE=PASS
V2_RESOURCE_PARITY_GATE=PASS
CONTEXT_BOUND_GATE=PASS
RESIDUAL_BOUND_GATE=PASS
AGGREGATE_WORK_GATE=PASS
CLI_BOUNDED_READ_GATE=PASS
ENCODER_ENFORCEMENT_GATE=PASS
WIRE_CHANGE_GATE=REJECT
```
