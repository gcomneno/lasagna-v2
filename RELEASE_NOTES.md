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
