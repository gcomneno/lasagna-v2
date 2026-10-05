# External codec benchmark

Date: 2026-10-05

Evidence status: executed comparative benchmark

## Scope

This benchmark compares Lasagna 2 against explicitly defined storage and compression baselines on the three example datasets tracked in this repository.

The comparison deliberately separates two different classes:

- **lossless baselines:** raw float64, gzip, zstd, Gorilla;
- **lossy rate-distortion codec:** Lasagna 2.

A smaller Lasagna stream is therefore not, by itself, evidence that Lasagna is superior to a lossless codec. Its encoded size must be interpreted together with reconstruction error.

The results apply only to the datasets, implementations and configurations executed here. They do not establish universal compression superiority.

## Reproduction

Canonical command:

```bash
python tools/benchmark_codec.py \
  data/examples/trend.csv \
  data/examples/sine_noise.csv \
  data/examples/flat_spike.csv \
  --repetitions 9 \
  --warmup 2 \
  --output docs/external-codec-benchmark.csv
```

Timing values are median wall-clock measurements from nine timed operations after two warm-up operations. Timing is not expected to be byte-for-byte reproducible across hosts or runs.

All non-timing result fields were regenerated in an independent replay and matched the primary run.

Canonical raw input representation:

```text
contiguous little-endian IEEE-754 binary64 samples
```

Gorilla is evaluated in values-only `f64` mode. Because the library payload is not independently self-describing, the benchmark adds and counts a deterministic 20-byte frame:

```text
8 bytes  GORILLA1 marker
8 bytes  unsigned sample count
4 bytes  f64 format marker
N bytes  Gorilla payload
```

## Environment and implementations

- Python: `3.12.3`
- `gorillacompression`: `1.0.2`
- `lasagna-v2`: `0.3.0`
- `python-gzip`: `1.3`
- `python-struct`: `3.12.3`
- `zstd-cli`: `*** Zstandard CLI (64-bit) v1.5.5, by Yann Collet ***`

## Results

When multiple Lasagna configurations have the same minimum encoded size, the
reported representative minimum is selected by:

```text
encoded bytes ascending
RMSE ascending
max absolute error ascending
```

This tie-break does not change the measured rows; it only avoids presenting an
arbitrary first configuration when several occupy the same rate point.

### `trend.csv`

| Codec | Class | Configuration | Bytes | Bits/sample | Ratio | RMSE | Max abs error | Encode ms | Decode ms |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| raw | lossless | float64_le | 1600 | 64.000000000 | 1.000000000 | 0 | 0 | 0.003314000 | 0.010757000 |
| gzip | lossless | level_9_mtime_0 | 460 | 18.400000000 | 3.478260870 | 0 | 0 | 0.070861000 | 0.018187000 |
| zstd | lossless | cli_default | 375 | 15.000000000 | 4.266666667 | 0 | 0 | 2.452760000 | 1.784384000 |
| gorilla | lossless | values_only_f64_canonical_frame | 1634 | 65.360000000 | 0.979192166 | 0 | 0 | 0.324859000 | 0.585033000 |
| lasagna | lossy | fixed_mean_raw | 1090 | 43.600000000 | 1.467889908 | 0.258312233816 | 0.450000190735 | 0.191071000 | 0.050529000 |
| lasagna | lossy | fixed_linear_raw | 1090 | 43.600000000 | 1.467889908 | 1.6774897675e-07 | 2.84612177381e-07 | 0.207576000 | 0.056501000 |
| lasagna | lossy | fixed_rw_raw | 1090 | 43.600000000 | 1.467889908 | 0.0280703339339 | 0.0494127005339 | 0.384494000 | 0.066001000 |
| lasagna | lossy | fixed_mean_varint | 490 | 19.600000000 | 3.265306122 | 0.258312233816 | 0.450000190735 | 0.280709000 | 0.106448000 |
| lasagna | lossy | fixed_linear_varint | 490 | 19.600000000 | 3.265306122 | 1.6774897675e-07 | 2.84612177381e-07 | 0.298521000 | 0.114373000 |
| lasagna | lossy | fixed_rw_varint | 490 | 19.600000000 | 3.265306122 | 0.0280703339339 | 0.0494127005339 | 0.297345000 | 0.113867000 |
| lasagna | lossy | adaptive_mean_varint | 622 | 24.880000000 | 2.572347267 | 0.129811550404 | 0.226691496372 | 0.404648000 | 0.123778000 |
| lasagna | lossy | adaptive_linear_varint | 402 | 16.080000000 | 3.980099502 | 1.71418414421e-07 | 2.96533105626e-07 | 4.270435000 | 0.110340000 |
| lasagna | lossy | adaptive_rw_varint | 402 | 16.080000000 | 3.980099502 | 0.0745284149268 | 0.15859290557 | 4.019145000 | 0.171693000 |
| lasagna | lossy | adaptive_auto_varint | 402 | 16.080000000 | 3.980099502 | 1.71418414421e-07 | 2.96533105626e-07 | 4.457076000 | 0.115874000 |

