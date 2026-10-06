# External dataset production qualification

Issue: #19 — `research: expand external dataset production qualification`

Date: 2026-10-06

Evidence status:

```text
FROZEN PROTOCOL = EXECUTED
TARGET CORPUS = 8 / 8
MACHINE-READABLE RESULTS = FROZEN
GATE 13 = PASS
```

## Evidence anchors

Initial pre-measurement selection anchor:

```text
291cd56450b3037be1a10b81b672fff2a9c19a7c
```

Canonical-input pre-codec anchor:

```text
34cf0270126942cefc605db572a2fd1f92bd94b1
```

Executed result SHA256:

```text
d5af5be4e474aa906d0000b6d40b94e1db208524ddff72d9e914c499c8fb31be
```

No Q04-Q08 codec measurement occurred before the second anchor was published.

## Frozen configuration

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

No per-dataset retuning was performed.

## Corpus

| ID | Dataset | Domain | Samples | Canonical SHA256 |
| --- | --- | --- | ---: | --- |
| Q01 | `appliances-energy.csv` | building-appliance-energy | 19735 | `a7af25a1bebf2cbb0a017b3ab34e96904a61eefba59beae4cde011e64eab9402` |
| Q02 | `metro-traffic.csv` | road-traffic-volume | 48204 | `23ce44d2d08325fb23bf4e8c04960c669281879b79e9cb2b8675d90e55294fde` |
| Q03 | `beijing-pm25.csv` | urban-particulate-pollution | 34139 | `d060d68f6ca94364d7e07a4961075f0ea660616aa543c59a20133319417db18d` |
| Q04 | `seoul-bike-demand.csv` | urban-bicycle-demand | 8760 | `717730a0fd79b34d265781450bc0e12758e0758bb100f0bfd6784f14aacd058d` |
| Q05 | `fan-vibration-x.csv` | mechanical-vibration | 153000 | `f04492df927bf24f41019990655451ecb7e997036bcc0a1a15db77b12eb54be4` |
| Q06 | `dow-jones-weekly-return.csv` | financial-market-returns | 25 | `c2d6c84ba8cac728b3e2f83288fc202ec2b6144dc868b3798f037392c5704f67` |
| Q07 | `room-occupancy-count.csv` | room-occupancy | 10129 | `cb5c023bae304933ecd15e9c8204b3832e7f35d3ef8c695ab7c7450d0242672a` |
| Q08 | `tetouan-zone1-power.csv` | electrical-distribution-load | 52416 | `fc2f9ba9cf34689c7abbc253565f795f3ce46c369834cccdc80e35224a2a9cf1` |

## Per-series qualification results

| Dataset | Best lossless | Best lossless B | Lasagna B | Delta | Lasagna bits/sample | RMSE | Max abs error |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `appliances-energy.csv` | gzip | 14745 | 46997 | +32252 (+218.73%) | 19.051228781 | 10.2364019199 | 63.4364929199 |
| `metro-traffic.csv` | gorilla | 90106 | 114626 | +24520 (+27.21%) | 19.023483528 | 224.401842859 | 829.730163574 |
| `beijing-pm25.csv` | gzip | 47214 | 81201 | +33987 (+71.99%) | 19.028325376 | 4.68227093084 | 63.3749084473 |
| `seoul-bike-demand.csv` | gorilla | 16857 | 20930 | +4073 (+24.16%) | 19.114155251 | 62.2773548717 | 235.591522217 |
| `fan-vibration-x.csv` | gzip | 225047 | 238914 | +13867 (+6.16%) | 12.492235294 | 0.105161964514 | 0.830831133127 |
| `dow-jones-weekly-return.csv` | raw | 200 | 183 | -17 (-8.50%) | 58.560000000 | 0.497013563793 | 0.797276387691 |
| `room-occupancy-count.csv` | gzip | 198 | 13763 | +13565 (+6851.01%) | 10.870174746 | 0.00506892158875 | 0.0905025005341 |
| `tetouan-zone1-power.csv` | gzip | 176165 | 124602 | -51563 (-29.27%) | 19.017399267 | 197.04610388 | 1164.58869913 |

## Aggregate

```text
datasets                    = 8
domains                     = 8
samples                     = 326408
raw bytes                   = 2611264
Lasagna bytes               = 641216
best-per-series lossless B  = 570532
Lasagna aggregate bits/sample = 15.715693243
best lossless aggregate bits/sample = 13.983284723
Lasagna smaller than best lossless = 2/8
Lasagna larger/equal             = 6/8
```

The aggregate is descriptive only. It does not erase the individual dataset outcomes.

## Favorable cases

- `dow-jones-weekly-return.csv`: Lasagna 183 B versus raw 200 B (-8.50% delta), with RMSE 0.497013563793 and maximum absolute error 0.797276387691.
- `tetouan-zone1-power.csv`: Lasagna 124602 B versus gzip 176165 B (-29.27% delta), with RMSE 197.04610388 and maximum absolute error 1164.58869913.

