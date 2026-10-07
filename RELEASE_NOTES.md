# Lasagna 2 — v0.3.0 (2026-10-07)

This release makes the frozen V2 wire format the default encoding path while
retaining explicit V1 encoding and full V1/V2 decode compatibility.

## Highlights

- `encode_timeseries()` now emits V2 by default.
- CLI `lasagna2 encode` now defaults to wire format V2.
- New public `encode_timeseries_v1()` API for explicit legacy V1 output.
- Existing public `encode_timeseries_v2()` remains available.
- CLI `--format-version 1` remains available for explicit legacy V1 output.
- `decode_timeseries()` continues to auto-detect and decode both V1 and V2.
- Existing V1 artifacts remain readable and the frozen V1 reference corpus
  remains the compatibility baseline.
- V1 is now compatibility-only; new encoder development targets V2.


## Numeric-domain hardening

Production encoders now reject unsupported numeric inputs explicitly instead of
relying on incidental Python or `struct` failures.

The supported encoder domain requires finite samples, finite positive `dt`,
finite `C_Q >= 0`, finite `Q_MIN > 0`, finite
`mse_threshold >= 0` and signed-int32 quantized residuals.

Out-of-range residuals are rejected consistently for raw, varint, zero-run and
automatic residual coding, including V2 residuals recomputed after binary32
metadata rounding.

These changes narrow previously accidental encoder acceptance in order to
prevent silent corruption and normalize numeric-domain failures to
`ValueError`.

No wire-format change is introduced. Existing V1/V2 artifacts retain their
documented decode compatibility, and historical V1 decoder behavior is
unchanged.

## Compatibility note

This is a behavioral change for callers that previously relied on the default
encoder producing V1 bytes.

In v0.3.0:

```text
encode_timeseries()    -> V2
encode_timeseries_v2() -> V2
encode_timeseries_v1() -> V1
```

Likewise, CLI encoding without `--format-version` now produces V2.

Callers requiring byte-compatible V1 output must use
`encode_timeseries_v1()` or `--format-version 1`.

Package version `0.3.0` and wire-format version `2` are separate version
domains. Existing V1 files remain supported by the decoder.

## Wire compatibility declaration

```text
DECODE:
    V1, V2

ENCODE DEFAULT:
    V2

ENCODE EXPLICIT:
    V1, V2

DEPRECATED:
    none
```

The V2 default transition follows the frozen-layout validation completed in
v0.2.2 and the subsequent independent road test confirming deterministic V2
encoding, V1/V2 decode compatibility, and materially smaller V2 output without
a meaningful reconstruction-quality change.

Lasagna 2 is production-qualified for the documented univariate whole-file
baseline. The qualification does not claim universal codec superiority or
support outside the documented operational boundaries.

---

# Lasagna 2 — v0.2.2 (2026-10-03)

This release completes the current V2 physical-layout validation cycle
without changing protocol revision 2.1.

## Highlights

- Frozen V2 segment layout: `L32`, `<IIIfffff>`, 32 bytes per segment.
- V1 remains the default encoder for compatibility.
- Explicit V2 encoding through `--format-version 2`.
- Public `encode_timeseries_v2()` Python API.
- V1/V2 auto-detection in decode and `info`.
- Unsupported wire versions fail closed.
- Canonical V1 references reproduced byte-for-byte: `1575/1575`.
- V2 deterministic double-encode check: `1575/1575`.
- 42 tests passing at empirical-validation close.

## Canonical V1 vs V2 result

Controlled synthetic corpus:

- 1,575 cases
- 806,400 samples
- 11,700 segments

Measured physical size:

- V1: 1,875,150 bytes
- V2: 1,500,750 bytes
- saving: 374,400 bytes
- reduction: 19.966402688%
- rate: 18.602678571 → 14.888392857 bits/sample

The residual payload remained exactly byte-neutral:

- V1 residual payload: 806,400 bytes
- V2 residual payload: 806,400 bytes
- delta: 0 bytes

The entire observed saving is therefore accounted for by the 64-byte → 32-byte
segment metadata reduction.

Full evidence:
[`docs/v2-empirical-validation.md`](docs/v2-empirical-validation.md).

## Interpretation

This is a V2-vs-V1 result on the project's frozen canonical corpus.

It is not a claim that Lasagna universally outperforms general-purpose or
domain-specific compressors.

The project remains experimental research software.

---

# Lasagna v2 – v0.1.0
## v0.1.0 – Univariate MVP (Lasagna v2)
First public MVP of **Lasagna v2**, a brain-inspired compressor for univariate
time series.

# Lasagna v2 – v0.1.1
## Bug fix
- Sistemato il comando `decode` della CLI: ora il CSV ricostruito include l’header `# value`
  e il round-trip `trend.csv -> encode -> decode` mantiene il numero di campioni.
- Aggiunto test end-to-end CLI su `data/examples/trend.csv` per evitare regressioni.
- Aggiornato `.gitignore`, `requirements-dev.txt` (dipendenza `pandas`) e aggiunto `CONTRIBUTING.md`.

## Highlights
- Univariate `TimeSeries` with metadata (`dt`, `t0`, `unit`).
- Fixed and adaptive segmentation, with MSE-based segment growth.
- Per-segment predictors:
  - `mean`, `linear`, `rw` (random-walk),
  - `auto` model selection (post-decode MSE).
- Residual coding:
  - raw int32,
  - ZigZag + varint.
- Segment patterns & salience:
  - `patt ∈ {flat, trend, oscillation, noisy}`,
  - `sal ∈ {0, 1, 2}`.
- Binary `.lsg2` format with header + segment table + residual blocks.
- Python package (`lasagna2`) + CLI:
  - `lasagna2 encode / info / decode`.
- Test suite and hardened CI:
  - pre-commit (black, ruff, detect-secrets),
  - pytest roundtrips + malformed input tests,
  - CodeQL, dependency-review, pip-audit, OpenSSF Scorecard.

## Status
Experimental **MVP**:
- format and API may change,
- currently focused on univariate time series and research/prototyping use-cases.
