#!/usr/bin/env python3
"""Shadow residual-codec benchmark for Lasagna 2 issue #8."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import statistics
import struct
import sys
import time
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"

for import_path in (ROOT, TOOLS):
    value = str(import_path)
    if value not in sys.path:
        sys.path.insert(0, value)

from lasagna2 import core
from benchmark_codec import load_csv_values


ZERO_RUN_MIN_LENGTH = 3
BENCHMARK_WARMUP = 1
BENCHMARK_RUNS = 7

RESULT_FIELDS = [
    "evidence_group",
    "dataset",
    "predictor",
    "n_samples",
    "segment_count",
    "raw_payload_bytes",
    "varint_payload_bytes",
    "zero_run_payload_bytes",
    "zero_run_delta_vs_varint",
    "zero_run_smaller_blocks",
    "zero_run_tie_blocks",
    "zero_run_larger_blocks",
    "hybrid_gross_payload_bytes",
    "hybrid_selector_bytes",
    "hybrid_payload_bytes",
    "hybrid_delta_vs_varint",
    "current_v2_varint_total_bytes",
    "projected_v2_zero_run_total_bytes",
    "projected_v2_hybrid_total_bytes",
    "zero_run_total_delta",
    "hybrid_total_delta",
    "varint_encode_median_ms",
    "varint_decode_median_ms",
    "zero_run_encode_median_ms",
    "zero_run_decode_median_ms",
]

WORST_CASE_FIELDS = [
    "case",
    "residual_count",
    "varint_bytes",
    "zero_run_bytes",
    "delta_bytes",
    "ratio_vs_varint",
]


def load_distribution_module():
    path = TOOLS / "analyze_residual_distributions.py"

    spec = importlib.util.spec_from_file_location(
        "analyze_residual_distributions",
        path,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError(
            "Unable to load residual distribution module"
        )

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


distribution = load_distribution_module()


def encode_zero_run_varint(
    values: list[int],
) -> bytes:
    out = bytearray()
    index = 0

    while index < len(values):
        if values[index] == 0:
            run_end = index + 1

            while (
                run_end < len(values)
                and values[run_end] == 0
            ):
                run_end += 1

            run_length = run_end - index

            if run_length >= ZERO_RUN_MIN_LENGTH:
                out += core._encode_varint(0)
                out += core._encode_varint(
                    run_length
                )
                index = run_end
                continue

        token = (
            core.zigzag_encode(
                int(values[index])
            )
            + 1
        )

        out += core._encode_varint(token)
        index += 1

    return bytes(out)


def decode_zero_run_varint(
    data: bytes,
    expected_count: int,
) -> list[int]:
    values: list[int] = []
    offset = 0

    while offset < len(data):
        token, offset = core._decode_varint(
            data,
            offset,
        )

        if token == 0:
            run_length, offset = (
                core._decode_varint(
                    data,
                    offset,
                )
            )

            if run_length < ZERO_RUN_MIN_LENGTH:
                raise ValueError(
                    "Invalid zero-run length"
                )

            if (
                len(values) + run_length
                > expected_count
            ):
                raise ValueError(
                    "Zero-run exceeds declared residual count"
                )

            values.extend(
                [0] * run_length
            )

        else:
            value = core.zigzag_decode(
                token - 1
            )

            values.append(value)

            if len(values) > expected_count:
                raise ValueError(
                    "Decoded residual count exceeds declaration"
                )

    if len(values) != expected_count:
        raise ValueError(
            "Decoded residual count does not match declaration"
        )

    return values


def encode_varint_blocks(
    blocks: list[list[int]],
) -> list[bytes]:
    return [
        core.encode_int_list_varint(
            block
        )
        for block in blocks
    ]


def decode_varint_blocks(
    payloads: list[bytes],
    lengths: list[int],
) -> list[list[int]]:
    return [
        core.decode_int_list_varint(
            payload,
            length,
        )
        for payload, length in zip(
            payloads,
            lengths,
        )
    ]


def encode_zero_run_blocks(
    blocks: list[list[int]],
) -> list[bytes]:
    return [
        encode_zero_run_varint(block)
        for block in blocks
    ]


def decode_zero_run_blocks(
    payloads: list[bytes],
    lengths: list[int],
) -> list[list[int]]:
    return [
        decode_zero_run_varint(
            payload,
            length,
        )
        for payload, length in zip(
            payloads,
            lengths,
        )
    ]


def median_runtime_ms(
    operation: Callable[[], object],
) -> float:
    for _ in range(BENCHMARK_WARMUP):
        operation()

    timings: list[float] = []

    for _ in range(BENCHMARK_RUNS):
        start = time.perf_counter_ns()
        operation()
        elapsed = (
            time.perf_counter_ns()
            - start
        ) / 1_000_000.0
        timings.append(elapsed)

    return statistics.median(timings)


def current_v2_total_bytes(
    values: list[float],
    predictor: str,
) -> int:
    ts = core.TimeSeries(
        values=values,
        dt=1.0,
        t0="1970-01-01T00:00:00Z",
        unit="residual-study",
    )

    encoded = core.encode_timeseries_v2(
        ts,
        segment_length=64,
        predictor=predictor,
        C_Q=0.125,
        Q_MIN=1e-6,
        segment_mode="adaptive",
        min_segment_length=32,
        max_segment_length=128,
        mse_threshold=0.5,
        residual_coding="varint",
    )

    return len(encoded)


def evaluate_stream(
    evidence_group: str,
    dataset: Path,
    predictor: str,
) -> dict[str, object]:
    values = load_csv_values(dataset)

    _segments, blocks = (
        distribution.build_v2_residual_stream(
            values,
            predictor,
        )
    )

    lengths = [
        len(block)
        for block in blocks
    ]

    varint_payloads = encode_varint_blocks(
        blocks
    )

    zero_run_payloads = (
        encode_zero_run_blocks(
            blocks
        )
    )

    if decode_varint_blocks(
        varint_payloads,
        lengths,
    ) != blocks:
        raise ValueError(
            "Varint roundtrip mismatch"
        )

    if decode_zero_run_blocks(
        zero_run_payloads,
        lengths,
    ) != blocks:
        raise ValueError(
            "Zero-run roundtrip mismatch"
        )

    varint_sizes = [
        len(payload)
        for payload in varint_payloads
    ]

    zero_run_sizes = [
        len(payload)
        for payload in zero_run_payloads
    ]

    raw_payload_bytes = (
        4 * sum(lengths)
    )

    varint_payload_bytes = sum(
        varint_sizes
    )

    zero_run_payload_bytes = sum(
        zero_run_sizes
    )

    smaller = sum(
        zero < varint
        for zero, varint in zip(
            zero_run_sizes,
            varint_sizes,
        )
    )

    ties = sum(
        zero == varint
        for zero, varint in zip(
            zero_run_sizes,
            varint_sizes,
        )
    )

    larger = sum(
        zero > varint
        for zero, varint in zip(
            zero_run_sizes,
            varint_sizes,
        )
    )

    hybrid_gross = sum(
        min(varint, zero)
        for varint, zero in zip(
            varint_sizes,
            zero_run_sizes,
        )
    )

    selector_bytes = len(blocks)

    hybrid_payload = (
        hybrid_gross
        + selector_bytes
    )

    current_total = current_v2_total_bytes(
        values,
        predictor,
    )

    projected_zero_total = (
        current_total
        - varint_payload_bytes
        + zero_run_payload_bytes
    )

    projected_hybrid_total = (
        current_total
        - varint_payload_bytes
        + hybrid_payload
    )

    varint_encode_ms = median_runtime_ms(
        lambda: encode_varint_blocks(
            blocks
        )
    )

    varint_decode_ms = median_runtime_ms(
        lambda: decode_varint_blocks(
            varint_payloads,
            lengths,
        )
    )

    zero_run_encode_ms = median_runtime_ms(
        lambda: encode_zero_run_blocks(
            blocks
        )
    )

    zero_run_decode_ms = median_runtime_ms(
        lambda: decode_zero_run_blocks(
            zero_run_payloads,
            lengths,
        )
    )

    return {
        "evidence_group": evidence_group,
        "dataset": dataset.name,
        "predictor": predictor,
        "n_samples": len(values),
        "segment_count": len(blocks),
        "raw_payload_bytes": (
            raw_payload_bytes
        ),
        "varint_payload_bytes": (
            varint_payload_bytes
        ),
        "zero_run_payload_bytes": (
            zero_run_payload_bytes
        ),
        "zero_run_delta_vs_varint": (
            zero_run_payload_bytes
            - varint_payload_bytes
        ),
        "zero_run_smaller_blocks": smaller,
        "zero_run_tie_blocks": ties,
        "zero_run_larger_blocks": larger,
        "hybrid_gross_payload_bytes": (
            hybrid_gross
        ),
        "hybrid_selector_bytes": (
            selector_bytes
        ),
        "hybrid_payload_bytes": (
            hybrid_payload
        ),
        "hybrid_delta_vs_varint": (
            hybrid_payload
            - varint_payload_bytes
        ),
        "current_v2_varint_total_bytes": (
            current_total
        ),
        "projected_v2_zero_run_total_bytes": (
            projected_zero_total
        ),
        "projected_v2_hybrid_total_bytes": (
            projected_hybrid_total
        ),
        "zero_run_total_delta": (
            projected_zero_total
            - current_total
        ),
        "hybrid_total_delta": (
            projected_hybrid_total
            - current_total
        ),
        "varint_encode_median_ms": (
            varint_encode_ms
        ),
        "varint_decode_median_ms": (
            varint_decode_ms
        ),
        "zero_run_encode_median_ms": (
            zero_run_encode_ms
        ),
        "zero_run_decode_median_ms": (
            zero_run_decode_ms
        ),
    }


def worst_case_streams() -> dict[str, list[int]]:
    return {
        "all_zero": [0] * 128,
        "alternating_zero_nonzero": (
            [0, 1] * 64
        ),
        "no_zero_small": [
            1 if index % 2 == 0 else -1
            for index in range(128)
        ],
        "isolated_zero": [
            0 if index % 8 == 0 else 1
            for index in range(128)
        ],
        "long_zero_run": (
            [1] * 8
            + [0] * 112
            + [-1] * 8
        ),
        "boundary_positive_63": [63] * 128,
        "boundary_negative_64": [-64] * 128,
        "boundary_positive_64": [64] * 128,
        "boundary_negative_65": [-65] * 128,
        "large_signed": [
            2**31 - 1
            if index % 2 == 0
            else -(2**31)
            for index in range(128)
        ],
    }


def evaluate_worst_cases() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    for name, values in (
        worst_case_streams().items()
    ):
        varint_payload = (
            core.encode_int_list_varint(
                values
            )
        )

        zero_run_payload = (
            encode_zero_run_varint(
                values
            )
        )

        decoded = decode_zero_run_varint(
            zero_run_payload,
            len(values),
        )

        if decoded != values:
            raise ValueError(
                f"Worst-case roundtrip mismatch: {name}"
            )

        varint_bytes = len(
            varint_payload
        )

        zero_run_bytes = len(
            zero_run_payload
        )

        rows.append(
            {
                "case": name,
                "residual_count": len(values),
                "varint_bytes": varint_bytes,
                "zero_run_bytes": zero_run_bytes,
                "delta_bytes": (
                    zero_run_bytes
                    - varint_bytes
                ),
                "ratio_vs_varint": (
                    zero_run_bytes
                    / varint_bytes
                ),
            }
        )

    return rows


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
        "--output",
        type=Path,
        default=Path(
            "/tmp/lasagna-v2-issue8-codecs.csv"
        ),
    )

    parser.add_argument(
        "--worst-case-output",
        type=Path,
        default=Path(
            "/tmp/lasagna-v2-issue8-codec-worst-cases.csv"
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    matrix = (
        distribution.load_matrix(
            args.matrix
        )
    )

    rows: list[
        dict[str, object]
    ] = []

    for index, row in enumerate(
        matrix,
        start=1,
    ):
        result = evaluate_stream(
            row.evidence_group,
            row.dataset,
            row.predictor,
        )

        rows.append(result)

        print(
            f"CASE={index}/{len(matrix)} "
            f"DATASET={result['dataset']} "
            f"PREDICTOR={result['predictor']} "
            f"VARINT={result['varint_payload_bytes']} "
            f"ZERO_RUN={result['zero_run_payload_bytes']} "
            f"ZERO_DELTA={result['zero_run_delta_vs_varint']} "
            f"HYBRID={result['hybrid_payload_bytes']} "
            f"HYBRID_DELTA={result['hybrid_delta_vs_varint']} "
            f"ZERO_SMALLER_BLOCKS="
            f"{result['zero_run_smaller_blocks']}"
        )

    worst_rows = (
        evaluate_worst_cases()
    )

    write_csv(
        args.output,
        RESULT_FIELDS,
        rows,
    )

    write_csv(
        args.worst_case_output,
        WORST_CASE_FIELDS,
        worst_rows,
    )

    print(
        f"RESULT_ROWS={len(rows)}"
    )
    print(
        f"WORST_CASE_ROWS={len(worst_rows)}"
    )
    print(
        f"OUTPUT={args.output}"
    )
    print(
        f"WORST_CASE_OUTPUT="
        f"{args.worst_case_output}"
    )
    print(
        "RESIDUAL_CODEC_BENCHMARK_GATE=PASS"
    )


if __name__ == "__main__":
    main()
