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
