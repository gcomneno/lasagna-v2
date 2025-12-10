# tests/test_core_roundtrip.py
from __future__ import annotations

import math

from lasagna2.core import TimeSeries, encode_timeseries, decode_timeseries


def rmse(a, b):
    assert len(a) == len(b)
    n = len(a)
    if n == 0:
        return 0.0
    s = 0.0
    for x, y in zip(a, b):
        d = x - y
        s += d * d
    return math.sqrt(s / n)


def test_roundtrip_trend_linear_fixed_raw():
    # x[i] = 0.1 * i
    values = [0.1 * i for i in range(200)]
    ts = TimeSeries(values=values, dt=60.0, t0="2025-01-01T00:00:00Z", unit="kW")

    data = encode_timeseries(
        ts,
        segment_length=50,
        predictor="linear",
        segment_mode="fixed",
        residual_coding="raw",
    )
    decoded = decode_timeseries(data)

    assert len(decoded.values) == len(values)
    assert decoded.dt == ts.dt
    assert decoded.t0 == ts.t0
    assert decoded.unit == ts.unit

    # deve essere praticamente lossless su trend perfetto
    e = rmse(values, decoded.values)
    assert e < 1e-6


def test_roundtrip_sine_noise_adaptive_auto_varint():
    # sinusoide + rumore leggero
    import random

    random.seed(123)
    values = []
    for i in range(300):
        angle = 2.0 * math.pi * i / 50.0
        v = math.sin(angle) + random.gauss(0.0, 0.1)
        values.append(v)

    ts = TimeSeries(values=values, dt=60.0, t0="2025-01-01T00:00:00Z", unit="arb")

    data = encode_timeseries(
        ts,
        segment_mode="adaptive",
        min_segment_length=30,
        max_segment_length=80,
        mse_threshold=0.2,
        predictor="auto",
        residual_coding="varint",
    )
    decoded = decode_timeseries(data)

    assert len(decoded.values) == len(values)

    e = rmse(values, decoded.values)
    # ci aspettiamo un RMSE moderato (0.0 < e < 0.3)
    assert e < 0.3
