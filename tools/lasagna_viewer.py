#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import List, Dict, Any

import matplotlib.pyplot as plt


def load_tags(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # normalizza qualche campo numerico
            for key in ("seg_id", "start", "end", "len", "sal"):
                if key in row and row[key] != "":
                    row[key] = int(float(row[key]))
            for key in ("energy", "mean", "slope", "Q"):
                if key in row and row[key] != "":
                    row[key] = float(row[key])
            rows.append(row)
    return rows


def plot_segments_position(tags: List[Dict[str, Any]], title: str | None = None):
    """Plot semplice: segmenti come barre orizzontali, colorati per pattern."""
    if not tags:
        return None

    fig, ax = plt.subplots()
    y = 0
    yticks = []
    ylabels = []

    for row in tags:
        start = row["start"]
        end = row["end"]
        patt = row.get("patt", "unknown")

        ax.hlines(y, start, end, linewidth=4)
        yticks.append(y)
        ylabels.append(f"{row['seg_id']} ({patt})")
        y += 1

    ax.set_xlabel("time index")
    ax.set_ylabel("segment id (pattern)")
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels)
    if title:
        ax.set_title(title)
    ax.grid(True, axis="x", linestyle="--", alpha=0.3)
    plt.tight_layout()
    return fig


def plot_energy_by_segment(tags: List[Dict[str, Any]], title: str | None = None):
    if not tags:
        return None

    seg_ids = [row["seg_id"] for row in tags]
    energies = [row.get("energy", 0.0) for row in tags]

    fig, ax = plt.subplots()
    ax.bar(seg_ids, energies)
    ax.set_xlabel("segment id")
    ax.set_ylabel("energy")
    if title:
        ax.set_title(title)
    ax.grid(True, axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout()
    return fig


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Simple viewer for Lasagna v2 export-tags CSV."
    )
    parser.add_argument("tags_csv", help="CSV file produced by 'lasagna2 export-tags'")
    parser.add_argument(
        "--no-position",
        action="store_true",
        help="disable segments position plot",
    )
    parser.add_argument(
        "--no-energy",
        action="store_true",
        help="disable energy-by-segment plot",
    )

    args = parser.parse_args(argv)
    tags_path = Path(args.tags_csv)
    tags = load_tags(tags_path)

    title = tags_path.name

    figs = []

    if not args.no_position:
        fig_pos = plot_segments_position(tags, title=title + " – segments")
        if fig_pos is not None:
            figs.append(("segments", fig_pos))

    if not args.no_energy:
        fig_energy = plot_energy_by_segment(tags, title=title + " – energy")
        if fig_energy is not None:
            figs.append(("energy", fig_energy))

    # Salva sempre i plot in PNG accanto al CSV, niente plt.show() (backend Agg-friendly)
    for kind, fig in figs:
        out_path = tags_path.with_suffix(f".{kind}.png")
        fig.savefig(out_path)
        print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
