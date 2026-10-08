from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "analyze_segment_byte_anatomy.py"

SPEC = importlib.util.spec_from_file_location(
    "analyze_segment_byte_anatomy",
    MODULE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load analyze_segment_byte_anatomy")

analysis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analysis)


def _row(
    *,
    segment_count: int,
    mean_count: int,
    linear_count: int,
    rw_count: int,
    global_bytes: int = 60,
    residual_bytes: int = 100,
) -> dict[str, str]:
    current_structural = global_bytes + 44 * segment_count
    encoded = current_structural + residual_bytes

    return {
        "point_id": "synthetic:A4:cq=0.5",
        "dataset": "synthetic.csv",
        "evidence_group": "external",
        "architecture": "A4",
        "architecture_name": "adaptive_auto",
        "C_Q": "0.5",
        "n_samples": "128",
        "segment_count": str(segment_count),
        "mean_predictor_segments": str(mean_count),
        "linear_predictor_segments": str(linear_count),
        "rw_predictor_segments": str(rw_count),
        "global_and_context_bytes": str(global_bytes),
        "residual_payload_bytes": str(residual_bytes),
        "structural_bytes": str(current_structural),
        "encoded_bytes": str(encoded),
    }


@pytest.mark.parametrize(
    ("mean_count", "linear_count", "rw_count", "expected"),
    (
        (1, 0, 0, 17),
        (0, 1, 0, 21),
        (0, 0, 1, 17),
    ),
)
def test_predictor_specific_projection(
    mean_count: int,
    linear_count: int,
    rw_count: int,
    expected: int,
) -> None:
    result = analysis._project_row(
        _row(
            segment_count=1,
            mean_count=mean_count,
            linear_count=linear_count,
            rw_count=rw_count,
        )
    )

    assert result["projected_segment_bytes"] == expected


def test_projection_reconciles_total_bytes() -> None:
    result = analysis._project_row(
        _row(
            segment_count=3,
            mean_count=1,
            linear_count=1,
            rw_count=1,
            global_bytes=50,
            residual_bytes=80,
        )
    )

    assert result["projected_segment_bytes"] == 55
    assert result["projected_structural_bytes"] == 105
    assert result["projected_encoded_bytes"] == 185
    assert result["current_encoded_bytes"] == 262
    assert result["total_byte_reduction"] == 77


def test_predictor_counts_must_reconcile() -> None:
    with pytest.raises(
        ValueError,
        match="predictor counts do not reconcile",
    ):
        analysis._project_row(
            _row(
                segment_count=2,
                mean_count=1,
                linear_count=0,
                rw_count=0,
            )
        )


def test_frozen_result_matrix_projects_completely() -> None:
    source = analysis._read_rows()

    assert len(source) == 385

    projected = analysis.project_rows(source)

    assert len(projected) == 385
    assert all(
        int(row["projected_encoded_bytes"]) <= int(row["current_encoded_bytes"])
        for row in projected
    )


def test_frozen_matrix_has_expected_external_a4_population() -> None:
    projected = analysis.project_rows(analysis._read_rows())

    external_a4 = [
        row
        for row in projected
        if row["evidence_group"] == "external" and row["architecture"] == "A4"
    ]

    assert len(external_a4) == 56
