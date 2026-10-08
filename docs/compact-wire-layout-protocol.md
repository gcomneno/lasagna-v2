# Compact Segment Wire Layout Experiment

Status: FROZEN BEFORE IMPLEMENTATION

Issue: #26

Baseline:

```text
6dd330b1b7162fca33607e3b131f6bff4b28d5df
```

## Purpose

Test whether the predictor-specific compact representation established by #25
can be realized as a real binary wire format with exact V2 reconstruction
semantics and strict fail-closed decoding.

This experiment does not promote a new public format.

## Immutable boundaries

The experiment must not alter:

```text
V1 wire format
V2 wire format
public default format
segmentation
predictor selection
quantization
residual integers
residual payload encoding
distortion
#24 evidence
#25 evidence
```

The public encoder remains V2.

The public decoder continues to support only the currently public versions.

The compact format is internal and opt-in.

## Experimental version

The prototype uses:

```text
FORMAT_VERSION_EXPERIMENTAL_COMPACT = 3
```

Version 3 is experimental only.

Its existence in this experiment does not itself authorize public format
promotion.

## Serialization rules

All integer values are little-endian fixed-width values.

All real metadata is IEEE-754 binary32.

Python struct layouts must use the `<` prefix so no native alignment or
padding is introduced.

No padding bytes, delimiters, or per-payload headers exist beyond the grammar
defined below.

## Exact wire grammar

```text
FILE :=
    FILE_HEADER
    CONTEXT[header_len]
    CODING_HEADER
    SEGMENT_PAIR repeated exactly n_segments times
    EOF
```

### File header

Unchanged physical structure:

```text
<4sHHIIIII>
28 bytes
```

Fields:

```text
magic        = b"LSG2"
version      = 3
flags        = 0
header_len   : uint32
n_points     : uint32
n_segments   : uint32
reserved1    = 0
reserved2    = 0
```

### Context

The context JSON bytes are identical to the V2 context representation.

### Coding header

Unchanged physical structure:

```text
<IIII>
16 bytes
```

Fields:

```text
coding_type:
    0 = RAW_INT32
    1 = ZIGZAG_VARINT
    2 = ZERO_RUN_VARINT

reserved1 = 0
reserved2 = 0
reserved3 = 0
```

The coding header appears before the first segment pair.

## Segment pair

```text
SEGMENT_PAIR :=
    RECORD
    PAYLOAD[payload_length]
```

Segment identity is its zero-based order in the stream.

Absolute sample position is derived from cumulative segment lengths.

Residual sample count equals segment_length.

## Common prefix

Exact struct format:

```text
<IBfI
```

Exact size:

```text
13 bytes
```

Fields and offsets:

```text
0..3    segment_length : uint32
4       predictor_type : uint8
5..8    quant_step_Q   : binary32
9..12   payload_length : uint32
```

## Predictor-specific records

### Mean

```text
<IBfIf
17 bytes
```

Fields:

```text
segment_length
predictor_type = 0
quant_step_Q
payload_length
mean : binary32
```

### Linear

```text
<IBfIff
21 bytes
```

Fields:

```text
segment_length
predictor_type = 1
quant_step_Q
payload_length
slope     : binary32
intercept : binary32
```

### Random walk

```text
<IBfIf
17 bytes
```

Fields:

```text
segment_length
predictor_type = 2
quant_step_Q
payload_length
seed_value : binary32
```

## Explicitly removed fields

The compact record does not serialize:

```text
start_idx
end_idx
seg_id
seg_len
unused predictor parameters
```

They are replaced by the following identities:

```text
start[0] = 0

start[k]
=
sum(segment_length[j] for j < k)

end[k]
=
start[k] + segment_length[k] - 1

seg_id
=
k

seg_len
=
segment_length[k]
```

## Payload length

payload_length is retained for every residual codec.

For RAW_INT32 it is redundant by design and must satisfy:

```text
payload_length == 4 * segment_length
```

The field is not conditionally removed because the experiment freezes one
simple record grammar independent of residual coding.

