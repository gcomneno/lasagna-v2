#!/usr/bin/env python3
"""Shadow predictor-candidate tournament for Lasagna 2 issue #7."""

from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"

for import_path in (
    ROOT,
    TOOLS,
):
    value = str(import_path)

    if value not in sys.path:
        sys.path.insert(0, value)

from lasagna2 import core  # noqa: E402

from benchmark_codec import (  # noqa: E402
    error_metrics,
    load_csv_values,
)


C_Q = 0.125
Q_MIN = 1e-6
COMMON_METADATA_BYTES = 16
RESIDUAL_BLOCK_HEADER_BYTES = 12

DATASETS = (
    ("internal", Path("data/examples/trend.csv")),
    ("internal", Path("data/examples/sine_noise.csv")),
    ("internal", Path("data/examples/flat_spike.csv")),
    ("real-world", Path("data/real-world/canonical/appliances-energy.csv")),
    ("real-world", Path("data/real-world/canonical/metro-traffic.csv")),
    ("real-world", Path("data/real-world/canonical/beijing-pm25.csv")),
)

RESULT_FIELDS = [
    "dataset",
    "evidence_group",
    "predictor",
    "candidate_class",
    "n_samples",
    "segment_count",
    "eligible_segment_count",
    "fallback_segment_count",
    "projected_metadata_bytes",
    "residual_payload_bytes",
    "projected_total_bytes",
    "bits_per_sample",
    "rmse",
    "max_abs_error",
    "fit_time_ms",
    "decode_simulation_time_ms",
]

WINNER_FIELDS = [
    "dataset",
    "evidence_group",
    "segment_index",
    "start_idx",
    "end_idx",
    "segment_length",
    "mse_winner",
    "mse_winner_rmse",
    "byte_winner",
    "byte_winner_projected_bytes",
]


@dataclass(frozen=True)
class CandidateSpec:
    name: str
    candidate_class: str
    parameter_payload_bytes: int
    recurrence: str
    seed_history_values: int


@dataclass
class SegmentEvaluation:
    predictor: str
    eligible: bool
    fallback: bool
    parameter_payload_bytes: int
    residual_payload_bytes: int
    projected_total_bytes: int
    reconstructed: list[float]
    rmse: float
    max_abs_error: float
    fit_time_ms: float
    decode_time_ms: float


def load_candidate_matrix(
    path: Path,
) -> list[CandidateSpec]:
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

    specs = [
        CandidateSpec(
            name=row["predictor"],
            candidate_class=row["candidate_class"],
            parameter_payload_bytes=int(row["parameter_payload_bytes"]),
            recurrence=row["recurrence"],
            seed_history_values=int(row["seed_history_values"]),
        )
        for row in rows
    ]

    if not specs:
        raise ValueError("Predictor candidate matrix is empty")

    if len(specs) != len({spec.name for spec in specs}):
        raise ValueError("Duplicate predictor candidate")

    return specs


def solve_3x3(
    matrix: list[list[float]],
    vector: list[float],
) -> tuple[float, float, float] | None:
    a = [
        row[:] + [rhs]
        for row, rhs in zip(
            matrix,
            vector,
        )
    ]

    n = 3

    for col in range(n):
        pivot = max(
            range(col, n),
            key=lambda row: abs(a[row][col]),
        )

        if abs(a[pivot][col]) < 1e-12:
            return None

        if pivot != col:
            a[col], a[pivot] = (
                a[pivot],
                a[col],
            )

        divisor = a[col][col]

        for j in range(col, n + 1):
            a[col][j] /= divisor

        for row in range(n):
            if row == col:
                continue

            factor = a[row][col]

            for j in range(col, n + 1):
                a[row][j] -= factor * a[col][j]

    return (
        a[0][3],
        a[1][3],
        a[2][3],
    )


