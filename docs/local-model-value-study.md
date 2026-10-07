# Local-model value study

Status: COMPLETED

## Scope

This study evaluates whether Lasagna 2's adaptive segmentation plus local predictor selection reduces total V2 rate enough to repay its structural cost relative to the frozen whole-series and fixed-64 linear baselines.

The result applies only to the frozen 8-dataset external corpus, the frozen seven-point C_Q grid, the common observed matched-distortion ranges, and the V2 accounting contract defined by the preregistered protocol.

Protocol freeze commit:

`198c8fd3434360c405d15a3e2a353dab039ca1ec`

Implementation commit:

`4308aedacb3f74463e02b340be409d48c73f4e6d`

## Primary result

- Execution completed: **True**
- Primary claim supported: **False**
- Overall outcome: **MIXED**
- Dataset median material wins: **0/8**
- Dataset median material losses: **7/8**
- Geometric mean of dataset median rate ratios: **1.876442**
- Pooled non-loss fraction: **0.084112**

The frozen primary empirical-advantage claim is therefore **NOT SUPPORTED**.

## Frozen decision gates

| Gate | Result |
| --- | --- |
| 0 — complete external coverage | PASS |
| 1 — at least 6/8 median wins | FAIL |
| 2 — geometric mean <= 0.95 | FAIL |
| 3 — at most 1/8 median losses | FAIL |
| 4 — pooled non-loss >= 75% | FAIL |
| 5 — exact byte accounting | PASS |

## Reproducibility gates

- `COMMON_CODEC_CONTROLS_GATE`: **PASS**
- `DETERMINISTIC_BYTES_GATE`: **PASS**
- `EXACT_BYTE_ACCOUNTING_GATE`: **PASS**
- `EXTERNAL_CORPUS_COVERAGE_GATE`: **PASS**
- `FULL_GRID_EXECUTION_GATE`: **PASS**
- `MATCHED_DISTORTION_GATE`: **PASS**
- `NEGATIVE_RESULT_PRESERVATION_GATE`: **PASS**
- `NO_DATASET_SPECIFIC_TUNING_GATE`: **PASS**
- `PARETO_REPORTING_GATE`: **PASS**
- `PER_DATASET_REPORTING_GATE`: **PASS**
- `PRIMARY_TARGET_COVERAGE_GATE`: **PASS**
- `PROTOCOL_FROZEN_BEFORE_EXECUTION_GATE`: **PASS**
- `RUNTIME_MEASUREMENT_GATE`: **PASS**

## External dataset results

| Dataset | Targets | Median ratio | Best | Worst | W/T/L | Non-loss |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| appliances-energy.csv | 17 | 2.361942 | 2.328248 | 2.361942 | 0/0/17 | 0.000000 |
| metro-traffic.csv | 17 | 2.369940 | 2.369940 | 2.370788 | 0/0/17 | 0.000000 |
| beijing-pm25.csv | 15 | 2.367264 | 2.350001 | 2.367264 | 0/0/15 | 0.000000 |
| seoul-bike-demand.csv | 17 | 2.345732 | 2.341273 | 2.345732 | 0/0/17 | 0.000000 |
| fan-vibration-x.csv | 15 | 1.559889 | 1.536565 | 1.559889 | 0/0/15 | 0.000000 |
| dow-jones-weekly-return.csv | 9 | 1.000000 | 1.000000 | 1.000000 | 0/9/0 | 1.000000 |
| room-occupancy-count.csv | 6 | 1.337640 | 1.337640 | 1.337640 | 0/0/6 | 0.000000 |
| tetouan-zone1-power.csv | 11 | 2.369822 | 2.369822 | 2.369822 | 0/0/11 | 0.000000 |

Seven of the eight external datasets are materially unfavorable at the dataset-median level. `dow-jones-weekly-return.csv` is neutral.

## Architectural decomposition

| Comparison | Pooled matched-distortion median ratio | Interpretation |
| --- | ---: | --- |
| A2/A1 | 1.000000 | no observed median rate change |
| A3/A1 | 1.404104 | higher rate |
| A4/A2 | 1.403392 | higher rate |
| A4/A3 | 1.000000 | no observed median rate change |

The frozen descriptive comparisons show essentially no rate benefit from predictor auto-selection (`A2/A1` and `A4/A3` are approximately 1.0). The dominant effect is adaptive segmentation: pooled `A3/A1` is about 1.4047, although adaptive segmentation is favorable on specific datasets.

Notable favorable adaptive cases:

- `fan-vibration-x.csv`: A3/A1 median = **0.924886**.
- `room-occupancy-count.csv`: A3/A1 median = **0.798458**.

## Structural overhead

| Architecture | Median structural fraction of encoded bytes |
| --- | ---: |
| A0 | 0.0065 |
| A1 | 0.4089 |
| A2 | 0.4089 |
| A3 | 0.5795 |
| A4 | 0.5795 |

The adaptive architectures carry substantially more structural overhead than the simpler baselines on this corpus. This result motivates a separate post-study investigation into segmentation economics and metadata amortization; no production change is implied by this experiment.

## Pooled Pareto presence

| Dataset | A0 | A1 | A2 | A3 | A4 |
| --- | ---: | ---: | ---: | ---: | ---: |
| appliances-energy.csv | 3 | 1 | 1 | 0 | 1 |
| metro-traffic.csv | 1 | 1 | 1 | 1 | 1 |
| beijing-pm25.csv | 3 | 1 | 1 | 1 | 1 |
| seoul-bike-demand.csv | 2 | 1 | 1 | 1 | 1 |
| fan-vibration-x.csv | 3 | 0 | 0 | 0 | 1 |
| dow-jones-weekly-return.csv | 1 | 1 | 1 | 1 | 1 |
| room-occupancy-count.csv | 1 | 0 | 1 | 0 | 3 |
| tetouan-zone1-power.csv | 1 | 1 | 1 | 1 | 1 |

Pareto analysis is complementary only and does not replace the frozen matched-distortion decision rule.

## Internal sanity corpus

| Dataset | Coverage | Median ratio |
| --- | --- | ---: |
| trend.csv | INSUFFICIENT_COVERAGE | n/a |
| sine_noise.csv | COMPLETE | 1.4721030042918455 |
| flat_spike.csv | COMPLETE | 1.2832618025751072 |

Internal datasets remain secondary evidence and do not contribute to the primary external-corpus claim.

## Execution provenance

- Dirty tree at execution start: `False`
- Warm-up calls: `1`
- Timed repetitions: `3`
- Python: `3.12.3 (main, Aug 31 2026, 10:18:26) [GCC 13.3.0]`
- Platform: `Linux-6.8.0-146-generic-x86_64-with-glibc2.39`
- CPU: `Intel(R) Core(TM) i3-4330 CPU @ 3.50GHz`
- Codec source: `lasagna2/core.py`
- Codec SHA256: `b9db63d5b4b37117e9eb2f55b21c0d75cabddd0ed3c195b6d4468981821c2a48`
- Recorded datasets: `11`
- Recorded evaluation points: `385`

Dataset SHA256 values, full architecture/configuration definitions, exact command line, execution order and dependency versions are retained in `docs/local-model-value-provenance.json`.

## Conclusion

Within the preregistered experiment, Lasagna 2's current adaptive structural architecture does **not** demonstrate a total-V2-rate advantage over the specified linear baselines at matched distortion.

The result is not evidence that local modeling is universally ineffective. The favorable adaptive results on fan vibration and room occupancy show that local segmentation can repay its structural cost for some signal shapes. The next research question is therefore whether segment creation and representation can become explicitly cost-aware without changing this completed experiment.
