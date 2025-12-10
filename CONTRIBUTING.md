# Contributing to Lasagna v2

Thanks for your interest in **Lasagna v2** – a security‑first, time‑series–oriented compressor.

This document explains how to set up your environment, run tests, and send good‑quality contributions.

---

## 1. Ground rules

- **No secrets in the repo.**
  - Never commit real API keys, tokens, or `.env` files.
  - Only commit example env files (e.g. `config.example.env`) with fake/sample values.
- **No private / sensitive datasets.**
  - The `data/examples/` directory is for small, synthetic, demonstrative datasets only.
  - Anything real, large, or sensitive should live *outside* the repo.
- **Tests must pass.**
  - Every PR should keep the test suite green.
- **Small, focused changes.**
  - Prefer multiple small PRs over a giant “kitchen sink” PR.

---

## 2. Project layout (quick tour)

- `lasagna2/` – library and CLI implementation.
- `tests/` – unit and CLI tests.
- `data/examples/` – small synthetic CSV/LSG2 examples used in docs/tests.
- `data/tmp/` – local scratch area for round‑trip experiments (ignored by Git).
- `docs/` – project manifesto and usage examples.
- `README.md` – overview and quick start.
- `RELEASE_NOTES_vX.Y.Z.md` – changes per release.

---

## 3. Getting started (local dev setup)

```bash
# 1. Clone the repo
git clone <REPO_URL> lasagna-v2
cd lasagna-v2

# 2. Create and activate a virtualenv (example with Python 3)
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate

# 3. Install in editable mode with dev deps
pip install -U pip
pip install -e . -r requirements-dev.txt
```

---

## 4. Running tests

Before pushing changes, run:

```bash
pytest
```

If the project uses additional checks (lint, type checking, etc.), they are usually listed in `requirements-dev.txt` and/or configured via `pre-commit` hooks.

Example (optional):

```bash
# Install hooks
pre-commit install

# Run all checks on the whole repo
pre-commit run --all-files
```

---

## 5. Coding style

- Follow the existing style in the codebase.
- Use **type hints** where they add clarity.
- Prefer small, pure functions over large, multipurpose ones.
- Keep public APIs stable and well documented:
  - If you change CLI flags or function signatures, update:
    - `README.md`
    - `docs/examples-trend-sine.md`
    - relevant tests in `tests/`.

If a linter/formatter is configured (e.g. `ruff`, `black`, `isort`), please run them before committing.

---

## 6. CLI contracts

The CLI is part of the public API. Changes to:

- sub‑commands (e.g. `encode`, `decode`, `info`),
- required flags (e.g. `--dt`, `--t0`, `--unit`),
- positional arguments (e.g. `input`, `output`),

**must** be reflected in:

- automated tests in `tests/test_cli_*.py`,
- the usage examples in the `README` and docs.

Whenever possible, add at least one test per new CLI behavior.

---

## 7. Working with data

- `data/examples/`:
  - Only small, synthetic, shareable datasets.
  - They can be tracked in Git and used in tests/docs.
- `data/tmp/`:
  - For local experiments only.
  - Tracked as a directory, but its contents are ignored (except for a `.gitkeep`).

**Please do not** commit:
- large binary artefacts (`*.csv`, `*.lsg2`) outside `data/examples/`,
- personal or proprietary datasets.

---

## 8. Submitting changes

1. **Create a branch:**

   ```bash
   git checkout -b feature/my-awesome-improvement
   ```

2. **Make your changes** and keep commits logically grouped.

3. **Run tests** and checks:

   ```bash
   pytest
   # plus any configured lint/format tools
   ```

4. **Update documentation** if behavior or public APIs have changed.

5. **Open a Pull Request**:
   - Describe the motivation (“why”), not only the implementation (“how”).
   - Reference any related issues.
   - List breaking changes, if any.

---

## 9. Security & responsible disclosure

If you believe you’ve found a **security issue** (e.g. unsafe decoding behavior, crashable input, suspicious dependency):

- **Do not** open a public issue with details right away.
- Please use a private, responsible disclosure channel (e.g. a security contact email, GitHub Security Advisory, or maintainer‑preferred channel).
- Provide:
  - a minimal reproducible example,
  - the impact (e.g. denial‑of‑service, arbitrary code execution),
  - the affected version(s).

We’ll work with you to verify and fix the issue, and coordinate disclosure if needed.

---

## 10. Questions & ideas

If you are unsure whether your idea fits the project:

- open a small “proposal” issue,
- or start a draft pull request with a short explanation.

Discussion early in the process usually saves time and leads to a better design.

Thanks again for helping to improve **Lasagna v2**!
