from __future__ import annotations

from argparse import Namespace

import pytest

from lasagna2 import core
from lasagna2 import cli


def _series(n: int = 8) -> core.TimeSeries:
    return core.TimeSeries(
        values=[float(index) for index in range(n)],
        dt=1.0,
        t0="1970-01-01T00:00:00Z",
        unit="test",
    )


def _header(data: bytes) -> list[object]:
    return list(
        core.FILE_HEADER_STRUCT.unpack_from(
            data,
            0,
        )
    )


@pytest.mark.parametrize(
    "encoder",
    [
        core.encode_timeseries_v1,
        core.encode_timeseries_v2,
    ],
)
def test_exact_point_limit_is_accepted(
    monkeypatch: pytest.MonkeyPatch,
    encoder,
) -> None:
    data = encoder(
        _series(4),
        segment_length=4,
        predictor="mean",
        residual_coding="raw",
    )

    monkeypatch.setattr(core, "MAX_POINTS", 4)

    decoded = core.decode_timeseries(data)

    assert len(decoded.values) == 4


@pytest.mark.parametrize(
    "encoder",
    [
        core.encode_timeseries_v1,
        core.encode_timeseries_v2,
    ],
)
def test_point_limit_plus_one_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    encoder,
) -> None:
    data = bytearray(
        encoder(
            _series(4),
            segment_length=4,
            predictor="mean",
            residual_coding="raw",
        )
    )

    header = _header(data)
    header[4] = 5

    core.FILE_HEADER_STRUCT.pack_into(
        data,
        0,
        *header,
    )

    monkeypatch.setattr(core, "MAX_POINTS", 4)

    with pytest.raises(
        ValueError,
        match="n_points=5 exceeds maximum 4",
    ):
        core.decode_timeseries(bytes(data))


def test_v2_segment_limit_rejected_before_widening(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = bytearray(
        core.encode_timeseries_v2(
            _series(4),
            segment_length=4,
            predictor="mean",
            residual_coding="raw",
        )
    )

    header = _header(data)
    header[5] = 2

    core.FILE_HEADER_STRUCT.pack_into(
        data,
        0,
        *header,
    )

    monkeypatch.setattr(core, "MAX_SEGMENTS", 1)

    with pytest.raises(
        ValueError,
        match="n_segments=2 exceeds maximum 1",
    ):
        core.decode_timeseries(bytes(data))


def test_context_limit_exact_and_plus_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = core.encode_timeseries_v2(
        _series(4),
        predictor="mean",
        residual_coding="raw",
    )

    header_len = int(_header(data)[3])

    monkeypatch.setattr(
        core,
        "MAX_CONTEXT_BYTES",
        header_len,
    )

    core.decode_timeseries(data)

    monkeypatch.setattr(
        core,
        "MAX_CONTEXT_BYTES",
        header_len - 1,
    )

    with pytest.raises(
        ValueError,
        match="Context JSON exceeds maximum size",
    ):
        core.decode_timeseries(data)


def test_context_depth_limit_respects_json_strings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        core,
        "MAX_CONTEXT_DEPTH",
        2,
    )

    core._validate_context_bytes(b'{"x":"[[[\\\\\\"]]]"}')

    with pytest.raises(
        ValueError,
        match="maximum nesting depth",
    ):
        core._validate_context_bytes(b'{"x":[[0]]}')


def test_residual_block_limit_checked_before_payload_decode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = core.encode_timeseries_v2(
        _series(4),
        segment_length=4,
        predictor="mean",
        residual_coding="raw",
    )

    (
        _magic,
        _version,
        _flags,
        header_len,
        _n_points,
        n_segments,
        _r1,
        _r2,
    ) = core.FILE_HEADER_STRUCT.unpack_from(
        data,
        0,
    )

    offset = (
        core.FILE_HEADER_STRUCT.size
        + header_len
        + n_segments * core.SEGMENT_ENTRY_V2_STRUCT.size
        + core.RESIDUAL_SECTION_HEADER_STRUCT.size
    )

    (
        _seg_id,
        _seg_len,
        byte_len,
    ) = core.RESIDUAL_BLOCK_HEADER_STRUCT.unpack_from(
        data,
        offset,
    )

    monkeypatch.setattr(
        core,
        "MAX_RESIDUAL_BLOCK_BYTES",
        byte_len,
    )

    core.decode_timeseries(data)

    monkeypatch.setattr(
        core,
        "MAX_RESIDUAL_BLOCK_BYTES",
        byte_len - 1,
    )

    with pytest.raises(
        ValueError,
        match="Residual block exceeds maximum size",
    ):
        core.decode_timeseries(data)


def test_input_limit_exact_and_plus_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = core.encode_timeseries_v2(
        _series(4),
        predictor="mean",
        residual_coding="raw",
    )

    monkeypatch.setattr(
        core,
        "MAX_INPUT_BYTES",
        len(data),
    )

    core.decode_timeseries(data)

    monkeypatch.setattr(
        core,
        "MAX_INPUT_BYTES",
        len(data) - 1,
    )

    with pytest.raises(
        ValueError,
        match="LSG2 input exceeds maximum size",
    ):
        core.decode_timeseries(data)


def test_v2_widened_bytes_do_not_reuse_external_input_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = core.encode_timeseries_v2(
        _series(4),
        segment_length=4,
        predictor="mean",
        residual_coding="raw",
    )

    monkeypatch.setattr(
        core,
        "MAX_INPUT_BYTES",
        len(data),
    )

    decoded = core.decode_timeseries(data)

    assert len(decoded.values) == 4


