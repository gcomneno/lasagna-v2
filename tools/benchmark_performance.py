#!/usr/bin/env python3
"""Reproducible large-series performance benchmark for Lasagna 2."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import platform
import random
import resource
import statistics
import subprocess
import sys
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, TypeVar

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lasagna2.cli import read_lsg2_metadata_and_segments  # noqa: E402
from lasagna2.core import (  # noqa: E402
    TimeSeries,
    decode_timeseries,
    encode_timeseries_v1,
    encode_timeseries_v2,
)

T = TypeVar("T")

SEED = 20261005

FIELDNAMES = [
    "codec",
    "signal",
    "n_samples",
    "segment_count",
    "encoded_bytes",
    "encode_median_ms",
    "decode_median_ms",
    "encode_samples_per_second",
    "decode_samples_per_second",
    "encode_raw_mib_per_second",
    "decode_raw_mib_per_second",
    "encode_traced_peak_bytes",
    "decode_traced_peak_bytes",
    "encode_peak_rss_kib",
    "decode_peak_rss_kib",
]


@dataclass(frozen=True)
class MatrixCase:
    codec: str
    signal: str
    n_samples: int


def project_version() -> str:
    pyproject = ROOT / "pyproject.toml"

    for line in pyproject.read_text(encoding="utf-8").splitlines():
        if line.startswith("version = "):
            return line.split("=", 1)[1].strip().strip('"')

    raise ValueError("Project version not found")


def generate_signal(
    signal: str,
    n_samples: int,
    *,
    seed: int = SEED,
) -> list[float]:
    if n_samples < 1:
        raise ValueError("n_samples must be >= 1")

    if signal == "trend":
        return [10.0 + 0.005 * index for index in range(n_samples)]

    if signal == "sine_noise":
        rng = random.Random(seed)

        return [
            (
                10.0
                + 0.0005 * index
                + 4.0 * math.sin(2.0 * math.pi * index / 240.0)
                + rng.gauss(0.0, 0.15)
            )
            for index in range(n_samples)
        ]

    if signal == "regime_spike":
        values: list[float] = []

        for index in range(n_samples):
            phase = index % 4096

            if phase < 1024:
                value = 20.0
            elif phase < 2048:
                value = 20.0 + (phase - 1024) * 0.02
            elif phase < 3072:
                value = 40.48 + 5.0 * math.sin(2.0 * math.pi * (phase - 2048) / 128.0)
            else:
                value = 25.0

            if index % 997 == 0:
                value += 30.0

            values.append(value)

        return values

    raise ValueError(f"Unknown signal family: {signal}")


def make_timeseries(
    signal: str,
    n_samples: int,
) -> TimeSeries:
    return TimeSeries(
        values=generate_signal(
            signal,
            n_samples,
        ),
        dt=1.0,
        t0="1970-01-01T00:00:00Z",
        unit="benchmark",
    )


def encode_case(
    codec: str,
    ts: TimeSeries,
) -> bytes:
    common = dict(
        segment_length=64,
        predictor="auto",
        Q_MIN=1e-6,
        segment_mode="adaptive",
        min_segment_length=32,
        max_segment_length=128,
        mse_threshold=0.5,
        residual_coding="varint",
    )

    if codec == "v2":
        return encode_timeseries_v2(
            ts,
            C_Q=0.125,
            **common,
        )

    if codec == "v1":
        return encode_timeseries_v1(
            ts,
            C_Q=0.5,
            **common,
        )

    raise ValueError(f"Unknown codec: {codec}")


def median_call_ms(
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


def deterministic_encode_ms(
    operation: Callable[[], bytes],
    *,
    repetitions: int,
    warmup: int,
) -> tuple[bytes, float]:
    first: bytes | None = None
    elapsed_ns: list[int] = []

    for _ in range(warmup):
        operation()

    for _ in range(repetitions):
        start = time.perf_counter_ns()
        encoded = operation()
        end = time.perf_counter_ns()

        if first is None:
            first = encoded
        elif encoded != first:
            raise ValueError("Non-deterministic encoded output")

        elapsed_ns.append(end - start)

    if first is None:
        raise ValueError("No timed encode result produced")

    return (
        first,
        statistics.median(elapsed_ns) / 1_000_000.0,
    )


def load_matrix(
    path: Path,
) -> list[MatrixCase]:
    with path.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        rows = list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )

    cases = [
        MatrixCase(
            codec=row["codec"],
            signal=row["signal"],
            n_samples=int(row["n_samples"]),
        )
        for row in rows
    ]

    if not cases:
        raise ValueError("Benchmark matrix is empty")

    if len(cases) != len(set(cases)):
        raise ValueError("Benchmark matrix contains duplicates")

    return cases


def throughput(
    n_samples: int,
    elapsed_ms: float,
) -> tuple[float, float]:
    seconds = elapsed_ms / 1000.0

    if seconds <= 0.0:
        return math.inf, math.inf

    samples_per_second = n_samples / seconds

    raw_mib = n_samples * 8 / (1024.0 * 1024.0)

    return (
        samples_per_second,
        raw_mib / seconds,
    )


def run_memory_worker(
    *,
    operation: str,
    codec: str,
    signal: str,
    n_samples: int,
) -> dict[str, int]:
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--memory-worker",
        operation,
        "--codec",
        codec,
        "--signal",
        signal,
        "--n-samples",
        str(n_samples),
    ]

    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    if completed.returncode != 0:
        raise RuntimeError("Memory worker failed: " + completed.stderr.strip())

    payload = json.loads(completed.stdout.strip())

    return {
        "traced_peak_bytes": int(payload["traced_peak_bytes"]),
        "peak_rss_kib": int(payload["peak_rss_kib"]),
    }


def memory_worker(
    *,
    operation: str,
    codec: str,
    signal: str,
    n_samples: int,
) -> None:
    ts = make_timeseries(
        signal,
        n_samples,
    )

    if operation == "encode":
        tracemalloc.start()

        encoded = encode_case(
            codec,
            ts,
        )

        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Keep the result alive until after peak capture.
        if not encoded:
            raise ValueError("Encode produced empty output")

    elif operation == "decode":
        encoded = encode_case(
            codec,
            ts,
        )

        tracemalloc.start()

        decoded = decode_timeseries(encoded)

        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        if len(decoded.values) != n_samples:
            raise ValueError("Decode sample count mismatch")

    else:
        raise ValueError(f"Unknown memory operation: {operation}")

    peak_rss_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    print(
        json.dumps(
            {
                "traced_peak_bytes": peak,
                "peak_rss_kib": peak_rss_kib,
            },
            separators=(",", ":"),
        )
    )


def timing_worker(
    *,
    codec: str,
    signal: str,
    n_samples: int,
    repetitions: int,
    warmup: int,
) -> None:
    ts = make_timeseries(
        signal,
        n_samples,
    )

    encoded, encode_ms = deterministic_encode_ms(
        lambda: encode_case(
            codec,
            ts,
        ),
        repetitions=repetitions,
        warmup=warmup,
    )

    decoded, decode_ms = median_call_ms(
        lambda: decode_timeseries(encoded),
        repetitions=repetitions,
        warmup=warmup,
    )

    if len(decoded.values) != n_samples:
        raise ValueError("Decoded sample count mismatch")

    (
        _context,
        n_points,
        segments,
        _coding_type,
    ) = read_lsg2_metadata_and_segments(encoded)

    if n_points != n_samples:
        raise ValueError("Encoded sample count mismatch")

    print(
        json.dumps(
            {
                "segment_count": len(segments),
                "encoded_bytes": len(encoded),
                "encode_median_ms": encode_ms,
                "decode_median_ms": decode_ms,
            },
            separators=(",", ":"),
        )
    )


def run_timing_worker(
    *,
    codec: str,
    signal: str,
    n_samples: int,
    repetitions: int,
    warmup: int,
) -> dict[str, object]:
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--timing-worker",
        "--codec",
        codec,
        "--signal",
        signal,
        "--n-samples",
        str(n_samples),
        "--repetitions",
        str(repetitions),
        "--warmup",
        str(warmup),
    ]

    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    if completed.returncode != 0:
        raise RuntimeError("Timing worker failed: " + completed.stderr.strip())

    return json.loads(completed.stdout.strip())


def evaluate_case(
    case: MatrixCase,
    *,
    repetitions: int,
    warmup: int,
) -> dict[str, object]:
    timing = run_timing_worker(
        codec=case.codec,
        signal=case.signal,
        n_samples=case.n_samples,
        repetitions=repetitions,
        warmup=warmup,
    )

    encode_memory = run_memory_worker(
        operation="encode",
        codec=case.codec,
        signal=case.signal,
        n_samples=case.n_samples,
    )

    decode_memory = run_memory_worker(
        operation="decode",
        codec=case.codec,
        signal=case.signal,
        n_samples=case.n_samples,
    )

    encode_ms = float(timing["encode_median_ms"])
    decode_ms = float(timing["decode_median_ms"])

    (
        encode_samples_per_second,
        encode_raw_mib_per_second,
    ) = throughput(
        case.n_samples,
        encode_ms,
    )

    (
        decode_samples_per_second,
        decode_raw_mib_per_second,
    ) = throughput(
        case.n_samples,
        decode_ms,
    )

    return {
        "codec": case.codec,
        "signal": case.signal,
        "n_samples": case.n_samples,
        "segment_count": int(timing["segment_count"]),
        "encoded_bytes": int(timing["encoded_bytes"]),
        "encode_median_ms": encode_ms,
        "decode_median_ms": decode_ms,
        "encode_samples_per_second": (encode_samples_per_second),
        "decode_samples_per_second": (decode_samples_per_second),
        "encode_raw_mib_per_second": (encode_raw_mib_per_second),
        "decode_raw_mib_per_second": (decode_raw_mib_per_second),
        "encode_traced_peak_bytes": (encode_memory["traced_peak_bytes"]),
        "decode_traced_peak_bytes": (decode_memory["traced_peak_bytes"]),
        "encode_peak_rss_kib": (encode_memory["peak_rss_kib"]),
        "decode_peak_rss_kib": (decode_memory["peak_rss_kib"]),
    }


def environment_record() -> dict[str, object]:
    return {
        "python_version": (platform.python_version()),
        "lasagna_version": (project_version()),
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "logical_cpu_count": (os.cpu_count()),
        "seed": SEED,
    }


def write_results(
    path: Path,
    rows: list[dict[str, object]],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=FIELDNAMES,
        )
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--matrix",
        type=Path,
        default=Path("docs/performance-benchmark-matrix.tsv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/tmp/lasagna-v2-issue6-performance.csv"),
    )
    parser.add_argument(
        "--environment-output",
        type=Path,
        default=Path("/tmp/lasagna-v2-issue6-environment.json"),
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--timing-worker",
        action="store_true",
    )
    parser.add_argument(
        "--memory-worker",
        choices=[
            "encode",
            "decode",
        ],
    )
    parser.add_argument(
        "--codec",
        choices=[
            "v1",
            "v2",
        ],
    )
    parser.add_argument(
        "--signal",
        choices=[
            "trend",
            "sine_noise",
            "regime_spike",
        ],
    )
    parser.add_argument(
        "--n-samples",
        type=int,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.timing_worker:
        if args.codec is None or args.signal is None or args.n_samples is None:
            raise SystemExit("Timing worker requires codec, " "signal and n-samples")

        timing_worker(
            codec=args.codec,
            signal=args.signal,
            n_samples=args.n_samples,
            repetitions=args.repetitions,
            warmup=args.warmup,
        )
        return

    if args.memory_worker is not None:
        if args.codec is None or args.signal is None or args.n_samples is None:
            raise SystemExit("Memory worker requires codec, " "signal and n-samples")

        memory_worker(
            operation=args.memory_worker,
            codec=args.codec,
            signal=args.signal,
            n_samples=args.n_samples,
        )
        return

    cases = load_matrix(args.matrix)

    environment = environment_record()

    args.environment_output.write_text(
        json.dumps(
            environment,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "ENVIRONMENT="
        + json.dumps(
            environment,
            sort_keys=True,
        )
    )

    rows: list[dict[str, object]] = []

    for index, case in enumerate(
        cases,
        start=1,
    ):
        row = evaluate_case(
            case,
            repetitions=args.repetitions,
            warmup=args.warmup,
        )
        rows.append(row)

        print(
            f"CASE={index}/{len(cases)} "
            f"CODEC={case.codec} "
            f"SIGNAL={case.signal} "
            f"N={case.n_samples} "
            f"SEGMENTS={row['segment_count']} "
            f"ENCODE_MS={float(row['encode_median_ms']):.3f} "
            f"DECODE_MS={float(row['decode_median_ms']):.3f} "
            f"ENCODE_RSS_KIB={row['encode_peak_rss_kib']} "
            f"DECODE_RSS_KIB={row['decode_peak_rss_kib']}"
        )

    write_results(
        args.output,
        rows,
    )

    print(f"RESULT_ROWS={len(rows)}")
    print(f"OUTPUT={args.output}")
    print(f"ENVIRONMENT_OUTPUT={args.environment_output}")
    print("PERFORMANCE_BENCHMARK_GATE=PASS")


if __name__ == "__main__":
    main()
