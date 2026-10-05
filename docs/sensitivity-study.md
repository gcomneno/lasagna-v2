# Segmentation and quantization sensitivity study

Date: 2026-10-05

Status: completed

## Purpose

Issue #5 characterizes sensitivity to quantization and adaptive segmentation parameters across the frozen internal examples and real-world validation corpus.

The study is deliberately not a per-dataset optimizer.

## Evidence volume

- Primary one-factor-at-a-time sweep: 18 configurations × 6 datasets = 108 evaluation points.
- Segmentation interaction follow-up: 12 configurations × 6 datasets = 72 evaluation points.
- Total evaluated points: 180.

## Quantization finding

The historical V2 implicit default `C_Q=0.5` is dominated by `C_Q=0.125` over the evaluated corpus.

| Dataset | Bytes at 0.5 | Bytes at 0.125 | RMSE at 0.5 | RMSE at 0.125 |
| --- | ---: | ---: | ---: | ---: |
| trend.csv | 402 | 402 | 1.71418414421e-07 | 1.71418414421e-07 |
| sine_noise.csv | 678 | 678 | 0.0831633437504 | 0.023933467074 |
| flat_spike.csv | 590 | 590 | 0.0911111324764 | 0.0270539909108 |
| appliances-energy.csv | 46997 | 46997 | 10.2364019199 | 2.53810370865 |
| metro-traffic.csv | 114626 | 114626 | 224.401842859 | 55.3474844594 |
| beijing-pm25.csv | 81201 | 81201 | 4.68227093084 | 1.19798575886 |

For the tested datasets, the lower `C_Q` preserves encoded size in the meaningful comparisons while substantially reducing reconstruction error.

Decision:

```text
V1 implicit C_Q default = 0.5   (unchanged legacy contract)
V2 implicit C_Q default = 0.125
encode_timeseries() C_Q default = 0.125
```

Historical benchmark artifacts explicitly evaluated with `C_Q=0.5` remain unchanged.

## Segmentation finding

The original adaptive window `32/128` creates substantial segment metadata overhead on long real-world series.

Larger windows can reduce encoded size dramatically:

| Dataset | Reference bytes | Reference segments | Aggressive bytes | Aggressive segments |
| --- | ---: | ---: | ---: | ---: |
| trend.csv | 402 | 2 | 358 | 1 |
| sine_noise.csv | 678 | 6 | 502 | 2 |
| flat_spike.csv | 590 | 4 | 502 | 2 |
| appliances-energy.csv | 46997 | 617 | 23281 | 78 |
| metro-traffic.csv | 114626 | 1507 | 56634 | 189 |
| beijing-pm25.csv | 81201 | 1067 | 40149 | 134 |

However, larger windows do not improve quality uniformly. Some datasets pay substantial reconstruction-error penalties.

The `128/512` cross-dataset follow-up reduced encoded size strongly on average, but the worst observed RMSE increase was too large to justify promotion to the default.

Therefore the adaptive `32/128` window remains the current default. Larger windows remain explicit experimental rate-distortion operating points.

## MSE-threshold finding

`mse_threshold` affects segmentation strongly on some datasets but is effectively inert over the tested range on others, notably Metro traffic under the tested configuration.

This demonstrates that a single threshold cannot currently be treated as a universal segmentation-control solution.

## Predictor distribution

Every evaluation point accounted for all emitted segments across the mean, linear and random-walk predictor classes. Predictor selection remained automatic throughout the study.

No predictor was manually selected per dataset.

## Scientific interpretation

The study identifies two distinct behaviors:

1. Quantization coefficient: the previous V2 default was unnecessarily aggressive. Lowering `C_Q` to `0.125` improves quality without a meaningful size penalty on the evaluated corpus.

2. Segmentation: metadata overhead is a major compression cost on long real-world series. Larger segments can remove roughly half of the encoded size in several cases, but the associated error trade-off is dataset-dependent.

The evidence therefore supports a V2 quantization-default revision but does not yet support a universal segmentation default revision.

## Acceptance gates

```text
PARAMETER_RANGES_FROZEN_GATE=PASS
SWEEP_REPRODUCIBILITY_GATE=PASS
SIZE_QUALITY_TRADEOFF_GATE=PASS
PER_DATASET_REPORTING_GATE=PASS
PREDICTOR_DISTRIBUTION_GATE=PASS
RUNTIME_MEASUREMENT_GATE=PASS
DEFAULT_REVISION_EVIDENCE_GATE=PASS
NO_PER_DATASET_TUNING_GATE=PASS
V1_COMPATIBILITY_PRESERVATION_GATE=PASS
```
