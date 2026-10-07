#!/usr/bin/env python3
"""Frozen local-model-value experiment for Lasagna 2 issue #24."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import platform
import re
import shlex
import statistics
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"

for import_path in (ROOT, TOOLS):
    value = str(import_path)
    if value not in sys.path:
        sys.path.insert(0, value)

from benchmark_codec import (  # noqa: E402
    _measure_deterministic_encode,
    _median_call_ms,
    canonical_float64_bytes,
    error_metrics,
    load_csv_values,
)

from lasagna2 import core  # noqa: E402
from lasagna2.cli import read_lsg2_metadata_and_segments  # noqa: E402

PROTOCOL_FREEZE_COMMIT = (
    "198c8fd3434360c405d15a3e2a353dab039ca1ec"  # pragma: allowlist secret
)

C_Q_VALUES = (
    0.0625,
    0.125,
    0.25,
    0.5,
    1.0,
    2.0,
    4.0,
)

Q_MIN = 1e-6
FIXED_SEGMENT_LENGTH = 64
ADAPTIVE_MIN = 32
ADAPTIVE_MAX = 128
ADAPTIVE_MSE_THRESHOLD = 0.5

CONTEXT_DT = 1.0
CONTEXT_T0 = "1970-01-01T00:00:00Z"
CONTEXT_UNIT = "local-model-value"

PRIMARY_ARCHITECTURES = ("A0", "A1", "A4")
SIMPLE_BASELINES = ("A0", "A1")
DESCRIPTIVE_PAIRS = (("A2", "A1"), ("A3", "A1"), ("A4", "A2"), ("A4", "A3"))
PROTOCOL_PATH = ROOT / "docs/local-model-value-protocol.md"
PROVENANCE_PATH = ROOT / "docs/local-model-value-provenance.json"
REPORT_PATH = ROOT / "docs/local-model-value-report.json"
STUDY_PATH = ROOT / "docs/local-model-value-study.md"

REPRODUCIBILITY_GATES = (
    "PROTOCOL_FROZEN_BEFORE_EXECUTION_GATE",
    "NO_DATASET_SPECIFIC_TUNING_GATE",
    "COMMON_CODEC_CONTROLS_GATE",
    "FULL_GRID_EXECUTION_GATE",
    "DETERMINISTIC_BYTES_GATE",
    "EXACT_BYTE_ACCOUNTING_GATE",
    "PRIMARY_TARGET_COVERAGE_GATE",
    "MATCHED_DISTORTION_GATE",
    "PER_DATASET_REPORTING_GATE",
    "EXTERNAL_CORPUS_COVERAGE_GATE",
    "PARETO_REPORTING_GATE",
    "RUNTIME_MEASUREMENT_GATE",
    "NEGATIVE_RESULT_PRESERVATION_GATE",
)

INTERNAL_DATASETS = (
    Path("data/examples/trend.csv"),
    Path("data/examples/sine_noise.csv"),
    Path("data/examples/flat_spike.csv"),
)

EXTERNAL_DATASETS = (
    Path("data/external-qualification/canonical/appliances-energy.csv"),
    Path("data/external-qualification/canonical/metro-traffic.csv"),
    Path("data/external-qualification/canonical/beijing-pm25.csv"),
    Path("data/external-qualification/canonical/seoul-bike-demand.csv"),
    Path("data/external-qualification/canonical/fan-vibration-x.csv"),
    Path("data/external-qualification/canonical/dow-jones-weekly-return.csv"),
    Path("data/external-qualification/canonical/room-occupancy-count.csv"),
    Path("data/external-qualification/canonical/tetouan-zone1-power.csv"),
)


@dataclass(frozen=True)
class Architecture:
    architecture: str
    name: str
    segment_mode: str
    predictor: str
    fixed_segment_length: int | None = None
    min_segment_length: int | None = None
    max_segment_length: int | None = None
    mse_threshold: float | None = None


ARCHITECTURES = (
    Architecture("A0", "whole_linear", "fixed", "linear"),
    Architecture(
        "A1",
        "fixed_linear",
        "fixed",
        "linear",
        fixed_segment_length=FIXED_SEGMENT_LENGTH,
    ),
    Architecture(
        "A2",
        "fixed_auto",
        "fixed",
        "auto",
        fixed_segment_length=FIXED_SEGMENT_LENGTH,
    ),
    Architecture(
        "A3",
        "adaptive_linear",
        "adaptive",
        "linear",
        min_segment_length=ADAPTIVE_MIN,
        max_segment_length=ADAPTIVE_MAX,
        mse_threshold=ADAPTIVE_MSE_THRESHOLD,
    ),
    Architecture(
        "A4",
        "adaptive_auto",
        "adaptive",
        "auto",
        min_segment_length=ADAPTIVE_MIN,
        max_segment_length=ADAPTIVE_MAX,
        mse_threshold=ADAPTIVE_MSE_THRESHOLD,
    ),
)


RAW_FIELDS = (
    "point_id",
    "dataset",
    "evidence_group",
    "architecture",
    "architecture_name",
    "C_Q",
    "Q_MIN",
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
    "min_segment_length_observed",
    "max_segment_length_observed",
    "mean_predictor_segments",
    "linear_predictor_segments",
    "rw_predictor_segments",
    "global_and_context_bytes",
    "segment_metadata_bytes",
    "residual_block_metadata_bytes",
    "residual_payload_bytes",
    "structural_bytes",
    "encode_time_ms",
    "decode_time_ms",
)

MATCHED_FIELDS = (
    "dataset",
    "evidence_group",
    "target_id",
    "target_rmse",
    "target_aliases",
    "architecture",
    "architecture_name",
    "match_status",
    "selected_point_id",
    "selected_C_Q",
    "selected_rmse",
    "selected_max_abs_error",
    "selected_encoded_bytes",
    "selected_bits_per_sample",
    "selected_baseline",
    "rate_ratio",
    "classification",
)

SUMMARY_FIELDS = (
    "dataset",
    "evidence_group",
    "coverage_status",
    "primary_target_count",
    "A0_covered",
    "A1_covered",
    "A4_covered",
    "complete_primary_coverage",
    "material_wins",
    "practical_ties",
    "material_losses",
    "non_loss_fraction",
    "median_rate_ratio",
    "best_rate_ratio",
    "worst_rate_ratio",
)


def git_output(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=ROOT,
        text=True,
    ).strip()


def architecture_by_id(architecture_id: str) -> Architecture:
    for architecture in ARCHITECTURES:
        if architecture.architecture == architecture_id:
            return architecture
    raise ValueError(f"Unknown architecture {architecture_id}")


def point_id(
    dataset: str,
    architecture: str,
    c_q: float,
) -> str:
    return f"{dataset}:{architecture}:cq={format(c_q, '.17g')}"


def make_timeseries(values: Sequence[float]) -> core.TimeSeries:
    return core.TimeSeries(
        values=list(values),
        dt=CONTEXT_DT,
        t0=CONTEXT_T0,
        unit=CONTEXT_UNIT,
    )


def architecture_options(
    architecture: Architecture,
    n_samples: int | str,
    c_q: float,
) -> dict[str, object]:
    """The same resolved options drive encoding and provenance."""
    return {
        "segment_length": (
            n_samples
            if architecture.architecture == "A0"
            else architecture.fixed_segment_length or FIXED_SEGMENT_LENGTH
        ),
        "predictor": architecture.predictor,
        "C_Q": c_q,
        "Q_MIN": Q_MIN,
        "segment_mode": architecture.segment_mode,
        "min_segment_length": architecture.min_segment_length or ADAPTIVE_MIN,
        "max_segment_length": architecture.max_segment_length or ADAPTIVE_MAX,
        "mse_threshold": (
            architecture.mse_threshold
            if architecture.mse_threshold is not None
            else ADAPTIVE_MSE_THRESHOLD
        ),
        "residual_coding": "varint",
    }


def encode_for_architecture(
    ts: core.TimeSeries,
    architecture: Architecture,
    c_q: float,
) -> bytes:
    return core.encode_timeseries_v2(
        ts, **architecture_options(architecture, len(ts.values), c_q)
    )


def segment_signature(encoded: bytes) -> tuple[tuple[int, int], ...]:
    (
        _context,
        _n_points,
        segments,
        _coding_type,
    ) = read_lsg2_metadata_and_segments(encoded)

    return tuple((segment.start_idx, segment.end_idx) for segment in segments)


def segment_metrics(
    encoded: bytes,
) -> tuple[int, float, int, int, dict[int, int]]:
    (
        _context,
        _n_points,
        segments,
        _coding_type,
    ) = read_lsg2_metadata_and_segments(encoded)

    if not segments:
        raise ValueError("Non-empty series produced no segments")

    lengths = [segment.end_idx - segment.start_idx + 1 for segment in segments]

    predictor_counts = {0: 0, 1: 0, 2: 0}
    for segment in segments:
        predictor_counts[segment.predictor_type] += 1

    return (
        len(segments),
        sum(lengths) / len(lengths),
        min(lengths),
        max(lengths),
        predictor_counts,
    )


def v2_byte_accounting(encoded: bytes) -> dict[str, int]:
    if len(encoded) < core.FILE_HEADER_STRUCT.size:
        raise ValueError("Encoded stream shorter than V2 file header")

    header = core.FILE_HEADER_STRUCT.unpack_from(encoded, 0)

    version = header[1]
    context_length = header[3]
    segment_count = header[5]

    if version != core.FORMAT_VERSION_V2:
        raise ValueError(f"Expected V2 stream, got version {version}")

    offset = core.FILE_HEADER_STRUCT.size

    context_end = offset + context_length
    if context_end > len(encoded):
        raise ValueError("Context extends beyond encoded stream")
    offset = context_end

    segment_bytes = core.SEGMENT_ENTRY_V2_STRUCT.size * segment_count
    segment_end = offset + segment_bytes
    if segment_end > len(encoded):
        raise ValueError("Segment metadata extends beyond encoded stream")
    offset = segment_end

    residual_header_end = offset + core.RESIDUAL_SECTION_HEADER_STRUCT.size
    if residual_header_end > len(encoded):
        raise ValueError("Residual-section header extends beyond encoded stream")
    offset = residual_header_end

    residual_payload_bytes = 0

    for _ in range(segment_count):
        block_header_end = offset + core.RESIDUAL_BLOCK_HEADER_STRUCT.size
        if block_header_end > len(encoded):
            raise ValueError("Residual block header extends beyond encoded stream")

        _segment_id, _sample_count, payload_length = (
            core.RESIDUAL_BLOCK_HEADER_STRUCT.unpack_from(encoded, offset)
        )
        offset = block_header_end

        payload_end = offset + payload_length
        if payload_end > len(encoded):
            raise ValueError("Residual payload extends beyond encoded stream")

        residual_payload_bytes += payload_length
        offset = payload_end

    if offset != len(encoded):
        raise ValueError(
            f"V2 byte accounting ended at {offset}, " f"stream length is {len(encoded)}"
        )

    global_and_context_bytes = (
        core.FILE_HEADER_STRUCT.size
        + context_length
        + core.RESIDUAL_SECTION_HEADER_STRUCT.size
    )
    segment_metadata_bytes = core.SEGMENT_ENTRY_V2_STRUCT.size * segment_count
    residual_block_metadata_bytes = (
        core.RESIDUAL_BLOCK_HEADER_STRUCT.size * segment_count
    )
    structural_bytes = len(encoded) - residual_payload_bytes

    if (
        global_and_context_bytes
        + segment_metadata_bytes
        + residual_block_metadata_bytes
        + residual_payload_bytes
        != len(encoded)
    ):
        raise ValueError("V2 byte partition does not reconcile")

    return {
        "global_and_context_bytes": global_and_context_bytes,
        "segment_metadata_bytes": segment_metadata_bytes,
        "residual_block_metadata_bytes": residual_block_metadata_bytes,
        "residual_payload_bytes": residual_payload_bytes,
        "structural_bytes": structural_bytes,
    }


def evaluate_point(
    dataset_path: Path,
    evidence_group: str,
    architecture: Architecture,
    c_q: float,
    *,
    repetitions: int,
    warmup: int,
) -> dict[str, object]:
    values = load_csv_values(dataset_path)
    ts = make_timeseries(values)

    def encode() -> bytes:
        return encode_for_architecture(
            ts,
            architecture,
            c_q,
        )

    encoded, encode_time_ms = _measure_deterministic_encode(
        encode,
        repetitions=repetitions,
        warmup=warmup,
    )

    decoded, decode_time_ms = _median_call_ms(
        lambda: core.decode_timeseries(encoded),
        repetitions=repetitions,
        warmup=warmup,
    )

    rmse, max_abs_error = error_metrics(
        values,
        decoded.values,
    )

    (
        segment_count,
        mean_segment_length,
        min_segment_length_observed,
        max_segment_length_observed,
        predictors,
    ) = segment_metrics(encoded)

    accounting = v2_byte_accounting(encoded)

    raw_bytes = len(canonical_float64_bytes(values))
    encoded_bytes = len(encoded)

    return {
        "point_id": point_id(
            dataset_path.name,
            architecture.architecture,
            c_q,
        ),
        "dataset": dataset_path.name,
        "evidence_group": evidence_group,
        "architecture": architecture.architecture,
        "architecture_name": architecture.name,
        "C_Q": c_q,
        "Q_MIN": Q_MIN,
        "n_samples": len(values),
        "raw_bytes": raw_bytes,
        "encoded_bytes": encoded_bytes,
        "bits_per_sample": encoded_bytes * 8.0 / len(values),
        "compression_ratio": raw_bytes / encoded_bytes,
        "mse": rmse * rmse,
        "rmse": rmse,
        "max_abs_error": max_abs_error,
        "segment_count": segment_count,
        "mean_segment_length": mean_segment_length,
        "min_segment_length_observed": min_segment_length_observed,
        "max_segment_length_observed": max_segment_length_observed,
        "mean_predictor_segments": predictors[0],
        "linear_predictor_segments": predictors[1],
        "rw_predictor_segments": predictors[2],
        **accounting,
        "encode_time_ms": encode_time_ms,
        "decode_time_ms": decode_time_ms,
    }


def evaluate_dataset(
    dataset_path: Path,
    evidence_group: str,
    *,
    repetitions: int,
    warmup: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    for c_q in C_Q_VALUES:
        encoded_by_architecture: dict[str, bytes] = {}
        values = load_csv_values(dataset_path)
        ts = make_timeseries(values)

        for architecture in ARCHITECTURES:
            row = evaluate_point(
                dataset_path,
                evidence_group,
                architecture,
                c_q,
                repetitions=repetitions,
                warmup=warmup,
            )
            rows.append(row)

            encoded_by_architecture[architecture.architecture] = (
                encode_for_architecture(
                    ts,
                    architecture,
                    c_q,
                )
            )

        if segment_signature(encoded_by_architecture["A1"]) != segment_signature(
            encoded_by_architecture["A2"]
        ):
            raise ValueError(
                f"{dataset_path.name}: A1/A2 boundary mismatch at C_Q={c_q}"
            )

        if segment_signature(encoded_by_architecture["A3"]) != segment_signature(
            encoded_by_architecture["A4"]
        ):
            raise ValueError(
                f"{dataset_path.name}: A3/A4 boundary mismatch at C_Q={c_q}"
            )

    return rows


def _selection_key(row: dict[str, object]) -> tuple[object, ...]:
    return (
        int(row["encoded_bytes"]),
        float(row["rmse"]),
        float(row["max_abs_error"]),
        float(row["C_Q"]),
        str(row["architecture"]),
        str(row["point_id"]),
    )


def select_envelope_point(
    rows: Iterable[dict[str, object]],
    target_rmse: float,
) -> dict[str, object] | None:
    eligible = [row for row in rows if float(row["rmse"]) <= target_rmse]

    if not eligible:
        return None

    return min(eligible, key=_selection_key)


def classify_rate_ratio(rate_ratio: float) -> str:
    if rate_ratio <= 0.95:
        return "MATERIAL_WIN"
    if rate_ratio >= 1.05:
        return "MATERIAL_LOSS"
    return "PRACTICAL_TIE"


def build_distortion_targets(
    dataset_rows: Sequence[dict[str, object]],
    architectures: Sequence[str],
) -> list[tuple[float, tuple[str, ...]]]:
    """Sorted full-precision union inside the architectures' closed common range."""
    rows_by_architecture = {
        architecture: [
            row for row in dataset_rows if row["architecture"] == architecture
        ]
        for architecture in architectures
    }

    if any(not rows for rows in rows_by_architecture.values()):
        return []

    minimums = {
        architecture: min(float(row["rmse"]) for row in rows)
        for architecture, rows in rows_by_architecture.items()
    }
    maximums = {
        architecture: max(float(row["rmse"]) for row in rows)
        for architecture, rows in rows_by_architecture.items()
    }

    d_min = max(minimums.values())
    d_max = min(maximums.values())

    if d_min > d_max:
        return []

    aliases: dict[float, list[str]] = {}

    for architecture in architectures:
        for row in rows_by_architecture[architecture]:
            rmse = float(row["rmse"])
            if d_min <= rmse <= d_max:
                aliases.setdefault(rmse, []).append(str(row["point_id"]))

    return [
        (
            target,
            tuple(sorted(aliases[target])),
        )
        for target in sorted(aliases)
    ]


