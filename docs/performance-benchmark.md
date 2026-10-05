# Large-series performance characterization

Date: 2026-10-05

Status: executed benchmark

## Scope

Issue #6 characterizes current Lasagna encode/decode throughput, scaling and
memory behavior before any performance optimization.

The benchmark follows the frozen protocol in:

```text
docs/performance-benchmark-protocol.md
docs/performance-benchmark-matrix.tsv
```

The raw measurements are preserved in:

```text
docs/performance-benchmark-results.csv
docs/performance-benchmark-environment.json
```

## Environment

The recorded environment was:

```text
Lasagna = 0.3.0
Python = 3.12.3
OS = Linux 6.8.0-146-generic
architecture = x86_64
logical CPUs = 4
seed = 20261005
```

Timing and memory measurements are intentionally separate.

Peak RSS measurements use fresh isolated Python workers for every measured
operation. This avoids carrying a previous process high-water mark into later
cases.

## V2 scaling

### Trend

| Samples | Segments | Encode ms | Decode ms | Encode RSS KiB | Decode RSS KiB |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 10,000 | 79 | 256.746 | 4.848 | 18,688 | 19,836 |
| 100,000 | 782 | 2,711.300 | 63.150 | 29,048 | 39,796 |
| 1,000,000 | 7,813 | 31,199.815 | 957.350 | 159,692 | 278,156 |

Adjacent scaling:

```text
10k -> 100k:
samples   x10.00
segments  x9.90
encode    x10.56
decode    x13.03

100k -> 1M:
samples   x10.00
segments  x9.99
encode    x11.51
decode    x15.16
```

### Sine + noise

| Samples | Segments | Encode ms | Decode ms | Encode RSS KiB | Decode RSS KiB |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 10,000 | 84 | 254.837 | 5.305 | 19,456 | 20,352 |
| 100,000 | 834 | 2,880.134 | 61.834 | 35,396 | 44,580 |
| 1,000,000 | 8,334 | 31,099.646 | 669.742 | 176,860 | 262,124 |

Adjacent scaling:

```text
10k -> 100k:
samples   x10.00
segments  x9.93
encode    x11.30
decode    x11.66

100k -> 1M:
samples   x10.00
segments  x9.99
encode    x10.80
decode    x10.83
```

### Regime / spike

| Samples | Segments | Encode ms | Decode ms | Encode RSS KiB | Decode RSS KiB |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 10,000 | 108 | 208.053 | 4.989 | 18,944 | 19,968 |
| 100,000 | 1,119 | 2,258.542 | 55.954 | 28,372 | 38,132 |
| 1,000,000 | 11,218 | 30,986.168 | 597.927 | 120,460 | 230,884 |

Adjacent scaling:

```text
10k -> 100k:
samples   x10.00
segments  x10.36
encode    x10.86
decode    x11.21

100k -> 1M:
samples   x10.00
segments  x10.03
encode    x13.72
decode    x10.69
```

## Throughput interpretation

At one million samples, V2 encode latency converges near 31 seconds across all
three signal structures.

This corresponds to roughly 32 thousand samples per second on the recorded
machine.

Decode remains substantially faster, between approximately 0.60 and 0.96
seconds for one million samples.

The measurements are consistent with approximately linear scaling in sample
count with measurable overhead growth at larger inputs. They do not show
quadratic scaling over the tested range.

Segment count is not by itself the dominant predictor of encode latency.

At one million samples:

```text
trend:
7,813 segments
31.20 s encode

regime_spike:
11,218 segments
30.99 s encode
```

The regime/spike signal emits about 44% more segments while encode latency is
essentially unchanged.

This distinguishes wire/metadata cost from computational cost: issue #5 showed
that segment metadata is important for encoded size, while issue #6 shows that
segment count alone does not explain encode CPU cost.

## Memory behavior

V2 peak RSS at one million samples was:

```text
encode:
120,460 .. 176,860 KiB

decode:
230,884 .. 278,156 KiB
```

Peak traced Python allocations were:

```text
encode:
34,737,365 .. 44,549,762 bytes

decode:
51,613,346 .. 60,773,471 bytes
```

Memory therefore grows materially with sample count.

