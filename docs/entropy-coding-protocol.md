# Entropy coding research protocol

Date: 2026-10-05

Status: FROZEN BEFORE MEASUREMENT

## Purpose

Issue #9 evaluates whether a second-stage entropy coder can reduce Lasagna V2
residual payload cost after the existing residual representation has already
been produced.

This study does not alter:

```text
segmentation
predictor selection
quantization
V2 metadata
residual integer semantics
```

The entropy stage operates only on existing residual payload bytes.

## Primary question

The study asks:

```text
Does entropy coding save enough payload bytes to repay its own block metadata
and operational cost?
```

Payload-only compression is insufficient.

Any adoption decision SHALL use total encoded cost.

## Existing V2 controls

Two controls are frozen.

### Control A — explicit ZigZag + varint

```text
residual_coding = varint
coding_type = 1
```

### Control B — current section-level automatic residual coding

```text
residual_coding = auto
```

This selects the smaller whole-section representation between:

```text
ZigZag + varint
zero-run + varint
```

with ties preferring varint.

Control B is the primary current-production reference for issue #9.

Entropy candidates SHALL receive the exact bytes produced by the selected
residual codec.

They SHALL NOT re-encode residual integers differently.

## Frozen corpus

Use the same six datasets and four predictor strata as issue #8:

```text
internal:
trend
sine_noise
flat_spike

real-world:
appliances-energy
metro-traffic
beijing-pm25
```

Predictor strata:

```text
auto
mean
linear
rw
```

Primary production-reference results are the six `auto` streams.

## V2 configuration

```text
segment_mode = adaptive
segment_length = 64
min_segment_length = 32
max_segment_length = 128
mse_threshold = 0.5
C_Q = 0.125
Q_MIN = 1e-6
```

## Measured block-size constraint

Issue #8 established that residual blocks are extremely small.

For the `auto` stratum:

```text
block count = 3203
median residual count = 32
mean residual count ~= 32.119

<= 32 residuals:
3193 / 3203
~= 99.6878%
```

Therefore small-block overhead is a first-class acceptance criterion.

## Candidate set

The candidate set is intentionally small.

### Candidate 1 — sparse canonical Huffman

Research name:

```text
huffman_sparse
```

Input alphabet:

```text
bytes of one existing residual block payload
```

Each residual block receives an independent canonical Huffman code.

The benchmark SHALL construct and decode a real deterministic bitstream.

Projected block framing SHALL include all information required for independent
decode.

Frozen sparse codebook representation:

```text
uint16 original_byte_length
uint16 encoded_bit_length
uint16 symbol_count

for each used symbol, sorted ascending:
    uint8 symbol
    uint8 code_length

followed by:
    canonical-Huffman bitstream
```

Fixed header:

```text
6 bytes
```

Codebook overhead:

```text
2 * symbol_count bytes
```

Total Huffman block cost:

```text
6
+ 2 * symbol_count
+ ceil(encoded_bit_length / 8)
```

A one-symbol alphabet SHALL use code length 1.

Canonical ordering SHALL be deterministic:

```text
(code_length, symbol)
```

The decoder SHALL reject malformed or truncated representations.

### Candidate 2 — raw DEFLATE

Research name:

```text
deflate_raw
```

Use Python's standard-library zlib implementation with:

```text
wbits = -15
level = 1
```

Each residual block is compressed independently.

The compressed DEFLATE stream itself is the candidate payload.

Projected block framing SHALL include:

```text
uint16 original_byte_length
uint16 compressed_byte_length
```

Therefore candidate cost is:

```text
4
+ len(raw_deflate_stream)
```

No gzip or zlib container header is permitted.

This candidate is a practical small-block compression control, not a claim
that DEFLATE is a pure entropy coder.

## Why no zstd-per-block candidate

The frozen corpus is dominated by roughly 32-symbol residual blocks.

Issue #9 SHALL not add a zstd process/container benchmark per block merely to
increase candidate count.

The project already has whole-stream zstd evidence.

A future larger-block or section-level experiment may evaluate zstd if the
access granularity changes.

## Same-block rule

For each V2 residual block:

```text
current payload bytes
huffman_sparse(current payload bytes)
deflate_raw(current payload bytes)
```

All candidates SHALL receive identical source bytes.

## Block adoption rule

For each candidate, report both:

```text
forced candidate cost
```

and:

```text
selective candidate cost
```

Selective mode means:

```text
if candidate_total_block_cost < current_payload_bytes:
    use candidate
else:
    retain current payload
```

Tie-break:

```text
retain current payload
```

However selective mode SHALL charge an explicit selector cost.

Frozen selector projection:

```text
1 byte per residual block
```

Thus:

```text
selective_total =
    sum(min(current, candidate_total))
    + block_count
```

This selector is a research projection only.

No wire layout is introduced by the benchmark.

## Metrics per block

Report at least:

```text
dataset
predictor
base_residual_codec
segment_index
segment_length

source_payload_bytes
source_symbol_count
source_byte_entropy_bits_per_symbol

huffman_bitstream_bytes
huffman_codebook_bytes
huffman_total_bytes
huffman_delta_bytes

deflate_stream_bytes
deflate_total_bytes
deflate_delta_bytes
```

## Metrics per stream

Report:

```text
block_count
source_payload_bytes

forced Huffman bytes
forced Huffman delta

forced DEFLATE bytes
forced DEFLATE delta

number/fraction of blocks where each candidate wins
number/fraction of ties
number/fraction of losses

gross selective savings
selector bytes
net selective bytes
net selective delta

current total V2 file bytes
projected total file bytes
projected total-file delta
```

Residual-payload savings and total-file savings SHALL be reported separately.

## Small-block reporting

Results SHALL be stratified by source payload size:

```text
1..16 bytes
17..32 bytes
33..64 bytes
65..128 bytes
>128 bytes
```

For every bucket report:

```text
block count
candidate win rate
median byte delta
p95 byte delta
worst byte delta
```

## Performance

For both candidates measure deterministic repeated median:

```text
encode latency
decode latency
```

at minimum for the six `auto` streams.

## Memory

Measure or derive bounded working-memory requirements.

At minimum document:

### Huffman

```text
frequency table
canonical code table
decode table/tree
encoded output buffer
```

### DEFLATE

```text
zlib compressor/decompressor state
encoded output buffer
```

If process RSS is too noisy for 32-byte blocks, implementation-level bounded
state SHALL be documented rather than presenting misleading per-block RSS.

## Random access

The study SHALL explicitly evaluate:

```text
Can one residual block be decoded without decoding preceding residual blocks?
```

For independent block coders the answer may be yes, but all required metadata
cost SHALL be included.

## Streaming

The study SHALL explicitly evaluate:

```text
Can one block be encoded and emitted without buffering the entire residual
section?
Can one block be decoded once its framed bytes arrive?
```

Any candidate requiring section-wide statistics SHALL be documented as having
different streaming semantics.

## Wire-format rule

Issue #9 is research-first.

No entropy candidate receives:

```text
a codec identifier
a V2 flag
a residual block field
an invisible implementation hook
```

before measurement.

Adoption requires a separate explicit wire-format design decision supported by
measurable total-file benefit.

## Promotion gate

An entropy stage is promotable only if all are true:

```text
measurable total-file savings exist on representative real-world auto streams
small-block overhead is repaid
deterministic roundtrip passes
decode complexity is characterized
memory requirements are characterized
random-access implications are acceptable
streaming implications are acceptable
wire representation is explicitly designed
```

A gain confined to synthetic or unusually large blocks is insufficient.
