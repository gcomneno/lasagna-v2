# Predictor candidate study

Date: 2026-10-05

Status: completed research study

## Scope

Issue #7 evaluates additional predictor families before allocating any new
predictor ID or changing the V2 wire format.

The experiment uses a shadow predictor harness. Production encoding and
decoding behavior remain unchanged.

Frozen protocol:

```text
docs/predictor-candidate-protocol.md
docs/predictor-candidate-matrix.tsv
```

Raw evidence:

```text
docs/predictor-candidate-results.csv
docs/predictor-candidate-winners.csv
```

## Baseline and candidate set

Existing baseline predictors:

```text
mean
linear
random_walk
```

Shadow candidates:

```text
median
quadratic
ar1
lag24
```

No candidate received a wire-format predictor ID.

## Corpus

Six datasets were evaluated:

```text
internal:
trend.csv
sine_noise.csv
flat_spike.csv

real-world:
appliances-energy.csv
metro-traffic.csv
beijing-pm25.csv
```

The real-world files are the canonical corpus already used by previous
validation and sensitivity studies.

All predictors use identical frozen segment boundaries per dataset.

## Main result

No new candidate predictor achieved a strict projected byte reduction over the
best existing baseline predictor at dataset level.

```text
CANDIDATE_STRICT_BYTE_WINS = 0
CANDIDATE_SAME_RATE_QUALITY_WINS = 4
CANDIDATE_NO_WINS = 2
```

The only repeatedly useful new candidate was `median`, and its observed benefit
was quality at the same projected rate rather than a reduction in projected
bytes.

## Dataset-level decisions

### Appliances Energy

```text
best baseline:
mean
39479 projected bytes
RMSE 3.02663371144

best candidate:
median
39479 projected bytes
RMSE 2.90446159287

decision:
SAME_RATE_QUALITY_WIN
```

### Beijing PM2.5

```text
best baseline:
mean
68283 projected bytes
RMSE 1.67009858578

best candidate:
median
68283 projected bytes
RMSE 1.65223443583

decision:
SAME_RATE_QUALITY_WIN
```

### Flat / spike

```text
best baseline:
random_walk
428 projected bytes
RMSE 0.0308306232207

best candidate:
median
428 projected bytes
RMSE 0.0332511118758

decision:
NO_WIN
```

### Metro traffic

```text
best baseline:
mean
96428 projected bytes
RMSE 67.2633413125

best candidate:
median
96428 projected bytes
RMSE 66.6718009874

decision:
SAME_RATE_QUALITY_WIN
```

### Sine + noise

```text
best baseline:
mean
492 projected bytes
RMSE 0.0260740942555

best candidate:
median
492 projected bytes
RMSE 0.0260274121798

decision:
SAME_RATE_QUALITY_WIN
```

### Trend

```text
best baseline:
mean
264 projected bytes
RMSE 0.116480937624

best candidate:
median
264 projected bytes
RMSE 0.116480937624

decision:
NO_WIN
```

## Predictor observations

### Median

`median` is the only new candidate that repeatedly improves reconstruction
quality without increasing projected total bytes.

It matches the projected metadata cost of the existing mean predictor.

It produces same-rate quality improvements on four of six datasets, but no
strict rate improvement.

This makes median a plausible future rate-distortion candidate, not sufficient
evidence for a new wire-format predictor ID in this issue.

### Quadratic

`quadratic` frequently improves RMSE, sometimes substantially.

However, its projected metadata cost is higher than the simpler baseline
predictors and the residual payload usually remains unchanged.

It therefore does not achieve a strict projected byte win.

### Lag24

`lag24` strongly improves reconstruction error on many segments and dominates
the segment-level MSE winner count.

After correcting the shadow decoder to use reconstructed lag history, the model
remains valid but expensive.

Its 24-value seed/history requirement dominates projected metadata cost.

The candidate therefore demonstrates that lower prediction error does not imply
better codec rate.

Segments shorter than 25 samples are ineligible, so dataset-level rows with
partial eligibility are not used for promotion decisions.

### AR1

`ar1` does not produce a rate advantage and shows severe reconstruction
instability on some datasets under the frozen causal decoder semantics.

No promotion is justified.

## Residual payload observation

A major result of the study is that most predictors produce the same varint
payload size over a dataset despite materially different reconstruction error.

For example:

```text
Appliances:
mean       payload 19735
median     payload 19735
linear     payload 19735
quadratic  payload 19735
ar1        payload 19735

Metro:
mean       payload 48204
median     payload 48204
linear     payload 48204
quadratic  payload 48204
ar1        payload 48204

Beijing:
mean       payload 34139
median     payload 34139
linear     payload 34139
quadratic  payload 34139
ar1        payload 34139
```

This is consistent with the current quantization rule:

```text
Q = max(C_Q * sigma(residuals), Q_MIN)
```

Because quantization scale adapts to residual dispersion, reducing residual
magnitude does not necessarily reduce quantized residual magnitude enough to
cross varint byte-width boundaries.

Consequently, predictor improvements often become quality improvements rather
than rate improvements.

## MSE selection versus byte selection

Across all 3203 evaluated segments:

```text
divergent MSE/byte decisions = 2955
divergence rate = 92.2572588%
```

Segment MSE winner counts:

```text
lag24        2550
quadratic     258
ar1           128
random_walk   126
median         97
mean           25
linear         19
```

Recorded projected-byte winner counts, with RMSE used only as a tie-breaker:

```text
median       1192
random_walk  1065
mean          946
```

No higher-metadata candidate (`quadratic`, `ar1`, `lag24`) wins the projected
byte decision.

The 92.26% divergence demonstrates that minimizing reconstruction MSE and
minimizing projected encoded cost are different objectives.

However, this study does not change production `auto`, because the current
projected-cost model is a research model rather than a frozen replacement wire
selection contract.

## Decision

Issue #7 does not allocate any new predictor ID.

```text
median:
PROMISING
same-rate quality benefit
no strict rate gain

quadratic:
REJECT FOR CURRENT WIRE
quality benefit does not repay metadata

ar1:
REJECT
no rate benefit + reconstruction instability

lag24:
REJECT FOR CURRENT WIRE
strong MSE benefit but metadata-heavy
```

Production behavior remains unchanged:

```text
predictor IDs = {0, 1, 2}
auto selector = unchanged
V1 = unchanged
V2 wire = unchanged
```

## Follow-up implications

The experiment suggests two future research directions:

1. Rate-aware predictor selection should be studied separately from the current
   minimum-MSE `auto` selector.

2. Predictor research and residual quantization/coding are coupled. A better
   predictor cannot improve byte rate if quantization and residual coding map
   its residuals to the same encoded byte widths.

No optimization or format change is introduced here.

## Acceptance gates

```text
REPRODUCIBLE_PREDICTOR_EXPERIMENT_GATE=PASS
TOTAL_ENCODED_COST_GATE=PASS
METADATA_OVERHEAD_GATE=PASS
DECODER_COMPLEXITY_GATE=PASS
BASELINE_COMPARISON_GATE=PASS
NO_NEW_PREDICTOR_ID_GATE=PASS
NO_WIRE_CHANGE_GATE=PASS
PROMOTION_EVIDENCE_GATE=FAIL
ISSUE_7_RESEARCH_COMPLETION_GATE=PASS
```
