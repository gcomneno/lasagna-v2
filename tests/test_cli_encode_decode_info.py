# tests/test_cli_encode_decode_info.py
from __future__ import annotations

import math
from pathlib import Path

from lasagna2.cli import main as lasagna_main


def _write_csv(path: Path, values) -> None:
    with path.open("w", encoding="utf-8") as f:
        for v in values:
            f.write(f"{v:.10g}\n")


def _read_csv(path: Path):
    vals = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            vals.append(float(line.split(",")[0]))
    return vals


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


def test_cli_encode_decode_and_info(tmp_path, capsys):
    # Genera un piccolo trend
    values = [0.1 * i for i in range(50)]
    inp = tmp_path / "trend.csv"
    out_lsg2 = tmp_path / "trend.lsg2"
    out_dec = tmp_path / "trend_decoded.csv"

    _write_csv(inp, values)

    # encode via CLI
    lasagna_main(
        [
            "encode",
            str(inp),
            str(out_lsg2),
            "--dt",
            "60",
            "--t0",
            "2025-01-01T00:00:00Z",
            "--unit",
            "kW",
            "--segment-mode",
            "adaptive",
            "--min-segment-length",
            "10",
            "--max-segment-length",
            "30",
            "--mse-threshold",
            "0.01",
            "--predictor",
            "auto",
            "--residual-coding",
            "varint",
            "-v",
        ]
    )
    assert out_lsg2.exists()
    assert out_lsg2.stat().st_size > 0

    # info via CLI (solo check che non esploda)
    lasagna_main(["info", str(out_lsg2), "-v"])
    captured = capsys.readouterr()
    # deve stampare almeno "Segments overview"
    assert "Segments overview" in captured.out

    # decode via CLI
    lasagna_main(["decode", str(out_lsg2), str(out_dec)])
    assert out_dec.exists()

    dec_values = _read_csv(out_dec)
    assert len(dec_values) == len(values)
    e = rmse(values, dec_values)
    assert e < 1e-3
