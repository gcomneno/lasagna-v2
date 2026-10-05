#!/usr/bin/env python3
"""Residual-distribution characterization for Lasagna 2 issue #8."""

from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"

for import_path in (ROOT, TOOLS):
    value = str(import_path)
    if value not in sys.path:
        sys.path.insert(0, value)

from lasagna2 import core
from benchmark_codec import load_csv_values


C_Q = 0.125
Q_MIN = 1e-6

STREAM_FIELDS = [
    "evidence_group",
    "dataset",
    "predictor",
    "n_samples",
    "segment_count",
    "residual_count",
    "min_q",
    "max_q",
    "max_abs_q",
    "zero_count",
    "zero_fraction",
    "positive_count",
    "negative_count",
    "mean_abs_q",
    "median_abs_q",
    "p95_abs_q",
    "p99_abs_q",
    "zigzag_min",
    "zigzag_max",
    "varint_1byte_count",
    "varint_2byte_count",
    "varint_3byte_count",
    "varint_4plus_count",
    "varint_1byte_fraction",
    "raw_int32_payload_bytes",
    "varint_payload_bytes",
    "longest_zero_run",
    "zero_run_count",
    "mean_zero_run_length",
    "median_zero_run_length",
    "p95_zero_run_length",
    "symbol_entropy_bits_per_residual",
]

BLOCK_FIELDS = [
    "evidence_group",
    "dataset",
    "predictor",
    "segment_index",
    "segment_length",
    "predictor_type",
    "zero_count",
    "zero_fraction",
    "max_abs_q",
    "varint_payload_bytes",
    "varint_bytes_per_residual",
    "longest_zero_run",
    "symbol_entropy_bits_per_residual",
]


@dataclass(frozen=True)
class MatrixRow:
    evidence_group: str
    dataset: Path
    predictor: str


def percentile_nearest_rank(
    values: list[int],
    percentile: float,
) -> float:
    if not values:
        return 0.0

    ordered = sorted(values)
    rank = max(
        1,
        math.ceil(percentile * len(ordered)),
    )
    return float(ordered[rank - 1])


def zero_runs(values: list[int]) -> list[int]:
    runs: list[int] = []
    current = 0

    for value in values:
        if value == 0:
            current += 1
        elif current:
            runs.append(current)
            current = 0

    if current:
        runs.append(current)

    return runs


def symbol_entropy(values: list[int]) -> float:
    if not values:
        return 0.0

    counts = Counter(values)
    total = len(values)

    return -sum(
        (count / total)
        * math.log2(count / total)
        for count in counts.values()
    )


def varint_width(value: int) -> int:
    zigzag = core.zigzag_encode(int(value))
    return len(core._encode_varint(zigzag))


def load_matrix(path: Path) -> list[MatrixRow]:
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

    matrix = [
        MatrixRow(
            evidence_group=row["evidence_group"],
            dataset=Path(row["dataset"]),
            predictor=row["predictor"],
        )
        for row in rows
    ]

    if len(matrix) != len(set(matrix)):
        raise ValueError(
            "Duplicate residual-distribution matrix row"
        )

    return matrix


def build_v2_residual_stream(
    values: list[float],
    predictor: str,
) -> tuple[
    list[core.SegmentEntry],
    list[list[int]],
]:
    ts = core.TimeSeries(
        values=values,
        dt=1.0,
        t0="1970-01-01T00:00:00Z",
        unit="residual-study",
    )

    (
        _context_bytes,
        model_segments,
        _model_residuals,
    ) = core._build_encoding_model(
        ts,
        segment_length=64,
        predictor=predictor,
        C_Q=C_Q,
        Q_MIN=Q_MIN,
        segment_mode="adaptive",
        min_segment_length=32,
        max_segment_length=128,
        mse_threshold=0.5,
    )

    v2_segments = [
        core._round_segment_entry_v2(segment)
        for segment in model_segments
    ]

    residual_segments: list[list[int]] = []

    for segment in v2_segments:
        x_seg = values[
            segment.start_idx : segment.end_idx + 1
        ]

        predictions = core._build_preds_for_segmentation(
            x_seg,
            predictor_type=segment.predictor_type,
            mean=segment.mean,
            slope=segment.slope,
            intercept=segment.intercept,
            seed_value=segment.seed_value,
        )

        q = segment.quant_step_Q

        q_res = [
            round(
                (value - prediction) / q
            )
            for value, prediction in zip(
                x_seg,
                predictions,
            )
        ]

        residual_segments.append(q_res)

    return v2_segments, residual_segments


