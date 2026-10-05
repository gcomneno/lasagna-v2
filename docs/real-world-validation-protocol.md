# Real-world validation protocol

Date: 2026-10-05

Status: FROZEN BEFORE DATA EXECUTION

## Purpose

This protocol defines the heterogeneous external validation corpus used for
Lasagna 2 issue #4.

It is separate from the synthetic M2.3 corpus and from the three internal
example datasets used by the external-codec benchmark.

## Domains

The corpus contains one univariate time series from each of three independent
real-world domains:

1. building energy consumption;
2. road traffic volume;
3. urban air pollution.

All three sources are distributed by the UCI Machine Learning Repository under
CC BY 4.0.

The canonical source identities and preprocessing rules are recorded in
`data/real-world/manifest.tsv`.

## Frozen Lasagna configuration

The evaluation SHALL use one configuration for every real-world series:

```text
segment_mode=adaptive
predictor=auto
residual_coding=varint
segment_length=64
min_segment_length=32
max_segment_length=128
mse_threshold=0.5
C_Q=0.5
Q_MIN=1e-6
```

No parameter SHALL be retuned per dataset after observing validation results.

## Canonical input representation

Each canonical file SHALL contain exactly one numeric sample per line encoded
as UTF-8 text with LF line endings.

Rows SHALL remain in source chronological order.

No normalization, scaling, smoothing, clipping, resampling, interpolation or
outlier removal SHALL be applied.

### Appliances Energy Prediction

Source field:

```text
Appliances
```

All source rows SHALL be retained.

Any missing value in the selected field SHALL invalidate preprocessing.

### Metro Interstate Traffic Volume

Source field:

```text
traffic_volume
```

All source rows SHALL be retained in source chronological order.

Any missing value in the selected field SHALL invalidate preprocessing.

### Beijing Multi-Site Air Quality

Frozen station:

```text
Aotizhongxin
```

Source field:

```text
PM2.5
```

Rows for other stations SHALL be excluded.

Rows where PM2.5 is missing SHALL be dropped.

Missing values SHALL NOT be interpolated or imputed.

This intentionally preserves an irregular observation sequence after missing
samples are removed. Any resulting regression in codec behavior remains part
of the evidence.

## Evaluation

Every canonical series SHALL be passed through the same benchmark machinery
used by the external-codec benchmark.

At minimum the report SHALL record per series:

```text
sample count
raw bytes
Lasagna encoded bytes
Lasagna bits/sample
Lasagna compression ratio
RMSE
max absolute error
lossless baseline sizes
```

Aggregate reporting SHALL preserve the individual dataset rows and SHALL NOT
hide unfavorable results behind an average.

## Interpretation boundary

This is a heterogeneous real-world validation corpus, not a representative
sample of all possible time-series domains.

Results SHALL be reported separately from synthetic evidence.

Failure cases and regressions SHALL be retained in the report.

No result from this corpus establishes universal codec superiority.