## V2 semantic equivalence

The retained predictor metadata is exactly:

```text
mean:
    mean
    Q

linear:
    slope
    intercept
    Q

random-walk:
    seed_value
    Q
```

Every retained float must preserve the exact four-byte binary32 representation
used by V2.

Reconstruction arithmetic remains the existing V2 arithmetic after lossless
widening of binary32 metadata.

No reconstruction arithmetic is performed in binary32.

## Random-walk rule

Random-walk remains segment-local.

For each segment:

```text
first reconstructed sample
=
seed_value + residual[0] * Q

later reconstructed sample
=
previous reconstructed sample + residual[i] * Q
```

The first residual is always preserved.

The experiment must preserve the current asymmetry:

```text
encoder:
later prediction uses previous original sample

decoder:
later prediction uses previous reconstructed sample
```

No cross-segment predictor dependency is introduced.

## Decoder invariants

The prototype decoder must fail closed.

### Envelope

Require:

```text
complete file header
magic == b"LSG2"
version == 3
flags == 0
reserved header fields == 0
bounded complete context
valid context JSON
complete coding header
reserved coding fields == 0
coding_type in {0, 1, 2}
```

### Resource bounds

Reuse current documented resource ceilings where applicable.

Require at least:

```text
n_points <= 10_000_000
n_segments <= 1_000_000
```

For non-empty data:

```text
1 <= n_segments <= n_points
```

Require:

```text
n_points == 0 iff n_segments == 0
```

Reject declarations that would exceed bounds before allocation or expansion.

### Segment parsing

Parse exactly n_segments record/payload pairs.

Each segment_length must be:

```text
> 0
<= MAX_SEGMENT_POINTS
<= n_points - cumulative_length
```

Validate the common prefix first.

Validate predictor_type before selecting the suffix size.

Unknown predictor tags fail closed.

### Float validation

Every serialized segment float must be finite.

Q must be:

```text
finite
> 0
```

Reject:

```text
+0 Q
-0 Q
negative Q
NaN
infinity
```

Positive binary32 subnormal Q remains valid.

Signed zero in other finite metadata remains valid.

### Coverage

After every segment:

```text
cumulative_length += segment_length
```

Final requirement:

```text
cumulative_length == n_points
```

### Payload framing

Require:

```text
payload_length > 0
payload_length <= MAX_RESIDUAL_BLOCK_BYTES
payload_length <= remaining input bytes
```

Variable-length codecs must additionally satisfy the existing bounded-token
resource policy, including a bound no greater than:

```text
10 * segment_length
```

Decode only inside the declared payload slice.

### RAW_INT32

Require:

```text
payload_length == 4 * segment_length
```

Decode exactly segment_length little-endian signed int32 residuals.

### ZigZag varint

Require:

```text
bounded tokens
no unterminated token
signed-int32 ZigZag range only
exactly segment_length residuals
complete payload consumption
```

Unused bytes inside the payload are invalid.

### Zero-run varint

Require:

```text
bounded tokens
signed-int32 literal range
valid run marker
run length >= 3
run length <= remaining residual count
exactly segment_length residuals
complete payload consumption
```

### EOF

After exactly n_segments segment/payload pairs:

```text
cursor == len(input)
```

Whole-file trailing bytes are invalid.

### Failure behavior

Malformed input must produce a controlled exception.

The decoder must never return a successfully decoded partial series.

## Prototype implementation strategy

The semantic control is canonical V2 output.

The prototype should derive its compact representation from the same
V2-rounded metadata and the same final encoded residual payloads.

It must not substitute pre-rounding or V1-semantic residuals.

The prototype may internally repack canonical V2 evidence or share lower-level
helpers only if bit equivalence is demonstrated.

## Mandatory pre-corpus tests

Before the frozen #24 corpus is executed, test all of:

