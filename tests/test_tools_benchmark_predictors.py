import importlib.util
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "benchmark_predictors.py"

SPEC = importlib.util.spec_from_file_location(
    "benchmark_predictors",
    MODULE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError(
        "Unable to load benchmark_predictors"
    )

benchmark_predictors = importlib.util.module_from_spec(
    SPEC
)

sys.modules[SPEC.name] = benchmark_predictors
SPEC.loader.exec_module(benchmark_predictors)


def candidate_specs():
    return {
        spec.name: spec
        for spec in benchmark_predictors.load_candidate_matrix(
            ROOT
            / "docs"
            / "predictor-candidate-matrix.tsv"
        )
    }


def test_frozen_candidate_matrix() -> None:
    specs = candidate_specs()

    assert set(specs) == {
        "mean",
        "linear",
        "random_walk",
        "median",
        "quadratic",
        "ar1",
        "lag24",
    }


def test_lag24_is_ineligible_for_short_segment() -> None:
    spec = candidate_specs()["lag24"]

    result = benchmark_predictors.evaluate_predictor(
        spec,
        [float(index) for index in range(24)],
    )

    assert not result.eligible


def test_lag24_reconstructs_periodic_signal_causally() -> None:
    spec = candidate_specs()["lag24"]

    values = [
        10.0
        + 2.0
        * math.sin(
            2.0
            * math.pi
            * index
            / 24.0
        )
        for index in range(128)
    ]

    result = benchmark_predictors.evaluate_predictor(
        spec,
        values,
    )

    assert result.eligible
    assert len(result.reconstructed) == len(values)
    assert result.rmse < 1e-12


def test_random_walk_decoder_is_reconstruction_causal() -> None:
    spec = candidate_specs()["random_walk"]

    values = [
        0.1 * index * index
        for index in range(64)
    ]

    result = benchmark_predictors.evaluate_predictor(
        spec,
        values,
    )

    assert result.eligible
    assert len(result.reconstructed) == len(values)
    assert result.projected_total_bytes > 0


def test_quadratic_fits_exact_quadratic_signal() -> None:
    spec = candidate_specs()["quadratic"]

    values = [
        1.0
        + 0.01 * index
        + 0.0001 * index * index
        for index in range(64)
    ]

    result = benchmark_predictors.evaluate_predictor(
        spec,
        values,
    )

    assert result.eligible
    assert not result.fallback
    assert result.rmse < 1e-12
