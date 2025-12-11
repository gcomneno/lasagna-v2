#!/usr/bin/env python3
"""
generate_fake_alarms.py

Genera un CSV di allarmi sintetici per la demo Lasagna v2.

Schema output:

    timestamp,type,severity

Esempio d'uso:

    python tools/generate_fake_alarms.py data/demo/alarms.csv

Pattern temporali (1 ora totale, t0 fisso = 2025-01-01T00:00:00):

- 0–20 min   : regime quasi piatto, pochi allarmi di tipo A (severity bassa)
- 20–40 min  : regime "in peggioramento", più allarmi A/B, severity mista
- 40–60 min  : burst oscillatori di allarmi C (severity alta)
"""

from __future__ import annotations

import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera un CSV di allarmi sintetici (timestamp,type,severity)."
    )
    parser.add_argument(
        "output_csv",
        help="Path del CSV di output (es. data/demo/alarms.csv)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed per il generatore random (default: 42)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    random.seed(args.seed)

    out_path = Path(args.output_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    t0 = datetime(2025, 1, 1, 0, 0, 0)

    rows = []

    # 1) 0–20 minuti: pochi allarmi A, severity bassa
    t = t0
    end1 = t0 + timedelta(minutes=20)
    step1 = timedelta(seconds=30)
    while t < end1:
        if random.random() < 0.2:  # 20% di probabilità di un allarme
            rows.append(
                {
                    "timestamp": t.isoformat(),
                    "type": "A",
                    "severity": "1",
                }
            )
        t += step1

    # 2) 20–40 minuti: più allarmi A/B, severity 1–3
    t = end1
    end2 = t0 + timedelta(minutes=40)
    step2 = timedelta(seconds=20)
    while t < end2:
        if random.random() < 0.5:  # 50% di probabilità
            alarm_type = random.choice(["A", "B"])
            severity = random.choice(["1", "2", "3"])
            rows.append(
                {
                    "timestamp": t.isoformat(),
                    "type": alarm_type,
                    "severity": severity,
                }
            )
        t += step2

    # 3) 40–60 minuti: burst oscillatori di C (severity alta)
    t = end2
    end3 = t0 + timedelta(minutes=60)
    burst_every = timedelta(minutes=2)
    burst_size = 5
    burst_step = timedelta(seconds=5)

    while t < end3:
        # Inizio finestra burst
        tb = t
        for _ in range(burst_size):
            if tb >= end3:
                break
            rows.append(
                {
                    "timestamp": tb.isoformat(),
                    "type": "C",
                    "severity": str(random.choice([2, 3])),
                }
            )
            tb += burst_step
        t += burst_every

    # Scrittura CSV
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "type", "severity"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"[generate_fake_alarms] scritto {len(rows)} eventi in {out_path}")
    print(
        "[generate_fake_alarms] t0 = 2025-01-01T00:00:00 (coerente con prep_alarms + encode)"
    )
    print("[generate_fake_alarms] durata ≈ 60 minuti")


if __name__ == "__main__":
    main()
