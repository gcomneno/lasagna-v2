from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "benchmark_codec.py"

SPEC = importlib.util.spec_from_file_location(
    "benchmark_codec",
    MODULE_PATH,
)

assert SPEC is not None
assert SPEC.loader is not None

benchmark_codec = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = benchmark_codec
SPEC.loader.exec_module(benchmark_codec)


def test_canonical_float64_bytes_size() -> None:
    values = [0.0, 1.0, -2.5, math.pi]

    raw = benchmark_codec.canonical_float64_bytes(values)

    assert len(raw) == len(values) * 8


def test_error_metrics_exact_roundtrip() -> None:
    values = [0.0, 1.0, -2.5, math.pi]

    rmse, max_abs_error = benchmark_codec.error_metrics(
        values,
        values,
    )

    assert rmse == 0.0
    assert max_abs_error == 0.0


def test_benchmark_trend_contains_expected_matrix() -> None:
    dataset = ROOT / "data" / "examples" / "trend.csv"

    results = benchmark_codec.benchmark_dataset(dataset)

    assert len(results) == 13

    assert results[0].codec == "raw"
    assert results[0].encoded_bytes == 200 * 8
    assert results[0].rmse == 0.0

    codecs = [result.codec for result in results]

    assert codecs.count("raw") == 1
    assert codecs.count("gzip") == 1
    assert codecs.count("zstd") == 1
    assert codecs.count("lasagna") == 10

    configurations = {
        result.configuration
        for result in results
        if result.codec == "lasagna"
    }

    assert configurations == {
        config.name
        for config in benchmark_codec.LASAGNA_CONFIGS
    }

    for result in results:
        assert result.n_samples == 200
        assert result.raw_bytes == 1600
        assert result.encoded_bytes > 0
        assert result.bits_per_sample > 0
        assert result.compression_ratio > 0
        assert result.rmse >= 0
        assert result.max_abs_error >= 0