```text
predictors:
    mean
    linear
    random-walk

residual codecs:
    raw
    varint
    zero-run

predictor × codec combinations:
    all 9

segment topology:
    singleton
    one longer segment
    multiple unequal segments
    short final segment
    mixed predictor tags

encoder integration:
    fixed segmentation
    adaptive segmentation
    predictor auto
    residual auto including tie behavior

numeric edges:
    positive residuals
    negative residuals
    signed-int32 endpoints
    zero runs length 2
    zero runs length 3
    long zero runs
    rounding-sensitive metadata
    signed zero
    positive subnormal Q
    nonzero first random-walk residual
```

## Exact equivalence gates

For every valid comparison case, require exact equality of:

```text
segment boundaries after derivation
predictor tags
Q binary32 bits
active predictor parameter binary32 bits
decoded residual integers
encoded residual payload bytes
context bytes
reconstructed binary64 sample bits
```

Approximate numeric comparison is insufficient for these gates.

## Malformed-stream qualification

The prototype must reject at least:

```text
truncated file header
truncated context
truncated coding header
truncated common prefix
truncated predictor suffix
truncated payload
unknown version
invalid flags
nonzero reserved fields
unknown predictor tag
unknown residual codec
zero segment length
oversized segment length
undercoverage of n_points
overcoverage of n_points
incorrect segment count
NaN metadata
infinite metadata
zero Q
negative Q
raw payload length mismatch
unterminated varint
oversized varint
out-of-range residual
invalid zero-run marker
zero-run shorter than minimum
zero-run exceeding remaining count
decoded residual count mismatch
extra bytes inside payload
whole-file trailing bytes
oversized declarations
resource-bound violations
```

## Accounting identity

For every valid prototype stream:

```text
encoded_bytes
=
28
+ context_length
+ 16
+ 17 * mean_segment_count
+ 21 * linear_segment_count
+ 17 * random_walk_segment_count
+ sum(payload_length)
```

The measured byte count must equal the actual serialized byte length exactly.

## Corpus execution

Only after all pre-corpus gates pass may the frozen #24 matrix be used.

No #24 parameter, dataset, architecture, C_Q value, segment boundary, predictor
choice, or residual payload may be retuned.

For every frozen #24 point require:

```text
prototype reconstruction bits == V2 reconstruction bits
prototype retained metadata bits == V2 retained metadata bits
prototype residual payload bytes == V2 residual payload bytes
actual prototype byte count == accounting formula
actual prototype byte count == #25 projected encoded bytes
```

## Frozen success criteria

The experiment is PASS only if all of the following hold:

```text
1. record sizes are exactly:
       mean        17 bytes
       linear      21 bytes
       random-walk 17 bytes

2. all mandatory pre-corpus valid-stream equivalence tests pass

3. all mandatory malformed-stream qualification tests pass

4. complete frozen #24 corpus executes without semantic mismatch

5. every #24 prototype stream satisfies exact byte accounting

6. every #24 prototype stream equals the corresponding #25 projected
   encoded-byte count

7. V1 and V2 encoded fixtures remain byte-identical

8. the public default remains V2

9. the public decoder continues to reject experimental version 3
```

No numerical threshold may be relaxed after execution begins.

## Outcome classes

### PASS

All frozen success criteria pass.

The compact format is technically realizable and may proceed to a separate
promotion/design decision.

### PARTIAL

The fixed-width compact grammar is realizable for only a proper subset of the
frozen contract, or exact accounting succeeds but equivalence/safety does not.

Preserve the result. Do not promote the format.

### FAIL

The 17/21/17-byte grammar cannot safely preserve the frozen semantics, fails
bounded decoding, or does not realize #25 accounting.

Do not promote the format.

## Explicitly deferred

Not part of #26:

```text
public V3 promotion
changing the default format
cost-aware segmentation
Tensor View
metadata varints
metadata delta coding
segment dictionaries
cross-segment predictors
ASHAPES
PETRA
COLLATZ
```

## Recovery point

If #26 fails:

```text
LASAGNA_BASELINE=6dd330b1b7162fca33607e3b131f6bff4b28d5df
```

V1 and V2 remain the production formats.
