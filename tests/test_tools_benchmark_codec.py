from __future__ import annotations

import importlib.util
import math
import struct
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


def test_gorilla_frame_is_deterministic_and_lossless() -> None:
    values = [
        0.0,
        1.0,
        -2.5,
        math.pi,
        math.pi,
    ]

    encoded_a = benchmark_codec.encode_gorilla(values)
    encoded_b = benchmark_codec.encode_gorilla(values)

    assert encoded_a == encoded_b

    (
        magic,
        nb_values,
        float_format,
    ) = benchmark_codec.GORILLA_HEADER_STRUCT.unpack_from(
        encoded_a,
        0,
    )

    assert magic == benchmark_codec.GORILLA_MAGIC
    assert nb_values == len(values)
    assert float_format == benchmark_codec.GORILLA_FLOAT_FORMAT

    decoded = benchmark_codec.decode_gorilla(encoded_a)

    assert len(decoded) == len(values)

    for original, restored in zip(
        values,
        decoded,
    ):
        assert struct.pack(
            ">d",
            original,
        ) == struct.pack(
            ">d",
            restored,
        )


def test_benchmark_trend_contains_expected_matrix() -> None:
    dataset = ROOT / "data" / "examples" / "trend.csv"

    results = benchmark_codec.benchmark_dataset(
        dataset,
        repetitions=1,
        warmup=0,
    )

    assert len(results) == 14

    assert results[0].codec == "raw"
    assert results[0].encoded_bytes == 200 * 8
    assert results[0].rmse == 0.0

    codecs = [result.codec for result in results]

    assert codecs.count("raw") == 1
    assert codecs.count("gzip") == 1
    assert codecs.count("zstd") == 1
    assert codecs.count("gorilla") == 1
    assert codecs.count("lasagna") == 10

    configurations = {
        result.configuration for result in results if result.codec == "lasagna"
    }

    assert configurations == {config.name for config in benchmark_codec.LASAGNA_CONFIGS}

    for result in results:
        assert result.n_samples == 200
        assert result.raw_bytes == 1600
        assert result.encoded_bytes > 0
        assert result.bits_per_sample > 0
        assert result.compression_ratio > 0
        assert result.implementation
        assert result.implementation_version
        assert result.encode_time_ms >= 0
        assert result.decode_time_ms >= 0

        if result.codec == "lasagna":
            assert result.comparison_class == "lossy"
            assert result.rmse >= 0
            assert result.max_abs_error >= 0
        else:
            assert result.comparison_class == "lossless"
            assert result.rmse == 0.0
            assert result.max_abs_error == 0.0


def test_project_version_comes_from_repository_metadata() -> None:
    assert benchmark_codec.project_version() == "0.3.0"
