#!/usr/bin/env python3
"""Synthetic sanity benchmark for the Lasagna v2 codec.

M1-A compares:

- canonical little-endian IEEE-754 float64 bytes;
- gzip over the same canonical bytes;
- zstd over the same canonical bytes;
- a frozen matrix of Lasagna v2 configurations.

This benchmark intentionally excludes timing. Performance measurements
belong to a separate protocol.

M1-A is a synthetic sanity benchmark and must not be interpreted as
evidence of general codec superiority.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import math
import struct
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from lasagna2.core import TimeSeries, decode_timeseries, encode_timeseries


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
    configuration: str
    n_samples: int
    raw_bytes: int
    encoded_bytes: int
    bits_per_sample: float
    compression_ratio: float
    rmse: float
    max_abs_error: float


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
    "configuration",
    "n_samples",
    "raw_bytes",
    "encoded_bytes",
    "bits_per_sample",
    "compression_ratio",
    "rmse",
    "max_abs_error",
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


def error_metrics(
    original: Sequence[float],
    reconstructed: Sequence[float],
) -> tuple[float, float]:
    if len(original) != len(reconstructed):
        raise ValueError(f"Length mismatch: {len(original)} != {len(reconstructed)}")

    if not original:
        return 0.0, 0.0

    squared_errors = [(a - b) ** 2 for a, b in zip(original, reconstructed)]
    absolute_errors = [abs(a - b) for a, b in zip(original, reconstructed)]

    rmse = math.sqrt(sum(squared_errors) / len(original))
    max_abs_error = max(absolute_errors)

    return rmse, max_abs_error


def make_result(
    *,
    dataset: str,
    codec: str,
    configuration: str,
    n_samples: int,
    raw_bytes: int,
    encoded_bytes: int,
    rmse: float,
    max_abs_error: float,
) -> BenchmarkResult:
    bits_per_sample = encoded_bytes * 8 / n_samples if n_samples else 0.0

    compression_ratio = raw_bytes / encoded_bytes if encoded_bytes else math.inf

    return BenchmarkResult(
        dataset=dataset,
        codec=codec,
        configuration=configuration,
        n_samples=n_samples,
        raw_bytes=raw_bytes,
        encoded_bytes=encoded_bytes,
        bits_per_sample=bits_per_sample,
        compression_ratio=compression_ratio,
        rmse=rmse,
        max_abs_error=max_abs_error,
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

        raise RuntimeError(f"zstd failed with status {completed.returncode}: {message}")

    return completed.stdout


def benchmark_dataset(
    dataset_path: Path,
    *,
    configs: Iterable[CodecConfig] = LASAGNA_CONFIGS,
) -> list[BenchmarkResult]:
    values = load_csv_values(dataset_path)
    raw = canonical_float64_bytes(values)

    n_samples = len(values)
    raw_bytes = len(raw)
    dataset = dataset_path.name

    results: list[BenchmarkResult] = []

    results.append(
        make_result(
            dataset=dataset,
            codec="raw",
            configuration="float64_le",
            n_samples=n_samples,
            raw_bytes=raw_bytes,
            encoded_bytes=raw_bytes,
            rmse=0.0,
            max_abs_error=0.0,
        )
    )

    gzip_bytes = gzip.compress(
        raw,
        compresslevel=9,
        mtime=0,
    )

    results.append(
        make_result(
            dataset=dataset,
            codec="gzip",
            configuration="level_9",
            n_samples=n_samples,
            raw_bytes=raw_bytes,
            encoded_bytes=len(gzip_bytes),
            rmse=0.0,
            max_abs_error=0.0,
        )
    )

    zstd_bytes = compress_zstd(raw)

    results.append(
        make_result(
            dataset=dataset,
            codec="zstd",
            configuration="cli_default",
            n_samples=n_samples,
            raw_bytes=raw_bytes,
            encoded_bytes=len(zstd_bytes),
            rmse=0.0,
            max_abs_error=0.0,
        )
    )

    ts = TimeSeries(
        values=list(values),
        dt=1.0,
        t0="1970-01-01T00:00:00Z",
        unit="benchmark",
    )

    for config in configs:
        encoded = encode_timeseries(
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

        decoded = decode_timeseries(encoded)

        rmse, max_abs_error = error_metrics(
            values,
            decoded.values,
        )

        results.append(
            make_result(
                dataset=dataset,
                codec="lasagna",
                configuration=config.name,
                n_samples=n_samples,
                raw_bytes=raw_bytes,
                encoded_bytes=len(encoded),
                rmse=rmse,
                max_abs_error=max_abs_error,
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
                "configuration": result.configuration,
                "n_samples": result.n_samples,
                "raw_bytes": result.raw_bytes,
                "encoded_bytes": result.encoded_bytes,
                "bits_per_sample": f"{result.bits_per_sample:.9f}",
                "compression_ratio": f"{result.compression_ratio:.9f}",
                "rmse": f"{result.rmse:.12g}",
                "max_abs_error": f"{result.max_abs_error:.12g}",
            }
        )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=("Run the Lasagna v2 M1-A synthetic sanity benchmark.")
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

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    results: list[BenchmarkResult] = []

    for dataset in args.datasets:
        results.extend(benchmark_dataset(dataset))

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
        write_results_csv(results, stream)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
