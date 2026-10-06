# External dataset production-qualification protocol

Issue: #19 — `research: expand external dataset production qualification`

Status:

```text
PROTOCOL = FROZEN BEFORE MEASUREMENT
CODEC RESULTS = NOT YET EXECUTED
TARGET CORPUS = 8 EXTERNAL SERIES / 8 SOURCE DATASETS
```

Date:

```text
2026-10-06
```

## Purpose

This protocol expands the existing three-dataset heterogeneous validation into
the external-data evidence required for production-readiness Gate 13.

The purpose is not to demonstrate universal codec superiority.

The purpose is to determine whether the already frozen Lasagna configuration
behaves coherently across a broader set of independently sourced univariate
signals.

Dataset selection and extraction rules are frozen before measuring Lasagna on
the five newly added sources.

## Qualification target

The production qualification SHALL contain exactly:

```text
8 canonical univariate series
8 independently identified external source datasets
```

The eight series SHALL span the following predeclared signal/domain cells:

```text
1. building appliance energy
2. road traffic volume
3. urban particulate pollution
4. urban bicycle demand
5. mechanical vibration
6. financial market returns
7. room occupancy count
8. electrical distribution load
```

This target is coverage-driven rather than a statistical claim that eight
datasets represent every possible time-series domain.

The target closes five gaps left by the previous three-series study:

```text
periodic urban demand
high-frequency vibration
small/noisy financial returns
piecewise-discrete occupancy
grid-scale electrical load
```

## Frozen corpus

### Q01 — Appliances Energy Prediction

```text
canonical id:
    appliances-energy

domain:
    building appliance energy

source:
    UCI Machine Learning Repository

DOI:
    10.24432/C5VC8G

license:
    CC BY 4.0

selected field:
    Appliances

preprocessing:
    retain every source row in chronological order
    reject the dataset if the selected field contains a missing value
    no interpolation
    no resampling
    no normalization
    no clipping
    no smoothing

status:
    inherited from the previously frozen validation corpus
```

### Q02 — Metro Interstate Traffic Volume

```text
canonical id:
    metro-traffic

domain:
    road traffic volume

source:
    UCI Machine Learning Repository

DOI:
    10.24432/C5X60B

license:
    CC BY 4.0

selected field:
    traffic_volume

preprocessing:
    retain every source row in source chronological order
    reject the dataset if the selected field contains a missing value
    no interpolation
    no resampling
    no normalization
    no clipping
    no smoothing

status:
    inherited from the previously frozen validation corpus
```

### Q03 — Beijing Multi-Site Air Quality

```text
canonical id:
    beijing-pm25

domain:
    urban particulate pollution

source:
    UCI Machine Learning Repository

DOI:
    10.24432/C5RK5G

license:
    CC BY 4.0

station:
    Aotizhongxin

selected field:
    PM2.5

preprocessing:
    retain Aotizhongxin rows only
    preserve source chronological order
    drop rows where PM2.5 is missing
    do not interpolate or impute
    no resampling
    no normalization
    no clipping
    no smoothing

status:
    inherited from the previously frozen validation corpus
```

### Q04 — Seoul Bike Sharing Demand

```text
canonical id:
    seoul-bike-demand

domain:
    urban bicycle demand

source:
    UCI Machine Learning Repository

DOI:
    10.24432/C5F62R

license:
    CC BY 4.0

selected field:
    Rented Bike Count

source cardinality:
    8760 rows

preprocessing:
    retain all rows in source order
    reject missing selected values
    convert the selected numeric field only
    no interpolation
    no resampling
    no normalization
    no clipping
    no smoothing
```

### Q05 — Accelerometer

```text
canonical id:
    fan-vibration-x

domain:
    mechanical vibration

source:
    UCI Machine Learning Repository

DOI:
    10.24432/C5Q61V

license:
    CC BY 4.0

selected field:
    x

source cardinality:
    153000 rows

preprocessing:
    retain all rows exactly in source order
    retain all weight configurations and fan-speed blocks
    reject missing selected values
    no regrouping by experimental condition
    no interpolation
    no resampling
    no normalization
    no clipping
    no smoothing
```

The retained concatenation is deliberate: regime boundaries between fan
configurations and speeds remain part of the signal presented to the codec.

### Q06 — Dow Jones Index

```text
canonical id:
    dow-jones-weekly-return

domain:
    financial market returns

source:
    UCI Machine Learning Repository

DOI:
    10.24432/C5788V

license:
    CC BY 4.0

selected entity:
    AA
```

Selected field:

```text
percent_change_price
```

Preprocessing:

```text
filter rows where stock == AA
sort by source date ascending
retain both published quarters
reject duplicate dates
reject missing selected values
strip any presentation characters required to parse the selected numeric field
no interpolation across non-trading periods
no resampling
no normalization
no clipping
no smoothing
```

A single predeclared stock is used so that the canonical object remains one
univariate chronological series rather than a concatenation of independent
equities.

`AA` is frozen before codec execution and SHALL NOT be replaced after observing
compression results.

### Q07 — Room Occupancy Estimation

```text
canonical id:
    room-occupancy-count

domain:
    room occupancy count

source:
    UCI Machine Learning Repository

DOI:
    10.24432/C5P605

license:
    CC BY 4.0

selected field:
    Room_Occupancy_Count

source cardinality:
    10129 rows

sampling:
    source records are collected at approximately 30-second intervals
```

