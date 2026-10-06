# Large-file qualification

Issue: #15 — `performance: qualify large-file behavior and scaling limits`

Status:

```text
QUALIFICATION = PASS
PRODUCTION-READINESS GATE 8 = PASS
```

## Purpose

This qualification characterizes the practical scale of the current Lasagna
whole-file Python implementation.

It does not reinterpret the resource ceilings from
`docs/resource-limits.md` as performance guarantees.

The distinction is intentional:

```text
resource limit = accepted safety boundary
qualified scale = empirically exercised operational scale
```

## Frozen qualification matrix

The machine-readable matrix is:

```text
docs/large-file-qualification-matrix.tsv
```

The qualification combines:

```text
existing V2 trend measurements at 10k, 100k and 1M points
a dedicated V2 trend pilot at 2M points
a synthetic valid V2 stream with 100k one-point segments
configured-limit boundary checks
offset/integer arithmetic checks
```

The 2M pilot is intentionally the upper runtime/RSS qualification point.

A larger 4M or 10M adaptive encode was not required because the 2M pilot
already established materially large behavior while taking approximately
475 seconds wall time under the existing benchmark methodology.

## Environment

Qualification environment:

```text
Python 3.12.3
Linux 6.8.0-146-generic
x86_64
4 logical CPUs
Lasagna 0.3.0
```

## V2 point-count scaling

Frozen trend-series results:

| Points | Segments | Encoded bytes | Encode ms | Decode ms | Encode RSS KiB | Decode RSS KiB |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10,000 | 79 | 13,590 | 256.746 | 4.848 | 18,688 | 19,836 |
| 100,000 | 782 | 134,522 | 2,711.300 | 63.150 | 29,048 | 39,796 |
| 1,000,000 | 7,813 | 1,672,014 | 31,199.815 | 957.350 | 159,692 | 278,156 |
| 2,000,000 | 15,625 | 3,793,918 | 56,855.487 | 1,559.378 | 320,276 | 554,244 |

Adjacent observed scaling:

```text
10k -> 100k
points           10.000x
encode time      10.560x
decode time      13.026x
encode RSS        1.554x
decode RSS        2.006x

100k -> 1M
points           10.000x
encode time      11.507x
decode time      15.160x
encode RSS        5.498x
decode RSS        6.990x

1M -> 2M
points            2.000x
encode time       1.822x
decode time       1.629x
encode RSS        2.006x
decode RSS        1.993x
```

The 1M -> 2M interval is the most relevant large-scale observation.

It does not show an abrupt superlinear cliff:

```text
2.000x points
1.822x encode time
1.629x decode time
2.006x encode peak RSS
1.993x decode peak RSS
```

The absolute cost is nevertheless substantial.

At 2M points:

```text
encode time       ~56.9 s
decode time        ~1.56 s
encode peak RSS   ~313 MiB
decode peak RSS   ~541 MiB
encoded stream     3,793,918 bytes
```

This confirms that the current whole-file Python implementation is bounded
but memory-intensive at multi-million-sample scale.

## High-segment-count qualification

A dedicated valid V2 stream was generated directly with:

```text
100,000 points
100,000 segments
one point per segment
raw residuals
```

This intentionally avoids paying adaptive segmentation cost while exercising
the structures whose cost depends on segment count:

```text
V2 segment table
residual block headers
segment-id bookkeeping
preflight segment traversal
V2 L32 -> V1 widening
full decode
```

Observed result:

```text
encoded bytes       4,800,110
builder time         0.061753 s
decode time          0.584363 s
process peak RSS    86,136 KiB
```

The stream decoded successfully and produced exactly 100,000 zero-valued
samples.

This is materially larger in segment count than the ordinary performance
matrix, whose 2M trend case contains 15,625 segments.

## Configured-limit behavior

The qualification verifies the real production constants:

```text
MAX_POINTS       = 10,000,000
MAX_SEGMENTS     = 1,000,000
MAX_INPUT_BYTES  = 176,065,580
UINT32_MAX       = 4,294,967,295
```

Checks:

```text
MAX_POINTS exact                 PASS
MAX_POINTS + 1                   PASS — rejected with ValueError
MAX_SEGMENTS exact               PASS
MAX_SEGMENTS + 1                 PASS — rejected with ValueError
MAX_INPUT_BYTES exact            PASS
MAX_INPUT_BYTES + 1              PASS — rejected with ValueError
derived maximum input arithmetic PASS
```

The exact-limit checks validate policy arithmetic without allocating
10 million samples or 1 million Python segment objects.

This is deliberate: the resource contract defines acceptance boundaries,
while this issue measures practical execution separately.

## Integer and offset safety

The maximum derived external V1 input allowance is:

```text
176,065,580 bytes
```

This remains below:

```text
UINT32_MAX = 4,294,967,295
```

Internal cursor calculations use Python integers and therefore do not wrap at
32-bit boundaries.

The qualification also retains the resource-limit regression tests that inject
`UINT32_MAX` into segment and residual fields and require deterministic
`ValueError` rejection before large allocation.

No fixed-width offset overflow was observed or required by the supported
resource envelope.

## Practical interpretation

Production qualification does not mean that every value allowed by
`MAX_POINTS` or `MAX_SEGMENTS` is recommended for routine use.

For the current implementation:

```text
empirically qualified point scale = 2,000,000
empirically qualified segment scale = 100,000
configured point ceiling = 10,000,000
configured segment ceiling = 1,000,000
```

The configured ceilings are defensive acceptance limits.

The empirically qualified scales are the sizes for which this repository
contains reproducible runtime/RSS evidence.

Applications expecting materially larger workloads should benchmark their own
hardware and should not infer a memory guarantee from the logical resource
ceilings.

## Reproduction

The historical 10k/100k/1M measurements are stored in:

```text
docs/performance-benchmark-results.csv
```

The frozen 2M pilot is stored in:

```text
docs/large-file-qualification-pilot.csv
```

The dedicated qualification tool is:

```text
tools/qualify_large_file.py
```

Run:

```text
python tools/qualify_large_file.py \
    --pilot docs/large-file-qualification-pilot.csv \
    --segments 100000 \
    --output docs/large-file-qualification-results.json
```

Machine-readable output:

```text
docs/large-file-qualification-results.json
```

Regression tests:

```text
tests/test_large_file_qualification.py
tests/test_resource_limits.py
```

## Qualification conclusion

The current whole-file implementation has now been exercised at materially
larger scales than ordinary unit tests, including multi-million-point and
high-segment-count workloads.

Observed runtime and memory growth are characterized, configured limits fail
closed, and offset/integer safety is covered by both arithmetic qualification
and malformed-field regression tests.

Therefore:

```text
LARGE_N_POINTS_GATE=PASS
LARGE_N_SEGMENTS_GATE=PASS
LARGE_ENCODED_STREAM_GATE=PASS
PEAK_MEMORY_GATE=PASS
RUNTIME_SCALING_GATE=PASS
INTEGER_OFFSET_SAFETY_GATE=PASS
CONFIGURED_LIMIT_FAILURE_GATE=PASS
REPRODUCIBILITY_GATE=PASS

PRODUCTION_READINESS_GATE_8=PASS
```
