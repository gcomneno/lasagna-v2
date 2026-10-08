from __future__ import annotations

import struct
from dataclasses import dataclass

import pytest

from lasagna2 import core
from lasagna2 import experimental_compact as compact


def _sample_values() -> list[float]:
    return [
        10.0,
        10.25,
        10.5,
        11.0,
        10.75,
        10.25,
        9.5,
        9.75,
        10.0,
        10.5,
        11.25,
        11.0,
    ]


def _ts() -> core.TimeSeries:
    return core.TimeSeries(
        values=_sample_values(),
        dt=0.25,
        t0="2026-10-08T00:00:00Z",
        unit="compact-test",
    )


def _bits(values: list[float]) -> bytes:
    return struct.pack(f"<{len(values)}d", *values)


# These readers deliberately use the frozen wire grammar, not the prototype's
# structs, repacker, payload decoders, or metadata extraction helpers.
@dataclass
class _WireSegment:
    start: int
    end: int
    tag: int
    q_bits: bytes
    parameter_bits: tuple[bytes, ...]
    payload: bytes
    residuals: list[int]
    record_offset: int
    payload_offset: int


@dataclass
class _Wire:
    context: bytes
    n_points: int
    coding: int
    segments: list[_WireSegment]
    eof: int


def _read_residuals(payload: bytes, coding: int, count: int) -> list[int]:
    if coding == 0:
        assert len(payload) == 4 * count
        return list(struct.unpack(f"<{count}i", payload))

    tokens = []
    value = shift = 0
    for byte in payload:
        value |= (byte & 127) << shift
        if byte & 128:
            shift += 7
        else:
            tokens.append(value)
            value = shift = 0
    assert shift == 0, "Oracle encountered an incomplete token"
    residuals = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        if coding == 2 and token == 0:
            run = tokens[index]
            index += 1
            assert run >= 3
            residuals.extend([0] * run)
        else:
            unsigned = token if coding == 1 else token - 1
            residuals.append((unsigned >> 1) ^ -(unsigned & 1))
    assert len(residuals) == count
    assert all(-(2**31) <= value < 2**31 for value in residuals)
    return residuals


def _read_wire(data: bytes, *, version: int) -> _Wire:
    magic, actual_version, flags, context_len, points, count, r1, r2 = (
        struct.unpack_from("<4sHHIIIII", data)
    )
    assert (magic, actual_version, flags, r1, r2) == (b"LSG2", version, 0, 0, 0)
    context = data[28 : 28 + context_len]
    cursor = 28 + context_len
    segments = []
    if version == 2:
        coding_offset = cursor + 32 * count
        coding, *reserved = struct.unpack_from("<IIII", data, coding_offset)
        assert reserved == [0, 0, 0]
        payload_cursor = coding_offset + 16
        for index in range(count):
            record_offset = cursor + 32 * index
            start, end, tag = struct.unpack_from("<III", data, record_offset)
            parameter_offsets = {0: (12,), 1: (16, 20), 2: (28,)}[tag]
            seg_id, length, payload_len = struct.unpack_from(
                "<III", data, payload_cursor
            )
            assert (seg_id, length) == (index, end - start + 1)
            payload_offset = payload_cursor + 12
            payload = data[payload_offset : payload_offset + payload_len]
            assert len(payload) == payload_len
            segments.append(
                _WireSegment(
                    start,
                    end,
                    tag,
                    data[record_offset + 24 : record_offset + 28],
                    tuple(
                        data[record_offset + p : record_offset + p + 4]
                        for p in parameter_offsets
                    ),
                    payload,
                    _read_residuals(payload, coding, length),
                    record_offset,
                    payload_offset,
                )
            )
            payload_cursor = payload_offset + payload_len
        cursor = payload_cursor
    else:
        assert version == 3
        coding, *reserved = struct.unpack_from("<IIII", data, cursor)
        assert reserved == [0, 0, 0]
        cursor += 16
        start = 0
        for _ in range(count):
            length, tag, _q, payload_len = struct.unpack_from("<IBfI", data, cursor)
            record_size = {0: 17, 1: 21, 2: 17}[tag]
            payload_offset = cursor + record_size
            payload = data[payload_offset : payload_offset + payload_len]
            assert len(payload) == payload_len
            segments.append(
                _WireSegment(
                    start,
                    start + length - 1,
                    tag,
                    data[cursor + 5 : cursor + 9],
                    tuple(
                        data[p : p + 4] for p in range(cursor + 13, payload_offset, 4)
                    ),
                    payload,
                    _read_residuals(payload, coding, length),
                    cursor,
                    payload_offset,
                )
            )
            start += length
            cursor = payload_offset + payload_len
        assert start == points
    assert cursor == len(data)
    return _Wire(context, points, coding, segments, cursor)


def _assert_accounting(data: bytes, wire: _Wire) -> None:
    counts = [sum(seg.tag == tag for seg in wire.segments) for tag in (0, 1, 2)]
    assert len(data) == (
        28
        + len(wire.context)
        + 16
        + 17 * counts[0]
        + 21 * counts[1]
        + 17 * counts[2]
        + sum(len(seg.payload) for seg in wire.segments)
    )
    cursor = 28 + len(wire.context) + 16
    for seg in wire.segments:
        assert seg.record_offset == cursor
        assert seg.payload_offset == cursor + (21 if seg.tag == 1 else 17)
        cursor = seg.payload_offset + len(seg.payload)
    assert cursor == wire.eof == len(data)


