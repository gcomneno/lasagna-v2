#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv

from pathlib import Path
from typing import Dict


def classify_profile(row: Dict[str, str]) -> str:
    """Assegna un cluster testuale a una riga di profiles.csv."""

    def f(name: str) -> float:
        try:
            return float(row.get(name, 0.0))
        except (TypeError, ValueError):
            return 0.0

    frac_flat = f("frac_flat")
    frac_trend = f("frac_trend")
    frac_osc = f("frac_oscillation")
    frac_noisy = f("frac_noisy")
    energy_avg = f("energy_avg")

    # 1) Dominanze nette
    if frac_osc >= 0.6:
        return "oscillation_dominated"

    if frac_trend >= 0.6:
        return "trend_dominated"

    if frac_flat >= 0.7 and frac_trend < 0.2 and frac_osc < 0.2:
        return "mostly_flat"

    if frac_noisy >= 0.5:
        return "noisy_dominated"

    # 2) Pattern "flat con bump di trend" (tipo flat_spike)
    if (
        frac_flat > 0.5
        and 0.1 < frac_trend < 0.4
        and frac_osc < 0.1
        and frac_noisy < 0.1
    ):
        return "flat_with_trend_bump"

    # 3) Mix trend + oscillation
    if frac_trend > 0.2 and frac_osc > 0.2:
        return "trend_oscillation_mix"

    # 4) Fallback in base all'energia
    if energy_avg > 15.0:
        return "high_energy_mixed"

    return "mixed_other"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Clusterizza i profili Lasagna (profiles.csv) in famiglie semantiche "
            "semplici, aggiungendo una colonna 'cluster'."
        )
    )
    parser.add_argument(
        "profiles_csv", help="Input profiles CSV (da batch_profile o export-profile)"
    )
    parser.add_argument("clusters_csv", help="Output CSV con colonna 'cluster'")

    args = parser.parse_args(argv)

    in_path = Path(args.profiles_csv)
    out_path = Path(args.clusters_csv)

    with in_path.open("r", encoding="utf-8") as f_in:
        reader = csv.DictReader(f_in)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    # Assicura la colonna cluster in coda
    out_fieldnames = list(fieldnames)
    if "cluster" not in out_fieldnames:
        out_fieldnames.append("cluster")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=out_fieldnames)
        writer.writeheader()

        for row in rows:
            cluster = classify_profile(row)
            row["cluster"] = cluster
            writer.writerow(row)


if __name__ == "__main__":
    main()
