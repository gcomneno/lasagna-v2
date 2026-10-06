# tests/test_decode_malicious.py
from __future__ import annotations

import pytest
from lasagna2 import core


from lasagna2 import encode_timeseries_v1

from lasagna2.core import TimeSeries, encode_timeseries, decode_timeseries


def test_decode_truncated_raises_valueerror():
    values = [0.1 * i for i in range(20)]
    ts = TimeSeries(values=values, dt=60.0, t0="2025-01-01T00:00:00Z", unit="kW")
    data = encode_timeseries(ts, segment_length=10, predictor="linear")

    # tronca brutalmente il file
    truncated = data[:10]
    try:
        decode_timeseries(truncated)
        assert False, "decode_timeseries should have raised on truncated data"
    except ValueError:
        pass


def test_decode_bad_magic_raises_valueerror():
    values = [0.1 * i for i in range(20)]
    ts = TimeSeries(values=values, dt=60.0, t0="2025-01-01T00:00:00Z", unit="kW")
    data = bytearray(encode_timeseries(ts, segment_length=10, predictor="linear"))

    # corrompi la magic "LSG2" -> "XXXX"
    data[0:4] = b"XXXX"

    try:
        decode_timeseries(bytes(data))
        assert False, "decode_timeseries should have raised on invalid magic"
    except ValueError as e:
        assert "magic" in str(e)


def test_decode_suspicious_npoints_raises_valueerror():
    values = [0.1 * i for i in range(20)]
    ts = TimeSeries(values=values, dt=60.0, t0="2025-01-01T00:00:00Z", unit="kW")
    data = bytearray(
        encode_timeseries_v1(
            ts,
            segment_length=10,
            predictor="linear",
        )
    )

    # manomette il campo n_points nel header (posizione 4sHHI I = offset 4+2+2+4=12)
    # FILE_HEADER_STRUCT = "<4sHHIIIII"
    # fields: magic, version, flags, header_len, n_points, ...

    from lasagna2.core import FILE_HEADER_STRUCT

    # unpack, modifica n_points, repack
    hdr = list(FILE_HEADER_STRUCT.unpack_from(data, 0))
    # hdr[4] = n_points -> pompalo tantissimo
    hdr[4] = 20_000_000
    FILE_HEADER_STRUCT.pack_into(data, 0, *hdr)

    try:
        decode_timeseries(bytes(data))
        assert False, "decode_timeseries should have raised on suspicious n_points"
    except ValueError as e:
        assert "n_points=20000000 exceeds maximum 10000000" in str(e)


def _replace_context(data: bytes, context: bytes) -> bytes:
    header = list(core.FILE_HEADER_STRUCT.unpack_from(data, 0))
    old_context_len = int(header[3])
    old_context_end = core.FILE_HEADER_STRUCT.size + old_context_len

    header[3] = len(context)

    return core.FILE_HEADER_STRUCT.pack(*header) + context + data[old_context_end:]


@pytest.mark.parametrize(
    "encoder",
    [
        core.encode_timeseries_v1,
        core.encode_timeseries_v2,
    ],
)
@pytest.mark.parametrize(
    "context",
    [
        b"[]",
        b"null",
        b'{"sampling":[]}',
        b'{"sampling":{"dt":[]}}',
        b'{"sampling":{"dt":null}}',
        (b'{"sampling":{"dt":' + b"9" * 1000 + b"}}"),
    ],
)
def test_malformed_context_shape_fails_with_value_error(
    encoder,
    context: bytes,
) -> None:
    data = encoder(
        core.TimeSeries(
            values=[1.0, 2.0, 3.0, 4.0],
        ),
        segment_length=4,
        predictor="mean",
        residual_coding="raw",
    )

    malformed = _replace_context(
        data,
        context,
    )

    with pytest.raises(ValueError):
        core.decode_timeseries(malformed)
