import pytest

from lasagna2 import core


def _timeseries(values: list[float]) -> core.TimeSeries:
    return core.TimeSeries(
        values=values,
        dt=1.0,
        t0="1970-01-01T00:00:00Z",
        unit="test",
    )


def _coding_type(data: bytes) -> int:
    (
        _magic,
        version,
        _flags,
        header_len,
        _n_points,
        n_segments,
        _reserved1,
        _reserved2,
    ) = core.FILE_HEADER_STRUCT.unpack_from(
        data,
        0,
    )

    assert version == core.FORMAT_VERSION_V2

    offset = (
        core.FILE_HEADER_STRUCT.size
        + header_len
        + (
            n_segments
            * core.SEGMENT_ENTRY_V2_STRUCT.size
        )
    )

    (
        coding_type,
        _reserved1,
        _reserved2,
        _reserved3,
    ) = core.RESIDUAL_SECTION_HEADER_STRUCT.unpack_from(
        data,
        offset,
    )

    return coding_type


def test_zero_run_helper_roundtrip() -> None:
    values = [
        1,
        0,
        0,
        0,
        0,
        -1,
        -64,
        64,
    ]

    encoded = (
        core.encode_int_list_zero_run_varint(
            values
        )
    )

    assert (
        core.decode_int_list_zero_run_varint(
            encoded,
            len(values),
        )
        == values
    )


def test_zero_run_decoder_rejects_short_run() -> None:
    payload = (
        core._encode_varint(0)
        + core._encode_varint(2)
    )

    with pytest.raises(
        ValueError,
        match="Invalid zero-run length",
    ):
        core.decode_int_list_zero_run_varint(
            payload,
            2,
        )


def test_v2_explicit_zero_run_roundtrip() -> None:
    ts = _timeseries(
        [
            0.1 * index
            for index in range(200)
        ]
    )

    encoded = core.encode_timeseries_v2(
        ts,
        predictor="linear",
        segment_mode="adaptive",
        residual_coding="zero-run",
    )

    assert _coding_type(encoded) == (
        core.RESIDUAL_CODEC_ZERO_RUN_VARINT
    )

    decoded = core.decode_timeseries(
        encoded
    )

    assert len(decoded.values) == len(ts.values)


def test_v2_auto_selects_zero_run_when_smaller() -> None:
    ts = _timeseries(
        [
            0.1 * index
            for index in range(200)
        ]
    )

    encoded_auto = core.encode_timeseries_v2(
        ts,
        predictor="linear",
        segment_mode="adaptive",
        residual_coding="auto",
    )

    encoded_varint = core.encode_timeseries_v2(
        ts,
        predictor="linear",
        segment_mode="adaptive",
        residual_coding="varint",
    )

    assert _coding_type(encoded_auto) == (
        core.RESIDUAL_CODEC_ZERO_RUN_VARINT
    )

    assert len(encoded_auto) < len(
        encoded_varint
    )


def test_v2_auto_never_exceeds_varint_size() -> None:
    cases = [
        [0.1 * index for index in range(200)],
        [
            float(index % 11)
            for index in range(300)
        ],
        [
            10.0
            if index % 37
            else 100.0
            for index in range(300)
        ],
    ]

    for values in cases:
        ts = _timeseries(values)

        auto = core.encode_timeseries_v2(
            ts,
            predictor="auto",
            segment_mode="adaptive",
            residual_coding="auto",
        )

        varint = core.encode_timeseries_v2(
            ts,
            predictor="auto",
            segment_mode="adaptive",
            residual_coding="varint",
        )

        assert len(auto) <= len(varint)


def test_v1_encoder_contract_remains_raw_or_varint() -> None:
    ts = _timeseries(
        [
            float(index)
            for index in range(64)
        ]
    )

    for residual_coding in (
        "zero-run",
        "auto",
    ):
        with pytest.raises(
            ValueError,
            match="expected 'raw' or 'varint'",
        ):
            core.encode_timeseries_v1(
                ts,
                residual_coding=residual_coding,
            )


def test_zero_run_worst_case_is_decodable() -> None:
    values = [-64] * 128

    varint = core.encode_int_list_varint(
        values
    )

    zero_run = (
        core.encode_int_list_zero_run_varint(
            values
        )
    )

    assert len(zero_run) == 2 * len(varint)

    assert (
        core.decode_int_list_zero_run_varint(
            zero_run,
            len(values),
        )
        == values
    )
