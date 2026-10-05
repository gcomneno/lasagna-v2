from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from benchmark_codec import (
    _measure_deterministic_encode,
    _median_call_ms,
    canonical_float64_bytes,
    error_metrics,
    load_csv_values,
)
from lasagna2.cli import read_lsg2_metadata_and_segments
from lasagna2.core import (
    TimeSeries,
    decode_timeseries,
    encode_timeseries,
)


@dataclass(frozen=True)
class SweepConfig:
    config_id: str
    axis: str
    C_Q: float
    Q_MIN: float
    min_segment_length: int
    max_segment_length: int
    mse_threshold: float


DATASETS = (
    ("internal", Path("data/examples/trend.csv")),
    ("internal", Path("data/examples/sine_noise.csv")),
    ("internal", Path("data/examples/flat_spike.csv")),
    (
        "real-world",
        Path("data/real-world/canonical/appliances-energy.csv"),
    ),
    (
        "real-world",
        Path("data/real-world/canonical/metro-traffic.csv"),
    ),
    (
        "real-world",
        Path("data/real-world/canonical/beijing-pm25.csv"),
    ),
)

FIELDNAMES = (
    "dataset",
    "evidence_group",
    "config_id",
    "axis",
    "C_Q",
    "Q_MIN",
    "min_segment_length",
    "max_segment_length",
    "mse_threshold",
    "n_samples",
    "raw_bytes",
    "encoded_bytes",
    "bits_per_sample",
    "compression_ratio",
    "mse",
    "rmse",
    "max_abs_error",
    "segment_count",
    "mean_segment_length",
    "min_observed_segment_length",
    "max_observed_segment_length",
    "mean_predictor_segments",
    "linear_predictor_segments",
    "rw_predictor_segments",
    "encode_time_ms",
    "decode_time_ms",
)


def load_sweep(path: Path) -> list[SweepConfig]:
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

    configs = [
        SweepConfig(
            config_id=row["config_id"],
            axis=row["axis"],
            C_Q=float(row["C_Q"]),
            Q_MIN=float(row["Q_MIN"]),
            min_segment_length=int(
                row["min_segment_length"]
            ),
            max_segment_length=int(
                row["max_segment_length"]
            ),
            mse_threshold=float(
                row["mse_threshold"]
            ),
        )
        for row in rows
    ]

    if not configs:
        raise ValueError(
            "Sweep matrix contains no configurations"
        )

    config_ids = [
        config.config_id
        for config in configs
    ]

    if len(config_ids) != len(set(config_ids)):
        raise ValueError(
            "Sweep matrix contains duplicate config_id values"
        )

    return configs


def segment_metrics(
    encoded: bytes,
) -> tuple[int, float, int, int, Counter[int]]:
    (
        _ctx,
        _n_points,
        segments,
        _coding_type,
    ) = read_lsg2_metadata_and_segments(encoded)

    if not segments:
        raise ValueError(
            "Non-empty benchmark series produced no segments"
        )

    lengths = [
        segment.end_idx - segment.start_idx + 1
        for segment in segments
    ]

    predictors = Counter(
        segment.predictor_type
        for segment in segments
    )

    return (
        len(segments),
        sum(lengths) / len(lengths),
        min(lengths),
        max(lengths),
        predictors,
    )