Preprocessing:

```text
retain all rows in source order
reject missing selected values
preserve integer occupancy counts as numeric samples
no interpolation
no resampling
no normalization
no clipping
no smoothing
```

This series intentionally exercises a piecewise-discrete regime.

### Q08 — Power Consumption of Tetouan City

```text
canonical id:
    tetouan-zone1-power

domain:
    electrical distribution load

source:
    UCI Machine Learning Repository

DOI:
    10.24432/C5B034

license:
    CC BY 4.0

selected field:
    Zone 1 Power Consumption

source cardinality:
    52417 rows

sampling:
    10 minutes
```

Preprocessing:

```text
retain all rows in source chronological order
reject missing selected values
no interpolation
no resampling
no normalization
no clipping
no smoothing
```

## Source policy

All eight source datasets are externally produced.

The qualification corpus SHALL record for every source:

```text
canonical source identity
source URL
DOI
license
source archive/file SHA256
source member/file selected
selected field
source row count
missing-value count
canonical sample count
canonical file SHA256
preprocessing rule
```

Source bytes may be cached locally but SHALL NOT be silently substituted with a
different upstream revision.

A source hash mismatch fails preparation.

## Canonical representation

Every resulting canonical Lasagna input SHALL contain:

```text
one numeric sample per line
UTF-8
LF line endings
no header
```

Numeric rendering SHALL use a deterministic round-trippable representation.

Rows retain the chronology defined by this protocol.

## Frozen Lasagna configuration

The qualification SHALL reuse the exact configuration from the previous
real-world validation:

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

No parameter may be retuned:

```text
per dataset
per domain
after observing qualification results
```

The purpose is external qualification of an already defined codec
configuration, not optimization against the qualification corpus.

## Comparison baselines

The same benchmark classes used by the existing real-world validation SHALL be
retained:

```text
raw float64
gzip
zstd
gorilla
lasagna
```

Lossless and lossy results SHALL remain explicitly distinguished.

## Required per-series metrics

For every canonical series the machine-readable result SHALL retain:

```text
sample count
raw bytes
encoded bytes
bits/sample
compression ratio
RMSE
maximum absolute error
encode timing
decode timing
codec implementation/version
configuration
```

## Qualification reporting

The final report SHALL include:

```text
one result table per canonical series
aggregate byte/rate totals
domain/regime coverage
provenance and canonical hashes
preprocessing decisions
failures and weak cases
excluded data, if any
known limitations
```

Individual rows SHALL NOT be hidden by aggregate averages.

If Lasagna loses to a comparison codec, that row remains first-class evidence.

If preprocessing or benchmark execution fails for one of the frozen sources,
the source SHALL NOT be silently replaced.

The failure must be documented and the protocol must be revised explicitly
before selecting any replacement.

## Exclusion policy

Post-result exclusion is forbidden for:

```text
poor compression
high reconstruction error
slow execution
unexpected signal structure
unfavorable comparison with lossless codecs
```

A dataset may be excluded only because the frozen acquisition/preparation
contract cannot be satisfied, for example:

```text
source unavailable
source identity changed
license incompatible with reproducible use
source hash cannot be established
required field absent
preprocessing contract fails
```

Such exclusion requires a documented protocol revision.

## Interpretation boundary

This qualification establishes only:

```text
evidence across the eight frozen external series
reproducibility of acquisition/preparation
behavior of the frozen Lasagna configuration
```

It does not establish:

```text
universal time-series representativeness
universal compression superiority
fitness for every production workload
optimal Lasagna parameter selection
```

## Freeze gates

Before any new codec measurement:

```text
TARGET_SIZE_GATE=PASS
DATASET_SELECTION_GATE=PASS
DOMAIN_REGIME_MATRIX_GATE=PASS
PREPROCESSING_POLICY_GATE=PASS
NO_POST_HOC_SELECTION_GATE=PASS
FROZEN_CONFIGURATION_GATE=PASS

NEW_DATASET_CODEC_EXECUTION_GATE=BLOCKED_UNTIL_SOURCE_MANIFEST_FREEZE
```

## Acquisition revision 1 — source cardinality correction

Anchor before acquisition:

```text
291cd56450b3037be1a10b81b672fff2a9c19a7c
```

This revision was made after source acquisition/reconnaissance and before any
Lasagna measurement on Q04-Q08.

Observed source facts require two manifest corrections:

```text
Q06 Dow Jones Index:
    source data rows = 750
    selected AA rows = 25
    missing selected values = 0

Q08 Tetouan City Power Consumption:
    source data rows = 52416
```

The original Q08 target of `52417 rows` reflected the published observation
count/header-inclusive file-line expectation rather than the actual number of
CSV data rows.

The downloaded member contains:

```text
52417 text lines
= 1 header
+ 52416 data rows
```

Therefore the deterministic preprocessing contract uses:

```text
expected source rows = 52416
expected canonical samples = 52416
```

No dataset was added, removed, replaced or selected based on codec results.

No codec result had been produced when this revision was made.

Revision classification:

```text
ACQUISITION_FACT_CORRECTION
```

Selection remains:

```text
Q01-Q08 unchanged
8 datasets
8 declared domains
```
