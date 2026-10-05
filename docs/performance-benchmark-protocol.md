# Large-series performance benchmark

Date: 2026-10-05

Status: FROZEN BEFORE BENCHMARK EXECUTION

## Purpose

This experiment characterizes computational cost of the current Lasagna
implementation on increasing time-series sizes.

It measures encode and decode separately and records scaling with both sample
count and emitted segment count.

This issue is diagnostic. No implementation optimization is performed before
the bottlenecks are measured and documented.

## Environment

The benchmark SHALL record at minimum:

- Python version;
- Lasagna project version;
- operating system / kernel;
- machine architecture;
- logical CPU count.

No absolute performance target is declared in advance.

## Signal families

Three deterministic synthetic structures are used.

### 1. Linear trend

A smooth deterministic linear trend.

Purpose:

- low structural complexity;
- highly predictable;
- low segmentation pressure.

### 2. Sine + deterministic noise

A sinusoidal signal with trend and pseudo-random Gaussian noise generated from
a frozen seed.

Purpose:

- continuously varying structure;
- moderate prediction difficulty;
- reproducible noisy residuals.

### 3. Regime / spike signal

A deterministic piecewise signal containing stable regions, ramps,
oscillation and periodic spikes.

Purpose:

- multiple local regimes;
- greater segmentation pressure;
- stress the relationship between sample count and segment count.

## Frozen seed

```text
seed = 20261005
```

## Input scales

V2 SHALL be measured at:

```text
10,000 samples
100,000 samples
1,000,000 samples
```

V1 is retained only as a regression/control path and SHALL be measured at:

```text
10,000 samples
100,000 samples
```

The 1,000,000-sample V1 point is deliberately excluded because V2 is the
current optimization target and issue #6 is not intended to become a legacy
performance campaign.

Expected encode/decode benchmark cases:

```text
V2:
3 signal families * 3 scales = 9 cases

V1:
3 signal families * 2 scales = 6 cases

total codec/series cases = 15
```

Encode and decode SHALL be reported independently for all 15 cases.

## Codec configurations

### Current V2

```text
format = V2
segment_mode = adaptive
predictor = auto
residual_coding = varint
segment_length = 64
min_segment_length = 32
max_segment_length = 128
mse_threshold = 0.5
C_Q = 0.125
Q_MIN = 1e-6
```

### Legacy V1 control

```text
format = V1
segment_mode = adaptive
predictor = auto
residual_coding = varint
segment_length = 64
min_segment_length = 32
max_segment_length = 128
mse_threshold = 0.5
C_Q = 0.5
Q_MIN = 1e-6
```

The V1 value is intentionally different because its implicit quantization
default is part of the frozen compatibility contract.

## Timing

Timing SHALL use:

```text
warm-up runs = 1
timed runs = 5
reported latency = median
clock = time.perf_counter_ns()
```

Encode and decode timing are measured independently.

Reported derived metrics SHALL include:

```text
samples / second
MiB of raw float64 input / second
```

Timing runs and memory runs SHALL be separate so memory instrumentation does
not contaminate latency measurements.

## Peak memory

Two memory measurements SHALL be reported.

### Python allocation peak

`tracemalloc` is started immediately before the measured encode or decode
operation.

Reported value:

```text
peak traced Python allocation bytes
```

### Process peak RSS

Each memory measurement runs in a fresh isolated Python worker.

The worker reports:

```text
resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
```

On Linux the value is interpreted as KiB.

RSS is reported as the peak process footprint of the isolated worker,
including the prepared input required by the operation. It is not described as
an incremental allocator-only measurement.

Encode and decode use separate workers.

## Segment count

The encoded V2/V1 stream SHALL be inspected and its emitted segment count
recorded.

This permits analysis of runtime and memory scaling against both:

```text
sample count
segment count
```

## Reproducibility

Signal generation is deterministic.

Encoded output for each benchmark case SHALL be deterministic.

The benchmark output SHALL record:

```text
signal family
codec version
sample count
segment count
encoded bytes
encode median ms
decode median ms
encode samples/s
decode samples/s
encode raw MiB/s
decode raw MiB/s
encode traced peak bytes
decode traced peak bytes
encode peak RSS KiB
decode peak RSS KiB
```

## Interpretation rules

The benchmark SHALL report raw per-case measurements.

Scaling claims must be based on observed ratios between adjacent input sizes.

A bottleneck may be identified only after measurement.

No optimization SHALL be implemented in issue #6 before the bottleneck report
is produced.

No universal throughput or memory target is declared without evidence.
