# Predictor candidate evaluation protocol

Date: 2026-10-05

Status: FROZEN BEFORE CANDIDATE EXECUTION

## Purpose

Issue #7 evaluates whether additional predictor families can improve Lasagna
total encoded cost on structured time series.

No predictor ID is allocated and no wire-format change is made during this
experiment.

Candidates are evaluated in a shadow research harness against the existing
predictor set.

## Central decision rule

Predictor usefulness SHALL NOT be determined by residual reconstruction error
alone.

The primary rate measure is projected total encoded cost:

```text
segment structural metadata
+ predictor-specific metadata
+ residual block framing
+ encoded residual payload
```

Quality remains a separately reported constraint.

A candidate that reduces residual error but increases total encoded bytes is
not considered an encoding improvement.

## Existing baseline predictors

The current predictor set is:

```text
mean
linear
random_walk
```

These remain the mandatory baseline.

The current production `auto` selector chooses the predictor with the lowest
post-quantization reconstruction MSE.

Issue #7 does not modify that behavior before candidate evidence exists.

## Shadow candidate predictors

The frozen candidate set is:

### median

Constant predictor using the segment median.

Properties:

```text
parameters = 1 float
decoder recurrence = none
```

Purpose:

- robust constant model in the presence of spikes/outliers;
- direct comparison with the existing mean predictor.

### quadratic

Bounded second-order local polynomial:

```text
prediction(i) = a + b*i + c*i^2
```

Properties:

```text
parameters = 3 floats
decoder recurrence = none
```

Purpose:

- represent smooth local curvature not captured by the linear predictor.

### ar1

First-order autoregressive model:

```text
prediction(0) = seed
prediction(i) = intercept + phi * reconstructed(i-1)
```

Properties:

```text
parameters = 2 fitted floats + 1 seed float
decoder recurrence = previous reconstructed sample
```

Purpose:

- represent locally autoregressive structure;
- compare against random walk, whose effective coefficient is fixed at 1.

Decoder simulation SHALL use previous reconstructed values, not original
future values.

### lag24

Fixed-lag predictor:

```text
prediction(i) = reconstructed(i-24), for i >= 24
```

The first 24 positions use explicit seed/history values.

Properties:

```text
lag = 24 samples
decoder recurrence = reconstructed history
seed/history = first 24 values
```

The number 24 means 24 samples, not 24 hours. No sampling-frequency semantic
claim is attached to it.

Purpose:

- test whether simple periodic repetition can repay its relatively expensive
  initialization metadata.

## Frozen datasets

Use the same six datasets employed by issue #5:

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

No dataset-specific predictor configuration is allowed.

## Frozen segmentation

Candidate evaluation SHALL use one common segmentation per dataset.

Segmentation configuration:

```text
segment_mode = adaptive
segmentation predictor = linear
min_segment_length = 32
max_segment_length = 128
mse_threshold = 0.5
```

This matches the current behavior of `predictor="auto"`.

Candidates SHALL NOT receive different segment boundaries.

This isolates predictor quality/cost from segmentation changes.

## Quantization and residual coding

All predictors SHALL use:

```text
C_Q = 0.125
Q_MIN = 1e-6
residual coding = ZigZag + varint
```

The value `C_Q=0.125` is the evidence-backed current V2 default from issue #5.

## Metadata cost model

This experiment does not allocate real predictor IDs.

For comparison, a deterministic projected metadata model is used.

Common per-segment structural fields:

```text
start_idx      uint32 = 4 bytes
end_idx        uint32 = 4 bytes
predictor_id   uint32 = 4 bytes
quant_step_Q   float32 = 4 bytes
```

Common structural metadata:

```text
16 bytes / segment
```

Predictor-specific projected payload:

```text
mean:
1 float32 = 4 bytes

linear:
2 float32 = 8 bytes

random_walk:
1 float32 seed = 4 bytes

median:
1 float32 = 4 bytes

quadratic:
3 float32 = 12 bytes

ar1:
intercept + phi + seed
3 float32 = 12 bytes

lag24:
24 float32 seed/history values
96 bytes
```

Each segment also pays the existing residual block header:

```text
12 bytes
```

Projected segment cost therefore includes:

```text
16 common metadata bytes
+ predictor-specific metadata bytes
+ 12 residual block-header bytes
+ actual varint residual payload bytes
```

This projected cost is a research comparison model, not a proposed future wire
layout.

The existing V2 wire remains unchanged.

## Fitting semantics

All fitting is deterministic.

### mean

Arithmetic mean of segment values.

### linear

Existing least-squares linear model semantics.

### random_walk

Existing random-walk semantics.

### median

Deterministic mathematical median.

### quadratic

Least-squares fit of a bounded second-order polynomial over local sample
indices.

Degenerate systems SHALL fail closed or fall back deterministically to the
linear model for research evaluation, and the fallback count SHALL be
reported.

### ar1

Least-squares fit of:

```text
x[i] = intercept + phi*x[i-1]
```

for positions `i >= 1`.

Degenerate variance SHALL deterministically fall back to random-walk
coefficient semantics.

### lag24

No fitted coefficient.

For segments shorter than 25 samples, the candidate is ineligible.

## Measurements

For every dataset and predictor candidate report:

```text
dataset
predictor
candidate_class
n_samples
segment_count
eligible_segment_count
fallback_segment_count
projected_metadata_bytes
residual_payload_bytes
projected_total_bytes
bits_per_sample
RMSE
max_abs_error
fit_time_ms
decode_simulation_time_ms
```

Also report per-segment winner counts under two distinct rules:

```text
MSE winner
projected-total-byte winner subject to quality comparison
```

The two rules SHALL remain separate.

## Decoder complexity

Decoder complexity SHALL be characterized by:

```text
metadata bytes
recurrence required: yes/no
seed/history values required
decode simulation latency
```

No subjective complexity score is used as a substitute for measurements.

## Acceptance rule

A new predictor becomes a candidate for later wire-format design only if it
shows reproducible total-cost benefit beyond the existing predictor set.

Evidence must include:

- total projected bytes;
- reconstruction quality;
- metadata overhead;
- decoder simulation cost;
- behavior across more than one dataset.

A predictor SHALL NOT be accepted solely because it wins one dataset.

A predictor SHALL NOT receive a wire-format ID in issue #7 until the
experimental evidence justifies promotion.

## Non-goals

This experiment does not:

- change V1;
- change V2 predictor IDs;
- change V2 segment layout;
- change production `auto`;
- optimize adaptive segmentation;
- introduce dataset-specific tuning.
