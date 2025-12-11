#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv

from pathlib import Path
from typing import Dict, List, Any


def infer_events(profile: Dict[str, Any]) -> List[str]:
    """Dato un profilo (una riga del profiles.csv), deduce alcuni 'eventi' semantici."""
    events: List[str] = []

    frac_trend = float(profile.get("frac_trend", 0.0))
    frac_osc = float(profile.get("frac_oscillation", 0.0))
    frac_noisy = float(profile.get("frac_noisy", 0.0))
    frac_flat = float(profile.get("frac_flat", 0.0))
    energy_avg = float(profile.get("energy_avg", 0.0))
    n_motifs_trend = int(profile.get("n_motifs_trend", 0))
    n_motifs_oscillation = int(profile.get("n_motifs_oscillation", 0))

    # Dominanza di oscillazione
    if frac_osc > 0.6 and n_motifs_oscillation >= 1:
        events.append("oscillation_dominated")

    # Dominanza di trend
    if frac_trend > 0.6 and n_motifs_trend == 1:
        events.append("single_trend_regime")
    elif 0.3 < frac_trend <= 0.6 and n_motifs_trend >= 1:
        events.append("mixed_trend_regime")

    # Mix trend + oscillation
    if frac_trend > 0.2 and frac_osc > 0.2:
        events.append("trend_oscillation_mix")

    # Pattern: flat con uno o pochi bump di trend (tipo flat_spike)
    if (
        frac_flat > 0.5
        and 0.1 < frac_trend < 0.4
        and n_motifs_trend == 1
        and frac_osc < 0.1
        and frac_noisy < 0.1
    ):
        events.append("flat_with_trend_bump")

    # Rumore significativo
    if frac_noisy > 0.3:
        events.append("noisy_segments_present")

    # Energia complessiva alta
    if energy_avg > 15.0:
        events.append("high_energy")

    if not events:
        events.append("none")

    return events


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Derive simple semantic events from a batch profiles CSV "
            "(produced by batch_profile.py or 'lasagna2 export-profile')."
        )
    )
    parser.add_argument("profiles_csv", help="input profiles CSV")
    parser.add_argument(
        "events_csv",
        nargs="?",
        help="output events CSV (positional, alternative to -o/--output)",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="events_csv_o",
        help="output events CSV (alternative to positional events_csv)",
    )

    args = parser.parse_args(argv)

    if args.events_csv and args.events_csv_o:
        parser.error(
            "Specify output only as positional 'events_csv' or only with -o/--output, not both."
        )

    out = args.events_csv or args.events_csv_o
    if not out:
        parser.error(
            "You must specify the output events CSV (positional or via -o/--output)."
        )

    args.events_csv = out
    return args


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    in_path = Path(args.profiles_csv)
    out_path = Path(args.events_csv)

    with in_path.open("r", encoding="utf-8") as f_in:
        reader = csv.DictReader(f_in)
        rows = list(reader)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8", newline="") as f_out:
        writer = csv.writer(f_out)
        writer.writerow(["file", "event_type"])
        for row in rows:
            file_name = row.get("file", "")
            events = infer_events(row)
            for ev in events:
                writer.writerow([file_name, ev])


if __name__ == "__main__":
    main()
