# Entropy coding study

Date: 2026-10-05

Issue:

```text
#9 research: evaluate entropy coding for Lasagna residual payloads
```

## Decision

```text
DO NOT ADOPT AN ENTROPY-CODING STAGE IN THE CURRENT V2 WIRE FORMAT
```

The measured corpus shows that entropy coding can exploit statistical
redundancy in some residual blocks, but the current V2 residual-block
granularity is generally too small for an independently framed entropy coder
to repay its own metadata and selection overhead.

No codec identifier, V2 flag, residual-block field or invisible wire behavior
is introduced by this study.

## Controls

The study retained the existing V2 residual representation as the control.

Two control modes were measured:

```text
explicit ZigZag + varint
current section-level residual auto
```

The current `auto` control selects between:

```text
ZigZag + varint
zero-run + varint
```

before the entropy candidate receives the block bytes.

Entropy candidates therefore operated on identical already-produced residual
payload bytes.

They did not alter:

```text
segmentation
predictor selection
quantization
residual integer semantics
```

## Corpus

The frozen issue #8 corpus was reused:

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

Total entropy benchmark cases:

```text
48
```

because every one of the 24 residual streams was measured against both
`varint` and `auto` controls.

Total block observations:

```text
25,632
```

## Candidates

### Sparse canonical Huffman

Independent canonical Huffman code per residual block.

Frozen representation:

```text
uint16 original_byte_length
uint16 encoded_bit_length
uint16 symbol_count

for each used byte symbol:
    uint8 symbol
    uint8 code_length

canonical-Huffman bitstream
```

Fixed framing:

```text
6 bytes
```

Variable codebook cost:

```text
2 bytes per used symbol
```

### Raw DEFLATE

Independent raw DEFLATE stream per residual block using:

```text
Python zlib
level = 1
wbits = -15
```

Projected framing:

```text
uint16 original_byte_length
uint16 compressed_byte_length
raw DEFLATE stream
```

Fixed framing:

```text
4 bytes
```

DEFLATE is included as a practical small-block compression control rather than
as a claim that DEFLATE is a pure entropy coder.

## Current V2 block-size constraint

Issue #8 established that current V2 adaptive segmentation produces extremely
small residual blocks.

For the `auto` stratum:

```text
block count = 3203
median residual count = 32
mean residual count ~= 32.119

<= 32 residuals:
3193 / 3203
~= 99.6878%
```

This is the central result required to interpret the entropy experiment.

## Primary `auto` results

### trend

Current selected residual representation:

```text
zero-run
```

Residual payload:

```text
5 bytes
```

Projected selective result:

```text
Huffman: +2 bytes
DEFLATE: +2 bytes
```

The existing zero-run representation is already too compact to repay any
additional block selector.

### sine_noise

Current selected representation:

```text
varint
```

Residual payload:

```text
300 bytes
```

Projected selective result:

```text
Huffman: +6 bytes
DEFLATE: +6 bytes
```

No candidate wins.

### flat_spike

Current selected representation:

```text
varint
```

Residual payload:

```text
300 bytes
```

Projected selective result:

```text
Huffman: +4 bytes
DEFLATE: -25 bytes
```

DEFLATE wins on this synthetic stream.

This synthetic-only result is insufficient for adoption.

### Appliances Energy

Current selected representation:

```text
zero-run
```

Residual payload:

```text
19,348 bytes
```

Block count:

```text
617
```

Huffman:

```text
forced delta:    +8,215 bytes
winning blocks:  120
selective delta: -99 bytes
```

DEFLATE:

```text
forced delta:    +1,781 bytes
winning blocks:  93
selective delta: +346 bytes
```

Huffman produces a small net benefit only when used selectively.

### Metro Traffic

Current selected representation:

```text
zero-run
```

Residual payload:

```text
47,834 bytes
```

Block count:

```text
1507
```

Huffman:

```text
forced delta:     +39,457 bytes
winning blocks:   1
selective delta:  +1,504 bytes
```

DEFLATE:

```text
forced delta:     +7,867 bytes
winning blocks:   8
selective delta:  +1,485 bytes
```

Both candidates lose.

### Beijing PM2.5

Current selected representation:

```text
zero-run
```

Residual payload:

```text
34,062 bytes
```

Block count:

```text
1067
```

Huffman:

```text
forced delta:     +29,563 bytes
winning blocks:   1
selective delta:  +1,060 bytes
```

