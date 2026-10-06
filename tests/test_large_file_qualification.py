from __future__ import annotations

import sys
from pathlib import Path

import pytest

from lasagna2 import core

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import qualify_large_file as qlf  # noqa: E402


def test_dense_v2_small_roundtrip() -> None:
    data = qlf.build_dense_v2(100)

    decoded = core.decode_timeseries(data)

    assert len(decoded.values) == 100
    assert decoded.values == [0.0] * 100


def test_dense_v2_layout_size() -> None:
    count = 100

    data = qlf.build_dense_v2(count)

    header = core.FILE_HEADER_STRUCT.unpack_from(
        data,
        0,
    )

    context_len = header[3]

    expected = (
        core.FILE_HEADER_STRUCT.size
        + context_len
        + count * core.SEGMENT_ENTRY_V2_STRUCT.size
        + core.RESIDUAL_SECTION_HEADER_STRUCT.size
        + count * (core.RESIDUAL_BLOCK_HEADER_STRUCT.size + 4)
    )

    assert len(data) == expected


def test_dense_v2_rejects_segment_limit_plus_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        core,
        "MAX_SEGMENTS",
        10,
    )

    with pytest.raises(
        ValueError,
        match="segment_count=11 exceeds maximum 10",
    ):
        qlf.build_dense_v2(11)


def test_boundary_checks_pass() -> None:
    checks = qlf.run_boundary_checks()

    assert checks
    assert all(check["status"] == "PASS" for check in checks)


def test_scaling_ratios() -> None:
    rows = [
        {
            "n_points": 100,
            "encode_ms": 10.0,
            "decode_ms": 5.0,
            "encode_peak_rss_kib": 1000,
            "decode_peak_rss_kib": 2000,
        },
        {
            "n_points": 200,
            "encode_ms": 20.0,
            "decode_ms": 10.0,
            "encode_peak_rss_kib": 2000,
            "decode_peak_rss_kib": 4000,
        },
    ]

    ratios = qlf.scaling_ratios(rows)

    assert len(ratios) == 1
    assert ratios[0]["point_ratio"] == pytest.approx(2.0)
    assert ratios[0]["encode_time_ratio"] == pytest.approx(2.0)
    assert ratios[0]["decode_time_ratio"] == pytest.approx(2.0)
    assert ratios[0]["encode_rss_ratio"] == pytest.approx(2.0)
    assert ratios[0]["decode_rss_ratio"] == pytest.approx(2.0)
