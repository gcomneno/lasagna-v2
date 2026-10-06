# Fuzzing qualification

Issue: #13 — `security: qualify decoder and residual codecs with fuzzing`

Status:

```text
HARNESS = IMPLEMENTED
QUALIFICATION RUN = PASS
PRODUCTION-READINESS GATE 5 = PASS
```

Qualification result:

```text
seed = 20261006
iterations per target = 25000
total target executions = 75000
unexpected crashes = 0
elapsed seconds = 5.948822
```

Canonical result artifact:

```text
docs/fuzzing-qualification-results.json
```

## Purpose

This qualification exercises Lasagna's untrusted-input boundaries with a
deterministic, replayable mutation harness.

The harness is intentionally dependency-free. It does not claim to replace
coverage-guided fuzzing forever; it provides a reproducible production
qualification campaign for the current Python implementation and frozen V1/V2
wire formats.

## Targets

Three independent targets are exercised:

```text
decoder
residual-varint
residual-zero-run
```

The decoder target invokes the public `decode_timeseries()` entry point and
therefore covers both V1 and V2 dispatch.

The canonical seed corpus contains:

```text
v1-raw.lsg2
v1-varint.lsg2
v2-raw.lsg2
v2-varint.lsg2
v2-zero-run.lsg2
```

## Structured decoder mutation surface

Every qualification run deterministically exercises named mutations covering:

```text
truncation
invalid magic
unknown version
context length
point count
segment count
invalid UTF-8 context
pathological context nesting
malformed context root/sampling shape
invalid context dt type/range conversion
segment start/end
predictor identifier
residual coding identifier
residual segment identifier
residual sample count
residual byte length
payload high-bit corruption
payload tail corruption
trailing data
```

Resource-bearing `n_points` and `n_segments` fields are not subjected to
unconstrained random in-policy values. Those values could intentionally request
multi-million-element allocations while adding little parser coverage.

Instead, resource fields are exercised with explicit boundary-violating
mutations governed by `docs/resource-limits.md`.

## Residual targets

The direct residual targets call:

```text
decode_int_list_varint()
decode_int_list_zero_run_varint()
```

Payloads are bounded to 256 bytes and requested decoded lengths to 256 samples.

The deterministic corpus includes:

```text
empty payload
single zero byte
truncated continuation
10-byte continuation chain
11-byte continuation chain
all-0xff 10-byte payload
known valid varints at width boundaries
```

Remaining cases are generated from a deterministic RNG stream.

## Expected rejection

Malformed fuzz inputs are allowed to raise:

```text
ValueError
```

Any other exception escaping a fuzz target is classified as an unexpected
crash and causes the campaign to fail.

Successful decoding of a mutation is not itself a failure: some byte changes
may still describe a structurally valid stream.

## Reproducibility

Canonical RNG seed:

```text
20261006
```

Qualification budget:

```text
25,000 cases per target
3 targets
minimum total = 75,000 target executions
```

The decoder additionally executes all named structured mutations before its
random campaign.

Run:

```text
PATH="$PWD/.venv/bin:$PATH" \
python tools/fuzz_qualification.py \
    --iterations 25000 \
    --seed 20261006 \
    --report docs/fuzzing-qualification-results.json
```

The generated JSON report records:

```text
seed
iterations per target
seed corpus filenames
accepted cases
rejected cases
crash count
total executed cases
elapsed runtime
crash artifact directory
```

Elapsed runtime is observational and is not expected to be bit-identical
between machines.

## Crash artifacts

Unexpected exceptions create:

```text
artifacts/fuzz-crashes/<identity>.bin
artifacts/fuzz-crashes/<identity>.json
```

The metadata records:

```text
target
iteration
seed
SHA-256
exception type
exception message
payload filename
```

A decoder artifact can be replayed with:

```text
python tools/fuzz_qualification.py \
    --replay artifacts/fuzz-crashes/<artifact>.bin \
    --target decoder
```

Residual targets use:

```text
--target residual-varint
--target residual-zero-run
```

Crash artifacts are investigation artifacts and are not automatically committed.
A minimized/relevant reproducer should become a regression test before a
finding is considered resolved.

## Gate rule

Gate 5 may move to `PASS` only after a qualification run at the frozen budget
completes with:

```text
TOTAL_CRASHES = 0
```

If the campaign finds a reproducible unexpected exception:

```text
Gate 5 remains REQUIRED or BLOCKER
the payload is retained
the defect is fixed or explicitly tracked
a regression test is added
the full qualification campaign is rerun
```

No frozen V2 wire semantic may be changed merely to make fuzzing pass.