@pytest.mark.parametrize(
    "encoder",
    [
        core.encode_timeseries_v1,
        core.encode_timeseries_v2,
        core.encode_timeseries,
    ],
)
def test_encoder_point_limit(
    monkeypatch: pytest.MonkeyPatch,
    encoder,
) -> None:
    monkeypatch.setattr(
        core,
        "MAX_POINTS",
        3,
    )

    with pytest.raises(
        ValueError,
        match="n_points=4 exceeds maximum 3",
    ):
        encoder(
            _series(4),
            predictor="mean",
            residual_coding="raw",
        )


def test_uint32_endpoint_rejected_without_large_allocation() -> None:
    data = bytearray(
        core.encode_timeseries_v1(
            _series(4),
            segment_length=4,
            predictor="mean",
            residual_coding="raw",
        )
    )

    (
        _magic,
        _version,
        _flags,
        header_len,
        _n_points,
        _n_segments,
        _r1,
        _r2,
    ) = core.FILE_HEADER_STRUCT.unpack_from(
        data,
        0,
    )

    segment_offset = core.FILE_HEADER_STRUCT.size + header_len

    segment = list(
        core.SEGMENT_ENTRY_STRUCT.unpack_from(
            data,
            segment_offset,
        )
    )

    segment[1] = core.UINT32_MAX

    core.SEGMENT_ENTRY_STRUCT.pack_into(
        data,
        segment_offset,
        *segment,
    )

    with pytest.raises(
        ValueError,
        match="Segment extent exceeds declared point count",
    ):
        core.decode_timeseries(bytes(data))


def test_residual_declared_count_must_match_segment() -> None:
    data = bytearray(
        core.encode_timeseries_v1(
            _series(4),
            segment_length=4,
            predictor="mean",
            residual_coding="raw",
        )
    )

    (
        _magic,
        _version,
        _flags,
        header_len,
        _n_points,
        n_segments,
        _r1,
        _r2,
    ) = core.FILE_HEADER_STRUCT.unpack_from(
        data,
        0,
    )

    block_offset = (
        core.FILE_HEADER_STRUCT.size
        + header_len
        + n_segments * core.SEGMENT_ENTRY_STRUCT.size
        + core.RESIDUAL_SECTION_HEADER_STRUCT.size
    )

    seg_id, _seg_len, byte_len = core.RESIDUAL_BLOCK_HEADER_STRUCT.unpack_from(
        data,
        block_offset,
    )

    core.RESIDUAL_BLOCK_HEADER_STRUCT.pack_into(
        data,
        block_offset,
        seg_id,
        core.UINT32_MAX,
        byte_len,
    )

    with pytest.raises(
        ValueError,
        match="Residual sample count does not match",
    ):
        core.decode_timeseries(bytes(data))


def test_duplicate_residual_segment_id_is_rejected() -> None:
    data = bytearray(
        core.encode_timeseries_v1(
            _series(8),
            segment_length=4,
            predictor="mean",
            residual_coding="raw",
        )
    )

    (
        _magic,
        _version,
        _flags,
        header_len,
        _n_points,
        n_segments,
        _r1,
        _r2,
    ) = core.FILE_HEADER_STRUCT.unpack_from(
        data,
        0,
    )

    offset = (
        core.FILE_HEADER_STRUCT.size
        + header_len
        + n_segments * core.SEGMENT_ENTRY_STRUCT.size
        + core.RESIDUAL_SECTION_HEADER_STRUCT.size
    )

    first = core.RESIDUAL_BLOCK_HEADER_STRUCT.unpack_from(
        data,
        offset,
    )

    first_block_size = core.RESIDUAL_BLOCK_HEADER_STRUCT.size + first[2]

    second_offset = offset + first_block_size

    second = list(
        core.RESIDUAL_BLOCK_HEADER_STRUCT.unpack_from(
            data,
            second_offset,
        )
    )

    second[0] = first[0]

    core.RESIDUAL_BLOCK_HEADER_STRUCT.pack_into(
        data,
        second_offset,
        *second,
    )

    with pytest.raises(
        ValueError,
        match="Duplicate residual block",
    ):
        core.decode_timeseries(bytes(data))


def test_cli_bounded_reader_rejects_oversized_file(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "oversized.lsg2"
    path.write_bytes(b"12345")

    monkeypatch.setattr(
        cli,
        "MAX_INPUT_BYTES",
        4,
    )

    with pytest.raises(
        ValueError,
        match="LSG2 input exceeds maximum size",
    ):
        cli._read_lsg2_bounded(path)


def test_cli_decode_uses_bounded_reader(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_path = tmp_path / "input.lsg2"
    output_path = tmp_path / "output.csv"

    input_path.write_bytes(
        core.encode_timeseries_v2(
            _series(4),
            predictor="mean",
            residual_coding="raw",
        )
    )

    seen = []

    original = cli._read_lsg2_bounded

    def tracked(path):
        seen.append(path)
        return original(path)

    monkeypatch.setattr(
        cli,
        "_read_lsg2_bounded",
        tracked,
    )

    cli.cli_decode(
        Namespace(
            input=str(input_path),
            output=str(output_path),
        )
    )

    assert seen == [input_path]
    assert output_path.exists()