def fit_quadratic(
    values: list[float],
) -> tuple[
    tuple[float, float, float],
    bool,
]:
    n = len(values)

    if n < 3:
        mean, slope, intercept, _ = core.compute_stats(values)
        return (
            (
                intercept,
                slope,
                0.0,
            ),
            True,
        )

    sx = sum(range(n))
    sx2 = sum(i * i for i in range(n))
    sx3 = sum(i * i * i for i in range(n))
    sx4 = sum(i * i * i * i for i in range(n))

    sy = sum(values)
    sxy = sum(i * value for i, value in enumerate(values))
    sx2y = sum(i * i * value for i, value in enumerate(values))

    solution = solve_3x3(
        [
            [float(n), float(sx), float(sx2)],
            [float(sx), float(sx2), float(sx3)],
            [float(sx2), float(sx3), float(sx4)],
        ],
        [
            sy,
            sxy,
            sx2y,
        ],
    )

    if solution is not None:
        return solution, False

    _mean, slope, intercept, _ = core.compute_stats(values)

    return (
        (
            intercept,
            slope,
            0.0,
        ),
        True,
    )


def fit_ar1(
    values: list[float],
) -> tuple[
    tuple[float, float, float],
    bool,
]:
    seed = values[0]

    if len(values) < 2:
        return (
            (0.0, 1.0, seed),
            True,
        )

    previous = values[:-1]
    current = values[1:]

    mean_x = sum(previous) / len(previous)
    mean_y = sum(current) / len(current)

    variance_x = sum((value - mean_x) ** 2 for value in previous)

    if variance_x <= 1e-18:
        return (
            (0.0, 1.0, seed),
            True,
        )

    covariance = sum(
        (x - mean_x) * (y - mean_y)
        for x, y in zip(
            previous,
            current,
        )
    )

    phi = covariance / variance_x
    intercept = mean_y - phi * mean_x

    if not (math.isfinite(phi) and math.isfinite(intercept)):
        return (
            (0.0, 1.0, seed),
            True,
        )

    return (
        (
            intercept,
            phi,
            seed,
        ),
        False,
    )


def quantize(
    residuals: list[float],
) -> tuple[list[int], float]:
    return core.quantize_residuals(
        residuals,
        C_Q=C_Q,
        Q_MIN=Q_MIN,
    )


def payload_size(
    quantized: list[int],
) -> int:
    return len(core.encode_int_list_varint(quantized))


def evaluate_nonrecurrent(
    values: list[float],
    predictions: list[float],
    *,
    predictor: str,
    parameter_payload_bytes: int,
    fallback: bool = False,
) -> SegmentEvaluation:
    residuals = [
        value - prediction
        for value, prediction in zip(
            values,
            predictions,
        )
    ]

    quantized, q = quantize(residuals)

    payload_bytes = payload_size(quantized)

    start_decode = time.perf_counter_ns()

    reconstructed = [
        prediction + residual * q
        for prediction, residual in zip(
            predictions,
            quantized,
        )
    ]

    decode_ms = (time.perf_counter_ns() - start_decode) / 1_000_000.0

    rmse, max_abs_error = error_metrics(
        values,
        reconstructed,
    )

    projected = (
        COMMON_METADATA_BYTES
        + parameter_payload_bytes
        + RESIDUAL_BLOCK_HEADER_BYTES
        + payload_bytes
    )

    return SegmentEvaluation(
        predictor=predictor,
        eligible=True,
        fallback=fallback,
        parameter_payload_bytes=parameter_payload_bytes,
        residual_payload_bytes=payload_bytes,
        projected_total_bytes=projected,
        reconstructed=reconstructed,
        rmse=rmse,
        max_abs_error=max_abs_error,
        fit_time_ms=0.0,
        decode_time_ms=decode_ms,
    )