Decode has a substantially larger peak process footprint than encode in the
one-million-sample cases even though decode latency is much lower.

The present evidence establishes the memory-growth behavior but does not
attribute all RSS growth to one specific function or allocation site.

A future memory-optimization issue should identify retained and temporary
per-sample structures before changing implementation.

## V1 control comparison

V1 was retained as a control at 10k and 100k samples.

At 100k samples:

```text
trend:
V2 encode 2711 ms
V1 encode 2840 ms

sine_noise:
V2 encode 2880 ms
V1 encode 3465 ms

regime_spike:
V2 encode 2259 ms
V1 encode 2664 ms
```

V2 encode is not slower than V1 in these measured 100k cases and is
substantially faster for the sine/noise and regime/spike signals.

Decode results are mixed and do not support a universal V2 decode-performance
advantage.

The V1 comparison is diagnostic only. V2 remains the optimization target.

## CPU bottleneck profile

A targeted `cProfile` inspection was performed on V2 at 100,000 samples using
the trend and regime/spike signals.

Profiler timing is used only to identify relative hotspots. It is not used as
the benchmark latency measurement because profiler instrumentation changes
absolute execution time.

### Encode

Trend profile:

```text
encode_timeseries_v2       7.361 s cumulative
_build_encoding_model      7.160 s
segment_series_adaptive    6.695 s
compute_stats              4.013 s
builtins.sum               5.902 s cumulative
```

Regime/spike profile:

```text
encode_timeseries_v2       5.213 s cumulative
_build_encoding_model      5.034 s
segment_series_adaptive    4.375 s
compute_stats              2.660 s
builtins.sum               4.036 s cumulative
```

The dominant measured encode bottleneck is therefore adaptive segmentation,
not V2 wire serialization.

`segment_series_adaptive()` repeatedly evaluates candidate windows and invokes
`compute_stats()`, producing millions of Python-level generator/sum operations.

Varint encoding is comparatively small in the encode profile.

This is the primary CPU optimization target identified by issue #6.

### Decode

Trend profile:

```text
_decode_timeseries_v2        0.190 s cumulative
legacy decode core           0.186 s
decode_int_list_varint       0.164 s
_decode_varint               0.056 s
```

Regime/spike profile:

```text
_decode_timeseries_v2        0.143 s cumulative
legacy decode core           0.137 s
decode_int_list_varint       0.116 s
_decode_varint               0.038 s
```

The measured decode CPU hotspot is residual varint decoding.

Decode remains much faster than encode, so this is a secondary CPU target
relative to adaptive segmentation.

## Bottleneck conclusions

The benchmark identifies three distinct concerns:

```text
ENCODE CPU
primary hotspot:
adaptive segmentation
    -> repeated compute_stats
    -> repeated Python sums / generator expressions

DECODE CPU
primary hotspot:
varint residual decoding

MEMORY
large-input peak footprint
especially decode
allocation-site attribution still required
```

No optimization was implemented as part of this study.

## Conclusions

The current implementation scales approximately with sample count over the
tested range and does not exhibit evidence of quadratic runtime growth.

However:

- V2 encode throughput is low for million-sample workloads;
- adaptive segmentation dominates encode CPU time;
- segment count alone does not explain runtime;
- decode is much faster but varint decoding dominates its CPU profile;
- both encode and decode have substantial large-input memory footprints;
- decode peak RSS exceeds encode peak RSS in all tested one-million-sample
  cases.

These observations establish evidence-backed optimization targets without
declaring an arbitrary performance target.

## Acceptance gates

```text
MULTIPLE_INPUT_SCALES_GATE=PASS
ENCODE_DECODE_SEPARATION_GATE=PASS
PEAK_MEMORY_GATE=PASS
ENVIRONMENT_RECORD_GATE=PASS
REPRODUCIBILITY_GATE=PASS
SAMPLE_SCALING_GATE=PASS
SEGMENT_SCALING_GATE=PASS
BOTTLENECK_IDENTIFICATION_GATE=PASS
NO_PREMATURE_OPTIMIZATION_GATE=PASS
NO_UNSUPPORTED_PERFORMANCE_TARGET_GATE=PASS
```