def evaluate(
    dataset_path: Path,
    evidence_group: str,
    config: SweepConfig,
    *,
    repetitions: int,
    warmup: int,
) -> dict[str, object]:
    values = load_csv_values(dataset_path)

    ts = TimeSeries(
        values=list(values),
        dt=1.0,
        t0="1970-01-01T00:00:00Z",
        unit="benchmark",
    )

    def encode() -> bytes:
        return encode_timeseries(
            ts,
            segment_length=64,
            predictor="auto",
            C_Q=config.C_Q,
            Q_MIN=config.Q_MIN,
            segment_mode="adaptive",
            min_segment_length=(
                config.min_segment_length
            ),
            max_segment_length=(
                config.max_segment_length
            ),
            mse_threshold=config.mse_threshold,
            residual_coding="varint",
        )

    encoded, encode_time_ms = (
        _measure_deterministic_encode(
            encode,
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

    mse = rmse * rmse

    (
        segment_count,
        mean_segment_length,
        min_observed_segment_length,
        max_observed_segment_length,
        predictors,
    ) = segment_metrics(encoded)

    raw_bytes = len(
        canonical_float64_bytes(values)
    )
    encoded_bytes = len(encoded)

    return {
        "dataset": dataset_path.name,
        "evidence_group": evidence_group,
        "config_id": config.config_id,
        "axis": config.axis,
        "C_Q": config.C_Q,
        "Q_MIN": config.Q_MIN,
        "min_segment_length": (
            config.min_segment_length
        ),
        "max_segment_length": (
            config.max_segment_length
        ),
        "mse_threshold": config.mse_threshold,
        "n_samples": len(values),
        "raw_bytes": raw_bytes,
        "encoded_bytes": encoded_bytes,
        "bits_per_sample": (
            encoded_bytes * 8.0 / len(values)
        ),
        "compression_ratio": (
            raw_bytes / encoded_bytes
        ),
        "mse": mse,
        "rmse": rmse,
        "max_abs_error": max_abs_error,
        "segment_count": segment_count,
        "mean_segment_length": (
            mean_segment_length
        ),
        "min_observed_segment_length": (
            min_observed_segment_length
        ),
        "max_observed_segment_length": (
            max_observed_segment_length
        ),
        "mean_predictor_segments": (
            predictors.get(0, 0)
        ),
        "linear_predictor_segments": (
            predictors.get(1, 0)
        ),
        "rw_predictor_segments": (
            predictors.get(2, 0)
        ),
        "encode_time_ms": encode_time_ms,
        "decode_time_ms": decode_time_ms,
    }


def write_results(
    rows: Sequence[dict[str, object]],
    path: Path,
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
            lineterminator="\n",
        )

        writer.writeheader()

        for row in rows:
            serialized = dict(row)

            for key in (
                "C_Q",
                "Q_MIN",
                "mse_threshold",
                "bits_per_sample",
                "compression_ratio",
                "mse",
                "rmse",
                "max_abs_error",
                "mean_segment_length",
                "encode_time_ms",
                "decode_time_ms",
            ):
                serialized[key] = (
                    f"{float(serialized[key]):.12g}"
                )

            writer.writerow(serialized)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Execute the frozen Lasagna V2 sensitivity sweep."
        )
    )

    parser.add_argument(
        "--matrix",
        type=Path,
        default=Path(
            "docs/sensitivity-sweep.tsv"
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--repetitions",
        type=int,
        default=3,
    )

    parser.add_argument(
        "--warmup",
        type=int,
        default=1,
    )

    return parser


def main() -> int:
    args = build_arg_parser().parse_args()

    configs = load_sweep(args.matrix)

    rows: list[dict[str, object]] = []

    for evidence_group, dataset_path in DATASETS:
        if not dataset_path.is_file():
            raise ValueError(
                f"Missing dataset: {dataset_path}"
            )

        for config in configs:
            row = evaluate(
                dataset_path,
                evidence_group,
                config,
                repetitions=args.repetitions,
                warmup=args.warmup,
            )

            rows.append(row)

            print(
                f"DATASET={row['dataset']} "
                f"CONFIG={config.config_id} "
                f"BYTES={row['encoded_bytes']} "
                f"RMSE={row['rmse']:.8g} "
                f"SEGMENTS={row['segment_count']}"
            )

    expected_rows = (
        len(configs) * len(DATASETS)
    )

    if len(rows) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} results, got {len(rows)}"
        )

    write_results(
        rows,
        args.output,
    )

    print(f"RESULT_ROWS={len(rows)}")
    print(f"OUTPUT={args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
