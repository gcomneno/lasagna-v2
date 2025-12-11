from __future__ import annotations

from pathlib import Path
from lasagna2.cli import main as lasagna_main

import csv
import math


def _write_csv(path: Path, values) -> None:
    """Scrive una colonna di float in CSV, una per riga."""
    with path.open("w", encoding="utf-8") as f:
        for v in values:
            f.write(f"{v:.10g}\n")


def _read_values(path: Path):
    vals = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            vals.append(float(line.split(",")[0]))
    return vals


def _rmse(a, b) -> float:
    assert len(a) == len(b)
    if not a:
        return 0.0
    s = 0.0
    for x, y in zip(a, b):
        d = x - y
        s += d * d
    return math.sqrt(s / len(a))


def test_cli_encode_decode_roundtrip_trend(tmp_path: Path):
    """Roundtrip semplice via CLI encode/decode su un trend lineare."""
    in_csv = tmp_path / "trend.csv"
    encoded = tmp_path / "trend.lsg2"
    out_csv = tmp_path / "trend_decoded.csv"

    values = [0.1 * i for i in range(200)]
    _write_csv(in_csv, values)

    # encode
    lasagna_main(
        [
            "encode",
            str(in_csv),
            str(encoded),
            "--dt",
            "1",
            "--t0",
            "0",
            "--unit",
            "step",
            "--segment-mode",
            "adaptive",
            "--min-segment-length",
            "30",
            "--max-segment-length",
            "80",
            "--mse-threshold",
            "0.01",
            "--predictor",
            "auto",
            "--residual-coding",
            "varint",
        ]
    )

    assert encoded.exists() and encoded.stat().st_size > 0

    # decode
    lasagna_main(
        [
            "decode",
            str(encoded),
            str(out_csv),
        ]
    )

    assert out_csv.exists()

    orig = _read_values(in_csv)
    dec = _read_values(out_csv)
    assert len(orig) == len(dec)
    assert _rmse(orig, dec) < 1e-3


def test_cli_info_basic(tmp_path: Path, capsys):
    """Verifica che 'info' giri senza eccezioni e stampi intestazioni chiave."""
    in_csv = tmp_path / "trend.csv"
    encoded = tmp_path / "trend.lsg2"

    values = [0.1 * i for i in range(100)]
    _write_csv(in_csv, values)

    lasagna_main(
        [
            "encode",
            str(in_csv),
            str(encoded),
            "--dt",
            "1",
            "--t0",
            "0",
            "--unit",
            "step",
        ]
    )

    lasagna_main(["info", str(encoded), "-v"])

    out = capsys.readouterr().out
    assert "Time series" in out
    assert "Segments overview" in out
    assert "Stats:" in out
    assert "Motifs:" in out
    assert "Profile:" in out


def test_export_tags_csv(tmp_path: Path):
    """export-tags deve produrre un CSV con header e pattern sensati."""
    in_csv = tmp_path / "trend.csv"
    encoded = tmp_path / "trend.lsg2"
    tags_csv = tmp_path / "trend_tags.csv"

    values = [0.1 * i for i in range(200)]
    _write_csv(in_csv, values)

    lasagna_main(
        [
            "encode",
            str(in_csv),
            str(encoded),
            "--dt",
            "1",
            "--t0",
            "0",
            "--unit",
            "step",
        ]
    )

    lasagna_main(["export-tags", str(encoded), str(tags_csv)])

    assert tags_csv.exists()

    with tags_csv.open("r", encoding="utf-8") as f:
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
        # su trend liscio ci aspettiamo pattern "trend"
        assert first_row[5] == "trend"


def test_export_motifs_csv(tmp_path: Path):
    """export-motifs deve produrre almeno un motif su un trend lungo."""
    in_csv = tmp_path / "trend.csv"
    encoded = tmp_path / "trend.lsg2"
    motifs_csv = tmp_path / "trend_motifs.csv"

    values = [0.1 * i for i in range(200)]
    _write_csv(in_csv, values)

    lasagna_main(
        [
            "encode",
            str(in_csv),
            str(encoded),
            "--dt",
            "1",
            "--t0",
            "0",
            "--unit",
            "step",
        ]
    )

    lasagna_main(["export-motifs", str(encoded), str(motifs_csv)])

    assert motifs_csv.exists()

    with motifs_csv.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == [
            "motif_id",
            "seg_start",
            "seg_end",
            "n_segs",
            "pattern",
            "total_len",
            "total_energy",
        ]
        first_row = next(reader, None)
        assert first_row is not None
        # su trend liscio ci aspettiamo un solo motif di tipo "trend"
        assert first_row[4] == "trend"


def test_export_profile_csv(tmp_path: Path):
    in_csv = tmp_path / "trend.csv"
    encoded = tmp_path / "trend.lsg2"
    profile_csv = tmp_path / "trend_profile.csv"

    values = [0.1 * i for i in range(200)]
    _write_csv(in_csv, values)

    lasagna_main(
        [
            "encode",
            str(in_csv),
            str(encoded),
            "--dt",
            "1",
            "--t0",
            "0",
            "--unit",
            "step",
        ]
    )

    lasagna_main(["export-profile", str(encoded), str(profile_csv)])

    assert profile_csv.exists()

    with profile_csv.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        row = next(reader)

    assert header[0] == "file"
    assert row[0] == "trend.lsg2"
    # su trend puro ci aspettiamo tutto "trend"
    frac_trend_idx = header.index("frac_trend")
    assert float(row[frac_trend_idx]) > 0.9
