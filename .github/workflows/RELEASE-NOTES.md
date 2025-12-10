# v0.1.0 – Univariate MVP (Lasagna v2)

First public MVP of **Lasagna v2**, a brain-inspired compressor for univariate
time series.

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
