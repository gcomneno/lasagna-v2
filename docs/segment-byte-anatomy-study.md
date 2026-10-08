# Segment Byte Anatomy Study

## Status

EXECUTED

## Scope

Accounting-only projection over the frozen #24 result matrix.

No codec bytes were re-encoded.

No V2 wire behavior, predictor semantics, residual payload, segment boundary,
or distortion value was changed.

## Frozen candidate

Projected logical per-segment cost:

```text
mean        17 bytes
linear      21 bytes
random-walk 17 bytes
```

Current V2 fixed cost:

```text
44 bytes / segment
```

## Population

```text
total rows: 385
external A4 rows: 56
```

## Frozen decision gates

```text
criterion 1
median row-level per-segment fixed-overhead reduction
observed = 0.522727272727
threshold >= 0.50
pass = True

criterion 2
external A4 median projected total encoded-byte reduction
observed = 0.318375543960
threshold >= 0.15
pass = True

criterion 3
external A4 median structural-fraction decrease
observed = 0.196349076636
threshold >= 0.10
pass = True
```

## External A4 structural economics

```text
median current structural fraction
0.579496484464

median projected structural fraction
0.374875995938

median total encoded-byte reduction
0.318375543960
```

## Decision

```text
PASS
```

A PASS means only that the logical compact representation is economically
promising enough to justify a separate wire-layout experiment.

It does not modify or replace V2.