def build_primary_targets(
    dataset_rows: Sequence[dict[str, object]],
) -> list[tuple[float, tuple[str, ...]]]:
    return build_distortion_targets(dataset_rows, PRIMARY_ARCHITECTURES)


def match_dataset(
    dataset_rows: Sequence[dict[str, object]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    if not dataset_rows:
        raise ValueError("Cannot match an empty dataset result set")

    dataset = str(dataset_rows[0]["dataset"])
    evidence_group = str(dataset_rows[0]["evidence_group"])

    targets = build_primary_targets(dataset_rows)

    if not targets:
        return [], {
            "dataset": dataset,
            "evidence_group": evidence_group,
            "coverage_status": "INSUFFICIENT_COVERAGE",
            "primary_target_count": 0,
            "A0_covered": 0,
            "A1_covered": 0,
            "A4_covered": 0,
            "complete_primary_coverage": 0,
            "material_wins": 0,
            "practical_ties": 0,
            "material_losses": 0,
            "non_loss_fraction": "",
            "median_rate_ratio": "",
            "best_rate_ratio": "",
            "worst_rate_ratio": "",
        }

    architecture_rows = {
        architecture.architecture: [
            row
            for row in dataset_rows
            if row["architecture"] == architecture.architecture
        ]
        for architecture in ARCHITECTURES
    }

    matched_rows: list[dict[str, object]] = []
    primary_ratios: list[float] = []
    complete_coverage = 0

    coverage = {
        "A0": 0,
        "A1": 0,
        "A4": 0,
    }

    for target_index, (target_rmse, aliases) in enumerate(targets, start=1):
        target_id = f"{dataset}:D{target_index:03d}"

        selected = {
            architecture.architecture: select_envelope_point(
                architecture_rows[architecture.architecture],
                target_rmse,
            )
            for architecture in ARCHITECTURES
        }

        for architecture in PRIMARY_ARCHITECTURES:
            if selected[architecture] is not None:
                coverage[architecture] += 1

        target_complete = all(
            selected[architecture] is not None for architecture in PRIMARY_ARCHITECTURES
        )
        complete_coverage += int(target_complete)
        baseline_candidates = (
            [selected[architecture] for architecture in SIMPLE_BASELINES]
            if target_complete
            else []
        )

        best_baseline = (
            min(baseline_candidates, key=_selection_key)
            if baseline_candidates
            else None
        )

        a4 = selected["A4"]

        primary_ratio: float | None = None
        primary_classification = ""

        if target_complete and best_baseline is not None and a4 is not None:
            primary_ratio = int(a4["encoded_bytes"]) / int(
                best_baseline["encoded_bytes"]
            )
            primary_classification = classify_rate_ratio(primary_ratio)
            primary_ratios.append(primary_ratio)

        for architecture in ARCHITECTURES:
            point = selected[architecture.architecture]

            matched_rows.append(
                {
                    "dataset": dataset,
                    "evidence_group": evidence_group,
                    "target_id": target_id,
                    "target_rmse": target_rmse,
                    "target_aliases": ";".join(aliases),
                    "architecture": architecture.architecture,
                    "architecture_name": architecture.name,
                    "match_status": ("ELIGIBLE" if point is not None else "INELIGIBLE"),
                    "selected_point_id": (
                        point["point_id"] if point is not None else ""
                    ),
                    "selected_C_Q": (point["C_Q"] if point is not None else ""),
                    "selected_rmse": (point["rmse"] if point is not None else ""),
                    "selected_max_abs_error": (
                        point["max_abs_error"] if point is not None else ""
                    ),
                    "selected_encoded_bytes": (
                        point["encoded_bytes"] if point is not None else ""
                    ),
                    "selected_bits_per_sample": (
                        int(point["encoded_bytes"]) * 8.0 / int(point["n_samples"])
                        if point is not None
                        else ""
                    ),
                    "selected_baseline": (
                        best_baseline["architecture"]
                        if (
                            architecture.architecture == "A4"
                            and best_baseline is not None
                        )
                        else ""
                    ),
                    "rate_ratio": (
                        primary_ratio
                        if architecture.architecture == "A4"
                        and primary_ratio is not None
                        else ""
                    ),
                    "classification": (
                        primary_classification
                        if architecture.architecture == "A4"
                        else ""
                    ),
                }
            )

    target_count = len(targets)
    if complete_coverage != target_count:
        coverage_status = "INSUFFICIENT_COVERAGE"
    else:
        coverage_status = "COMPLETE"

    material_wins = sum(
        classify_rate_ratio(value) == "MATERIAL_WIN" for value in primary_ratios
    )
    practical_ties = sum(
        classify_rate_ratio(value) == "PRACTICAL_TIE" for value in primary_ratios
    )
    material_losses = sum(
        classify_rate_ratio(value) == "MATERIAL_LOSS" for value in primary_ratios
    )

    if primary_ratios:
        median_ratio: object = statistics.median(primary_ratios)
        best_ratio: object = min(primary_ratios)
        worst_ratio: object = max(primary_ratios)
        non_loss_fraction: object = (material_wins + practical_ties) / len(
            primary_ratios
        )
    else:
        median_ratio = ""
        best_ratio = ""
        worst_ratio = ""
        non_loss_fraction = ""

    summary = {
        "dataset": dataset,
        "evidence_group": evidence_group,
        "coverage_status": coverage_status,
        "primary_target_count": target_count,
        "A0_covered": coverage["A0"],
        "A1_covered": coverage["A1"],
        "A4_covered": coverage["A4"],
        "complete_primary_coverage": complete_coverage,
        "material_wins": material_wins,
        "practical_ties": practical_ties,
        "material_losses": material_losses,
        "non_loss_fraction": non_loss_fraction,
        "median_rate_ratio": median_ratio,
        "best_rate_ratio": best_ratio,
        "worst_rate_ratio": worst_ratio,
    }

    return matched_rows, summary


def _rejected_decision(
    reason: str,
    accounting_verified: bool,
    *,
    coverage_verified: bool = False,
) -> dict[str, object]:
    return {
        "claim_supported": False,
        "reason": reason,
        "gate_0": coverage_verified,
        "gate_1": None,
        "gate_2": None,
        "gate_3": None,
        "gate_4": None,
        "gate_5": accounting_verified,
    }


def external_decision(
    summaries: Sequence[dict[str, object]],
    *,
    byte_accounting_verified: bool = False,
) -> dict[str, object]:
    external = [row for row in summaries if row["evidence_group"] == "external"]

    if len(external) != 8:
        return _rejected_decision("EXTERNAL_DATASET_COUNT", byte_accounting_verified)

    if {str(row["dataset"]) for row in external} != {
        path.name for path in EXTERNAL_DATASETS
    }:
        return _rejected_decision("EXTERNAL_DATASET_IDENTITY", byte_accounting_verified)

    if any(
        row["coverage_status"] != "COMPLETE"
        or int(row["primary_target_count"]) <= 0
        or int(row["complete_primary_coverage"]) != int(row["primary_target_count"])
        or any(
            int(row[f"{architecture}_covered"]) != int(row["primary_target_count"])
            for architecture in PRIMARY_ARCHITECTURES
        )
        for row in external
    ):
        return _rejected_decision("INSUFFICIENT_COVERAGE", byte_accounting_verified)

    try:
        medians = [float(row["median_rate_ratio"]) for row in external]
    except (TypeError, ValueError, OverflowError):
        return _rejected_decision(
            "INVALID_DATASET_MEDIAN",
            byte_accounting_verified,
            coverage_verified=True,
        )

    if any(not math.isfinite(value) or value <= 0 for value in medians):
        return _rejected_decision(
            "INVALID_DATASET_MEDIAN",
            byte_accounting_verified,
            coverage_verified=True,
        )

    geometric_mean = math.exp(sum(math.log(value) for value in medians) / 8)

    gate_1 = sum(value <= 0.95 for value in medians) >= 6
    gate_2 = geometric_mean <= 0.95
    gate_3 = sum(value >= 1.05 for value in medians) <= 1

    total_targets = sum(int(row["primary_target_count"]) for row in external)
    total_non_losses = sum(
        int(row["material_wins"]) + int(row["practical_ties"]) for row in external
    )

    pooled_non_loss_fraction = (
        total_non_losses / total_targets if total_targets else 0.0
    )
    gate_4 = pooled_non_loss_fraction >= 0.75

    return {
        "claim_supported": (
            gate_1 and gate_2 and gate_3 and gate_4 and byte_accounting_verified
        ),
        "reason": "GATES_EVALUATED",
        "dataset_median_win_count": sum(value <= 0.95 for value in medians),
        "dataset_median_loss_count": sum(value >= 1.05 for value in medians),
        "geometric_mean_dataset_medians": geometric_mean,
        "pooled_non_loss_fraction": pooled_non_loss_fraction,
        "gate_0": True,
        "gate_1": gate_1,
        "gate_2": gate_2,
        "gate_3": gate_3,
        "gate_4": gate_4,
        "gate_5": byte_accounting_verified,
    }


def pareto_frontier(
    rows: Sequence[dict[str, object]],
) -> list[dict[str, object]]:
    """Keep all nondominated IDs, including equal coordinates, in stable order.

    Call with one dataset: its common sample count makes integer encoded bytes
    equivalent to bits/sample. Timing is deliberately absent from this logic.
    """
    if len({(row["dataset"], int(row["n_samples"])) for row in rows}) > 1:
        raise ValueError("Pareto candidates must share a dataset and sample count")
    return sorted(
        [
            candidate
            for candidate in rows
            if not any(
                int(other["encoded_bytes"]) <= int(candidate["encoded_bytes"])
                and float(other["rmse"]) <= float(candidate["rmse"])
                and (
                    int(other["encoded_bytes"]) < int(candidate["encoded_bytes"])
                    or float(other["rmse"]) < float(candidate["rmse"])
                )
                for other in rows
            )
        ],
        key=_selection_key,
    )


def _rate_distortion_point(row: dict[str, object]) -> dict[str, object]:
    return {
        "point_id": row["point_id"],
        "architecture": row["architecture"],
        "C_Q": row["C_Q"],
        "encoded_bytes": int(row["encoded_bytes"]),
        "bits_per_sample": int(row["encoded_bytes"]) * 8.0 / int(row["n_samples"]),
        "rmse": float(row["rmse"]),
    }


def pareto_report(rows: Sequence[dict[str, object]]) -> dict[str, object]:
    return {
        "per_architecture": {
            architecture.architecture: [
                _rate_distortion_point(row)
                for row in pareto_frontier(
                    [
                        row
                        for row in rows
                        if row["architecture"] == architecture.architecture
                    ]
                )
            ]
            for architecture in ARCHITECTURES
        },
        "pooled": [_rate_distortion_point(row) for row in pareto_frontier(rows)],
    }


def descriptive_comparisons(
    rows: Sequence[dict[str, object]],
) -> list[dict[str, object]]:
    """Pair-specific common-range budgets; no interpolation or causal estimates.

    These targets and ratios are independent of primary targets and gates.
    Empty pair ranges remain explicit in the report.
    """
    comparisons = []
    for numerator, denominator in DESCRIPTIVE_PAIRS:
        targets = build_distortion_targets(rows, (numerator, denominator))
        observations = []
        for target, aliases in targets:
            selected = {
                architecture: select_envelope_point(
                    [row for row in rows if row["architecture"] == architecture],
                    target,
                )
                for architecture in (numerator, denominator)
            }
            top, bottom = selected[numerator], selected[denominator]
            complete = top is not None and bottom is not None
            observations.append(
                {
                    "target_rmse": target,
                    "target_aliases": list(aliases),
                    "match_status": "ELIGIBLE" if complete else "INELIGIBLE",
                    "numerator": (
                        _rate_distortion_point(top) if top is not None else None
                    ),
                    "denominator": (
                        _rate_distortion_point(bottom) if bottom is not None else None
                    ),
                    "rate_ratio": (
                        int(top["encoded_bytes"]) / int(bottom["encoded_bytes"])
                        if complete
                        else None
                    ),
                }
            )
        comparisons.append(
            {
                "comparison": f"{numerator}/{denominator}",
                "interpretation": "DESCRIPTIVE_ONLY",
                "coverage_status": (
                    "COMPLETE"
                    if observations
                    and all(row["match_status"] == "ELIGIBLE" for row in observations)
                    else "INSUFFICIENT_COVERAGE"
                ),
                "observations": observations,
            }
        )
    return comparisons


def byte_accounting_verified(rows: Sequence[dict[str, object]]) -> bool:
    if not rows:
        return False
    for row in rows:
        sizes = [
            int(row[field])
            for field in (
                "global_and_context_bytes",
                "segment_metadata_bytes",
                "residual_block_metadata_bytes",
                "residual_payload_bytes",
            )
        ]
        if (
            any(size < 0 for size in sizes)
            or sum(sizes) != int(row["encoded_bytes"])
            or sizes[0] < 44
            or sizes[1] != 32 * int(row["segment_count"])
            or sizes[2] != 12 * int(row["segment_count"])
            or int(row["structural_bytes"]) != sum(sizes[:3])
        ):
            return False
    return True


def dataset_outcome(summary: dict[str, object]) -> str:
    if summary["coverage_status"] != "COMPLETE":
        return "INSUFFICIENT_COVERAGE"
    classification = classify_rate_ratio(float(summary["median_rate_ratio"]))
    return {
        "MATERIAL_WIN": "FAVORABLE",
        "PRACTICAL_TIE": "NEUTRAL",
        "MATERIAL_LOSS": "UNFAVORABLE",
    }[classification]


def build_report(
    rows: Sequence[dict[str, object]],
    matched: Sequence[dict[str, object]],
    summaries: Sequence[dict[str, object]],
    execution_provenance: dict[str, object],
    *,
    execution_completed: bool = False,
) -> dict[str, object]:
    """Build machine-readable study inputs only after measured evidence exists."""
    accounting = byte_accounting_verified(rows)
    decision = external_decision(summaries, byte_accounting_verified=accounting)
    datasets = []
    for summary in summaries:
        dataset_rows = [row for row in rows if row["dataset"] == summary["dataset"]]
        datasets.append(
            {
                "summary": dict(summary),
                "outcome": dataset_outcome(summary),
                "evaluated_points": [
                    _rate_distortion_point(row)
                    for row in sorted(dataset_rows, key=_selection_key)
                ],
                "matched": [
                    row for row in matched if row["dataset"] == summary["dataset"]
                ],
                "pareto": pareto_report(dataset_rows),
                "descriptive_comparisons": descriptive_comparisons(dataset_rows),
            }
        )
    expected_ids = [
        item["point_id"] for item in execution_provenance["execution_order"]
    ]
    full_grid = [row["point_id"] for row in rows] == expected_ids and bool(rows)
    primary_summaries = [
        summary for summary in summaries if summary["evidence_group"] == "external"
    ]
    coverage = len(primary_summaries) == 8 and all(
        summary["coverage_status"] == "COMPLETE"
        and int(summary["primary_target_count"]) > 0
        and int(summary["complete_primary_coverage"])
        == int(summary["primary_target_count"])
        for summary in primary_summaries
    )
    checks = (
        execution_provenance["verified_protocol_freeze_commit"]
        == PROTOCOL_FREEZE_COMMIT,
        execution_completed,
        execution_completed and all(float(row["Q_MIN"]) == Q_MIN for row in rows),
        full_grid,
        execution_completed,  # evaluate_point rejects nondeterministic timed bytes
        accounting,
        coverage,
        execution_completed,  # in-memory matching, with no interpolation
        len(datasets) == len(INTERNAL_DATASETS) + len(EXTERNAL_DATASETS),
        decision["reason"]
        not in ("EXTERNAL_DATASET_COUNT", "EXTERNAL_DATASET_IDENTITY"),
        full_grid and len(datasets) == len(summaries),
        execution_completed
        and all(
            math.isfinite(float(row[field])) and float(row[field]) >= 0
            for row in rows
            for field in ("encode_time_ms", "decode_time_ms")
        )
        and execution_provenance["warmup"] == 1
        and execution_provenance["repetitions"] == 3,
        True,  # unfavorable and incomplete results are serialized without filtering
    )
    gates = dict(zip(REPRODUCIBILITY_GATES, checks))
    supported = decision["claim_supported"] and all(gates.values())
    decision = {
        **decision,
        "statistical_gates_supported": decision["claim_supported"],
        "claim_supported": supported,
    }
    external_outcomes = [
        item["outcome"]
        for item in datasets
        if item["summary"]["evidence_group"] == "external"
    ]
    outcome = (
        "FAVORABLE"
        if supported
        else (
            "INSUFFICIENT_COVERAGE"
            if "INSUFFICIENT_COVERAGE" in external_outcomes
            or decision["reason"]
            in ("EXTERNAL_DATASET_COUNT", "EXTERNAL_DATASET_IDENTITY")
            else (
                "NEUTRAL"
                if external_outcomes and set(external_outcomes) == {"NEUTRAL"}
                else (
                    "UNFAVORABLE"
                    if external_outcomes and set(external_outcomes) == {"UNFAVORABLE"}
                    else "MIXED"
                )
            )
        )
    )
    return {
        "schema_version": 1,
        "execution_completed": execution_completed,
        "primary_claim_supported": supported,
        "outcome": outcome,
        "frozen_gates": gates,
        "decision": decision,
        "datasets": datasets,
        "provenance": execution_provenance,
    }


def render_study(report: dict[str, object]) -> str:
    """Deterministic Markdown for docs/local-model-value-study.md; no evaluation."""
    if not report["execution_completed"] or not report["datasets"]:
        raise ValueError("Study rendering requires completed execution evidence")
    sections = [
        "# Local-model value study",
        f"Execution completed: {report['execution_completed']}",
        f"Primary claim supported: {report['primary_claim_supported']}",
        f"Outcome: {report['outcome']}",
        "Conclusions apply only to the frozen corpus, grid and distortion range.",
        "Descriptive comparisons are not strict causal estimates.",
    ]
    for title, value in (
        ("Frozen gates", report["frozen_gates"]),
        ("Cross-dataset decision", report["decision"]),
        (
            "Per-dataset evidence (including internal sanity results)",
            report["datasets"],
        ),
        ("Execution provenance", report["provenance"]),
    ):
        sections.extend(
            [
                f"## {title}",
                "```json\n"
                + json.dumps(value, sort_keys=True, indent=2, allow_nan=False)
                + "\n```",
            ]
        )
    return "\n\n".join(sections) + "\n"


def write_study(report: dict[str, object], path: Path = STUDY_PATH) -> None:
    """Explicit later rendering step; main deliberately does not invoke this."""
    content = render_study(report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_protocol_freeze() -> str:
    verified = git_output(
        "rev-parse", "--verify", f"{PROTOCOL_FREEZE_COMMIT}^{{commit}}"
    )
    if verified != PROTOCOL_FREEZE_COMMIT:
        raise ValueError("Protocol freeze commit identity mismatch")
    committed = subprocess.check_output(
        ["git", "show", f"{verified}:docs/local-model-value-protocol.md"], cwd=ROOT
    )
    current = PROTOCOL_PATH.read_bytes()
    if committed != current:
        raise ValueError("Protocol freeze content mismatch")
    if (
        b"Status: FROZEN" not in current
        or b"Status: FROZEN BEFORE EXECUTION" in current
    ):
        raise ValueError("Protocol lacks an explicit committed freeze state")
    return verified


def cpu_identity() -> str:
    if platform.system() == "Linux":
        try:
            for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
                key, separator, value = line.partition(":")
                if (
                    separator
                    and key.strip() in ("model name", "Hardware", "Processor")
                    and value.strip()
                ):
                    return value.strip()
        except OSError:
            pass
    return platform.processor().strip() or platform.machine().strip() or "unknown"


def dependency_versions() -> dict[str, object]:
    # The codec uses stdlib only; benchmark_codec imports gorillacompression.
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    project_section = project.split("[project]", 1)[1].split("\n[", 1)[0]
    identity = {}
    for key in ("name", "version"):
        match = re.search(rf'^{key}\s*=\s*"([^"]+)"', project_section, re.MULTILINE)
        if match is None:
            raise ValueError(f"Missing project {key} in pyproject.toml")
        identity[key] = match.group(1)
    versions: dict[str, object] = {
        "project": identity,
        "stdlib": platform.python_version(),
    }
    for package in (identity["name"], "gorillacompression"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "not installed as a distribution"
    return versions


def execution_order(
    corpus: Sequence[tuple[str, Path]],
    repetitions: int,
    warmup: int,
) -> list[dict[str, object]]:
    """Mirror evaluate_dataset's C_Q-major, architecture-minor call order."""
    return [
        {
            "dataset": path.name,
            "dataset_path": str(path),
            "evidence_group": group,
            "architecture": architecture.architecture,
            "C_Q": c_q,
            "point_id": point_id(path.name, architecture.architecture, c_q),
            "operations": [
                {"operation": "encode_warmup", "calls": warmup},
                {"operation": "encode_timed", "calls": repetitions},
                {"operation": "decode_warmup", "calls": warmup},
                {"operation": "decode_timed", "calls": repetitions},
                {"operation": "encode_for_boundary_check", "calls": 1},
            ],
            "boundary_checks_after_point": (
                ["A1=A2", "A3=A4"] if architecture.architecture == "A4" else []
            ),
        }
        for group, path in corpus
        for c_q in C_Q_VALUES
        for architecture in ARCHITECTURES
    ]


def provenance(
    corpus: Sequence[tuple[str, Path]],
    *,
    repetitions: int,
    warmup: int,
    command_line: Sequence[str],
) -> dict[str, object]:
    if repetitions < 1 or warmup < 0:
        raise ValueError("repetitions must be >= 1 and warmup must be >= 0")
    verified = verify_protocol_freeze()
    codec_path = Path(core.__file__).resolve()
    codec_relative = codec_path.relative_to(ROOT)
    return {
        "schema_version": 1,
        "protocol_freeze_commit": PROTOCOL_FREEZE_COMMIT,
        "verified_protocol_freeze_commit": verified,
        "protocol_sha256": sha256_file(PROTOCOL_PATH),
        "implementation_commit": git_output("rev-parse", "HEAD"),
        "codec_source_identity": {
            "path": codec_relative.as_posix(),
            "sha256": sha256_file(codec_path),
        },
        "dirty_tree": bool(
            git_output("status", "--porcelain", "--untracked-files=all")
        ),
        "dataset_sha256": {str(path): sha256_file(path) for _group, path in corpus},
        "architecture_matrix": [asdict(architecture) for architecture in ARCHITECTURES],
        "configurations": {
            architecture.architecture: [
                architecture_options(architecture, "n_samples", c_q)
                for c_q in C_Q_VALUES
            ]
            for architecture in ARCHITECTURES
        },
        "frozen_controls": {
            "wire_format": "V2",
            "residual_coding": "varint",
            "Q_MIN": Q_MIN,
            "C_Q": list(C_Q_VALUES),
            "numeric_contract": "current production-qualified V2 contract",
            "primary_architectures": list(PRIMARY_ARCHITECTURES),
            "primary_baseline_family": list(SIMPLE_BASELINES),
            "material_win_max": 0.95,
            "material_loss_min": 1.05,
            "required_external_datasets": 8,
            "required_median_wins": 6,
            "maximum_median_losses": 1,
            "maximum_geometric_mean": 0.95,
            "minimum_pooled_non_loss_fraction": 0.75,
            "warmup": 1,
            "repetitions": 3,
            "timing_statistic": "median wall-clock time",
            "target_identity": "full-precision measured RMSE",
            "target_range": "closed common observed range of A0/A1/A4",
            "envelope_tie_breaks": [
                "encoded_bytes",
                "rmse",
                "max_abs_error",
                "C_Q",
                "architecture",
                "point_id",
            ],
            "interpolation": False,
            "boundary_pairs": ["A1=A2", "A3=A4"],
            "adaptive_boundary_predictor": "linear",
            "auto_selection": "post-quantization reconstruction MSE before V2 rounding",
            "final_residuals": "recomputed after binary32 segment-metadata rounding",
        },
        "timeseries_context": {
            "dt": CONTEXT_DT,
            "t0": CONTEXT_T0,
            "unit": CONTEXT_UNIT,
        },
        "serialized_context": core.build_context_json(make_timeseries([])).decode(
            "utf-8"
        ),
        "repetitions": repetitions,
        "warmup": warmup,
        "command_line": list(command_line),
        "command": shlex.join(command_line),
        "working_directory": str(Path.cwd()),
        "dataset_order": [
            {"evidence_group": group, "path": str(path)} for group, path in corpus
        ],
        "execution_order": execution_order(corpus, repetitions, warmup),
        "python_executable": sys.executable,
        "python_version": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_identity": cpu_identity(),
        "dependency_versions": dependency_versions(),
    }


def write_json(value: dict[str, object], path: Path) -> None:
    # Serialize first, then persist and verify before callers start evaluation.
    content = json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if path.read_text(encoding="utf-8") != content:
        raise OSError(f"JSON artifact verification failed: {path}")


def write_csv(
    rows: Sequence[dict[str, object]],
    path: Path,
    fieldnames: Sequence[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(rows)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=("Execute the frozen Lasagna 2 local-model-value experiment.")
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=Path("docs/local-model-value-results.csv"),
    )
    parser.add_argument(
        "--matched",
        type=Path,
        default=Path("docs/local-model-value-matched.csv"),
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("docs/local-model-value-summary.csv"),
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

    all_rows: list[dict[str, object]] = []
    matched_rows: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []

    corpus = [("internal", path) for path in INTERNAL_DATASETS] + [
        ("external", path) for path in EXTERNAL_DATASETS
    ]

    execution_provenance = provenance(
        corpus,
        repetitions=args.repetitions,
        warmup=args.warmup,
        command_line=sys.orig_argv,
    )
    write_json(execution_provenance, PROVENANCE_PATH)

    for evidence_group, dataset_path in corpus:
        rows = evaluate_dataset(
            dataset_path,
            evidence_group,
            repetitions=args.repetitions,
            warmup=args.warmup,
        )
        all_rows.extend(rows)

        dataset_matched, dataset_summary = match_dataset(rows)
        matched_rows.extend(dataset_matched)
        summaries.append(dataset_summary)

    write_csv(
        all_rows,
        args.results,
        RAW_FIELDS,
    )
    write_csv(
        matched_rows,
        args.matched,
        MATCHED_FIELDS,
    )
    write_csv(
        summaries,
        args.summary,
        SUMMARY_FIELDS,
    )

    report = build_report(
        all_rows,
        matched_rows,
        summaries,
        execution_provenance,
        execution_completed=True,
    )
    write_json(report, REPORT_PATH)
    decision = report["decision"]

    print(f"PROTOCOL_FREEZE_COMMIT={PROTOCOL_FREEZE_COMMIT}")
    print(f"IMPLEMENTATION_COMMIT={execution_provenance['implementation_commit']}")
    print(f"RAW_POINTS={len(all_rows)}")
    print(f"MATCHED_ROWS={len(matched_rows)}")
    print(f"SUMMARY_ROWS={len(summaries)}")
    print(f"PRIMARY_CLAIM_SUPPORTED={decision['claim_supported']}")
    print(f"PRIMARY_DECISION_REASON={decision['reason']}")
    print("LOCAL_MODEL_VALUE_EXECUTION_COMPLETED=True")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