Observed size minima within the frozen comparison matrix:

- smallest lossless stream: `zstd` / `cli_default` — 375 bytes, 15.000000000 bits/sample;
- smallest Lasagna stream: `adaptive_linear_varint` — 402 bytes, 16.080000000 bits/sample, RMSE 1.71418414421e-07, max absolute error 2.96533105626e-07.

### `sine_noise.csv`

| Codec | Class | Configuration | Bytes | Bits/sample | Ratio | RMSE | Max abs error | Encode ms | Decode ms |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| raw | lossless | float64_le | 2400 | 64.000000000 | 1.000000000 | 0 | 0 | 0.004455000 | 0.006159000 |
| gzip | lossless | level_9_mtime_0 | 2353 | 62.746666667 | 1.019974501 | 0 | 0 | 0.097238000 | 0.024532000 |
| zstd | lossless | cli_default | 2345 | 62.533333333 | 1.023454158 | 0 | 0 | 1.899300000 | 1.358272000 |
| gorilla | lossless | values_only_f64_canonical_frame | 2480 | 66.133333333 | 0.967741935 | 0 | 0 | 0.479047000 | 0.858704000 |
| lasagna | lossy | fixed_mean_raw | 1534 | 40.906666667 | 1.564537158 | 0.0969860998839 | 0.180166046345 | 0.278471000 | 0.071716000 |
| lasagna | lossy | fixed_linear_raw | 1534 | 40.906666667 | 1.564537158 | 0.0892330664908 | 0.182828235942 | 0.300230000 | 0.077772000 |
| lasagna | lossy | fixed_rw_raw | 1534 | 40.906666667 | 1.564537158 | 0.142471494638 | 0.393202070273 | 0.291283000 | 0.073263000 |
| lasagna | lossy | fixed_mean_varint | 634 | 16.906666667 | 3.785488959 | 0.0969860998839 | 0.180166046345 | 0.486836000 | 0.160402000 |
| lasagna | lossy | fixed_linear_varint | 634 | 16.906666667 | 3.785488959 | 0.0892330664908 | 0.182828235942 | 0.438250000 | 0.165679000 |
| lasagna | lossy | fixed_rw_varint | 634 | 16.906666667 | 3.785488959 | 0.142471494638 | 0.393202070273 | 0.570773000 | 0.164180000 |
| lasagna | lossy | adaptive_mean_varint | 766 | 20.426666667 | 3.133159269 | 0.10373818548 | 0.192529869584 | 1.704410000 | 0.167434000 |
| lasagna | lossy | adaptive_linear_varint | 678 | 18.080000000 | 3.539823009 | 0.0995883116595 | 0.175326193145 | 2.623594000 | 0.172672000 |
| lasagna | lossy | adaptive_rw_varint | 546 | 14.560000000 | 4.395604396 | 0.148390708116 | 0.391169280432 | 8.650926000 | 0.180989000 |
| lasagna | lossy | adaptive_auto_varint | 678 | 18.080000000 | 3.539823009 | 0.0831633437504 | 0.18020470504 | 3.435763000 | 0.197682000 |

Observed size minima within the frozen comparison matrix:

- smallest lossless stream: `zstd` / `cli_default` — 2345 bytes, 62.533333333 bits/sample;
- smallest Lasagna stream: `adaptive_rw_varint` — 546 bytes, 14.560000000 bits/sample, RMSE 0.148390708116, max absolute error 0.391169280432.

