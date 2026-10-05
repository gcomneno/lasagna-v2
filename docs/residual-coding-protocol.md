# Residual coding research protocol

Date: 2026-10-05

Status: FROZEN BEFORE RESIDUAL MEASUREMENT

## Purpose

Issue #8 evaluates whether residual representations beyond raw int32 and
ZigZag + varint can reduce Lasagna total encoded cost.

The study is divided into two ordered phases:

```text
Phase A
measure actual quantized residual distributions

Phase B
benchmark residual codec candidates on the exact same frozen residual streams
```

No residual codec is added to the production wire before both phases provide
supporting evidence.

## Existing codec identifiers

Current constants are:

```text
RESIDUAL_CODEC_RAW_INT32        = 0
RESIDUAL_CODEC_VARINT           = 1
RESIDUAL_CODEC_ZERO_RUN_VARINT  = 2
```

IDs 0 and 1 are implemented production codecs.

ID 2 is an existing historical/reserved candidate identifier. It is not
currently accepted by the public encoder or decoder.

Issue #8 SHALL NOT reuse ID 2 for another representation.

The presence of the constant does not constitute evidence sufficient to enable
the codec.

## Frozen corpus

Use the same six datasets employed by issues #5 and #7:

```text
internal:
data/examples/trend.csv
data/examples/sine_noise.csv
data/examples/flat_spike.csv

real-world:
data/real-world/canonical/appliances-energy.csv
data/real-world/canonical/metro-traffic.csv
data/real-world/canonical/beijing-pm25.csv
```

## Frozen V2 configuration

Residual streams SHALL be generated from the current V2 semantics:

```text
format_version = 2
segment_mode = adaptive
segment_length = 64
min_segment_length = 32
max_segment_length = 128
mse_threshold = 0.5
C_Q = 0.125
Q_MIN = 1e-6
```

V2 binary32 segment metadata rounding SHALL occur before the final quantized
residual stream is derived, matching the production V2 encoder.

## Predictor strata

Measure four current predictor modes:

```text
auto
mean
linear
rw
```

Each mode SHALL use its actual current segmentation behavior.

`auto` therefore uses the current linear segmentation predictor before
per-segment predictor selection.

The explicit predictor strata are diagnostics. The current default `auto`
stream remains the primary production reference.

## Phase A: residual distribution measurements

For every dataset/predictor stream report:

```text
n_samples
segment_count
residual_count

minimum signed q
maximum signed q
maximum absolute q

zero_count
zero_fraction

positive_count
negative_count

mean_abs_q
median_abs_q
p95_abs_q
p99_abs_q

zigzag_min
zigzag_max

varint_1byte_count
varint_2byte_count
varint_3byte_count
varint_4plus_count
varint_1byte_fraction

raw_int32_payload_bytes
varint_payload_bytes

longest_zero_run
zero_run_count
mean_zero_run_length
median_zero_run_length
p95_zero_run_length

symbol_entropy_bits_per_residual
```

Entropy is the empirical Shannon entropy of the signed quantized residual
symbols:

```text
H = -sum(p(x) * log2(p(x)))
```

It is diagnostic only and is not itself an achievable codec-size claim.

## Per-block measurements

Every residual block SHALL additionally report:

```text
dataset
predictor
segment_index
segment_length
predictor_type
zero_count
zero_fraction
max_abs_q
varint_payload_bytes
varint_bytes_per_residual
longest_zero_run
symbol_entropy_bits_per_residual
```

This is required because a specialized residual codec may be useful only for a
subset of blocks.

## Varint width semantics

Varint width SHALL be measured after ZigZag conversion using the existing
production varint representation.

Width classes are:

```text
1 byte
2 bytes
3 bytes
4+ bytes
```

The measurement SHALL use the exact existing `_encode_varint()` semantics or
an exactly equivalent byte-length calculation.

## Phase B gate

Candidate codec benchmarking SHALL begin only after Phase A results exist.

At minimum Phase B SHALL include:

```text
raw int32
ZigZag + varint
zero-run + varint
```

Additional candidates may be frozen only after Phase A shows a distributional
property they are intended to exploit.

No candidate is selected because residuals merely appear suitable.

The candidate must produce a smaller measured representation.

## Same-stream rule

All Phase B codecs SHALL encode the exact same quantized integer residual
streams.

Candidate codec comparison MUST NOT alter:

```text
segmentation
predictor
quantization
V2 metadata rounding
```

This isolates residual representation from upstream modeling decisions.

## Total-file accounting

Payload bytes alone are insufficient.

For each candidate report:

```text
residual payload bytes
codec-specific framing bytes
residual section bytes
projected or actual total file bytes
```

Any per-block codec selector or marker cost SHALL be included.

## Performance

Phase B SHALL separately measure:

```text
encode latency
decode latency
```

with deterministic repeated measurements.

## Worst-case behavior

Every Phase B candidate SHALL be tested against hostile residual streams,
including at least:

