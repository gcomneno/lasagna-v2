# tests/test_decode_malicious.py
from __future__ import annotations

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
    data = bytearray(encode_timeseries(ts, segment_length=10, predictor="linear"))

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
        assert "Suspicious n_points" in str(e)
