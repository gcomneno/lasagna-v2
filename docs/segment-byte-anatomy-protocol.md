# Segment Byte Anatomy Experiment

Status: FROZEN BEFORE EXECUTION

Issue: #25

Baseline commit:

```text
98f0112ca543ce5d4381bbf3b5408775d31c970a
```

## Research question

How much of Lasagna V2's current 44-byte fixed per-segment overhead is
semantically required, and how much can be eliminated by removing redundant
coordinates and predictor-unused fields?

## Current V2 cost

Each segment currently pays:

```text
SEGMENT_ENTRY_V2_STRUCT      32 bytes
RESIDUAL_BLOCK_HEADER_STRUCT 12 bytes
-------------------------------------
TOTAL                        44 bytes
```

## Current segment metadata

The V2 segment entry contains:

```text
start_idx
end_idx
predictor_type
mean
slope
intercept
quant_step_Q
seed_value
```

The residual block header contains:

```text
seg_id
seg_len
byte_len
```

## Frozen semantic observations

Segments are contiguous and ordered.

Therefore:

```text
start_idx
```

is derivable from the cumulative lengths of prior segments.

Given segment start and length:

```text
end_idx
```

is derivable.

Residual blocks occur in segment order, therefore:

```text
seg_id
```

is derivable from stream position.

The residual sample count equals segment length, therefore:

```text
seg_len
```

duplicates segment extent.

The residual payload byte length remains in the conservative candidate because
it provides explicit framing and supports bounded decoding.

## Predictor-specific parameter requirements

### Mean predictor

Decoder requires:

```text
mean
quant_step_Q
```

It does not require:

```text
slope
intercept
seed_value
```

### Linear predictor

Decoder requires:

```text
slope
intercept
quant_step_Q
```

It does not require:

```text
mean
seed_value
```

### Random-walk predictor

Decoder requires:

```text
seed_value
quant_step_Q
```

It does not require:

```text
mean
slope
intercept
```

## Conservative compact candidate

This experiment deliberately avoids varints, delta coding, dictionaries,
cross-segment prediction and Tensor View.

Logical common fields:

```text
segment_length : uint32   4 bytes
predictor_type : uint8    1 byte
quant_step_Q   : float32  4 bytes
payload_length : uint32   4 bytes
```

Common cost:

```text
13 bytes
```

Predictor-specific fields:

```text
mean:
    mean        : float32  4 bytes

linear:
    slope       : float32  4 bytes
    intercept   : float32  4 bytes

random-walk:
    seed_value  : float32  4 bytes
```

Projected logical cost:

```text
mean        17 bytes / segment
linear      21 bytes / segment
random-walk 17 bytes / segment
```

These are accounting candidates only.

They are not wire-layout specifications.

No alignment or padding assumption is promoted by this experiment.

## Baseline comparison

For every frozen #24 encoded point, compute:

```text
current_structural_bytes
projected_compact_structural_bytes
projected_encoded_bytes
projected_bits_per_sample
projected_rate_ratio
```

where:

```text
projected_compact_structural_bytes
=
current global/context bytes
+
sum(projected logical segment cost)
```

Residual payload bytes remain unchanged.

Distortion remains unchanged.

## Required measurements

Report at least:

```text
dataset
architecture
C_Q
segment_count
predictor counts
current structural bytes
projected structural bytes
structural byte reduction
current encoded bytes
projected encoded bytes
projected rate ratio
current structural fraction
projected structural fraction
```

Aggregate separately for:

```text
internal corpus
external corpus
A0
A1
A2
A3
A4
```

## Controls

The experiment must preserve:

```text
same datasets
same architecture matrix
same C_Q values
same segment boundaries
same predictors
same V2-rounded metadata semantics
same residual payload bytes
same distortion
```

The experiment is accounting-only.

It must not re-encode using a new format.

## Success criteria

The compact representation is considered structurally promising only if all of
the following hold:

```text
1. median per-segment fixed-overhead reduction >= 50%

2. median projected total encoded-byte reduction
   on external A4 rows >= 15%

3. projected structural fraction on external A4
   decreases materially relative to the frozen baseline

4. no result requires changing distortion or residual payload

5. every projected field removal is justified by decoder semantics,
   not only by empirical correlation
```

These thresholds are frozen before execution.

## Outcome classes

### PASS

All success criteria pass.

Proceed to a separate compact-wire-layout experiment.

### PARTIAL

Per-segment structural cost drops materially, but projected total-stream savings
do not meet the frozen threshold.

Preserve the result and reconsider segmentation economics before wire changes.

### FAIL

The candidate cannot materially reduce structural or total stream cost, or a
supposedly redundant field is semantically required.

Do not pursue this compact layout.

## Explicitly deferred

Not part of 25A:

```text
wire-format V3
cost-aware segmentation
Tensor View
metadata delta coding
segment dictionaries
cross-segment predictors
bucketization
ASHAPES / PETRA / COLLATZ
```

## Recovery point

If the experiment fails:

```text
LASAGNA_BASELINE=98f0112ca543ce5d4381bbf3b5408775d31c970a
```

No production behavior has changed.
