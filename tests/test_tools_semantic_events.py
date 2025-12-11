# tests/test_tools_semantic_events.py
from __future__ import annotations

import csv
import subprocess

from pathlib import Path


def _write_trend_csv(path: Path, n: int = 200) -> None:
    """Trend semplice: x[i] = 0.1 * i."""
    with path.open("w", encoding="utf-8") as f:
        for i in range(n):
            f.write(f"{0.1 * i}\n")


def test_batch_profile_and_semantic_events_trend(tmp_path: Path) -> None:
    """
    Smoke-test per la pipeline:
    CSV -> lasagna2 encode -> batch_profile -> semantic_events.

    Ci aspettiamo che per un trend puro compaia almeno 'single_trend_regime'.
    """
    repo_root = Path(__file__).resolve().parents[1]

    in_csv = tmp_path / "trend.csv"
    encoded = tmp_path / "trend.lsg2"
    profiles_csv = tmp_path / "profiles.csv"
    events_csv = tmp_path / "events.csv"

    _write_trend_csv(in_csv)

    # 1) Encode con lasagna2 (CLI standard)
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

    # 2) Profilo batch usando tools/batch_profile.py
    batch_script = repo_root / "tools" / "batch_profile.py"
    result_prof = subprocess.run(
        [
            "python",
            str(batch_script),
            str(encoded),
            "-o",
            str(profiles_csv),
        ],
        capture_output=True,
        text=True,
    )
    assert result_prof.returncode == 0, result_prof.stderr
    assert profiles_csv.is_file(), "profiles.csv non generato"

    # 3) Eventi semantici usando tools/semantic_events.py
    events_script = repo_root / "tools" / "semantic_events.py"
    result_ev = subprocess.run(
        [
            "python",
            str(events_script),
            str(profiles_csv),
            str(events_csv),
        ],
        capture_output=True,
        text=True,
    )
    assert result_ev.returncode == 0, result_ev.stderr
    assert events_csv.is_file(), "events.csv non generato"

    # 4) Verifica che 'single_trend_regime' compaia per questo file
    events = []
    with events_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            events.append((row.get("file"), row.get("event_type")))

    # file name deve essere il .lsg2 (solo basename)
    filenames = {fname for (fname, _ev) in events}
    assert "trend.lsg2" in filenames

    types_for_trend = {ev for (fname, ev) in events if fname == "trend.lsg2"}
    assert "single_trend_regime" in types_for_trend
