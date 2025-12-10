# tests/test_core_roundtrip.py
from __future__ import annotations

import math
import subprocess
import pandas as pd

from pathlib import Path
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


def test_cli_roundtrip_trend(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    examples_dir = repo_root / "data" / "examples"

    in_csv = examples_dir / "trend.csv"
    encoded = tmp_path / "trend.lsg2"
    out_csv = tmp_path / "trend_decoded.csv"

    # 1) ENCODE via CLI (usa gli stessi parametri che usi tu a mano)
    result_enc = subprocess.run(
        [
            "lasagna2",
            "encode",
            "--dt",
            "1",
            "--t0",
            "0",
            "--unit",
            "step",
            str(in_csv),
            str(encoded),
        ],
        capture_output=True,
        text=True,
    )
    assert result_enc.returncode == 0, result_enc.stderr

    # 2) DECODE via CLI (senza -o, se non è supportato)
    result_dec = subprocess.run(
        [
            "lasagna2",
            "decode",
            str(encoded),
            str(out_csv),
        ],
        capture_output=True,
        text=True,
    )
    assert result_dec.returncode == 0, result_dec.stderr

    # 3) Confronto CSV original vs decoded
    orig = pd.read_csv(in_csv)
    dec = pd.read_csv(out_csv)

    # Se il codec è lossless:
    pd.testing.assert_frame_equal(orig, dec)

    # Se è lossy, puoi usare una tolleranza numerica, ad es.:
    # pd.testing.assert_frame_equal(orig, dec, atol=1e-9, rtol=1e-9)


def test_cli_roundtrip_sine_noise(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    examples_dir = repo_root / "data" / "examples"

    in_csv = examples_dir / "sine_noise.csv"
    encoded = tmp_path / "sine_noise.lsg2"
    out_csv = tmp_path / "sine_noise_decoded.csv"

    result_enc = subprocess.run(
        [
            "lasagna2",
            "encode",
            "--dt",
            "1",  # usa gli stessi parametri che usi a mano
            "--t0",
            "0",
            "--unit",
            "step",
            str(in_csv),
            str(encoded),
        ],
        capture_output=True,
        text=True,
    )
    assert result_enc.returncode == 0, result_enc.stderr

    result_dec = subprocess.run(
        [
            "lasagna2",
            "decode",
            str(encoded),
            str(out_csv),
        ],
        capture_output=True,
        text=True,
    )
    assert result_dec.returncode == 0, result_dec.stderr

    orig_df = pd.read_csv(in_csv)
    dec_df = pd.read_csv(out_csv)

    orig = orig_df["# value"].tolist()
    dec = dec_df["# value"].tolist()

    # stessa lunghezza
    assert len(orig) == len(dec)

    # codec lossy: controlliamo l'errore medio, non l'uguaglianza esatta
    e = rmse(orig, dec)
    # soglia da tarare se serve, ma deve restare “piccola”
    assert e < 0.3