def _assert_equivalent(v2: bytes, encoded: bytes) -> tuple[_Wire, _Wire]:
    baseline = _read_wire(v2, version=2)
    experimental = _read_wire(encoded, version=3)
    assert experimental.context == baseline.context
    assert experimental.n_points == baseline.n_points
    assert experimental.coding == baseline.coding
    assert len(experimental.segments) == len(baseline.segments)
    for expected, actual in zip(baseline.segments, experimental.segments, strict=True):
        assert (actual.start, actual.end) == (expected.start, expected.end)
        assert actual.tag == expected.tag
        assert actual.q_bits == expected.q_bits
        assert actual.parameter_bits == expected.parameter_bits
        assert actual.residuals == expected.residuals
        assert actual.payload == expected.payload
    decoded_v2 = core.decode_timeseries(v2)
    decoded_compact = compact.decode_timeseries_compact_experimental(encoded)
    assert _bits(decoded_compact.values) == _bits(decoded_v2.values)
    assert (decoded_compact.dt, decoded_compact.t0, decoded_compact.unit) == (
        decoded_v2.dt,
        decoded_v2.t0,
        decoded_v2.unit,
    )
    _assert_accounting(encoded, experimental)
    return baseline, experimental


def _encode_pair(values: list[float], **options) -> tuple[bytes, bytes]:
    ts = core.TimeSeries(values=values, dt=0.25, t0="qualification", unit="test")
    v2 = core.encode_timeseries_v2(ts, **options)
    encoded = compact.encode_timeseries_compact_experimental(ts, **options)
    _assert_equivalent(v2, encoded)
    return v2, encoded


@pytest.mark.parametrize(
    "predictor",
    ["mean", "linear", "rw"],
)
@pytest.mark.parametrize(
    "residual_coding",
    ["raw", "varint", "zero-run"],
)
def test_all_predictor_codec_combinations_are_v2_equivalent(
    predictor: str,
    residual_coding: str,
) -> None:
    ts = _ts()

    options = {
        "segment_length": 5,
        "predictor": predictor,
        "C_Q": 0.125,
        "segment_mode": "fixed",
        "residual_coding": residual_coding,
    }

    v2 = core.encode_timeseries_v2(ts, **options)
    encoded = compact.encode_timeseries_compact_experimental(
        ts,
        **options,
    )

    _assert_equivalent(v2, encoded)


@pytest.mark.parametrize(
    ("predictor_type", "expected_size"),
    [
        (0, 17),
        (1, 21),
        (2, 17),
    ],
)
def test_record_sizes_are_frozen(
    predictor_type: int,
    expected_size: int,
) -> None:
    structures = {
        0: compact.MEAN_RECORD_STRUCT,
        1: compact.LINEAR_RECORD_STRUCT,
        2: compact.RANDOM_WALK_RECORD_STRUCT,
    }

    assert structures[predictor_type].size == expected_size
    assert structures[predictor_type].format.startswith("<")
    assert compact.COMMON_PREFIX_STRUCT.format == "<IBfI"
    assert compact.COMMON_PREFIX_STRUCT.size == 13


def test_public_decoder_rejects_experimental_version() -> None:
    encoded = compact.encode_timeseries_compact_experimental(
        _ts(),
        segment_length=5,
        predictor="linear",
        residual_coding="varint",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported LSG2 version 3",
    ):
        core.decode_timeseries(encoded)


def test_public_default_remains_v2() -> None:
    encoded = core.encode_timeseries(_ts())

    (_, version, *_) = core.FILE_HEADER_STRUCT.unpack_from(encoded, 0)

    assert version == core.FORMAT_VERSION_V2
    assert encoded == core.encode_timeseries_v2(_ts())


def test_compact_encoder_preserves_context() -> None:
    ts = _ts()

    encoded = compact.encode_timeseries_compact_experimental(
        ts,
        residual_coding="varint",
    )
    decoded = compact.decode_timeseries_compact_experimental(encoded)
    _assert_equivalent(core.encode_timeseries_v2(ts, residual_coding="varint"), encoded)

    assert decoded.dt == ts.dt
    assert decoded.t0 == ts.t0
    assert decoded.unit == ts.unit


def test_trailing_bytes_are_rejected() -> None:
    encoded = compact.encode_timeseries_compact_experimental(
        _ts(),
        residual_coding="varint",
    )

    with pytest.raises(ValueError, match="Trailing bytes"):
        compact.decode_timeseries_compact_experimental(encoded + b"\x00")


def test_zero_segment_length_is_rejected() -> None:
    encoded = bytearray(
        compact.encode_timeseries_compact_experimental(
            _ts(),
            segment_length=len(_sample_values()),
            predictor="mean",
            residual_coding="varint",
        )
    )

    (_, _, _, header_len, *_) = core.FILE_HEADER_STRUCT.unpack_from(
        encoded,
        0,
    )

    record_offset = (
        core.FILE_HEADER_STRUCT.size
        + header_len
        + core.RESIDUAL_SECTION_HEADER_STRUCT.size
    )

    struct.pack_into("<I", encoded, record_offset, 0)

    with pytest.raises(
        ValueError,
        match="segment length must be positive",
    ):
        compact.decode_timeseries_compact_experimental(bytes(encoded))


