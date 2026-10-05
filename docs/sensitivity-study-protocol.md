# Segmentation and quantization sensitivity study

Date: 2026-10-05

Status: FROZEN BEFORE SWEEP EXECUTION

## Purpose

This experiment characterizes how Lasagna V2 encoded size, reconstruction
quality, segmentation structure, predictor selection and runtime respond to
changes in segmentation and quantization parameters.

The experiment is diagnostic. It is not a per-dataset optimizer.

## Dataset groups

Two evidence groups remain explicitly separate.

### Internal examples

- `data/examples/trend.csv`
- `data/examples/sine_noise.csv`
- `data/examples/flat_spike.csv`

### Frozen real-world corpus

- `data/real-world/canonical/appliances-energy.csv`
- `data/real-world/canonical/metro-traffic.csv`
- `data/real-world/canonical/beijing-pm25.csv`

The real-world inputs retain the canonical SHA256 identities frozen by issue
#4.

## Reference configuration

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

Under adaptive segmentation, `segment_length` is not an active segmentation
control and remains fixed only for API completeness.

## Experimental design

The study uses a one-factor-at-a-time design around the reference
configuration.

Only one parameter family changes in each sweep row.

This deliberately avoids a full factorial search and prevents the experiment
from becoming an implicit per-dataset optimizer.

### Quantization axis

```text
C_Q =
0.0625
0.125
0.25
0.5
1
2
4
```

All segmentation parameters remain at the reference configuration.

### Segmentation-error axis

```text
mse_threshold =
0.125
0.5
2
8
32
128
512
2048
```

All other parameters remain at the reference configuration.

The wide geometric range is intentional because the threshold is expressed in
the native value scale and the validation datasets have very different
magnitudes.

### Segment-window axis

```text
min/max =
16/64
32/128
64/256
128/512
256/1024
```

All other parameters remain at the reference configuration.

### Frozen controls

The following are not swept in this experiment:

```text
segment_mode=adaptive
predictor=auto
residual_coding=varint
Q_MIN=1e-6
segment_length=64
```

Predictor selection remains automatic so that predictor distribution can be
observed as an output rather than manually tuned per dataset.

`Q_MIN` remains fixed because this study first isolates the dominant
quantization coefficient and adaptive-segmentation controls. A separate
experiment is required before making claims about `Q_MIN` sensitivity.

## Unique configurations

The reference configuration occurs on all three axes but SHALL be evaluated
only once.

Expected unique configurations per dataset:

```text
7 C_Q rows
8 MSE-threshold rows
5 segment-window rows
-2 duplicate reference rows
=18 unique configurations
```

With six datasets:

```text
18 * 6 = 108 evaluation points
```

## Measurements

Each evaluation point SHALL report at minimum:

```text
dataset
evidence group
sweep axis
configuration id
C_Q
Q_MIN
min segment length
max segment length
MSE threshold
encoded bytes
bits/sample
compression ratio
MSE
RMSE
maximum absolute error
segment count
mean segment length
minimum observed segment length
maximum observed segment length
mean predictor segment count
linear predictor segment count
random-walk predictor segment count
encode time
decode time
```

## Timing protocol

Timing SHALL use:

```text
3 timed repetitions
1 warm-up
median wall-clock time
```

Encoded bytes must be deterministic across timed encode repetitions.

Timing values are observational and are not expected to reproduce exactly
across hosts.

## Analysis rules

Results SHALL be reported per dataset.

Internal-example and real-world results SHALL remain separately identifiable.

No configuration may be declared a new default solely because it wins on one
dataset.

The reference configuration SHALL remain the default unless the evidence
supports an explicit cross-dataset revision.

Stable regions, pathological regions and unfavorable trade-offs SHALL be
reported, not filtered out.

Any proposed default revision must be stated separately from the raw sweep
results and must explain its cross-dataset trade-off.

No hidden per-dataset tuning is permitted.

## Follow-up segmentation interaction study

Status: FROZEN BEFORE FOLLOW-UP EXECUTION

The first one-factor-at-a-time sweep showed that:

- `C_Q` strongly affects reconstruction error but usually has little effect on
  encoded size in the tested range;
- larger adaptive segment windows substantially reduce encoded size;
- very large windows may increase reconstruction error;
- `mse_threshold` can reduce segmentation overhead on some datasets but is
  inactive over the tested range on others.

A second, explicitly frozen follow-up therefore studies the interaction
between the adaptive segment window and segmentation MSE threshold.

This is not a per-dataset search. Every configuration is evaluated on every
dataset.

Frozen controls remain:

```text
segment_mode=adaptive
predictor=auto
residual_coding=varint
segment_length=64
C_Q=0.5
Q_MIN=1e-6
```

Interaction grid:

```text
segment windows:
64/256
128/512
256/1024

mse_threshold:
32
128
512
2048
```

Expected follow-up size:

```text
3 windows * 4 thresholds = 12 configurations
12 configurations * 6 datasets = 72 evaluation points
```

The purpose is to identify cross-dataset rate-distortion regions where larger
potential segments are still constrained by model error, rather than simply
forcing maximum-length segments.

No configuration may be selected as a new default from a single dataset.

## Evidence-based default decision

The frozen sensitivity study found that the historical V2 quantization default
`C_Q=0.5` is dominated by `C_Q=0.125` over the evaluated corpus.

Across the tested datasets, reducing `C_Q` from `0.5` to `0.125` preserved
encoded size in the relevant comparisons while substantially reducing
reconstruction error. No dataset showed a meaningful encoded-size penalty that
would justify retaining `0.5` as the current V2 default.

Decision:

```text
legacy V1 implicit C_Q default = 0.5
current V2 implicit C_Q default = 0.125
current encode_timeseries() default = 0.125
```

The V1 default remains unchanged because it is part of the frozen legacy
compatibility contract.

Historical benchmark and validation artifacts that explicitly used `C_Q=0.5`
remain unchanged. They are evidence of the configuration evaluated at that
time and are not rewritten retroactively.

The segmentation-window evidence is not yet strong enough to justify changing
the current `32/128` V2 adaptive defaults. Larger windows remain experimental
rate-distortion operating points.
