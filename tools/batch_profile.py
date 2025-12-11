#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable, List

from lasagna2.cli import (
    read_lsg2_metadata_and_segments,
    classify_segment_pattern,
    extract_motifs,
)


PROFILE_HEADER = [
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


def compute_profile_row(path: Path) -> list[str]:
    data = path.read_bytes()
    ctx, n_points, segments, coding_type = read_lsg2_metadata_and_segments(data)

    dt = float(ctx.get("sampling", {}).get("dt", 1.0))
    unit = str(ctx.get("unit", "unknown"))
    n_segments = len(segments)

    patterns: list[str] = []
    saliences: list[int] = []
    lengths: list[int] = []
    energies: list[float] = []

    for seg in segments:
        length = seg.end_idx - seg.start_idx + 1
        lengths.append(length)
        pattern, sal, energy = classify_segment_pattern(seg)
        patterns.append(pattern)
        saliences.append(sal)
        energies.append(energy)

    total_points = n_points if n_points > 0 else sum(lengths) or 1

    # punti per pattern
    by_pattern_points: dict[str, int] = {}
    for seg in segments:
        length = seg.end_idx - seg.start_idx + 1
        pattern, _sal, _energy = classify_segment_pattern(seg)
        by_pattern_points[pattern] = by_pattern_points.get(pattern, 0) + length

    frac_flat = by_pattern_points.get("flat", 0) / total_points
    frac_trend = by_pattern_points.get("trend", 0) / total_points
    frac_osc = by_pattern_points.get("oscillation", 0) / total_points
    frac_noisy = by_pattern_points.get("noisy", 0) / total_points

    # salienza
    if saliences:
        sal_min = min(saliences)
        sal_max = max(saliences)
        sal_avg = sum(saliences) / len(saliences)
    else:
        sal_min = sal_max = sal_avg = 0.0

    # energia
    if energies:
        e_min = min(energies)
        e_max = max(energies)
        e_avg = sum(energies) / len(energies)
    else:
        e_min = e_max = e_avg = 0.0

    # motifs per pattern
    motifs = extract_motifs(segments)
    by_pattern_motifs: dict[str, int] = {}
    for m in motifs:
        by_pattern_motifs[m.pattern] = by_pattern_motifs.get(m.pattern, 0) + 1

    n_motifs_flat = by_pattern_motifs.get("flat", 0)
    n_motifs_trend = by_pattern_motifs.get("trend", 0)
    n_motifs_oscillation = by_pattern_motifs.get("oscillation", 0)
    n_motifs_noisy = by_pattern_motifs.get("noisy", 0)

    return [
        path.name,
        str(n_points),
        f"{dt:g}",
        unit,
        str(n_segments),
        f"{frac_flat:.6f}",
        f"{frac_trend:.6f}",
        f"{frac_osc:.6f}",
        f"{frac_noisy:.6f}",
        f"{sal_min:.3f}",
        f"{sal_max:.3f}",
        f"{sal_avg:.3f}",
        f"{e_min:.6f}",
        f"{e_max:.6f}",
        f"{e_avg:.6f}",
        str(n_motifs_flat),
        str(n_motifs_trend),
        str(n_motifs_oscillation),
        str(n_motifs_noisy),
    ]


def iter_lsg2_files(inputs: Iterable[str], recursive: bool) -> List[Path]:
    files: list[Path] = []
    for raw in inputs:
        p = Path(raw)
        if p.is_dir():
            if recursive:
                for sub in p.rglob("*.lsg2"):
                    if sub.is_file():
                        files.append(sub)
            else:
                for sub in p.glob("*.lsg2"):
                    if sub.is_file():
                        files.append(sub)
        elif p.is_file() and p.suffix == ".lsg2":
            files.append(p)
    # dedup e sort
    uniq = sorted({f.resolve() for f in files})
    return list(uniq)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Batch semantic profiling for Lasagna v2 .lsg2 files"
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="input directories and/or .lsg2 files",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="output CSV path (profiles)",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="recurse into subdirectories when scanning dirs",
    )

    args = parser.parse_args(argv)

    lsg2_files = iter_lsg2_files(args.inputs, recursive=args.recursive)
    if not lsg2_files:
        raise SystemExit("No .lsg2 files found in the given inputs")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PROFILE_HEADER)
        for path in lsg2_files:
            row = compute_profile_row(path)
            writer.writerow(row)


if __name__ == "__main__":
    main()