DEFLATE:

```text
forced delta:     +5,932 bytes
winning blocks:   2
selective delta:  +1,059 bytes
```

Both candidates lose.

## Real-world promotion result

For the three representative real-world `auto` streams:

```text
Huffman total-file wins:
1 / 3

DEFLATE total-file wins:
0 / 3
```

Huffman improves Appliances by only:

```text
99 bytes
```

while losing:

```text
Metro:   +1,504 bytes
Beijing: +1,060 bytes
```

This is not sufficient evidence for a general V2 entropy stage.

## Block-level results

Across all 25,632 measured block observations:

```text
Huffman:
wins   = 1,296
ties   =   122
losses = 24,214
win fraction ~= 5.0562%

DEFLATE:
wins   = 1,342
ties   =   509
losses = 23,781
win fraction ~= 5.2356%
```

Approximately 95% of blocks therefore fail to produce a strict candidate win.

## Small-block behavior

### 1..16 byte source blocks

Huffman:

```text
wins = 0
median delta = +17 bytes
worst delta = +23 bytes
```

DEFLATE:

```text
wins = 0
median delta = +6 bytes
worst delta = +6 bytes
```

### 17..32 byte source blocks

This is the dominant bucket.

Block observations:

```text
25,549
```

Huffman:

```text
wins = 1,288
win fraction ~= 5.0413%
median delta = +26 bytes
p95 delta = +34 bytes
worst delta = +47 bytes
```

DEFLATE:

```text
wins = 1,312
win fraction ~= 5.1352%
median delta = +6 bytes
p95 delta = +6 bytes
worst delta = +6 bytes
```

This bucket explains the rejection of block-level entropy coding under the
current V2 segmentation regime.

### 33..64 byte source blocks

Huffman:

```text
wins = 0 / 36
median delta = +29.5 bytes
```

DEFLATE:

```text
wins = 2 / 36
median delta = +4 bytes
```

Neither candidate is generally attractive.

### 65..128 byte source blocks

Huffman:

```text
wins = 4 / 24
median delta = +27 bytes
```

DEFLATE:

```text
wins = 24 / 24
median delta = -18 bytes
worst measured delta = -9 bytes
```

At this granularity DEFLATE becomes consistently beneficial in the measured
corpus.

### Greater than 128 bytes

Only four block observations exist.

Both candidates win all four.

Huffman:

```text
median delta = -149.5 bytes
worst measured delta = -104 bytes
```

DEFLATE:

```text
median delta = -188 bytes
worst measured delta = -132 bytes
```

This shows that entropy/compression potential exists when the coding unit is
large enough.

The current V2 residual-block granularity usually is not.

## Interpretation

The study does not support the claim:

```text
Lasagna residuals contain no exploitable statistical redundancy.
```

It supports the narrower and more useful claim:

```text
The current approximately-32-byte V2 residual-block granularity is generally
too small for independently framed Huffman or DEFLATE stages to repay their
own representation cost.
```

The experiment therefore identifies granularity as the limiting factor.

## Selector accounting

Selective candidate projections used:

```text
min(current block bytes, candidate block bytes)
+
1 selector byte per residual block
```

Ties retain the existing representation.

The one-byte selector is a research projection.

No such selector exists in the V2 wire format.

Its explicit inclusion prevents local compression wins from being mistaken
for free total-file savings.

## Performance

Median whole-stream candidate timings for the three real-world `auto` cases:

### Appliances Energy

```text
Huffman encode: 48.830359 ms
Huffman decode: 19.335839 ms

DEFLATE encode: 4.003475 ms
DEFLATE decode: 0.969340 ms
```

### Metro Traffic

```text
Huffman encode: 167.949178 ms
Huffman decode: 59.474021 ms

DEFLATE encode: 9.729478 ms
DEFLATE decode: 2.165055 ms
```

### Beijing PM2.5

```text
Huffman encode: 123.142495 ms
Huffman decode: 43.622498 ms

DEFLATE encode: 6.894426 ms
DEFLATE decode: 1.540285 ms
```

The pure-Python Huffman prototype is substantially more expensive than the
zlib-backed DEFLATE control.

These timings characterize the research implementations, not an optimized
native Huffman implementation.

## Memory requirements

### Sparse Huffman

Independent-block encoding requires bounded per-block state:

```text
input block
frequency table over at most 256 byte symbols
Huffman tree
canonical code-length table
canonical code table
encoded output buffer
```