```text
all zero
alternating zero/non-zero
no zeros
small signed values
large signed values
isolated zero values
single long zero run
```

Worst-case expansion relative to existing ZigZag + varint SHALL be reported.

## Selection rule

A new residual codec may be promoted only if:

```text
measurable total-file benefit exists
AND
deterministic roundtrip is demonstrated
AND
worst-case behavior is documented
AND
implementation/decode cost is characterized
```

A payload-only win that disappears after framing or codec-selection overhead
is not sufficient.

## Non-goals

Issue #8 does not:

- alter predictor selection;
- alter quantization;
- alter segmentation;
- change V1;
- enable residual codec ID 2 before evidence;
- allocate another codec ID before evidence.

## Phase B frozen candidate semantics

Phase A showed that almost all current quantized residuals already occupy one
byte under ZigZag + varint.

The first Phase B candidate therefore targets repeated zero structure rather
than smaller integer magnitude.

### Candidate: zero-run + shifted ZigZag varint

Research name:

```text
zero_run_varint
```

Historical/reserved identifier:

```text
RESIDUAL_CODEC_ZERO_RUN_VARINT = 2
```

The identifier SHALL remain disabled in the production encoder and decoder
during the experiment.

### Token representation

Literal residual `q`:

```text
token = ZigZag(q) + 1
encode token as unsigned varint
```

The `+1` reserves token value zero as a run marker.

A zero run of length at least three is encoded as:

```text
varint(0)
varint(run_length)
```

Zero runs of length one or two SHALL remain literal zero tokens.

Therefore:

```text
single zero:
varint(1)
1 byte in the common case

two zeros:
varint(1), varint(1)
2 bytes

three or more zeros:
varint(0), varint(run_length)
```

The minimum run threshold is frozen at:

```text
ZERO_RUN_MIN_LENGTH = 3
```

This threshold follows directly from byte break-even when both marker and run
length occupy one byte.

### Deterministic decode

Decoder logic SHALL:

1. read one unsigned varint token;
2. if token is non-zero:
   - subtract one;
   - ZigZag-decode the result;
   - emit one residual;
3. if token is zero:
   - read one unsigned varint run length;
   - reject run lengths below `ZERO_RUN_MIN_LENGTH`;
   - emit that many zero residuals;
4. reject any stream that decodes beyond or short of the declared residual
   count;
5. reject malformed/truncated varints.

### Same-stream comparison

The candidate SHALL encode exactly the same quantized residual integers
measured in Phase A.

No predictor, segmentation, quantization or V2 metadata change is permitted.

### Baselines

Phase B baselines are:

```text
raw_int32
zigzag_varint
```

Candidate:

```text
zero_run_varint
```

### Global-codec comparison

First compare a whole residual section using one codec for every residual
block.

For the candidate:

```text
global_zero_run_payload =
    sum(zero_run_varint(block))
```

No per-block selector overhead is charged in this comparison because this
models use of the existing section-level `coding_type`.

### Projected per-block hybrid comparison

A second diagnostic SHALL model future per-block codec selection:

```text
for each block:
    choose smaller of:
        zigzag_varint
        zero_run_varint
```

The projected representation SHALL charge:

```text
1 selector byte per residual block
```

even when the winning codec is ordinary varint.

Therefore:

```text
hybrid_residual_cost =
    sum(min(varint_block, zero_run_block))
    + block_count
```

This one-byte selector is a research projection, not an implemented wire
layout.

### Total-file accounting

For each dataset/predictor stream report:

```text
raw payload bytes
varint payload bytes
zero-run payload bytes

zero-run delta vs varint

blocks where zero-run is smaller
blocks where costs tie
blocks where zero-run is larger

gross per-block hybrid payload before selector
selector bytes
net projected hybrid residual bytes
hybrid delta vs current varint

current V2 total file bytes with varint
projected V2 total file bytes with global zero-run
projected V2 total file bytes with per-block hybrid
```

The projection SHALL preserve every non-residual byte from the current V2 file.

### Performance measurements

For every stream measure deterministic repeated median latency for:

```text
varint encode
varint decode
zero-run encode
zero-run decode
```

Use identical residual streams.

### Worst-case corpus

The candidate SHALL additionally be tested on synthetic residual streams:

```text
all_zero
alternating_zero_nonzero
no_zero_small
isolated_zero
long_zero_run
boundary_positive_63
boundary_negative_64
boundary_positive_64
boundary_negative_65
large_signed
```

These cases specifically test:

- zero-run gains;
- isolated-zero behavior;
- the `ZigZag + 1` varint-width boundary;
- expansion relative to ordinary ZigZag + varint.

### Promotion rule

Codec ID 2 SHALL remain disabled unless at least one representative current
production `auto` dataset obtains a measurable total-file reduction after all
required overhead.

A synthetic-only win is insufficient.

A per-block hybrid is not justified unless its selector-inclusive total is
smaller than the existing varint representation.