def summarize_values(
    values: list[int],
) -> dict[str, float | int]:
    if not values:
        raise ValueError(
            "Residual stream must not be empty"
        )

    abs_values = [
        abs(value)
        for value in values
    ]

    zigzag_values = [
        core.zigzag_encode(int(value))
        for value in values
    ]

    widths = [
        varint_width(value)
        for value in values
    ]

    runs = zero_runs(values)

    zero_count = sum(
        value == 0
        for value in values
    )

    positive_count = sum(
        value > 0
        for value in values
    )

    negative_count = sum(
        value < 0
        for value in values
    )

    return {
        "residual_count": len(values),
        "min_q": min(values),
        "max_q": max(values),
        "max_abs_q": max(abs_values),
        "zero_count": zero_count,
        "zero_fraction": zero_count / len(values),
        "positive_count": positive_count,
        "negative_count": negative_count,
        "mean_abs_q": statistics.fmean(abs_values),
        "median_abs_q": statistics.median(abs_values),
        "p95_abs_q": percentile_nearest_rank(
            abs_values,
            0.95,
        ),
        "p99_abs_q": percentile_nearest_rank(
            abs_values,
            0.99,
        ),
        "zigzag_min": min(zigzag_values),
        "zigzag_max": max(zigzag_values),
        "varint_1byte_count": widths.count(1),
        "varint_2byte_count": widths.count(2),
        "varint_3byte_count": widths.count(3),
        "varint_4plus_count": sum(
            width >= 4
            for width in widths
        ),
        "varint_1byte_fraction": (
            widths.count(1) / len(widths)
        ),
        "raw_int32_payload_bytes": (
            4 * len(values)
        ),
        "varint_payload_bytes": sum(widths),
        "longest_zero_run": (
            max(runs)
            if runs
            else 0
        ),
        "zero_run_count": len(runs),
        "mean_zero_run_length": (
            statistics.fmean(runs)
            if runs
            else 0.0
        ),
        "median_zero_run_length": (
            statistics.median(runs)
            if runs
            else 0.0
        ),
        "p95_zero_run_length": (
            percentile_nearest_rank(
                runs,
                0.95,
            )
            if runs
            else 0.0
        ),
        "symbol_entropy_bits_per_residual": (
            symbol_entropy(values)
        ),
    }


def analyze_case(
    row: MatrixRow,
) -> tuple[
    dict[str, object],
    list[dict[str, object]],
]:
    values = load_csv_values(
        row.dataset
    )

    segments, residual_segments = (
        build_v2_residual_stream(
            values,
            row.predictor,
        )
    )

    flat = [
        value
        for segment in residual_segments
        for value in segment
    ]

    if len(flat) != len(values):
        raise ValueError(
            "Residual count does not match sample count"
        )

    stream_stats = summarize_values(flat)

    stream_row: dict[str, object] = {
        "evidence_group": row.evidence_group,
        "dataset": row.dataset.name,
        "predictor": row.predictor,
        "n_samples": len(values),
        "segment_count": len(segments),
        **stream_stats,
    }

    block_rows: list[
        dict[str, object]
    ] = []

    for index, (
        segment,
        q_res,
    ) in enumerate(
        zip(
            segments,
            residual_segments,
        )
    ):
        block_stats = summarize_values(
            q_res
        )

        block_rows.append(
            {
                "evidence_group": (
                    row.evidence_group
                ),
                "dataset": (
                    row.dataset.name
                ),
                "predictor": row.predictor,
                "segment_index": index,
                "segment_length": len(q_res),
                "predictor_type": (
                    segment.predictor_type
                ),
                "zero_count": (
                    block_stats[
                        "zero_count"
                    ]
                ),
                "zero_fraction": (
                    block_stats[
                        "zero_fraction"
                    ]
                ),
                "max_abs_q": (
                    block_stats[
                        "max_abs_q"
                    ]
                ),
                "varint_payload_bytes": (
                    block_stats[
                        "varint_payload_bytes"
                    ]
                ),
                "varint_bytes_per_residual": (
                    block_stats[
                        "varint_payload_bytes"
                    ]
                    / len(q_res)
                ),
                "longest_zero_run": (
                    block_stats[
                        "longest_zero_run"
                    ]
                ),
                "symbol_entropy_bits_per_residual": (
                    block_stats[
                        "symbol_entropy_bits_per_residual"
                    ]
                ),
            }
        )

    return stream_row, block_rows


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
        default=Path(
            "docs/residual-distribution-matrix.tsv"
        ),
    )

    parser.add_argument(
        "--stream-output",
        type=Path,
        default=Path(
            "/tmp/lasagna-v2-issue8-residual-streams.csv"
        ),
    )

    parser.add_argument(
        "--block-output",
        type=Path,
        default=Path(
            "/tmp/lasagna-v2-issue8-residual-blocks.csv"
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    matrix = load_matrix(
        args.matrix
    )

    stream_rows: list[
        dict[str, object]
    ] = []

    block_rows: list[
        dict[str, object]
    ] = []

    for index, row in enumerate(
        matrix,
        start=1,
    ):
        stream_row, case_blocks = (
            analyze_case(row)
        )

        stream_rows.append(
            stream_row
        )
        block_rows.extend(
            case_blocks
        )

        print(
            f"CASE={index}/{len(matrix)} "
            f"DATASET={stream_row['dataset']} "
            f"PREDICTOR={row.predictor} "
            f"N={stream_row['n_samples']} "
            f"SEGMENTS={stream_row['segment_count']} "
            f"ZERO_FRAC="
            f"{float(stream_row['zero_fraction']):.6f} "
            f"VARINT_1B_FRAC="
            f"{float(stream_row['varint_1byte_fraction']):.6f} "
            f"VARINT_BYTES="
            f"{stream_row['varint_payload_bytes']} "
            f"LONGEST_ZERO_RUN="
            f"{stream_row['longest_zero_run']}"
        )

    write_csv(
        args.stream_output,
        STREAM_FIELDS,
        stream_rows,
    )

    write_csv(
        args.block_output,
        BLOCK_FIELDS,
        block_rows,
    )

    print(
        f"STREAM_ROWS={len(stream_rows)}"
    )
    print(
        f"BLOCK_ROWS={len(block_rows)}"
    )
    print(
        f"STREAM_OUTPUT={args.stream_output}"
    )
    print(
        f"BLOCK_OUTPUT={args.block_output}"
    )
    print(
        "RESIDUAL_DISTRIBUTION_GATE=PASS"
    )


if __name__ == "__main__":
    main()