### `flat_spike.csv`

| Codec | Class | Configuration | Bytes | Bits/sample | Ratio | RMSE | Max abs error | Encode ms | Decode ms |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| raw | lossless | float64_le | 2400 | 64.000000000 | 1.000000000 | 0 | 0 | 0.005055000 | 0.009485000 |
| gzip | lossless | level_9_mtime_0 | 2369 | 63.173333333 | 1.013085690 | 0 | 0 | 0.082228000 | 0.022851000 |
| zstd | lossless | cli_default | 2365 | 63.066666667 | 1.014799154 | 0 | 0 | 3.470374000 | 1.792265000 |
| gorilla | lossless | values_only_f64_canonical_frame | 2498 | 66.613333333 | 0.960768615 | 0 | 0 | 0.476427000 | 1.251502000 |
| lasagna | lossy | fixed_mean_raw | 1534 | 40.906666667 | 1.564537158 | 0.136843027419 | 0.657151703609 | 0.290163000 | 0.071808000 |
| lasagna | lossy | fixed_linear_raw | 1534 | 40.906666667 | 1.564537158 | 0.17831847573 | 0.643853647448 | 0.319553000 | 0.080317000 |
| lasagna | lossy | fixed_rw_raw | 1534 | 40.906666667 | 1.564537158 | 0.142346422706 | 0.662916043211 | 0.566488000 | 0.098436000 |
| lasagna | lossy | fixed_mean_varint | 634 | 16.906666667 | 3.785488959 | 0.136843027419 | 0.657151703609 | 0.870711000 | 0.318777000 |
| lasagna | lossy | fixed_linear_varint | 634 | 16.906666667 | 3.785488959 | 0.17831847573 | 0.643853647448 | 0.500536000 | 0.168773000 |
| lasagna | lossy | fixed_rw_varint | 634 | 16.906666667 | 3.785488959 | 0.142346422706 | 0.662916043211 | 0.882079000 | 0.356867000 |
| lasagna | lossy | adaptive_mean_varint | 590 | 15.733333333 | 4.067796610 | 0.192797098412 | 0.622249617981 | 5.266530000 | 0.165445000 |
| lasagna | lossy | adaptive_linear_varint | 590 | 15.733333333 | 4.067796610 | 0.105944802971 | 0.414831347198 | 6.136111000 | 0.166059000 |
| lasagna | lossy | adaptive_rw_varint | 590 | 15.733333333 | 4.067796610 | 0.173164941979 | 0.775953691776 | 5.637777000 | 0.288005000 |
| lasagna | lossy | adaptive_auto_varint | 590 | 15.733333333 | 4.067796610 | 0.0911111324764 | 0.587404639863 | 6.996265000 | 0.161372000 |

Observed size minima within the frozen comparison matrix:

- smallest lossless stream: `zstd` / `cli_default` — 2365 bytes, 63.066666667 bits/sample;
- smallest Lasagna stream: `adaptive_auto_varint` — 590 bytes, 15.733333333 bits/sample, RMSE 0.0911111324764, max absolute error 0.587404639863.

## Interpretation boundary

The benchmark answers a narrow empirical question: how the current Lasagna V2 implementation behaves, at its frozen configuration matrix, relative to selected lossless baselines on these three tracked example datasets.

It does **not** demonstrate that Lasagna is generally smaller, faster, or better than gzip, zstd, Gorilla, or other time-series codecs.

In particular:

- gzip, zstd and Gorilla reconstruct the canonical float64 input exactly;
- Lasagna trades reconstruction fidelity for rate according to its quantization and predictor configuration;
- timing results are host- and runtime-dependent and should be treated as observational rather than deterministic;
- the three repository examples are not a representative survey of real-world time-series distributions.

Broader claims require the heterogeneous real-world validation tracked separately by the project.

## Reproducibility gates

```text
PRIMARY_BENCHMARK_GATE=PASS
DETERMINISTIC_NON_TIMING_FIELDS=PASS
LOSSLESS_RECONSTRUCTION_GATE=PASS
LOSSY_ERROR_REPORTED_GATE=PASS
UNIVERSAL_SUPERIORITY_CLAIM=NO
```
