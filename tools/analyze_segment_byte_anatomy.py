"""Accounting-only analysis for Lasagna issue #25.

This tool projects a compact logical per-segment representation onto the
already-frozen #24 evidence. It does not re-encode data and does not modify
codec semantics or V2 wire behavior.
"""

from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = ROOT / "docs" / "local-model-value-results.csv"
RESULTS_PATH = ROOT / "docs" / "segment-byte-anatomy-results.csv"
SUMMARY_PATH = ROOT / "docs" / "segment-byte-anatomy-summary.csv"
STUDY_PATH = ROOT / "docs" / "segment-byte-anatomy-study.md"

CURRENT_PER_SEGMENT_BYTES = 44

MEAN_PROJECTED_BYTES = 17
LINEAR_PROJECTED_BYTES = 21
RW_PROJECTED_BYTES = 17

CRITERION_1_MIN = 0.50
CRITERION_2_MIN = 0.15
CRITERION_3_MIN = 0.10

RESULT_FIELDS = (
    "point_id",
    "dataset",
    "evidence_group",
    "architecture",
    "architecture_name",
    "C_Q",
    "n_samples",
    "segment_count",
    "mean_predictor_segments",
    "linear_predictor_segments",
    "rw_predictor_segments",
    "global_and_context_bytes",
    "residual_payload_bytes",
    "current_segment_bytes",
    "projected_segment_bytes",
    "current_structural_bytes",
    "projected_structural_bytes",
    "structural_byte_reduction",
    "structural_reduction_fraction",
    "current_encoded_bytes",
    "projected_encoded_bytes",
    "total_byte_reduction",
    "total_reduction_fraction",
    "projected_rate_ratio",
    "current_structural_fraction",
    "projected_structural_fraction",
    "structural_fraction_decrease",
    "per_segment_overhead_reduction_fraction",
)

SUMMARY_FIELDS = (
    "evidence_group",
    "architecture",
    "row_count",
    "median_segment_count",
    "median_per_segment_overhead_reduction_fraction",
    "median_total_reduction_fraction",
    "median_current_structural_fraction",
    "median_projected_structural_fraction",
    "median_structural_fraction_decrease",
)


def _read_rows(path: Path = INPUT_PATH) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _project_row(row: dict[str, str]) -> dict[str, object]:
    segment_count = int(row["segment_count"])
    mean_count = int(row["mean_predictor_segments"])
    linear_count = int(row["linear_predictor_segments"])
    rw_count = int(row["rw_predictor_segments"])

    if segment_count <= 0:
        raise ValueError("segment_count must be positive")

    if mean_count + linear_count + rw_count != segment_count:
        raise ValueError(f"predictor counts do not reconcile for {row['point_id']}")

    global_bytes = int(row["global_and_context_bytes"])
    residual_payload_bytes = int(row["residual_payload_bytes"])
    current_structural_bytes = int(row["structural_bytes"])
    current_encoded_bytes = int(row["encoded_bytes"])

    current_segment_bytes = CURRENT_PER_SEGMENT_BYTES * segment_count

    if current_structural_bytes != global_bytes + current_segment_bytes:
        raise ValueError(
            f"current structural accounting mismatch for {row['point_id']}"
        )

    if current_encoded_bytes != (current_structural_bytes + residual_payload_bytes):
        raise ValueError(f"current encoded accounting mismatch for {row['point_id']}")

    projected_segment_bytes = (
        mean_count * MEAN_PROJECTED_BYTES
        + linear_count * LINEAR_PROJECTED_BYTES
        + rw_count * RW_PROJECTED_BYTES
    )

    projected_structural_bytes = global_bytes + projected_segment_bytes
    projected_encoded_bytes = projected_structural_bytes + residual_payload_bytes

    structural_byte_reduction = current_structural_bytes - projected_structural_bytes
    total_byte_reduction = current_encoded_bytes - projected_encoded_bytes

    current_structural_fraction = current_structural_bytes / current_encoded_bytes
    projected_structural_fraction = projected_structural_bytes / projected_encoded_bytes

    result: dict[str, object] = {
        "point_id": row["point_id"],
        "dataset": row["dataset"],
        "evidence_group": row["evidence_group"],
        "architecture": row["architecture"],
        "architecture_name": row["architecture_name"],
        "C_Q": row["C_Q"],
        "n_samples": int(row["n_samples"]),
        "segment_count": segment_count,
        "mean_predictor_segments": mean_count,
        "linear_predictor_segments": linear_count,
        "rw_predictor_segments": rw_count,
        "global_and_context_bytes": global_bytes,
        "residual_payload_bytes": residual_payload_bytes,
        "current_segment_bytes": current_segment_bytes,
        "projected_segment_bytes": projected_segment_bytes,
        "current_structural_bytes": current_structural_bytes,
        "projected_structural_bytes": projected_structural_bytes,
        "structural_byte_reduction": structural_byte_reduction,
        "structural_reduction_fraction": (
            structural_byte_reduction / current_structural_bytes
        ),
        "current_encoded_bytes": current_encoded_bytes,
        "projected_encoded_bytes": projected_encoded_bytes,
        "total_byte_reduction": total_byte_reduction,
        "total_reduction_fraction": (total_byte_reduction / current_encoded_bytes),
        "projected_rate_ratio": (projected_encoded_bytes / current_encoded_bytes),
        "current_structural_fraction": current_structural_fraction,
        "projected_structural_fraction": projected_structural_fraction,
        "structural_fraction_decrease": (
            current_structural_fraction - projected_structural_fraction
        ),
        "per_segment_overhead_reduction_fraction": (
            1.0 - projected_segment_bytes / current_segment_bytes
        ),
    }

    if projected_encoded_bytes > current_encoded_bytes:
        raise ValueError(
            f"projection unexpectedly increases bytes for {row['point_id']}"
        )

    return result