def evaluate_predictor(
    spec: CandidateSpec,
    values: list[float],
) -> SegmentEvaluation:
    start_fit = time.perf_counter_ns()

    fallback = False

    if spec.name == "mean":
        mean = sum(values) / len(values)
        predictions = [mean for _ in values]

    elif spec.name == "linear":
        (
            _mean,
            slope,
            intercept,
            _variance,
        ) = core.compute_stats(values)

        predictions = [intercept + slope * index for index in range(len(values))]

    elif spec.name == "random_walk":
        seed = values[0]

        residuals = [0.0] * len(values)
        residuals[0] = values[0] - seed

        for index in range(1, len(values)):
            residuals[index] = values[index] - values[index - 1]

        quantized, q = quantize(residuals)

        payload_bytes = payload_size(quantized)

        fit_ms = (time.perf_counter_ns() - start_fit) / 1_000_000.0

        start_decode = time.perf_counter_ns()

        reconstructed = [0.0] * len(values)

        reconstructed[0] = seed + quantized[0] * q

        for index in range(1, len(values)):
            reconstructed[index] = reconstructed[index - 1] + quantized[index] * q

        decode_ms = (time.perf_counter_ns() - start_decode) / 1_000_000.0

        rmse, max_abs_error = error_metrics(
            values,
            reconstructed,
        )

        projected = (
            COMMON_METADATA_BYTES
            + spec.parameter_payload_bytes
            + RESIDUAL_BLOCK_HEADER_BYTES
            + payload_bytes
        )

        return SegmentEvaluation(
            predictor=spec.name,
            eligible=True,
            fallback=False,
            parameter_payload_bytes=(spec.parameter_payload_bytes),
            residual_payload_bytes=payload_bytes,
            projected_total_bytes=projected,
            reconstructed=reconstructed,
            rmse=rmse,
            max_abs_error=max_abs_error,
            fit_time_ms=fit_ms,
            decode_time_ms=decode_ms,
        )

    elif spec.name == "median":
        median = statistics.median(values)
        predictions = [median for _ in values]

    elif spec.name == "quadratic":
        (
            coefficients,
            fallback,
        ) = fit_quadratic(values)

        a, b, c = coefficients

        predictions = [
            a + b * index + c * index * index for index in range(len(values))
        ]

    elif spec.name == "ar1":
        (
            coefficients,
            fallback,
        ) = fit_ar1(values)

        intercept, phi, seed = coefficients

        residuals = [0.0] * len(values)
        reconstructed = [0.0] * len(values)

        residuals[0] = values[0] - seed

        # Initial quantization scale is fitted from causal residuals
        # formed against original history; decoder simulation below is
        # strictly reconstruction-causal.
        for index in range(1, len(values)):
            prediction = intercept + phi * values[index - 1]
            residuals[index] = values[index] - prediction

        quantized, q = quantize(residuals)

        payload_bytes = payload_size(quantized)

        fit_ms = (time.perf_counter_ns() - start_fit) / 1_000_000.0

        start_decode = time.perf_counter_ns()

        reconstructed[0] = seed + quantized[0] * q

        for index in range(1, len(values)):
            prediction = intercept + phi * reconstructed[index - 1]
            reconstructed[index] = prediction + quantized[index] * q

        decode_ms = (time.perf_counter_ns() - start_decode) / 1_000_000.0

        rmse, max_abs_error = error_metrics(
            values,
            reconstructed,
        )

        projected = (
            COMMON_METADATA_BYTES
            + spec.parameter_payload_bytes
            + RESIDUAL_BLOCK_HEADER_BYTES
            + payload_bytes
        )

        return SegmentEvaluation(
            predictor=spec.name,
            eligible=True,
            fallback=fallback,
            parameter_payload_bytes=(spec.parameter_payload_bytes),
            residual_payload_bytes=payload_bytes,
            projected_total_bytes=projected,
            reconstructed=reconstructed,
            rmse=rmse,
            max_abs_error=max_abs_error,
            fit_time_ms=fit_ms,
            decode_time_ms=decode_ms,
        )

    elif spec.name == "lag24":
        if len(values) < 25:
            return SegmentEvaluation(
                predictor=spec.name,
                eligible=False,
                fallback=False,
                parameter_payload_bytes=(spec.parameter_payload_bytes),
                residual_payload_bytes=0,
                projected_total_bytes=0,
                reconstructed=[],
                rmse=math.inf,
                max_abs_error=math.inf,
                fit_time_ms=(time.perf_counter_ns() - start_fit) / 1_000_000.0,
                decode_time_ms=0.0,
            )

        history = values[:24]

        residuals = [
            values[index] - values[index - 24]
            for index in range(
                24,
                len(values),
            )
        ]

        quantized, q = quantize(residuals)

        payload_bytes = payload_size(quantized)

        fit_ms = (time.perf_counter_ns() - start_fit) / 1_000_000.0

        start_decode = time.perf_counter_ns()

        reconstructed = list(history)

        for residual_index, index in enumerate(
            range(
                24,
                len(values),
            )
        ):
            reconstructed.append(
                reconstructed[index - 24] + quantized[residual_index] * q
            )

        decode_ms = (time.perf_counter_ns() - start_decode) / 1_000_000.0

        rmse, max_abs_error = error_metrics(
            values,
            reconstructed,
        )

        projected = (
            COMMON_METADATA_BYTES
            + spec.parameter_payload_bytes
            + RESIDUAL_BLOCK_HEADER_BYTES
            + payload_bytes
        )

        return SegmentEvaluation(
            predictor=spec.name,
            eligible=True,
            fallback=False,
            parameter_payload_bytes=(spec.parameter_payload_bytes),
            residual_payload_bytes=payload_bytes,
            projected_total_bytes=projected,
            reconstructed=reconstructed,
            rmse=rmse,
            max_abs_error=max_abs_error,
            fit_time_ms=fit_ms,
            decode_time_ms=decode_ms,
        )

    else:
        raise ValueError(f"Unknown predictor: {spec.name}")

    fit_ms = (time.perf_counter_ns() - start_fit) / 1_000_000.0

    result = evaluate_nonrecurrent(
        values,
        predictions,
        predictor=spec.name,
        parameter_payload_bytes=(spec.parameter_payload_bytes),
        fallback=fallback,
    )

    result.fit_time_ms = fit_ms

    return result


