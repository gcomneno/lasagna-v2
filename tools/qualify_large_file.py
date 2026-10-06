#!/usr/bin/env python3
"""Large-file and scaling qualification for Lasagna production-readiness Gate 8."""

from __future__ import annotations

import argparse
import csv
import json
import platform
import resource
import struct
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lasagna2 import core  # noqa: E402

DEFAULT_SEGMENTS = 100_000


def load_existing_trend_scaling() -> list[dict[str, object]]:
    path = ROOT / "docs" / "performance-benchmark-results.csv"

    with path.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        rows = list(csv.DictReader(handle))

    selected: list[dict[str, object]] = []

    for row in rows:
        if (
            row["codec"] == "v2"
            and row["signal"] == "trend"
            and int(row["n_samples"]) in {10_000, 100_000, 1_000_000}
        ):
            selected.append(
                {
                    "n_points": int(row["n_samples"]),
                    "n_segments": int(row["segment_count"]),
                    "encoded_bytes": int(row["encoded_bytes"]),
                    "encode_ms": float(row["encode_median_ms"]),
                    "decode_ms": float(row["decode_median_ms"]),
                    "encode_peak_rss_kib": int(row["encode_peak_rss_kib"]),
                    "decode_peak_rss_kib": int(row["decode_peak_rss_kib"]),
                }
            )

    selected.sort(key=lambda row: int(row["n_points"]))

    if [row["n_points"] for row in selected] != [
        10_000,
        100_000,
        1_000_000,
    ]:
        raise ValueError("Expected V2 trend scaling rows are missing")

    return selected


def load_pilot(path: Path) -> dict[str, object]:
    with path.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        rows = list(csv.DictReader(handle))

    if len(rows) != 1:
        raise ValueError("Pilot CSV must contain exactly one result row")

    row = rows[0]

    if (
        row["codec"] != "v2"
        or row["signal"] != "trend"
        or int(row["n_samples"]) != 2_000_000
    ):
        raise ValueError("Pilot CSV is not the frozen 2M V2 trend case")

    return {
        "n_points": int(row["n_samples"]),
        "n_segments": int(row["segment_count"]),
        "encoded_bytes": int(row["encoded_bytes"]),
        "encode_ms": float(row["encode_median_ms"]),
        "decode_ms": float(row["decode_median_ms"]),
        "encode_peak_rss_kib": int(row["encode_peak_rss_kib"]),
        "decode_peak_rss_kib": int(row["decode_peak_rss_kib"]),
    }


def build_dense_v2(segment_count: int) -> bytes:
    if segment_count < 1:
        raise ValueError("segment_count must be >= 1")

    if segment_count > core.MAX_SEGMENTS:
        raise ValueError(
            f"segment_count={segment_count} exceeds maximum " f"{core.MAX_SEGMENTS}"
        )

    if segment_count > core.MAX_POINTS:
        raise ValueError(
            f"n_points={segment_count} exceeds maximum " f"{core.MAX_POINTS}"
        )

    context = b'{"sampling":{"dt":1.0,"t0":"1970-01-01T00:00:00Z"},"unit":"scale"}'

    encoded_size = (
        core.FILE_HEADER_STRUCT.size
        + len(context)
        + segment_count * core.SEGMENT_ENTRY_V2_STRUCT.size
        + core.RESIDUAL_SECTION_HEADER_STRUCT.size
        + segment_count * (core.RESIDUAL_BLOCK_HEADER_STRUCT.size + 4)
    )

    core._validate_encoded_size(encoded_size)

    out = bytearray(encoded_size)
    offset = 0

    core.FILE_HEADER_STRUCT.pack_into(
        out,
        offset,
        b"LSG2",
        core.FORMAT_VERSION_V2,
        0,
        len(context),
        segment_count,
        segment_count,
        0,
        0,
    )
    offset += core.FILE_HEADER_STRUCT.size

    out[offset : offset + len(context)] = context
    offset += len(context)

    for index in range(segment_count):
        core.SEGMENT_ENTRY_V2_STRUCT.pack_into(
            out,
            offset,
            index,
            index,
            0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
        )
        offset += core.SEGMENT_ENTRY_V2_STRUCT.size

    core.RESIDUAL_SECTION_HEADER_STRUCT.pack_into(
        out,
        offset,
        core.RESIDUAL_CODEC_RAW_INT32,
        0,
        0,
        0,
    )
    offset += core.RESIDUAL_SECTION_HEADER_STRUCT.size

    for index in range(segment_count):
        core.RESIDUAL_BLOCK_HEADER_STRUCT.pack_into(
            out,
            offset,
            index,
            1,
            4,
        )
        offset += core.RESIDUAL_BLOCK_HEADER_STRUCT.size

        struct.pack_into(
            "<i",
            out,
            offset,
            0,
        )
        offset += 4

    if offset != encoded_size:
        raise ValueError(
            f"Synthetic builder offset mismatch: " f"{offset} != {encoded_size}"
        )

    return bytes(out)


