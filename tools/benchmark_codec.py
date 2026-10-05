#!/usr/bin/env python3
"""Reproducible external-codec benchmark for Lasagna 2.

The benchmark compares the same canonical little-endian IEEE-754 float64
sample stream using:

- raw float64 storage;
- gzip level 9;
- zstd CLI default compression;
- Gorilla values-only float64 compression with explicit canonical framing;
- a frozen matrix of Lasagna V2 configurations.

raw, gzip, zstd and Gorilla are lossless baselines.

Lasagna is a lossy rate-distortion codec and is therefore reported in a
separate comparison class even when a particular dataset happens to
reconstruct with zero measured error.

Timing values are median wall-clock measurements over a fixed number of
repetitions. Byte counts and reconstruction metrics are deterministic where
the underlying codec permits it; timing measurements are inherently subject
to runtime and host variation.

This benchmark is evidence for the explicitly tested datasets and
configurations only. It must not be interpreted as evidence of universal
codec superiority.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import importlib.metadata
import math
import platform
import statistics
import struct
import subprocess
import sys
import time
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence, TypeVar

import gorillacompression as gc

from lasagna2.core import TimeSeries, decode_timeseries, encode_timeseries


T = TypeVar("T")

GORILLA_MAGIC = b"GORILLA1"
GORILLA_FLOAT_FORMAT = b"f64\x00"
GORILLA_HEADER_STRUCT = struct.Struct("<8sQ4s")


@dataclass(frozen=True)
class CodecConfig:
    name: str
    segment_mode: str
    predictor: str
    residual_coding: str


@dataclass(frozen=True)
class BenchmarkResult:
    dataset: str
    codec: str
    comparison_class: str
    implementation: str
    implementation_version: str
    configuration: str
    n_samples: int
    raw_bytes: int
    encoded_bytes: int
    bits_per_sample: float
    compression_ratio: float
    rmse: float
    max_abs_error: float
    encode_time_ms: float
    decode_time_ms: float


LASAGNA_CONFIGS: tuple[CodecConfig, ...] = (
    CodecConfig("fixed_mean_raw", "fixed", "mean", "raw"),
    CodecConfig("fixed_linear_raw", "fixed", "linear", "raw"),
    CodecConfig("fixed_rw_raw", "fixed", "rw", "raw"),
    CodecConfig("fixed_mean_varint", "fixed", "mean", "varint"),
    CodecConfig("fixed_linear_varint", "fixed", "linear", "varint"),
    CodecConfig("fixed_rw_varint", "fixed", "rw", "varint"),
    CodecConfig("adaptive_mean_varint", "adaptive", "mean", "varint"),
    CodecConfig("adaptive_linear_varint", "adaptive", "linear", "varint"),
    CodecConfig("adaptive_rw_varint", "adaptive", "rw", "varint"),
    CodecConfig("adaptive_auto_varint", "adaptive", "auto", "varint"),
)

FIELDNAMES = (
    "dataset",
    "codec",
    "comparison_class",
    "implementation",
    "implementation_version",
    "configuration",
    "n_samples",
    "raw_bytes",
    "encoded_bytes",
    "bits_per_sample",
    "compression_ratio",
    "rmse",
    "max_abs_error",
    "encode_time_ms",
    "decode_time_ms",
)


def load_csv_values(path: Path) -> list[float]:
    """Read the first numeric column from a simple CSV file."""
    values: list[float] = []

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        try:
            values.append(float(line.split(",")[0]))
        except ValueError:
            continue

    if not values:
        raise ValueError(f"No numeric values found in {path}")

    return values


def canonical_float64_bytes(values: Sequence[float]) -> bytes:
    """Serialize values as contiguous little-endian IEEE-754 float64."""
    return struct.pack(f"<{len(values)}d", *values)


def decode_canonical_float64(data: bytes) -> list[float]:
    """Decode canonical contiguous little-endian IEEE-754 float64."""
    if len(data) % 8:
        raise ValueError("Canonical float64 payload length is not divisible by 8")

    return list(
        struct.unpack(
            f"<{len(data) // 8}d",
            data,
        )
    )


def error_metrics(
    original: Sequence[float],
    reconstructed: Sequence[float],
) -> tuple[float, float]:
    if len(original) != len(reconstructed):
        raise ValueError(
            f"Length mismatch: {len(original)} != {len(reconstructed)}"
        )

    if not original:
        return 0.0, 0.0

    squared_errors = [
        (a - b) ** 2
        for a, b in zip(original, reconstructed)
    ]
    absolute_errors = [
        abs(a - b)
        for a, b in zip(original, reconstructed)
    ]

    rmse = math.sqrt(
        sum(squared_errors) / len(original)
    )
    max_abs_error = max(absolute_errors)

    return rmse, max_abs_error


def _median_call_ms(
    operation: Callable[[], T],
    *,
    repetitions: int,
    warmup: int,
) -> tuple[T, float]:
    if repetitions < 1:
        raise ValueError("repetitions must be >= 1")

    if warmup < 0:
        raise ValueError("warmup must be >= 0")

    for _ in range(warmup):
        operation()

    values: list[T] = []
    elapsed_ns: list[int] = []

    for _ in range(repetitions):
        start = time.perf_counter_ns()
        value = operation()
        end = time.perf_counter_ns()

        values.append(value)
        elapsed_ns.append(end - start)

    return (
        values[-1],
        statistics.median(elapsed_ns) / 1_000_000.0,
    )


def _measure_deterministic_encode(
    operation: Callable[[], bytes],
    *,
    repetitions: int,
    warmup: int,
) -> tuple[bytes, float]:
    if repetitions < 1:
        raise ValueError("repetitions must be >= 1")

    for _ in range(warmup):
        operation()

    encoded_values: list[bytes] = []
    elapsed_ns: list[int] = []

    for _ in range(repetitions):
        start = time.perf_counter_ns()
        encoded = operation()
        end = time.perf_counter_ns()

        encoded_values.append(encoded)
        elapsed_ns.append(end - start)

    first = encoded_values[0]

    if any(encoded != first for encoded in encoded_values[1:]):
        raise ValueError("Codec produced non-deterministic encoded bytes")

    return (
        first,
        statistics.median(elapsed_ns) / 1_000_000.0,
    )


def make_result(
    *,
    dataset: str,
    codec: str,
    comparison_class: str,
    implementation: str,
    implementation_version: str,
    configuration: str,
    n_samples: int,
    raw_bytes: int,
    encoded_bytes: int,
    rmse: float,
    max_abs_error: float,
    encode_time_ms: float,
    decode_time_ms: float,
) -> BenchmarkResult:
    bits_per_sample = (
        encoded_bytes * 8 / n_samples
        if n_samples
        else 0.0
    )

    compression_ratio = (
        raw_bytes / encoded_bytes
        if encoded_bytes
        else math.inf
    )

    return BenchmarkResult(
        dataset=dataset,
        codec=codec,
        comparison_class=comparison_class,
        implementation=implementation,
        implementation_version=implementation_version,
        configuration=configuration,
        n_samples=n_samples,
        raw_bytes=raw_bytes,
        encoded_bytes=encoded_bytes,
        bits_per_sample=bits_per_sample,
        compression_ratio=compression_ratio,
        rmse=rmse,
        max_abs_error=max_abs_error,
        encode_time_ms=encode_time_ms,
        decode_time_ms=decode_time_ms,
    )


def compress_zstd(raw: bytes) -> bytes:
    """Compress bytes using the host zstd CLI."""
    completed = subprocess.run(
        ["zstd", "-q", "-c"],
        input=raw,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if completed.returncode != 0:
        message = completed.stderr.decode(
            "utf-8",
            errors="replace",
        ).strip()

        raise RuntimeError(
            "zstd compression failed with status "
            f"{completed.returncode}: {message}"
        )

    return completed.stdout


def decompress_zstd(encoded: bytes) -> bytes:
    """Decompress bytes using the host zstd CLI."""
    completed = subprocess.run(
        ["zstd", "-q", "-d", "-c"],
        input=encoded,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if completed.returncode != 0:
        message = completed.stderr.decode(
            "utf-8",
            errors="replace",
        ).strip()

        raise RuntimeError(
            "zstd decompression failed with status "
            f"{completed.returncode}: {message}"
        )

    return completed.stdout


def project_version() -> str:
    """Read the version declared by the repository under benchmark."""
    pyproject = (
        Path(__file__).resolve().parents[1]
        / "pyproject.toml"
    )

    for line in pyproject.read_text(
        encoding="utf-8"
    ).splitlines():
        stripped = line.strip()

        if stripped.startswith("version = "):
            return stripped.split("=", 1)[1].strip().strip('"')

    raise ValueError(
        "Project version not found in pyproject.toml"
    )


def zstd_version() -> str:
    completed = subprocess.run(
        ["zstd", "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        text=True,
    )

    return completed.stdout.strip()


def encode_gorilla(values: Sequence[float]) -> bytes:
    """Encode regular float64 samples with deterministic Gorilla framing."""
    result = gc.ValuesEncoder.encode_all(
        list(values),
        float_format="f64",
    )

    if result["float_format"] != "f64":
        raise ValueError(
            "Unexpected Gorilla float format "
            f"{result['float_format']!r}"
        )

    if result["nb_values"] != len(values):
        raise ValueError(
            "Unexpected Gorilla sample count "
            f"{result['nb_values']}"
        )

    return (
        GORILLA_HEADER_STRUCT.pack(
            GORILLA_MAGIC,
            result["nb_values"],
            GORILLA_FLOAT_FORMAT,
        )
        + result["encoded"]
    )


def decode_gorilla(encoded: bytes) -> list[float]:
    """Decode the canonical benchmark Gorilla frame."""
    if len(encoded) < GORILLA_HEADER_STRUCT.size:
        raise ValueError("Truncated Gorilla benchmark frame")

    magic, nb_values, float_format = (
        GORILLA_HEADER_STRUCT.unpack_from(
            encoded,
            0,
        )
    )

    if magic != GORILLA_MAGIC:
        raise ValueError("Invalid Gorilla benchmark magic")

    if float_format != GORILLA_FLOAT_FORMAT:
        raise ValueError(
            "Unsupported Gorilla benchmark float format"
        )

    payload = encoded[
        GORILLA_HEADER_STRUCT.size :
    ]

    decoded = gc.ValuesDecoder.decode_all(
        {
            "encoded": payload,
            "nb_values": nb_values,
            "float_format": "f64",
        }
    )

    if len(decoded) != nb_values:
        raise ValueError(
            "Decoded Gorilla sample count mismatch"
        )

    return list(decoded)


def _append_lossless_result(
    results: list[BenchmarkResult],
    *,
    dataset: str,
    codec: str,
    implementation: str,
    implementation_version: str,
    configuration: str,
    values: Sequence[float],
    raw_bytes: int,
    encode: Callable[[], bytes],
    decode: Callable[[bytes], Sequence[float]],
    repetitions: int,
    warmup: int,
) -> None:
    encoded, encode_time_ms = (
        _measure_deterministic_encode(
            encode,
            repetitions=repetitions,
            warmup=warmup,
        )
    )

    reconstructed, decode_time_ms = _median_call_ms(
        lambda: list(decode(encoded)),
        repetitions=repetitions,
        warmup=warmup,
    )

    rmse, max_abs_error = error_metrics(
        values,
        reconstructed,
    )

    if rmse != 0.0 or max_abs_error != 0.0:
        raise ValueError(
            f"Lossless codec {codec} did not reconstruct exactly"
        )

    results.append(
        make_result(
            dataset=dataset,
            codec=codec,
            comparison_class="lossless",
            implementation=implementation,
            implementation_version=implementation_version,
            configuration=configuration,
            n_samples=len(values),
            raw_bytes=raw_bytes,
            encoded_bytes=len(encoded),
            rmse=rmse,
            max_abs_error=max_abs_error,
            encode_time_ms=encode_time_ms,
            decode_time_ms=decode_time_ms,
        )
    )


def benchmark_dataset(
    dataset_path: Path,
    *,
    configs: Iterable[CodecConfig] = LASAGNA_CONFIGS,
    repetitions: int = 7,
    warmup: int = 1,
) -> list[BenchmarkResult]:
    values = load_csv_values(dataset_path)
    raw = canonical_float64_bytes(values)

    raw_bytes = len(raw)
    dataset = dataset_path.name

    results: list[BenchmarkResult] = []

    _append_lossless_result(
        results,
        dataset=dataset,
        codec="raw",
        implementation="python-struct",
        implementation_version=platform.python_version(),
        configuration="float64_le",
        values=values,
        raw_bytes=raw_bytes,
        encode=lambda: canonical_float64_bytes(values),
        decode=decode_canonical_float64,
        repetitions=repetitions,
        warmup=warmup,
    )

    _append_lossless_result(
        results,
        dataset=dataset,
        codec="gzip",
        implementation="python-gzip",
        implementation_version=zlib.ZLIB_RUNTIME_VERSION,
        configuration="level_9_mtime_0",
        values=values,
        raw_bytes=raw_bytes,
        encode=lambda: gzip.compress(
            raw,
            compresslevel=9,
            mtime=0,
        ),
        decode=lambda encoded: decode_canonical_float64(
            gzip.decompress(encoded)
        ),
        repetitions=repetitions,
        warmup=warmup,
    )

    zstd_impl_version = zstd_version()

    _append_lossless_result(
        results,
        dataset=dataset,
        codec="zstd",
        implementation="zstd-cli",
        implementation_version=zstd_impl_version,
        configuration="cli_default",
        values=values,
        raw_bytes=raw_bytes,
        encode=lambda: compress_zstd(raw),
        decode=lambda encoded: decode_canonical_float64(
            decompress_zstd(encoded)
        ),
        repetitions=repetitions,
        warmup=warmup,
    )

    _append_lossless_result(
        results,
        dataset=dataset,
        codec="gorilla",
        implementation="gorillacompression",
        implementation_version=importlib.metadata.version(
            "gorillacompression"
        ),
        configuration="values_only_f64_canonical_frame",
        values=values,
        raw_bytes=raw_bytes,
        encode=lambda: encode_gorilla(values),
        decode=decode_gorilla,
        repetitions=repetitions,
        warmup=warmup,
    )

    ts = TimeSeries(
        values=list(values),
        dt=1.0,
        t0="1970-01-01T00:00:00Z",
        unit="benchmark",
    )

    lasagna_version = project_version()

    for config in configs:
        def encode_lasagna(
            config: CodecConfig = config,
        ) -> bytes:
            return encode_timeseries(
                ts,
                segment_length=64,
                predictor=config.predictor,
                C_Q=0.5,
                Q_MIN=1e-6,
                segment_mode=config.segment_mode,
                min_segment_length=32,
                max_segment_length=128,
                mse_threshold=0.5,
                residual_coding=config.residual_coding,
            )

        encoded, encode_time_ms = (
            _measure_deterministic_encode(
                encode_lasagna,
                repetitions=repetitions,
                warmup=warmup,
            )
        )

        decoded, decode_time_ms = _median_call_ms(
            lambda: decode_timeseries(encoded),
            repetitions=repetitions,
            warmup=warmup,
        )

        rmse, max_abs_error = error_metrics(
            values,
            decoded.values,
        )

        results.append(
            make_result(
                dataset=dataset,
                codec="lasagna",
                comparison_class="lossy",
                implementation="lasagna-v2",
                implementation_version=lasagna_version,
                configuration=config.name,
                n_samples=len(values),
                raw_bytes=raw_bytes,
                encoded_bytes=len(encoded),
                rmse=rmse,
                max_abs_error=max_abs_error,
                encode_time_ms=encode_time_ms,
                decode_time_ms=decode_time_ms,
            )
        )

    return results


def write_results_csv(
    results: Sequence[BenchmarkResult],
    stream,
) -> None:
    writer = csv.DictWriter(
        stream,
        fieldnames=FIELDNAMES,
        lineterminator="\n",
    )

    writer.writeheader()

    for result in results:
        writer.writerow(
            {
                "dataset": result.dataset,
                "codec": result.codec,
                "comparison_class": result.comparison_class,
                "implementation": result.implementation,
                "implementation_version": result.implementation_version,
                "configuration": result.configuration,
                "n_samples": result.n_samples,
                "raw_bytes": result.raw_bytes,
                "encoded_bytes": result.encoded_bytes,
                "bits_per_sample": (
                    f"{result.bits_per_sample:.9f}"
                ),
                "compression_ratio": (
                    f"{result.compression_ratio:.9f}"
                ),
                "rmse": f"{result.rmse:.12g}",
                "max_abs_error": (
                    f"{result.max_abs_error:.12g}"
                ),
                "encode_time_ms": (
                    f"{result.encode_time_ms:.9f}"
                ),
                "decode_time_ms": (
                    f"{result.decode_time_ms:.9f}"
                ),
            }
        )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark Lasagna V2 against explicit "
            "lossless codec baselines."
        )
    )

    parser.add_argument(
        "datasets",
        nargs="+",
        type=Path,
        help="CSV datasets to benchmark",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="write CSV results to this file instead of stdout",
    )

    parser.add_argument(
        "--repetitions",
        type=int,
        default=7,
        help="timed repetitions per encode/decode operation",
    )

    parser.add_argument(
        "--warmup",
        type=int,
        default=1,
        help="warm-up calls before timed repetitions",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    results: list[BenchmarkResult] = []

    for dataset in args.datasets:
        results.extend(
            benchmark_dataset(
                dataset,
                repetitions=args.repetitions,
                warmup=args.warmup,
            )
        )

    if args.output is None:
        write_results_csv(results, sys.stdout)
        return 0

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with args.output.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as stream:
        write_results_csv(
            results,
            stream,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