def dataset_segments(
    values: list[float],
) -> list[tuple[int, int]]:
    return core.segment_series_adaptive(
        values,
        predictor_type=1,
        min_len=32,
        max_len=128,
        mse_threshold=0.5,
    )


def evaluate_dataset(
    evidence_group: str,
    path: Path,
    specs: list[CandidateSpec],
) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
]:
    values = load_csv_values(path)

    segments = dataset_segments(values)

    aggregate: dict[
        str,
        dict[str, object],
    ] = {
        spec.name: {
            "eligible": 0,
            "fallback": 0,
            "metadata": 0,
            "payload": 0,
            "total": 0,
            "reconstructed": [],
            "fit_ms": 0.0,
            "decode_ms": 0.0,
        }
        for spec in specs
    }

    winners: list[dict[str, object]] = []

    for segment_index, (
        start,
        end,
    ) in enumerate(segments):
        segment_values = values[start : end + 1]

        evaluated = {
            spec.name: evaluate_predictor(
                spec,
                segment_values,
            )
            for spec in specs
        }

        eligible = [result for result in evaluated.values() if result.eligible]

        if not eligible:
            raise ValueError("Segment has no eligible predictor")

        mse_winner = min(
            eligible,
            key=lambda item: (
                item.rmse,
                item.projected_total_bytes,
                item.predictor,
            ),
        )

        byte_winner = min(
            eligible,
            key=lambda item: (
                item.projected_total_bytes,
                item.rmse,
                item.predictor,
            ),
        )

        winners.append(
            {
                "dataset": path.name,
                "evidence_group": evidence_group,
                "segment_index": segment_index,
                "start_idx": start,
                "end_idx": end,
                "segment_length": (end - start + 1),
                "mse_winner": (mse_winner.predictor),
                "mse_winner_rmse": (mse_winner.rmse),
                "byte_winner": (byte_winner.predictor),
                "byte_winner_projected_bytes": (byte_winner.projected_total_bytes),
            }
        )

        for spec in specs:
            result = evaluated[spec.name]

            bucket = aggregate[spec.name]

            if not result.eligible:
                continue

            bucket["eligible"] = int(bucket["eligible"]) + 1
            bucket["fallback"] = int(bucket["fallback"]) + int(result.fallback)
            bucket["metadata"] = (
                int(bucket["metadata"])
                + COMMON_METADATA_BYTES
                + spec.parameter_payload_bytes
                + RESIDUAL_BLOCK_HEADER_BYTES
            )
            bucket["payload"] = int(bucket["payload"]) + result.residual_payload_bytes
            bucket["total"] = int(bucket["total"]) + result.projected_total_bytes
            bucket["fit_ms"] = float(bucket["fit_ms"]) + result.fit_time_ms
            bucket["decode_ms"] = float(bucket["decode_ms"]) + result.decode_time_ms

            reconstructed = bucket["reconstructed"]

            if not isinstance(
                reconstructed,
                list,
            ):
                raise TypeError("Invalid reconstructed accumulator")

            reconstructed.extend(result.reconstructed)

    rows: list[dict[str, object]] = []

    for spec in specs:
        bucket = aggregate[spec.name]

        reconstructed = bucket["reconstructed"]

        if not isinstance(
            reconstructed,
            list,
        ):
            raise TypeError("Invalid reconstructed values")

        eligible_segments = int(bucket["eligible"])

        if eligible_segments == len(segments):
            (
                rmse,
                max_abs_error,
            ) = error_metrics(
                values,
                reconstructed,
            )
        else:
            rmse = math.nan
            max_abs_error = math.nan

        total_bytes = int(bucket["total"])

        rows.append(
            {
                "dataset": path.name,
                "evidence_group": (evidence_group),
                "predictor": spec.name,
                "candidate_class": (spec.candidate_class),
                "n_samples": len(values),
                "segment_count": (len(segments)),
                "eligible_segment_count": (eligible_segments),
                "fallback_segment_count": (int(bucket["fallback"])),
                "projected_metadata_bytes": (int(bucket["metadata"])),
                "residual_payload_bytes": (int(bucket["payload"])),
                "projected_total_bytes": (total_bytes),
                "bits_per_sample": (
                    total_bytes * 8 / len(values) if total_bytes else math.nan
                ),
                "rmse": rmse,
                "max_abs_error": (max_abs_error),
                "fit_time_ms": float(bucket["fit_ms"]),
                "decode_simulation_time_ms": (float(bucket["decode_ms"])),
            }
        )

    return rows, winners


