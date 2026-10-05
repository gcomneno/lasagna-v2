import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "benchmark_performance.py"

SPEC = importlib.util.spec_from_file_location(
    "benchmark_performance",
    MODULE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError(
        "Unable to load benchmark_performance"
    )

benchmark_performance = importlib.util.module_from_spec(
    SPEC
)

sys.modules[SPEC.name] = benchmark_performance
SPEC.loader.exec_module(benchmark_performance)


@pytest.mark.parametrize(
    "signal",
    [
        "trend",
        "sine_noise",
        "regime_spike",
    ],
)
def test_signal_generation_is_deterministic(
    signal: str,
) -> None:
    first = benchmark_performance.generate_signal(
        signal,
        256,
    )
    second = benchmark_performance.generate_signal(
        signal,
        256,
    )

    assert first == second
    assert len(first) == 256


def test_frozen_performance_matrix_shape() -> None:
    cases = benchmark_performance.load_matrix(
        ROOT
        / "docs"
        / "performance-benchmark-matrix.tsv"
    )

    assert len(cases) == 15
    assert len(set(cases)) == 15

    v2 = [
        case
        for case in cases
        if case.codec == "v2"
    ]
    v1 = [
        case
        for case in cases
        if case.codec == "v1"
    ]

    assert len(v2) == 9
    assert len(v1) == 6


def test_throughput_uses_float64_raw_size() -> None:
    samples_per_second, mib_per_second = (
        benchmark_performance.throughput(
            1_048_576,
            1000.0,
        )
    )

    assert samples_per_second == pytest.approx(
        1_048_576.0
    )
    assert mib_per_second == pytest.approx(
        8.0
    )