These are rate-distortion outcomes, not lossless-codec victories: Lasagna is lossy.

The 25-sample Dow Jones series is especially too small for a broad efficiency claim; fixed container/header costs dominate such a small input.

## Failure and weak-case evidence

- `appliances-energy.csv`: Lasagna 46997 B versus gzip 14745 B (+218.73%), while also introducing reconstruction error (RMSE 10.2364019199).
- `metro-traffic.csv`: Lasagna 114626 B versus gorilla 90106 B (+27.21%), while also introducing reconstruction error (RMSE 224.401842859).
- `beijing-pm25.csv`: Lasagna 81201 B versus gzip 47214 B (+71.99%), while also introducing reconstruction error (RMSE 4.68227093084).
- `seoul-bike-demand.csv`: Lasagna 20930 B versus gorilla 16857 B (+24.16%), while also introducing reconstruction error (RMSE 62.2773548717).
- `fan-vibration-x.csv`: Lasagna 238914 B versus gzip 225047 B (+6.16%), while also introducing reconstruction error (RMSE 0.105161964514).
- `room-occupancy-count.csv`: Lasagna 13763 B versus gzip 198 B (+6851.01%), while also introducing reconstruction error (RMSE 0.00506892158875).

The room-occupancy series is the strongest negative case: a highly repetitive discrete signal is extremely compact under gzip while the frozen Lasagna configuration carries much larger structural overhead.

The vibration series is a near-rate case rather than a win: Lasagna is only modestly larger than the best lossless stream but remains lossy.

No weak case was removed or replaced after measurement.

## Timing observations

Timing is retained as machine-readable evidence but is not used as a cross-machine performance claim.

| Dataset | Lasagna encode ms | Lasagna decode ms |
| --- | ---: | ---: |
| `appliances-energy.csv` | 77.510583 | 11.674164 |
| `metro-traffic.csv` | 189.933704 | 28.813941 |
| `beijing-pm25.csv` | 133.219007 | 20.479860 |
| `seoul-bike-demand.csv` | 33.970052 | 5.086912 |
| `fan-vibration-x.csv` | 3544.059930 | 78.641693 |
| `dow-jones-weekly-return.csv` | 0.139438 | 0.034370 |
| `room-occupancy-count.csv` | 301.881864 | 4.539609 |
| `tetouan-zone1-power.csv` | 228.007089 | 36.247774 |

The vibration workload is the clearest encode-time outlier in this run.

## Acquisition and preprocessing

Full source URLs, archive SHA256 values, source member SHA256 values, encodings, row counts, selected fields and missing-value counts are frozen in:

```text
data/external-qualification/acquisition.tsv
```

Canonical sample counts and SHA256 values are frozen in:

```text
data/external-qualification/canonical-manifest.tsv
```

The preparation implementation is:

```text
tools/prepare_external_qualification.py
```

Raw source archives and generated canonical series remain intentionally untracked. They are reproduced from the frozen metadata and preparation tool.

## Known limitations

- Eight series across eight declared domains improve coverage but do not constitute a statistically representative sample of all time-series workloads.
- Every canonical object is univariate.
- The frozen configuration is intentionally not tuned per dataset.
- Comparison against lossless codecs is informative for size but not quality-equivalent because Lasagna is lossy.
- The Dow Jones AA series contains only 25 samples and is retained as a deliberately small/noisy regime, not as evidence of general financial performance.
- The Accelerometer series concatenates the source's experimental regimes as preregistered.
- Timing values are environment-specific and are not used for universal throughput claims.

## Interpretation

The expanded corpus rejects a simple universal compression-superiority narrative.

The frozen configuration behaves differently across signal structures: it is strongly unfavorable on highly repetitive occupancy data, moderately unfavorable on several heterogeneous measurements, near the best lossless size on vibration, and reaches smaller streams than the best lossless comparison on two frozen series only by accepting reconstruction error.

The production qualification claim is therefore about breadth, reproducibility and characterized behavior, not universal superiority.

## Qualification gates

```text
TARGET_CORPUS_SIZE_GATE=PASS
MULTI_DOMAIN_CORPUS_GATE=PASS
PREMEASUREMENT_SELECTION_GATE=PASS
SOURCE_PROVENANCE_GATE=PASS
SOURCE_LICENSE_GATE=PASS
SOURCE_HASH_GATE=PASS
DETERMINISTIC_PREPROCESSING_GATE=PASS
CANONICAL_HASH_GATE=PASS
FROZEN_CONFIGURATION_GATE=PASS
MACHINE_READABLE_RESULTS_GATE=PASS
PER_DATASET_METRICS_GATE=PASS
AGGREGATE_METRICS_GATE=PASS
FAILURE_CASE_RETENTION_GATE=PASS
KNOWN_LIMITATIONS_GATE=PASS
NO_POST_HOC_SELECTION_GATE=PASS
UNIVERSAL_SUPERIORITY_CLAIM=NO
PRODUCTION_READINESS_GATE_13=PASS
```
