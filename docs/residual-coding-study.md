# Residual coding study

Date: 2026-10-05

Status: research complete; implementation decision justified

## Scope

Issue #8 evaluates residual representations beyond raw int32 and ZigZag +
varint using the exact current V2 quantized residual streams.

No predictor, segmentation or quantization change participates in the
comparison.

## Phase A: residual distributions

The frozen study measured 24 streams:

```text
6 datasets
x
4 predictor strata:
auto
mean
linear
rw
```

The six datasets are the same internal and real-world corpus used by previous
Lasagna research issues.

### Varint occupancy

For the complete corpus:

```text
auto:
102878 / 102878 residuals use one-byte varints

mean:
102878 / 102878 residuals use one-byte varints

linear:
102878 / 102878 residuals use one-byte varints

rw:
102680 / 102878 residuals use one-byte varints
198 / 102878 use two-byte varints
```

Therefore ordinary ZigZag + varint is already at its one-byte-per-symbol floor
for essentially the entire measured corpus.

Reducing residual magnitude alone cannot materially improve rate unless the
residual representation exploits structure across symbols.

### Current `auto` zero structure

```text
trend:
zero fraction 1.000000
longest zero run 200

sine_noise:
zero fraction 0.036667
longest zero run 1

flat_spike:
zero fraction 0.053333
longest zero run 2

Appliances Energy:
zero fraction 0.129212
longest zero run 10

Metro Traffic:
zero fraction 0.109244
longest zero run 16

Beijing PM2.5:
zero fraction 0.063241
longest zero run 14
```

Across all measured residual blocks:

```text
run >= 2:  27.6841%
run >= 4:   4.7207%
run >= 8:   0.2107%
run >= 16:  0.0702%
```

Zero-heavy structure exists, but long runs are uncommon outside specialized
signals.

## Phase B candidate

The historical/reserved residual codec identifier:

```text
RESIDUAL_CODEC_ZERO_RUN_VARINT = 2
```

was evaluated as a shadow codec.

Frozen semantics:

```text
literal q:
    varint(ZigZag(q) + 1)

zero run length >= 3:
    varint(0)
    varint(run_length)
```

Runs of one or two zeros remain literals.

The `+1` reserves token zero as the run marker.

## Primary production-reference results

Current `auto` results:

```text
trend.csv
current V2 varint total:      407 B
projected zero-run total:     212 B
delta:                       -195 B
delta percent:              -47.9115%

sine_noise.csv
current:                      683 B
zero-run:                     683 B
delta:                          0 B

flat_spike.csv
current:                      595 B
zero-run:                     595 B
delta:                          0 B

appliances-energy.csv
current:                    47002 B
zero-run:                  46615 B
delta:                       -387 B
delta percent:              -0.8234%

metro-traffic.csv
current:                   114631 B
zero-run:                 114261 B
delta:                       -370 B
delta percent:              -0.3228%

beijing-pm25.csv
current:                    81206 B
zero-run:                   81129 B
delta:                        -77 B
delta percent:              -0.0948%
```

The candidate therefore demonstrates measurable total-file benefit on all
three frozen real-world `auto` datasets.

It ties rather than loses on the two non-zero-run internal `auto` datasets.

## All measured streams

Across the 24 dataset/predictor streams:

```text
global zero-run wins:   15
global zero-run ties:    9
global zero-run losses:  0
```

This result applies only to the measured corpus.

It is not a universal no-expansion property.

## Per-block hybrid result

A projected per-block hybrid was also evaluated:

```text
choose min(varint, zero-run) per residual block
+
1 selector byte per block
```

Results across 24 streams:

```text
wins:   4
ties:   0
losses: 20
```

For current `auto`, the hybrid wins only on the synthetic trend stream.

It loses on all three real-world `auto` datasets:

```text
Appliances: +230 B
Metro:     +1137 B
Beijing:    +990 B
```

The one-byte-per-block selector cost dominates the sparse local gains.

The per-block hybrid is therefore rejected in its frozen form.

## Worst-case behavior

The shifted-literal design has a specific varint-boundary hazard.

For:

```text
q = -64
```

ordinary ZigZag produces:

```text
127
```

which occupies one varint byte.

The zero-run literal mapping produces:

```text
127 + 1 = 128
```

which occupies two bytes.

Measured hostile stream:

```text
128 x -64

ordinary varint: 128 B
zero-run codec:  256 B
expansion:       2.0x
```

This is the measured worst case in the frozen hostile corpus.

Therefore zero-run coding MUST NOT replace ordinary varint unconditionally.

## Performance

Performance is workload-dependent.

Examples for current `auto`:

```text
Appliances:
zero-run encode / varint encode ~= 0.785x
zero-run decode / varint decode ~= 1.288x

Metro:
encode ~= 1.159x
decode ~= 1.250x

Beijing:
encode ~= 1.783x
decode ~= 1.831x
```

The codec therefore has measurable decode cost and is not universally faster.

## Decision

### `zero_run_varint`

Decision:

```text
PROMOTE AS EXPLICIT SUPPORTED CODEC
```

Rationale:

- deterministic roundtrip demonstrated;
- reserved codec identifier 2 already exists;
- measurable total-file wins occur on all three real-world `auto` datasets;
- worst-case behavior is known and documented;
- encode/decode cost is measured.

It SHALL NOT become the unconditional default because the hostile corpus
demonstrates up to 2x payload expansion.

### Section-level automatic selection

A safe encoder-side selection mode is justified:

```text
encode varint candidate
encode zero-run candidate
select the smaller residual representation
```

Tie-break:

```text
prefer existing ZigZag + varint
```

This requires no new wire identifier:

```text
selected varint   -> coding_type 1
selected zero-run -> coding_type 2
```

The comparison is section-level because the frozen V2 residual header contains
one `coding_type` for the whole residual section.

This mode guarantees that residual payload size is never larger than ordinary
varint solely because zero-run was selected.

The existing encoder default SHALL remain unchanged in issue #8.

### Per-block hybrid

Decision:

```text
REJECT
```

The frozen selector-inclusive representation loses on the representative
real-world `auto` corpus.

## Wire decision

Issue #8 may enable the already-reserved codec identifier:

```text
RESIDUAL_CODEC_ZERO_RUN_VARINT = 2
```

with explicit compatibility tests.

No additional residual codec identifier is allocated.

No existing codec identifier changes meaning.

V1 compatibility remains unchanged.

## Evidence artifacts

```text
docs/residual-coding-protocol.md
docs/residual-distribution-matrix.tsv
docs/residual-distribution-results.csv
docs/residual-distribution-blocks.csv
docs/residual-codec-candidate-matrix.tsv
docs/residual-codec-results.csv
docs/residual-codec-worst-cases.csv
```

## Research gates

```text
RESIDUAL_DISTRIBUTION_MEASUREMENT_GATE=PASS
RAW_BASELINE_GATE=PASS
VARINT_BASELINE_GATE=PASS
SAME_STREAM_COMPARISON_GATE=PASS
TOTAL_FILE_ACCOUNTING_GATE=PASS
DETERMINISTIC_ROUNDTRIP_GATE=PASS
PERFORMANCE_CHARACTERIZATION_GATE=PASS
WORST_CASE_DOCUMENTATION_GATE=PASS
ZERO_RUN_REAL_WORLD_BENEFIT_GATE=PASS
PER_BLOCK_HYBRID_GATE=FAIL
CODEC_ID_2_PROMOTION_EVIDENCE_GATE=PASS
NEW_CODEC_ID_ALLOCATION_GATE=NOT_REQUIRED
```