def test_unknown_predictor_is_rejected_before_suffix_parse() -> None:
    encoded = bytearray(
        compact.encode_timeseries_compact_experimental(
            _ts(),
            segment_length=len(_sample_values()),
            predictor="mean",
            residual_coding="varint",
        )
    )

    (_, _, _, header_len, *_) = core.FILE_HEADER_STRUCT.unpack_from(
        encoded,
        0,
    )

    record_offset = (
        core.FILE_HEADER_STRUCT.size
        + header_len
        + core.RESIDUAL_SECTION_HEADER_STRUCT.size
    )

    encoded[record_offset + 4] = 255
    # No suffix bytes are available: predictor validation must still win.
    encoded = encoded[: record_offset + 13]

    with pytest.raises(
        ValueError,
        match="Unsupported compact predictor_type",
    ):
        compact.decode_timeseries_compact_experimental(bytes(encoded))


def test_zero_q_is_rejected() -> None:
    encoded = bytearray(
        compact.encode_timeseries_compact_experimental(
            _ts(),
            segment_length=len(_sample_values()),
            predictor="mean",
            residual_coding="varint",
        )
    )

    (_, _, _, header_len, *_) = core.FILE_HEADER_STRUCT.unpack_from(
        encoded,
        0,
    )

    record_offset = (
        core.FILE_HEADER_STRUCT.size
        + header_len
        + core.RESIDUAL_SECTION_HEADER_STRUCT.size
    )

    struct.pack_into("<f", encoded, record_offset + 5, 0.0)

    with pytest.raises(
        ValueError,
        match="quantization step Q",
    ):
        compact.decode_timeseries_compact_experimental(bytes(encoded))


def test_truncated_payload_is_rejected() -> None:
    encoded = compact.encode_timeseries_compact_experimental(
        _ts(),
        segment_length=len(_sample_values()),
        predictor="linear",
        residual_coding="varint",
    )

    with pytest.raises(
        ValueError,
        match="Truncated compact residual payload",
    ):
        compact.decode_timeseries_compact_experimental(encoded[:-1])


def test_raw_payload_length_must_match_segment_length() -> None:
    encoded = bytearray(
        compact.encode_timeseries_compact_experimental(
            _ts(),
            segment_length=len(_sample_values()),
            predictor="mean",
            residual_coding="raw",
        )
    )

    (_, _, _, header_len, *_) = core.FILE_HEADER_STRUCT.unpack_from(
        encoded,
        0,
    )

    record_offset = (
        core.FILE_HEADER_STRUCT.size
        + header_len
        + core.RESIDUAL_SECTION_HEADER_STRUCT.size
    )

    payload_length_offset = record_offset + 9
    current = struct.unpack_from(
        "<I",
        encoded,
        payload_length_offset,
    )[0]

    struct.pack_into(
        "<I",
        encoded,
        payload_length_offset,
        current - 1,
    )

    with pytest.raises(
        ValueError,
        match="RAW_INT32 payload length",
    ):
        compact.decode_timeseries_compact_experimental(bytes(encoded))


def test_extra_varint_payload_byte_is_rejected() -> None:
    encoded = bytearray(
        compact.encode_timeseries_compact_experimental(
            _ts(),
            segment_length=len(_sample_values()),
            predictor="mean",
            residual_coding="varint",
        )
    )

    (_, _, _, header_len, *_) = core.FILE_HEADER_STRUCT.unpack_from(
        encoded,
        0,
    )

    record_offset = (
        core.FILE_HEADER_STRUCT.size
        + header_len
        + core.RESIDUAL_SECTION_HEADER_STRUCT.size
    )

    payload_length_offset = record_offset + 9
    payload_length = struct.unpack_from(
        "<I",
        encoded,
        payload_length_offset,
    )[0]

    record_end = record_offset + compact.MEAN_RECORD_STRUCT.size
    payload_end = record_end + payload_length

    encoded[payload_end:payload_end] = b"\x00"
    struct.pack_into(
        "<I",
        encoded,
        payload_length_offset,
        payload_length + 1,
    )

    with pytest.raises(
        ValueError,
        match="Extra bytes inside varint payload",
    ):
        compact.decode_timeseries_compact_experimental(bytes(encoded))


