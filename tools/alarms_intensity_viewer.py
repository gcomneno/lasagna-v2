#!/usr/bin/env python3
"""
alarms_intensity_viewer.py

Piccolo viewer per serie di intensità allarmi generate da prep_alarms.py.

Input:  CSV con una colonna "value" (come data/demo/alarms_intensity.csv)
Output: PNG con il grafico linea dell'intensità nel tempo.

Uso tipico:

    python tools/alarms_intensity_viewer.py data/demo/alarms_intensity.csv

Opzionalmente:

    python tools/alarms_intensity_viewer.py data/demo/alarms_intensity.csv \
        -o data/demo/alarms_intensity.png
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Visualizza una serie di intensità allarmi (CSV con colonna 'value') "
            "come grafico PNG."
        )
    )
    parser.add_argument(
        "csv_path",
        help="Path del CSV di input (es. data/demo/alarms_intensity.csv)",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output_png",
        help=(
            "Path del PNG di output. "
            "Default: stesso stem del CSV con suffisso '.alarms.png'"
        ),
    )
    return parser.parse_args(argv)


def load_values(path: Path) -> List[float]:
    values: List[float] = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        # supporta sia 'value' come prima colonna che CSV senza header
        for row in reader:
            if not row:
                continue
            try:
                v = float(row[0])
            except ValueError:
                continue
            values.append(v)
    return values


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)

    csv_path = Path(args.csv_path)
    values = load_values(csv_path)
    if not values:
        print(f"Nessun valore valido trovato in {csv_path}")
        return

    xs = list(range(len(values)))

    fig, ax = plt.subplots()
    ax.plot(xs, values)
    ax.set_title(f"Alarm intensity – {csv_path.name}")
    ax.set_xlabel("bin index")
    ax.set_ylabel("intensity (arbitrary units)")

    out_path = (
        Path(args.output_png)
        if args.output_png
        else csv_path.with_suffix(".alarms.png")
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