def project_rows(
    rows: Iterable[dict[str, str]],
) -> list[dict[str, object]]:
    return [_project_row(row) for row in rows]


def _median(rows: list[dict[str, object]], field: str) -> float:
    return float(statistics.median(float(row[field]) for row in rows))


def summarize(
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[
        tuple[str, str],
        list[dict[str, object]],
    ] = defaultdict(list)

    for row in rows:
        grouped[
            (
                str(row["evidence_group"]),
                str(row["architecture"]),
            )
        ].append(row)

    output: list[dict[str, object]] = []

    for (evidence_group, architecture), group in sorted(grouped.items()):
        output.append(
            {
                "evidence_group": evidence_group,
                "architecture": architecture,
                "row_count": len(group),
                "median_segment_count": _median(
                    group,
                    "segment_count",
                ),
                "median_per_segment_overhead_reduction_fraction": _median(
                    group,
                    "per_segment_overhead_reduction_fraction",
                ),
                "median_total_reduction_fraction": _median(
                    group,
                    "total_reduction_fraction",
                ),
                "median_current_structural_fraction": _median(
                    group,
                    "current_structural_fraction",
                ),
                "median_projected_structural_fraction": _median(
                    group,
                    "projected_structural_fraction",
                ),
                "median_structural_fraction_decrease": _median(
                    group,
                    "structural_fraction_decrease",
                ),
            }
        )

    return output


def decision(
    rows: list[dict[str, object]],
) -> dict[str, object]:
    external_a4 = [
        row
        for row in rows
        if row["evidence_group"] == "external" and row["architecture"] == "A4"
    ]

    if not external_a4:
        raise ValueError("external A4 population is empty")

    criterion_1 = _median(
        rows,
        "per_segment_overhead_reduction_fraction",
    )
    criterion_2 = _median(
        external_a4,
        "total_reduction_fraction",
    )
    criterion_3 = _median(
        external_a4,
        "structural_fraction_decrease",
    )

    gates = (
        criterion_1 >= CRITERION_1_MIN,
        criterion_2 >= CRITERION_2_MIN,
        criterion_3 >= CRITERION_3_MIN,
    )

    if all(gates):
        outcome = "PASS"
    elif criterion_1 >= CRITERION_1_MIN:
        outcome = "PARTIAL"
    else:
        outcome = "FAIL"

    return {
        "criterion_1_median_per_segment_overhead_reduction": criterion_1,
        "criterion_1_pass": gates[0],
        "criterion_2_external_a4_median_total_reduction": criterion_2,
        "criterion_2_pass": gates[1],
        "criterion_3_external_a4_median_structural_fraction_decrease": criterion_3,
        "criterion_3_pass": gates[2],
        "external_a4_rows": len(external_a4),
        "outcome": outcome,
    }


def _write_csv(
    path: Path,
    rows: list[dict[str, object]],
    fields: tuple[str, ...],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _write_study(
    rows: list[dict[str, object]],
    summaries: list[dict[str, object]],
    result: dict[str, object],
) -> None:
    external_a4_summary = next(
        row
        for row in summaries
        if row["evidence_group"] == "external" and row["architecture"] == "A4"
    )

    text = f"""# Segment Byte Anatomy Study

## Status

EXECUTED

## Scope

Accounting-only projection over the frozen #24 result matrix.

No codec bytes were re-encoded.

No V2 wire behavior, predictor semantics, residual payload, segment boundary,
or distortion value was changed.

## Frozen candidate

Projected logical per-segment cost:

```text
mean        17 bytes
linear      21 bytes
random-walk 17 bytes
```

Current V2 fixed cost:

```text
44 bytes / segment
```

## Population

```text
total rows: {len(rows)}
external A4 rows: {result["external_a4_rows"]}
```

## Frozen decision gates

```text
criterion 1
median row-level per-segment fixed-overhead reduction
observed = {float(result["criterion_1_median_per_segment_overhead_reduction"]):.12f}
threshold >= {CRITERION_1_MIN:.2f}
pass = {result["criterion_1_pass"]}

criterion 2
external A4 median projected total encoded-byte reduction
observed = {float(result["criterion_2_external_a4_median_total_reduction"]):.12f}
threshold >= {CRITERION_2_MIN:.2f}
pass = {result["criterion_2_pass"]}

criterion 3
external A4 median structural-fraction decrease
observed = {float(result["criterion_3_external_a4_median_structural_fraction_decrease"]):.12f}
threshold >= {CRITERION_3_MIN:.2f}
pass = {result["criterion_3_pass"]}
```

## External A4 structural economics

```text
median current structural fraction
{float(external_a4_summary["median_current_structural_fraction"]):.12f}

median projected structural fraction
{float(external_a4_summary["median_projected_structural_fraction"]):.12f}

median total encoded-byte reduction
{float(external_a4_summary["median_total_reduction_fraction"]):.12f}
```

## Decision

```text
{result["outcome"]}
```

A PASS means only that the logical compact representation is economically
promising enough to justify a separate wire-layout experiment.

It does not modify or replace V2.
"""

    STUDY_PATH.write_text(text, encoding="utf-8")


def main() -> int:
    source_rows = _read_rows()

    if len(source_rows) != 385:
        raise ValueError(f"expected 385 frozen #24 rows, found {len(source_rows)}")

    rows = project_rows(source_rows)
    summaries = summarize(rows)
    result = decision(rows)

    _write_csv(RESULTS_PATH, rows, RESULT_FIELDS)
    _write_csv(SUMMARY_PATH, summaries, SUMMARY_FIELDS)
    _write_study(rows, summaries, result)

    print(f"ROWS={len(rows)}")
    print(f"SUMMARY_ROWS={len(summaries)}")
    print(f"EXTERNAL_A4_ROWS={result['external_a4_rows']}")
    print(
        "CRITERION_1="
        f"{result['criterion_1_median_per_segment_overhead_reduction']:.12f}"
    )
    print(f"CRITERION_1_PASS={result['criterion_1_pass']}")
    print(
        f"CRITERION_2={result['criterion_2_external_a4_median_total_reduction']:.12f}"
    )
    print(f"CRITERION_2_PASS={result['criterion_2_pass']}")
    print(
        "CRITERION_3="
        f"{result['criterion_3_external_a4_median_structural_fraction_decrease']:.12f}"
    )
    print(f"CRITERION_3_PASS={result['criterion_3_pass']}")
    print(f"OUTCOME={result['outcome']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
