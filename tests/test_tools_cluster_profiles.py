from __future__ import annotations

import csv
import subprocess

from pathlib import Path


def _write_fake_profiles(path: Path) -> None:
    fieldnames = [
        "file",
        "n_points",
        "dt",
        "unit",
        "n_segments",
        "frac_flat",
        "frac_trend",
        "frac_oscillation",
        "frac_noisy",
        "sal_min",
        "sal_max",
        "sal_avg",
        "energy_min",
        "energy_max",
        "energy_avg",
        "n_motifs_flat",
        "n_motifs_trend",
        "n_motifs_oscillation",
        "n_motifs_noisy",
    ]

    rows = [
        # trend dominato
        {
            "file": "trend.lsg2",
            "n_points": "200",
            "dt": "1",
            "unit": "step",
            "n_segments": "2",
            "frac_flat": "0.0",
            "frac_trend": "1.0",
            "frac_oscillation": "0.0",
            "frac_noisy": "0.0",
            "sal_min": "2.0",
            "sal_max": "2.0",
            "sal_avg": "2.0",
            "energy_min": "7.2",
            "energy_max": "12.8",
            "energy_avg": "10.0",
            "n_motifs_flat": "0",
            "n_motifs_trend": "1",
            "n_motifs_oscillation": "0",
            "n_motifs_noisy": "0",
        },
        # oscillation dominata
        {
            "file": "sine_noise.lsg2",
            "n_points": "300",
            "dt": "1",
            "unit": "step",
            "n_segments": "6",
            "frac_flat": "0.0",
            "frac_trend": "0.296667",
            "frac_oscillation": "0.703333",
            "frac_noisy": "0.0",
            "sal_min": "2.0",
            "sal_max": "2.0",
            "sal_avg": "2.0",
            "energy_min": "10.5",
            "energy_max": "22.9",
            "energy_avg": "17.2",
            "n_motifs_flat": "0",
            "n_motifs_trend": "1",
            "n_motifs_oscillation": "1",
            "n_motifs_noisy": "0",
        },
        # flat con bump di trend
        {
            "file": "flat_spike.lsg2",
            "n_points": "300",
            "dt": "1",
            "unit": "arb",
            "n_segments": "4",
            "frac_flat": "0.786667",
            "frac_trend": "0.213333",
            "frac_oscillation": "0.0",
            "frac_noisy": "0.0",
            "sal_min": "1.0",
            "sal_max": "2.0",
            "sal_avg": "1.5",
            "energy_min": "1.12",
            "energy_max": "33.55",
            "energy_avg": "16.9",
            "n_motifs_flat": "2",
            "n_motifs_trend": "1",
            "n_motifs_oscillation": "0",
            "n_motifs_noisy": "0",
        },
    ]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def test_cluster_profiles_basic(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    profiles_csv = tmp_path / "profiles_fake.csv"
    clusters_csv = tmp_path / "clusters_fake.csv"

    _write_fake_profiles(profiles_csv)

    script = repo_root / "tools" / "cluster_profiles.py"
    result = subprocess.run(
        ["python", str(script), str(profiles_csv), str(clusters_csv)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert clusters_csv.is_file(), "clusters CSV non generato"

    clusters = {}
    with clusters_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            clusters[row["file"]] = row.get("cluster")

    assert clusters["trend.lsg2"] == "trend_dominated"
    assert clusters["sine_noise.lsg2"] == "oscillation_dominated"
    assert clusters["flat_spike.lsg2"] == "flat_with_trend_bump"