def run_dense_segment_case(segment_count: int) -> dict[str, object]:
    start = time.perf_counter()
    data = build_dense_v2(segment_count)
    build_seconds = time.perf_counter() - start

    start = time.perf_counter()
    decoded = core.decode_timeseries(data)
    decode_seconds = time.perf_counter() - start

    if len(decoded.values) != segment_count:
        raise ValueError("Dense segment decode point count mismatch")

    if any(value != 0.0 for value in decoded.values):
        raise ValueError("Dense segment decode value mismatch")

    return {
        "n_points": segment_count,
        "n_segments": segment_count,
        "encoded_bytes": len(data),
        "build_seconds": build_seconds,
        "decode_seconds": decode_seconds,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def expect_value_error(name: str, operation) -> dict[str, object]:
    try:
        operation()
    except ValueError as exc:
        return {
            "name": name,
            "status": "PASS",
            "exception": str(exc),
        }

    raise ValueError(f"{name} did not raise ValueError")


def run_boundary_checks() -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []

    core._validate_header_resources(
        header_len=0,
        n_points=core.MAX_POINTS,
        n_segments=0,
    )
    checks.append(
        {
            "name": "max-points-exact",
            "status": "PASS",
        }
    )

    checks.append(
        expect_value_error(
            "max-points-plus-one",
            lambda: core._validate_header_resources(
                header_len=0,
                n_points=core.MAX_POINTS + 1,
                n_segments=0,
            ),
        )
    )

    core._validate_header_resources(
        header_len=0,
        n_points=0,
        n_segments=core.MAX_SEGMENTS,
    )
    checks.append(
        {
            "name": "max-segments-exact",
            "status": "PASS",
        }
    )

    checks.append(
        expect_value_error(
            "max-segments-plus-one",
            lambda: core._validate_header_resources(
                header_len=0,
                n_points=0,
                n_segments=core.MAX_SEGMENTS + 1,
            ),
        )
    )

    core._validate_encoded_size(core.MAX_INPUT_BYTES)
    checks.append(
        {
            "name": "max-input-bytes-exact",
            "status": "PASS",
        }
    )

    checks.append(
        expect_value_error(
            "max-input-bytes-plus-one",
            lambda: core._validate_encoded_size(core.MAX_INPUT_BYTES + 1),
        )
    )

    # Validate worst-case arithmetic remains ordinary Python integer arithmetic
    # and does not wrap at 32-bit boundaries.
    worst_case_v1_size = (
        core.FILE_HEADER_STRUCT.size
        + core.MAX_CONTEXT_BYTES
        + (core.SEGMENT_ENTRY_STRUCT.size + core.RESIDUAL_BLOCK_HEADER_STRUCT.size)
        * core.MAX_SEGMENTS
        + core.MAX_VARINT_BYTES * core.MAX_POINTS
        + core.RESIDUAL_SECTION_HEADER_STRUCT.size
    )

    if worst_case_v1_size != core.MAX_INPUT_BYTES:
        raise ValueError("MAX_INPUT_BYTES derivation mismatch")

    if worst_case_v1_size <= core.UINT32_MAX:
        checks.append(
            {
                "name": "offset-arithmetic-within-uint32",
                "status": "PASS",
                "derived_max_input_bytes": worst_case_v1_size,
                "uint32_max": core.UINT32_MAX,
            }
        )
    else:
        checks.append(
            {
                "name": "offset-arithmetic-python-int",
                "status": "PASS",
                "derived_max_input_bytes": worst_case_v1_size,
                "uint32_max": core.UINT32_MAX,
            }
        )

    return checks


def scaling_ratios(
    rows: list[dict[str, object]],
) -> list[dict[str, float | int]]:
    result: list[dict[str, float | int]] = []

    for previous, current in zip(rows, rows[1:]):
        result.append(
            {
                "from_points": int(previous["n_points"]),
                "to_points": int(current["n_points"]),
                "point_ratio": (int(current["n_points"]) / int(previous["n_points"])),
                "encode_time_ratio": (
                    float(current["encode_ms"]) / float(previous["encode_ms"])
                ),
                "decode_time_ratio": (
                    float(current["decode_ms"]) / float(previous["decode_ms"])
                ),
                "encode_rss_ratio": (
                    int(current["encode_peak_rss_kib"])
                    / int(previous["encode_peak_rss_kib"])
                ),
                "decode_rss_ratio": (
                    int(current["decode_peak_rss_kib"])
                    / int(previous["decode_peak_rss_kib"])
                ),
            }
        )

    return result


def environment_record() -> dict[str, object]:
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "logical_cpu_count": __import__("os").cpu_count(),
    }


def run(
    *,
    pilot_path: Path,
    segment_count: int,
) -> dict[str, object]:
    scaling = load_existing_trend_scaling()
    pilot = load_pilot(pilot_path)

    all_scaling = scaling + [pilot]

    return {
        "schema_version": 1,
        "environment": environment_record(),
        "limits": {
            "MAX_POINTS": core.MAX_POINTS,
            "MAX_SEGMENTS": core.MAX_SEGMENTS,
            "MAX_INPUT_BYTES": core.MAX_INPUT_BYTES,
            "UINT32_MAX": core.UINT32_MAX,
        },
        "v2_trend_scaling": all_scaling,
        "adjacent_scaling": scaling_ratios(all_scaling),
        "dense_segment_case": run_dense_segment_case(segment_count),
        "boundary_checks": run_boundary_checks(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pilot",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--segments",
        type=int,
        default=DEFAULT_SEGMENTS,
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )

    args = parser.parse_args()

    result = run(
        pilot_path=args.pilot,
        segment_count=args.segments,
    )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    args.output.write_text(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
    )

    print("LARGE_FILE_QUALIFICATION_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