@pytest.mark.parametrize(
    "residual_coding",
    ["raw", "varint", "zero-run", "auto"],
)
def test_adaptive_auto_matches_v2(
    residual_coding: str,
) -> None:
    values = [
        float(index // 4) + (0.1 if index % 7 == 0 else 0.0) for index in range(96)
    ]
    ts = core.TimeSeries(
        values=values,
        dt=0.5,
        t0="2026-10-08T00:00:00Z",
        unit="adaptive",
    )

    options = {
        "predictor": "auto",
        "C_Q": 0.125,
        "segment_mode": "adaptive",
        "min_segment_length": 8,
        "max_segment_length": 24,
        "mse_threshold": 0.5,
        "residual_coding": residual_coding,
    }

    v2 = core.encode_timeseries_v2(ts, **options)
    experimental = compact.encode_timeseries_compact_experimental(
        ts,
        **options,
    )

    _assert_equivalent(v2, experimental)


@pytest.mark.parametrize("predictor", ["mean", "linear", "rw", "auto"])
def test_actual_size_matches_frozen_formula(predictor: str) -> None:
    values = [0.0] * 4 + [0.0, 1.0, 2.0, 3.0] + [0.0, 1.0, 2.0, 2.0]
    _, encoded = _encode_pair(
        values, segment_length=4, predictor=predictor, residual_coding="varint"
    )
    wire = _read_wire(encoded, version=3)
    expected_tags = {
        "mean": [0] * 3,
        "linear": [1] * 3,
        "rw": [2] * 3,
        "auto": [0, 1, 2],
    }
    assert [seg.tag for seg in wire.segments] == expected_tags[predictor]
    _assert_accounting(encoded, wire)
    # Q and the length field begin at unaligned record-relative offsets 5 and
    # 9. The first metadata float immediately follows the 13-byte prefix.
    for seg in wire.segments:
        assert encoded[seg.record_offset + 5 : seg.record_offset + 9] == seg.q_bits
        assert (
            encoded[seg.record_offset + 13 : seg.record_offset + 17]
            == seg.parameter_bits[0]
        )


@pytest.mark.parametrize(
    ("values", "options", "expected_bounds", "expected_tags"),
    [
        pytest.param(
            [0.1],
            {"segment_length": 1, "predictor": "mean"},
            [(0, 0)],
            [0],
            id="singleton",
        ),
        pytest.param(
            _sample_values(),
            {"segment_length": 12, "predictor": "linear"},
            [(0, 11)],
            [1],
            id="one-longer-segment",
        ),
        pytest.param(
            [0.0] * 3 + [10.0] * 5 + [0.0] * 4,
            {
                "predictor": "linear",
                "segment_mode": "adaptive",
                "min_segment_length": 2,
                "max_segment_length": 7,
                "mse_threshold": 0.01,
            },
            [(0, 2), (3, 7), (8, 11)],
            [1, 1, 1],
            id="multiple-unequal",
        ),
        pytest.param(
            _sample_values(),
            {"segment_length": 5, "predictor": "rw"},
            [(0, 4), (5, 9), (10, 11)],
            [2, 2, 2],
            id="short-final",
        ),
        pytest.param(
            [0.0] * 4 + [0.0, 1.0, 2.0, 3.0] + [0.0, 1.0, 2.0, 2.0],
            {"segment_length": 4, "predictor": "auto"},
            [(0, 3), (4, 7), (8, 11)],
            [0, 1, 2],
            id="mixed-tags",
        ),
    ],
)
@pytest.mark.parametrize("coding", ["raw", "varint", "zero-run", "auto"])
def test_explicit_segment_topologies(
    values, options, expected_bounds, expected_tags, coding: str
) -> None:
    v2, encoded = _encode_pair(values, residual_coding=coding, **options)
    baseline, experimental = _assert_equivalent(v2, encoded)
    # Assert independently known topology as well as deriving compact boundaries
    # cumulatively and comparing them with the absolute V2 fields.
    for wire in (baseline, experimental):
        assert [(seg.start, seg.end) for seg in wire.segments] == expected_bounds
        assert [seg.tag for seg in wire.segments] == expected_tags


@pytest.mark.parametrize("coding", ["raw", "varint", "zero-run", "auto"])
def test_signed_int32_endpoints_and_both_residual_signs(coding: str) -> None:
    v2, encoded = _encode_pair(
        [0.0, -2147483648.0, -1.0],
        predictor="rw",
        segment_length=3,
        C_Q=0.0,
        Q_MIN=1.0,
        residual_coding=coding,
    )
    baseline, experimental = _assert_equivalent(v2, encoded)
    assert baseline.segments[0].residuals == [0, -(2**31), 2**31 - 1]
    assert experimental.segments[0].residuals[1] < 0
    assert experimental.segments[0].residuals[2] > 0


@pytest.mark.parametrize("run_length", [2, 3, 257], ids=["two", "three", "long"])
def test_zero_run_minimum_and_long_run(run_length: int) -> None:
    _, encoded = _encode_pair(
        [1.0] * run_length,
        predictor="mean",
        segment_length=run_length,
        C_Q=0.0,
        Q_MIN=1.0,
        residual_coding="zero-run",
    )
    seg = _read_wire(encoded, version=3).segments[0]
    assert seg.residuals == [0] * run_length
    # Two zeros remain literal tokens; only runs of at least three use marker 0.
    expected = {2: b"\x01\x01", 3: b"\x00\x03", 257: b"\x00\x81\x02"}
    assert seg.payload == expected[run_length]


@pytest.mark.parametrize("predictor", ["mean", "linear", "rw"])
def test_rounding_sensitive_metadata(predictor: str) -> None:
    values = [0.1, 0.2, 0.4, 0.7]
    _, encoded = _encode_pair(
        values,
        predictor=predictor,
        segment_length=4,
        C_Q=0.0,
        Q_MIN=0.1,
        residual_coding="varint",
    )
    seg = _read_wire(encoded, version=3).segments[0]
    mean, slope, intercept, _ = core.compute_stats(values)
    original_parameters = {
        "mean": (mean,),
        "linear": (slope, intercept),
        "rw": (values[0],),
    }[predictor]
    assert seg.q_bits == struct.pack("<f", 0.1)
    assert struct.unpack("<f", seg.q_bits)[0] != 0.1
    assert seg.parameter_bits == tuple(
        struct.pack("<f", p) for p in original_parameters
    )
    assert any(
        struct.unpack("<f", bits)[0] != original
        for bits, original in zip(seg.parameter_bits, original_parameters, strict=True)
    )


def test_signed_zero_seed_metadata_is_preserved() -> None:
    _, encoded = _encode_pair(
        [-0.0] * 4,
        predictor="rw",
        segment_length=2,
        residual_coding="raw",
    )
    assert [seg.parameter_bits for seg in _read_wire(encoded, version=3).segments] == [
        (b"\x00\x00\x00\x80",),
        (b"\x00\x00\x00\x80",),
    ]


@pytest.mark.parametrize("predictor", ["mean", "linear", "rw"])
def test_positive_binary32_subnormal_q_is_valid(predictor: str) -> None:
    q = 2.0**-149
    _, encoded = _encode_pair(
        [0.0] * 4,
        predictor=predictor,
        C_Q=0.0,
        Q_MIN=q,
        residual_coding="zero-run",
    )
    seg = _read_wire(encoded, version=3).segments[0]
    assert seg.q_bits == b"\x01\x00\x00\x00"
    assert 0.0 < struct.unpack("<f", seg.q_bits)[0] < 2.0**-126
    assert seg.residuals == [0] * 4


@pytest.mark.parametrize("coding", ["raw", "varint", "zero-run", "auto"])
def test_random_walk_nonzero_first_residual_and_segment_local_reset(
    coding: str,
) -> None:
    q = 2.0**-27
    values = [
        1.0 + 4.25 * q,
        1.0 + 6.75 * q,
        1.0 + 6.0 * q,
        2.0 + 8.25 * q,
        2.0 + 10.75 * q,
        2.0 + 10.0 * q,
    ]
    v2, encoded = _encode_pair(
        values,
        predictor="rw",
        segment_length=3,
        C_Q=0.0,
        Q_MIN=q,
        residual_coding=coding,
    )
    baseline, experimental = _assert_equivalent(v2, encoded)
    reconstructed = compact.decode_timeseries_compact_experimental(encoded).values
    assert [seg.residuals for seg in experimental.segments] == [[4, 2, -1], [8, 2, -1]]
    for expected, seg in zip(baseline.segments, experimental.segments, strict=True):
        seed = struct.unpack("<f", seg.parameter_bits[0])[0]
        assert seed != values[seg.start]
        assert seg.parameter_bits == expected.parameter_bits
        assert seg.payload == expected.payload
        assert seg.residuals[0] != 0
        step = struct.unpack("<f", seg.q_bits)[0]
        local = [seed + seg.residuals[0] * step]
        for residual in seg.residuals[1:]:
            local.append(local[-1] + residual * step)
        assert _bits(local) == _bits(reconstructed[seg.start : seg.end + 1])
        assert _bits(local) != _bits(values[seg.start : seg.end + 1])
        # Encoding predicts from previous ORIGINAL samples. This fixture
        # distinguishes that rule from feeding reconstructed samples back.
        for index in range(seg.start + 1, seg.end + 1):
            assert seg.residuals[index - seg.start] == round(
                (values[index] - values[index - 1]) / step
            )
        assert any(
            seg.residuals[index - seg.start]
            != round((values[index] - reconstructed[index - 1]) / step)
            for index in range(seg.start + 1, seg.end + 1)
        )
        if seg.start:
            continued = reconstructed[seg.start - 1] + seg.residuals[0] * step
            assert _bits([continued]) != _bits([reconstructed[seg.start]])
    assert _bits(reconstructed) == _bits(core.decode_timeseries(v2).values)


@pytest.mark.parametrize(
    ("values", "expected_tag", "expected_mses"),
    [
        pytest.param([0.0] * 4, 0, (0.0, 0.0, 0.0), id="three-way-tie-mean-first"),
        pytest.param(
            [0.0, 1.0, 2.0, 3.0], 1, (0.25, 0.0, 0.0), id="linear-rw-tie-linear-first"
        ),
        pytest.param([0.0, 1.0, 2.0, 2.0], 2, None, id="rw-strict-winner"),
    ],
)
def test_predictor_auto_candidate_order(values, expected_tag, expected_mses) -> None:
    # Reproduce the actual V2 model's candidate calculation and establish exact
    # ties before testing the choice made through the production V2 encoder.
    mean, slope, intercept, _ = core.compute_stats(values)
    mses = []
    for tag in (0, 1, 2):
        predictions = core._build_preds_for_segmentation(
            values,
            predictor_type=tag,
            mean=mean,
            slope=slope,
            intercept=intercept,
            seed_value=values[0],
        )
        residuals, q = core.quantize_residuals(
            [v - p for v, p in zip(values, predictions, strict=True)],
            C_Q=0.0,
            Q_MIN=1.0,
        )
        if tag == 2:
            restored = [values[0] + residuals[0] * q]
            for residual in residuals[1:]:
                restored.append(restored[-1] + residual * q)
        else:
            restored = [p + r * q for p, r in zip(predictions, residuals, strict=True)]
        mses.append(
            sum((v - r) ** 2 for v, r in zip(values, restored, strict=True))
            / len(values)
        )
    if expected_mses is not None:
        assert tuple(mses) == expected_mses
    else:
        assert mses[2] == 0.0 < min(mses[:2])
    _, encoded = _encode_pair(
        values, predictor="auto", C_Q=0.0, Q_MIN=1.0, residual_coding="auto"
    )
    assert _read_wire(encoded, version=3).segments[0].tag == expected_tag


@pytest.mark.parametrize(
    ("values", "expected_sizes", "expected_coding"),
    [
        pytest.param([0.0, 0.0], (2, 2), 1, id="tie-prefers-varint"),
        pytest.param([0.0, -64.0], (2, 3), 1, id="varint-strict-winner"),
        pytest.param([0.0] * 3, (3, 2), 2, id="zero-run-strict-winner"),
    ],
)
def test_residual_auto_tie_and_strict_winners(
    values, expected_sizes, expected_coding
) -> None:
    wires = {}
    for coding in ("varint", "zero-run", "auto"):
        _, encoded = _encode_pair(
            values, predictor="rw", C_Q=0.0, Q_MIN=1.0, residual_coding=coding
        )
        wires[coding] = _read_wire(encoded, version=3)
    assert (
        tuple(
            sum(len(seg.payload) for seg in wires[c].segments)
            for c in ("varint", "zero-run")
        )
        == expected_sizes
    )
    assert wires["auto"].coding == expected_coding
    selected = wires["varint" if expected_coding == 1 else "zero-run"]
    assert [seg.payload for seg in wires["auto"].segments] == [
        seg.payload for seg in selected.segments
    ]


def _malformed_base(*, coding: str = "varint", predictor: str = "mean") -> bytes:
    return compact.encode_timeseries_compact_experimental(
        core.TimeSeries(values=[0.0] * 4),
        segment_length=4,
        predictor=predictor,
        residual_coding=coding,
    )


def _record_offset(data: bytes) -> int:
    return 28 + struct.unpack_from("<I", data, 8)[0] + 16


def _replace_field(data: bytes, offset: int, fmt: str, value) -> bytes:
    mutated = bytearray(data)
    struct.pack_into(fmt, mutated, offset, value)
    return bytes(mutated)


def _replace_context(data: bytes, context: bytes) -> bytes:
    old_length = struct.unpack_from("<I", data, 8)[0]
    data = _replace_field(data, 8, "<I", len(context))
    return data[:28] + context + data[28 + old_length :]


def _replace_payload(data: bytes, payload: bytes) -> bytes:
    # The malformed base has exactly one record/payload pair.
    record = _record_offset(data)
    tag = data[record + 4]
    start = record + (21 if tag == 1 else 17)
    return _replace_field(data[:start], record + 9, "<I", len(payload)) + payload


@pytest.mark.parametrize(
    ("location", "fmt", "value", "message"),
    [
        pytest.param(0, "<4s", b"NOPE", "Invalid magic", id="magic"),
        pytest.param(4, "<H", 65535, "Expected experimental compact", id="version"),
        pytest.param(6, "<H", 1, "header reserved fields", id="flags"),
        pytest.param(20, "<I", 1, "header reserved fields", id="header-reserved1"),
        pytest.param(24, "<I", 1, "header reserved fields", id="header-reserved2"),
        pytest.param(
            "coding", "<I", 3, "Unsupported residual coding", id="coding-type"
        ),
        pytest.param(
            "coding+4", "<I", 1, "coding reserved fields", id="coding-reserved1"
        ),
        pytest.param(
            "coding+8", "<I", 1, "coding reserved fields", id="coding-reserved2"
        ),
        pytest.param(
            "coding+12", "<I", 1, "coding reserved fields", id="coding-reserved3"
        ),
        pytest.param(
            "record", "<I", 0, "segment length must be positive", id="zero-length"
        ),
        pytest.param(
            "record", "<I", 5, "coverage exceeds n_points", id="over-coverage"
        ),
        pytest.param(
            16, "<I", 5, "n_segments cannot exceed n_points", id="segments-above-points"
        ),
        pytest.param(
            12, "<I", 0, "both be zero or both be nonzero", id="zero-points-only"
        ),
        pytest.param(
            16, "<I", 0, "both be zero or both be nonzero", id="zero-segments-only"
        ),
        pytest.param(
            12,
            "<I",
            5,
            "do not cover the declared point count",
            id="missing-final-coverage",
        ),
        pytest.param(
            16, "<I", 2, "Truncated compact segment prefix", id="missing-segment-pair"
        ),
        pytest.param(
            "record+4",
            "<B",
            255,
            "Unsupported compact predictor_type",
            id="unknown-predictor",
        ),
        pytest.param(
            "record+9", "<I", 0, "payload must be non-empty", id="empty-payload"
        ),
        pytest.param(
            "record+9",
            "<I",
            5,
            "Truncated compact residual payload",
            id="payload-beyond-input",
        ),
        pytest.param(
            "record+9",
            "<I",
            41,
            "variable-length residual payload exceeds bound",
            id="variable-payload-bound",
        ),
    ],
)
def test_malformed_field_matrix(location, fmt, value, message: str) -> None:
    data = _malformed_base()
    if isinstance(location, str):
        area, _, relative = location.partition("+")
        offset = _record_offset(data) - (16 if area == "coding" else 0)
        offset += int(relative or 0)
    else:
        offset = location
    with pytest.raises(ValueError, match=message):
        compact.decode_timeseries_compact_experimental(
            _replace_field(data, offset, fmt, value)
        )


@pytest.mark.parametrize(
    ("boundary", "message"),
    [
        ("header", "Data too short to contain header"),
        ("context", "Truncated LSG2 context"),
        ("coding", "Truncated residual coding header"),
        ("prefix", "Truncated compact segment prefix"),
        ("suffix", "Truncated compact predictor record"),
        ("payload", "Truncated compact residual payload"),
    ],
)
@pytest.mark.parametrize("predictor", ["mean", "linear", "rw"])
def test_truncated_stream_matrix(boundary: str, message: str, predictor: str) -> None:
    data = _malformed_base(predictor=predictor)
    record = _record_offset(data)
    offsets = {
        "header": 28,
        "context": record - 16,
        "coding": record,
        "prefix": record + 13,
        "suffix": record + (21 if predictor == "linear" else 17),
        "payload": len(data),
    }
    with pytest.raises(ValueError, match=message):
        compact.decode_timeseries_compact_experimental(data[: offsets[boundary] - 1])


@pytest.mark.parametrize(
    "context",
    [
        pytest.param(b"\xff", id="invalid-utf8"),
        pytest.param(b'{"x":', id="malformed-json"),
        pytest.param(b"[]", id="non-object-array"),
        pytest.param(b"null", id="non-object-null"),
    ],
)
def test_invalid_context_matrix(context: bytes) -> None:
    non_object = context in (b"[]", b"null")
    with pytest.raises(
        TypeError if non_object else ValueError,
        match="must decode to an object" if non_object else "Invalid context JSON",
    ):
        compact.decode_timeseries_compact_experimental(
            _replace_context(_malformed_base(), context)
        )


@pytest.mark.parametrize(
    "q",
    [float("nan"), float("inf"), -float("inf"), 0.0, -1.0, -0.0],
    ids=["nan", "positive-inf", "negative-inf", "zero", "negative", "negative-zero"],
)
def test_invalid_q_matrix(q: float) -> None:
    data = _malformed_base()
    with pytest.raises(ValueError, match="quantization step Q must be finite and > 0"):
        compact.decode_timeseries_compact_experimental(
            _replace_field(data, _record_offset(data) + 5, "<f", q)
        )


@pytest.mark.parametrize(
    ("predictor", "relative"),
    [
        pytest.param("mean", 13, id="mean"),
        pytest.param("linear", 13, id="slope"),
        pytest.param("linear", 17, id="intercept"),
        pytest.param("rw", 13, id="seed"),
    ],
)
@pytest.mark.parametrize(
    "value",
    [float("nan"), float("inf"), -float("inf")],
    ids=["nan", "positive-inf", "negative-inf"],
)
def test_nonfinite_active_metadata_matrix(
    predictor: str, relative: int, value: float
) -> None:
    data = _malformed_base(predictor=predictor)
    with pytest.raises(ValueError, match="segment metadata must be finite"):
        compact.decode_timeseries_compact_experimental(
            _replace_field(data, _record_offset(data) + relative, "<f", value)
        )


@pytest.mark.parametrize(
    ("coding", "payload", "message"),
    [
        pytest.param(
            "raw", b"\x00" * 15, "RAW_INT32 payload length", id="raw-length-mismatch"
        ),
        pytest.param(
            "varint",
            b"\x00" * 3 + b"\x80",
            "Truncated varint",
            id="unterminated-varint",
        ),
        pytest.param(
            "varint",
            b"\x80" * 10 + b"\x00" * 3,
            "maximum encoded length",
            id="excessive-varint",
        ),
        pytest.param(
            "varint",
            b"\x80\x80\x80\x80\x10" + b"\x00" * 3,
            "signed int32 range",
            id="positive-out-of-range",
        ),
        pytest.param(
            "varint",
            b"\x81\x80\x80\x80\x10" + b"\x00" * 3,
            "signed int32 range",
            id="negative-out-of-range",
        ),
        pytest.param("varint", b"\x00" * 3, "Truncated varint", id="varint-undercount"),
        pytest.param(
            "varint",
            b"\x00" * 5,
            "Extra bytes inside varint payload",
            id="varint-overcount",
        ),
        pytest.param(
            "varint",
            b"\x00" * 4 + b"\x80",
            "Extra bytes inside varint payload",
            id="varint-unused-byte",
        ),
        # All positive tokens denote literals; marker 0 followed by an invalid
        # run (including zero) is the invalid-marker case in this grammar.
        pytest.param(
            "zero-run",
            b"\x00\x00",
            "Invalid zero-run length",
            id="invalid-zero-run-marker",
        ),
        pytest.param(
            "zero-run", b"\x00", "Truncated varint", id="marker-without-run-length"
        ),
        pytest.param(
            "zero-run", b"\x00\x01", "Invalid zero-run length", id="run-length-one"
        ),
        pytest.param(
            "zero-run", b"\x00\x02", "Invalid zero-run length", id="run-length-two"
        ),
        pytest.param(
            "zero-run",
            b"\x00\x05",
            "Zero-run exceeds declared residual count",
            id="run-exceeds-remaining",
        ),
        pytest.param(
            "zero-run",
            b"\x01\x00\x04",
            "Zero-run exceeds declared residual count",
            id="run-after-literal-exceeds-remaining",
        ),
        pytest.param(
            "zero-run",
            b"\x00\x80",
            "Truncated varint",
            id="incomplete-zero-run-payload",
        ),
        pytest.param(
            "zero-run",
            b"\x01" * 3,
            "does not match declaration",
            id="zero-run-undercount",
        ),
        pytest.param(
            "zero-run",
            b"\x01" * 5,
            "count exceeds declaration",
            id="zero-run-overcount",
        ),
        pytest.param(
            "zero-run",
            b"\x81\x80\x80\x80\x10" + b"\x01" * 3,
            "signed int32 range",
            id="zero-run-out-of-range-literal",
        ),
        pytest.param(
            "zero-run",
            b"\x00\x04\x00\x03",
            "Zero-run exceeds declared residual count",
            id="zero-run-unused-run",
        ),
    ],
)
def test_malformed_payload_matrix(coding: str, payload: bytes, message: str) -> None:
    data = _replace_payload(_malformed_base(coding=coding), payload)
    with pytest.raises(ValueError, match=message):
        compact.decode_timeseries_compact_experimental(data)


@pytest.mark.parametrize(
    ("limit", "message"),
    [
        ("MAX_INPUT_BYTES", "Input exceeds maximum size"),
        ("MAX_CONTEXT_BYTES", "Context JSON exceeds maximum size"),
        ("MAX_POINTS", "n_points=4 exceeds maximum 3"),
        ("MAX_SEGMENTS", "n_segments=2 exceeds maximum 1"),
        ("MAX_SEGMENT_POINTS", "segment length exceeds maximum"),
        ("MAX_RESIDUAL_BLOCK_BYTES", "residual payload exceeds maximum"),
    ],
)
def test_resource_limits_exact_and_plus_one(
    monkeypatch: pytest.MonkeyPatch, limit: str, message: str
) -> None:
    data = compact.encode_timeseries_compact_experimental(
        core.TimeSeries(values=[0.0] * 4),
        segment_length=2,
        predictor="mean",
        residual_coding="raw",
    )
    wire = _read_wire(data, version=3)
    maximum = {
        "MAX_INPUT_BYTES": len(data),
        "MAX_CONTEXT_BYTES": len(wire.context),
        "MAX_POINTS": 4,
        "MAX_SEGMENTS": 2,
        "MAX_SEGMENT_POINTS": 2,
        "MAX_RESIDUAL_BLOCK_BYTES": len(wire.segments[0].payload),
    }[limit]
    monkeypatch.setattr(core, limit, maximum)
    assert _bits(compact.decode_timeseries_compact_experimental(data).values) == _bits(
        [0.0] * 4
    )
    monkeypatch.setattr(core, limit, maximum - 1)

    # Enforce the bound before entering the numerical reconstruction path.
    def unexpected_reconstruction(*args, **kwargs):
        pytest.fail("Out-of-bound stream reached numerical reconstruction")

    monkeypatch.setattr(core, "_decode_timeseries_v1", unexpected_reconstruction)
    with pytest.raises(ValueError, match=message):
        compact.decode_timeseries_compact_experimental(data)


def test_context_depth_bound_with_small_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    data = _malformed_base()
    monkeypatch.setattr(core, "MAX_CONTEXT_DEPTH", 2)
    valid = _replace_context(data, b'{"x":[0],"brackets":"[[["}')
    assert compact.decode_timeseries_compact_experimental(valid).values == [0.0] * 4
    too_deep = _replace_context(data, b'{"x":[[0]]}')
    with pytest.raises(ValueError, match="maximum nesting depth 2"):
        compact.decode_timeseries_compact_experimental(too_deep)


def test_empty_compact_stream_has_consistent_zero_counts() -> None:
    # V2 encoding rejects empty series, but both zero declarations are legal
    # decoder topology in the frozen compact protocol.
    empty = struct.pack("<4sHHIIIII", b"LSG2", 3, 0, 2, 0, 0, 0, 0)
    empty += b"{}" + struct.pack("<IIII", 1, 0, 0, 0)
    wire = _read_wire(empty, version=3)
    _assert_accounting(empty, wire)
    assert compact.decode_timeseries_compact_experimental(empty).values == []
    with pytest.raises(ValueError, match="Trailing bytes"):
        compact.decode_timeseries_compact_experimental(empty + b"\x00")
