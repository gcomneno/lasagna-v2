import struct

import pytest
from lasagna2 import core


def _header(data: bytes):
    return core.FILE_HEADER_STRUCT.unpack_from(
        data,
        0,
    )


def test_explicit_v1_encoder_still_emits_version_1() -> None:
    ts = core.TimeSeries(
        values=[1.0, 2.0, 3.0, 4.0],
        dt=1.0,
        t0="1970-01-01T00:00:00Z",
        unit="test",
    )

    encoded = core.encode_timeseries_v1(
        ts,
        segment_length=4,
        predictor="linear",
        residual_coding="raw",
    )

    assert _header(encoded)[1] == core.FORMAT_VERSION_V1


def test_default_encoder_emits_version_2() -> None:
    ts = core.TimeSeries(
        values=[1.0, 2.0, 3.0, 4.0],
        dt=1.0,
        t0="1970-01-01T00:00:00Z",
        unit="test",
    )

    default_bytes = core.encode_timeseries(
        ts,
        segment_length=4,
        predictor="linear",
        residual_coding="raw",
    )
    explicit_v2_bytes = core.encode_timeseries_v2(
        ts,
        segment_length=4,
        predictor="linear",
        residual_coding="raw",
    )

    assert _header(default_bytes)[1] == core.FORMAT_VERSION_V2
    assert default_bytes == explicit_v2_bytes


def test_v2_linear_raw_byte_layout() -> None:
    ts = core.TimeSeries(
        values=[1.0, 2.0, 3.0, 4.0],
        dt=1.0,
        t0="1970-01-01T00:00:00Z",
        unit="test",
    )

    encoded = core.encode_timeseries_v2(
        ts,
        segment_length=4,
        predictor="linear",
        C_Q=0.5,
        Q_MIN=1e-6,
        segment_mode="fixed",
        residual_coding="raw",
    )

    (
        magic,
        version,
        flags,
        header_len,
        n_points,
        n_segments,
        reserved1,
        reserved2,
    ) = _header(encoded)

    assert magic == b"LSG2"
    assert version == core.FORMAT_VERSION_V2
    assert flags == 0
    assert n_points == 4
    assert n_segments == 1
    assert reserved1 == 0
    assert reserved2 == 0

    context = core.build_context_json(ts)

    assert header_len == len(context)

    segment_offset = core.FILE_HEADER_STRUCT.size + header_len

    expected_entry = core.SEGMENT_ENTRY_V2_STRUCT.pack(
        0,
        3,
        1,
        2.5,
        1.0,
        1.0,
        1e-6,
        1.0,
    )

    actual_entry = encoded[
        segment_offset : segment_offset + core.SEGMENT_ENTRY_V2_STRUCT.size
    ]

    assert actual_entry == expected_entry
    assert len(actual_entry) == 32

    residual_header_offset = segment_offset + core.SEGMENT_ENTRY_V2_STRUCT.size

    assert core.RESIDUAL_SECTION_HEADER_STRUCT.unpack_from(
        encoded,
        residual_header_offset,
    ) == (core.RESIDUAL_CODEC_RAW_INT32, 0, 0, 0)

    block_offset = residual_header_offset + core.RESIDUAL_SECTION_HEADER_STRUCT.size

    assert core.RESIDUAL_BLOCK_HEADER_STRUCT.unpack_from(
        encoded,
        block_offset,
    ) == (0, 4, 16)

    payload_offset = block_offset + core.RESIDUAL_BLOCK_HEADER_STRUCT.size

    assert encoded[payload_offset:] == (
        struct.pack(
            "<4i",
            0,
            0,
            0,
            0,
        )
    )

    expected_size = (
        core.FILE_HEADER_STRUCT.size
        + len(context)
        + 32
        + core.RESIDUAL_SECTION_HEADER_STRUCT.size
        + core.RESIDUAL_BLOCK_HEADER_STRUCT.size
        + 16
    )

    assert len(encoded) == expected_size

    decoded = core.decode_timeseries(encoded)

    assert decoded.values == pytest.approx(
        ts.values,
        rel=0.0,
        abs=1e-6,
    )


@pytest.mark.parametrize(
    ("predictor", "values"),
    [
        ("mean", [2.0] * 8),
        (
            "linear",
            [1.0 + 0.5 * index for index in range(8)],
        ),
        ("rw", [3.0] * 8),
        (
            "auto",
            [1.0 + 0.5 * index for index in range(8)],
        ),
    ],
)
@pytest.mark.parametrize(
    "residual_coding",
    ["raw", "varint"],
)
def test_v2_roundtrip_supported_modes(
    predictor: str,
    values: list[float],
    residual_coding: str,
) -> None:
    ts = core.TimeSeries(
        values=values,
        dt=0.25,
        t0="2026-10-02T00:00:00Z",
        unit="test-unit",
    )

    encoded = core.encode_timeseries_v2(
        ts,
        segment_length=len(values),
        predictor=predictor,
        segment_mode="fixed",
        residual_coding=residual_coding,
    )

    assert _header(encoded)[1] == (core.FORMAT_VERSION_V2)

    decoded = core.decode_timeseries(encoded)

    assert decoded.dt == ts.dt
    assert decoded.t0 == ts.t0
    assert decoded.unit == ts.unit

    assert decoded.values == pytest.approx(
        ts.values,
        rel=0.0,
        abs=2e-6,
    )


def test_public_decoder_preserves_v1_path() -> None:
    ts = core.TimeSeries(
        values=[
            0.25,
            0.5,
            0.75,
            1.0,
        ],
        dt=1.0,
        t0="v1",
        unit="unit",
    )

    encoded = core.encode_timeseries_v1(
        ts,
        segment_length=4,
        predictor="linear",
        residual_coding="varint",
    )

    historical = core._decode_timeseries_v1(encoded)

    dispatched = core.decode_timeseries(encoded)

    assert dispatched == historical


def test_unknown_version_fails_closed() -> None:
    ts = core.TimeSeries(
        values=[1.0, 2.0],
    )

    encoded = bytearray(
        core.encode_timeseries(
            ts,
            segment_length=2,
            predictor="linear",
        )
    )

    struct.pack_into(
        "<H",
        encoded,
        4,
        65535,
    )

    with pytest.raises(
        ValueError,
        match=(r"Unsupported LSG2 version 65535"),
    ):
        core.decode_timeseries(bytes(encoded))


def test_v2_rejects_q_that_rounds_to_zero() -> None:
    ts = core.TimeSeries(
        values=[1.0] * 4,
    )

    with pytest.raises(
        ValueError,
        match=(r"quantization step Q " r"must be finite and > 0"),
    ):
        core.encode_timeseries_v2(
            ts,
            segment_length=4,
            predictor="mean",
            C_Q=0.0,
            Q_MIN=1e-50,
            segment_mode="fixed",
        )