Decode requires:

```text
encoded block
sparse codebook
canonical decode table
decoded output block
```

State is independent of preceding or following residual blocks.

For current roughly-32-byte blocks, the fixed table/object overhead is large
relative to the payload even though absolute memory usage remains bounded.

### Raw DEFLATE

Independent-block encoding requires:

```text
input block
zlib compressor state
encoded output buffer
```

Decode requires:

```text
encoded block
zlib decompressor state
decoded output block
```

The internal zlib state is implementation-dependent and substantially larger
than a typical 32-byte Lasagna residual payload.

Per-process RSS was intentionally not presented as a per-block memory metric:
allocator/runtime noise would dominate such tiny inputs and imply false
precision.

## Random access

Both candidates were evaluated as independent block coders.

Therefore a residual block can, in principle, be entropy-decoded without
entropy-decoding preceding residual blocks, provided its framing and candidate
selection metadata are independently addressable.

This preserves the conceptual random-access property of the existing residual
block organization.

However, introducing per-block entropy selection would require new wire
metadata or a new deterministic selection rule.

The current V2 wire does not contain that representation.

## Streaming

Both benchmark candidates can operate block-by-block.

Encoding can:

```text
receive one residual block
encode it
emit the framed result
discard candidate state
```

Decoding can:

```text
receive one complete framed block
decode it
emit its residual bytes
discard candidate state
```

Neither benchmark candidate requires statistics from the complete residual
section.

Therefore block-level streaming is technically compatible.

The rejection is economic, not caused by an inherent streaming dependency.

## Wire-format decision

Issue #9 does not introduce entropy coding into V2.

Specifically, it does not add:

```text
new residual codec IDs
new entropy codec IDs
new section flags
new block flags
new block selectors
implicit entropy transforms
```

Adoption would require a separate explicit wire-format design.

The current evidence does not justify such a change.

## Future research boundary

The data does justify one narrower future question:

```text
Would entropy coding become worthwhile if the entropy-coding unit were larger
than the current residual block?
```

Measured evidence supporting that question:

```text
DEFLATE wins 24 / 24 measured blocks in the 65..128 byte bucket.

Both Huffman and DEFLATE win 4 / 4 measured blocks above 128 bytes.
```

Therefore future work may investigate:

```text
coarser entropy groups
section-level entropy coding
grouped consecutive residual blocks
larger random-access pages
```

Such work must explicitly account for the resulting trade-off between:

```text
compression ratio
random-access granularity
streaming latency
memory
wire framing
```

It is not part of issue #9.

## Final decision

```text
CURRENT V2 BLOCK-LEVEL ENTROPY CODING:
REJECT
```

Reason:

```text
statistical redundancy exists
BUT
current block granularity is too small
AND
real-world total-file benefit is not representative
AND
selector/framing overhead dominates most blocks
```

No production code or wire-format change is warranted.

## Evidence artifacts

```text
docs/entropy-coding-protocol.md
docs/entropy-coding-candidate-matrix.tsv
docs/entropy-coding-results.csv
docs/entropy-coding-blocks.csv
docs/entropy-coding-buckets.csv
tools/benchmark_entropy_coding.py
tests/test_tools_benchmark_entropy_coding.py
```

## Research gates

```text
EXISTING_V2_CONTROL_GATE=PASS
IDENTICAL_RESIDUAL_BLOCK_GATE=PASS
HUFFMAN_REAL_BITSTREAM_GATE=PASS
DEFLATE_REAL_BITSTREAM_GATE=PASS
ROUNDTRIP_GATE=PASS
PAYLOAD_ACCOUNTING_GATE=PASS
TOTAL_FILE_ACCOUNTING_GATE=PASS
SMALL_BLOCK_OVERHEAD_GATE=PASS
PERFORMANCE_CHARACTERIZATION_GATE=PASS
MEMORY_CHARACTERIZATION_GATE=PASS
RANDOM_ACCESS_ANALYSIS_GATE=PASS
STREAMING_ANALYSIS_GATE=PASS

HUFFMAN_REAL_WORLD_REPRESENTATIVE_GAIN_GATE=FAIL
DEFLATE_REAL_WORLD_REPRESENTATIVE_GAIN_GATE=FAIL

CURRENT_V2_ENTROPY_ADOPTION_GATE=REJECT
NO_WIRE_CHANGE_GATE=PASS
```
