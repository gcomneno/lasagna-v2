# Real-world heterogeneous validation

Date: 2026-10-05

Evidence status: executed frozen evaluation

## Scope

This report evaluates Lasagna 2 on three externally sourced real-world univariate time series from distinct domains.

The corpus and preprocessing rules were frozen before codec evaluation. No Lasagna parameter was tuned independently for any validation dataset.

The real-world evidence is intentionally separate from the synthetic M2.3 corpus and from the internal example benchmark.

## Frozen Lasagna configuration

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

## Corpus provenance

| Dataset | Domain | DOI | License | Samples | Canonical SHA256 |
| --- | --- | --- | --- | ---: | --- |
| appliances-energy.csv | building-energy | 10.24432/C5VC8G | CC-BY-4.0 | 19735 | `a7af25a1bebf2cbb0a017b3ab34e96904a61eefba59beae4cde011e64eab9402` |
| metro-traffic.csv | transportation | 10.24432/C5X60B | CC-BY-4.0 | 48204 | `23ce44d2d08325fb23bf4e8c04960c669281879b79e9cb2b8675d90e55294fde` |
| beijing-pm25.csv | environment | 10.24432/C5RK5G | CC-BY-4.0 | 34139 | `d060d68f6ca94364d7e07a4961075f0ea660616aa543c59a20133319417db18d` |

Full download URLs, source archive hashes, source members, missing-value policies and expected cardinalities are frozen in `data/real-world/manifest.tsv`.

## Per-dataset results

### `appliances-energy.csv`

| Codec | Class | Bytes | Bits/sample | Ratio | RMSE | Max abs error |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| raw | lossless | 157880 | 64.000000000 | 1.000000000 | 0 | 0 |
| gzip | lossless | 14745 | 5.977197872 | 10.707358427 | 0 | 0 |
| zstd | lossless | 21164 | 8.579275399 | 7.459837460 | 0 | 0 |
| gorilla | lossless | 26799 | 10.863541931 | 5.891264599 | 0 | 0 |
| lasagna | lossy | 46997 | 19.051228781 | 3.359363364 | 10.2364019199 | 63.4364929199 |

Best lossless result: `gzip` at 14745 bytes.

Frozen Lasagna result: 46997 bytes, RMSE 10.2364019199, max absolute error 63.4364929199.

Lasagna is 32252 bytes (218.73%) larger than the best lossless stream on this dataset while also being lossy.

### `metro-traffic.csv`

| Codec | Class | Bytes | Bits/sample | Ratio | RMSE | Max abs error |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| raw | lossless | 385632 | 64.000000000 | 1.000000000 | 0 | 0 |
| gzip | lossless | 102749 | 17.052360800 | 3.753146016 | 0 | 0 |
| zstd | lossless | 99896 | 16.578873123 | 3.860334748 | 0 | 0 |
| gorilla | lossless | 90106 | 14.954111692 | 4.279759394 | 0 | 0 |
| lasagna | lossy | 114626 | 19.023483528 | 3.364262907 | 224.401842859 | 829.730163574 |

Best lossless result: `gorilla` at 90106 bytes.

Frozen Lasagna result: 114626 bytes, RMSE 224.401842859, max absolute error 829.730163574.

Lasagna is 24520 bytes (27.21%) larger than the best lossless stream on this dataset while also being lossy.

### `beijing-pm25.csv`

| Codec | Class | Bytes | Bits/sample | Ratio | RMSE | Max abs error |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| raw | lossless | 273112 | 64.000000000 | 1.000000000 | 0 | 0 |
| gzip | lossless | 47214 | 11.063944462 | 5.784555428 | 0 | 0 |
| zstd | lossless | 57649 | 13.509241630 | 4.737497615 | 0 | 0 |
| gorilla | lossless | 109173 | 25.583174668 | 2.501644179 | 0 | 0 |
| lasagna | lossy | 81201 | 19.028325376 | 3.363406855 | 4.68227093084 | 63.3749084473 |

Best lossless result: `gzip` at 47214 bytes.

Frozen Lasagna result: 81201 bytes, RMSE 4.68227093084, max absolute error 63.3749084473.

Lasagna is 33987 bytes (71.99%) larger than the best lossless stream on this dataset while also being lossy.

## Aggregate results

| Codec | Total bytes | Aggregate bits/sample |
| --- | ---: | ---: |
| raw | 816624 | 64.000000000 |
| gzip | 164708 | 12.908403378 |
| zstd | 178709 | 14.005681930 |
| gorilla | 226078 | 17.718058739 |
| lasagna | 242824 | 19.030466898 |

The per-dataset best lossless streams total **152065 bytes**. The frozen Lasagna streams total **242824 bytes**.

## Failure / regression evidence

The frozen Lasagna configuration does not beat the best lossless baseline in encoded size on any of the three real-world datasets.

This is an unfavorable result for the current configuration and is retained as first-class evidence.

Observed failures:

- `appliances-energy.csv`: Lasagna 46997 B vs gzip 14745 B; RMSE 10.2364019199; max error 63.4364929199.
- `metro-traffic.csv`: Lasagna 114626 B vs gorilla 90106 B; RMSE 224.401842859; max error 829.730163574.
- `beijing-pm25.csv`: Lasagna 81201 B vs gzip 47214 B; RMSE 4.68227093084; max error 63.3749084473.

No post-hoc predictor, segmentation, quantization or residual coding change was made after observing these results.

## Interpretation

The synthetic and internal-example evidence established that Lasagna can exploit deliberately structured signals and can occupy useful rate-distortion points on those corpora.

This frozen real-world evaluation shows that the same configuration does not transfer automatically to heterogeneous measurements. On all three datasets, a mature lossless codec produces a smaller stream while preserving the input exactly.

The result therefore weakens any broad compression claim and strengthens the case for investigating model selection, segmentation, quantization policy and residual coding as separate future research questions.

No universal superiority claim is supported.

## Reproducibility gates

```text
MULTI_DOMAIN_CORPUS_GATE=PASS
PROVENANCE_LICENSE_GATE=PASS
DETERMINISTIC_PREPROCESSING_GATE=PASS
CANONICAL_HASH_GATE=PASS
FROZEN_CONFIGURATION_GATE=PASS
PER_DATASET_METRICS_GATE=PASS
AGGREGATE_METRICS_GATE=PASS
FAILURE_CASE_RETENTION_GATE=PASS
SYNTHETIC_REAL_WORLD_SEPARATION_GATE=PASS
UNIVERSAL_SUPERIORITY_CLAIM=NO
```
