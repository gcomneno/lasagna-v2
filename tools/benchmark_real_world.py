from __future__ import annotations

import argparse
from pathlib import Path

from benchmark_codec import (
    BenchmarkResult,
    CodecConfig,
    benchmark_dataset,
    write_results_csv,
)


FROZEN_LASAGNA_CONFIG = CodecConfig(
    "adaptive_auto_varint",
    "adaptive",
    "auto",
    "varint",
)

EXPECTED_DATASETS = (
    "appliances-energy.csv",
    "metro-traffic.csv",
    "beijing-pm25.csv",
)


def benchmark_real_world_corpus(
    input_dir: Path,
    *,
    repetitions: int,
    warmup: int,
) -> list[BenchmarkResult]:
    results: list[BenchmarkResult] = []

    for filename in EXPECTED_DATASETS:
        path = input_dir / filename

        if not path.is_file():
            raise ValueError(f"Missing canonical dataset: {path}")

        dataset_results = benchmark_dataset(
            path,
            configs=(FROZEN_LASAGNA_CONFIG,),
            repetitions=repetitions,
            warmup=warmup,
        )

        if len(dataset_results) != 5:
            raise ValueError(
                f"{filename}: expected 5 benchmark rows, " f"got {len(dataset_results)}"
            )

        lasagna_rows = [row for row in dataset_results if row.codec == "lasagna"]

        if len(lasagna_rows) != 1:
            raise ValueError(f"{filename}: expected exactly one " "Lasagna result")

        if lasagna_rows[0].configuration != FROZEN_LASAGNA_CONFIG.name:
            raise ValueError(f"{filename}: unexpected Lasagna " "configuration")

        results.extend(dataset_results)

    return results


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark the frozen Lasagna 2 real-world "
            "validation corpus without per-dataset tuning."
        )
    )

    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/real-world/canonical"),
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--repetitions",
        type=int,
        default=9,
    )

    parser.add_argument(
        "--warmup",
        type=int,
        default=2,
    )

    return parser


def main() -> int:
    args = build_arg_parser().parse_args()

    results = benchmark_real_world_corpus(
        args.input_dir,
        repetitions=args.repetitions,
        warmup=args.warmup,
    )

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

    print(f"RESULT_ROWS={len(results)}")
    print("LASAGNA_CONFIGURATION=" f"{FROZEN_LASAGNA_CONFIG.name}")
    print(f"OUTPUT={args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
