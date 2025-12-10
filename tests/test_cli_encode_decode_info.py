# tests/test_cli_encode_decode_info.py
from __future__ import annotations
from pathlib import Path
from lasagna2.cli import main as lasagna_main

import csv
import subprocess
import math


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


def test_cli_export_tags_trend(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    examples_dir = repo_root / "data" / "examples"

    in_csv = examples_dir / "trend.csv"
    encoded = tmp_path / "trend.lsg2"
    tags_csv = tmp_path / "trend_tags.csv"

    # encode prima (parametri come negli altri test/README)
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

    # export-tags
    result_tags = subprocess.run(
        [
            "lasagna2",
            "export-tags",
            str(encoded),
            str(tags_csv),
        ],
        capture_output=True,
        text=True,
    )
    assert result_tags.returncode == 0, result_tags.stderr
    assert tags_csv.exists()

    # controlla intestazione e almeno una riga
    with tags_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == [
            "seg_id",
            "start",
            "end",
            "len",
            "pred",
            "patt",
            "sal",
            "energy",
            "mean",
            "slope",
            "Q",
        ]
        first_row = next(reader, None)
        assert first_row is not None