def write_csv(
    path: Path,
    fieldnames: list[str],
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
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--matrix",
        type=Path,
        default=Path("docs/predictor-candidate-matrix.tsv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/tmp/lasagna-v2-issue7-predictors.csv"),
    )
    parser.add_argument(
        "--winner-output",
        type=Path,
        default=Path("/tmp/lasagna-v2-issue7-predictor-winners.csv"),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    specs = load_candidate_matrix(args.matrix)

    all_rows: list[dict[str, object]] = []
    all_winners: list[dict[str, object]] = []

    for evidence_group, path in DATASETS:
        rows, winners = evaluate_dataset(
            evidence_group,
            path,
            specs,
        )

        all_rows.extend(rows)
        all_winners.extend(winners)

        print(
            f"DATASET={path.name} "
            f"SEGMENTS={rows[0]['segment_count']} "
            f"PREDICTORS={len(rows)}"
        )

        eligible_rows = [
            row
            for row in rows
            if (int(row["eligible_segment_count"]) == int(row["segment_count"]))
        ]

        best = min(
            eligible_rows,
            key=lambda row: (
                int(row["projected_total_bytes"]),
                float(row["rmse"]),
            ),
        )

        print(
            f"DATASET_BEST_PROJECTED="
            f"{best['predictor']}:"
            f"bytes={best['projected_total_bytes']}:"
            f"rmse={best['rmse']}"
        )

    write_csv(
        args.output,
        RESULT_FIELDS,
        all_rows,
    )

    write_csv(
        args.winner_output,
        WINNER_FIELDS,
        all_winners,
    )

    print(f"RESULT_ROWS={len(all_rows)}")
    print(f"WINNER_ROWS={len(all_winners)}")
    print(f"OUTPUT={args.output}")
    print(f"WINNER_OUTPUT={args.winner_output}")
    print("PREDICTOR_TOURNAMENT_GATE=PASS")


if __name__ == "__main__":
    main()
