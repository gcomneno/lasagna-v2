#!/usr/bin/env python3
"""
prep_alarms.py

Pre-elabora una sequenza di allarmi (eventi discreti multivalore) in una
serie temporale univariata di "intensità allarmi" compatibile con Lasagna v2.

Input atteso (CSV con header almeno):
    timestamp,type,severity

Esempio:
    2025-01-01T00:00:03,A,2
    2025-01-01T00:00:10,B,1
    ...

Output (CSV):
    value
    0.0
    1.0
    3.0
    ...

Ogni riga di output è l'intensità nella finestra [t0 + k*dt, t0 + (k+1)*dt).

Uso tipico:

    python tools/prep_alarms.py alarms.csv data/demo/alarms_intensity.csv --dt 60

Poi:

    lasagna2 encode --dt 60 --t0 2025-01-01T00:00:00 --unit s \
        data/demo/alarms_intensity.csv \
        data/demo/alarms_intensity.lsg2

(t0 deve essere allineato a quello stampato da questo script)
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class AlarmEvent:
    ts: datetime
    alarm_type: str
    severity: float


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Aggrega un log di allarmi (timestamp,type,severity) in una serie "
            "temporale univariata di intensità allarmi."
        )
    )
    parser.add_argument("input_csv", help="CSV di input con allarmi")
    parser.add_argument("output_csv", help="CSV di output con colonna 'value'")
    parser.add_argument(
        "--dt",
        type=float,
        default=60.0,
        help=("Passo temporale (in secondi) della serie di output. " "Default: 60.0"),
    )
    parser.add_argument(
        "--time-column",
        default="timestamp",
        help="Nome della colonna timestamp in input (default: timestamp)",
    )
    parser.add_argument(
        "--type-column",
        default="type",
        help="Nome della colonna tipo allarme in input (default: type)",
    )
    parser.add_argument(
        "--severity-column",
        default="severity",
        help="Nome della colonna severità in input (default: severity)",
    )
    parser.add_argument(
        "--time-format",
        default=None,
        help=(
            "Formato datetime per datetime.strptime(). "
            "Se omesso, si usa datetime.fromisoformat()."
        ),
    )

    return parser.parse_args(argv)


def parse_timestamp(raw: str, fmt: Optional[str]) -> datetime:
    raw = raw.strip()
    if fmt:
        return datetime.strptime(raw, fmt)
    # fallback ISO 8601
    return datetime.fromisoformat(raw)


def load_events(
    path: Path,
    time_col: str,
    type_col: str,
    severity_col: str,
    time_fmt: Optional[str],
) -> List[AlarmEvent]:
    events: List[AlarmEvent] = []

    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get(time_col):
                continue
            ts = parse_timestamp(row[time_col], time_fmt)
            alarm_type = (row.get(type_col) or "").strip()
            try:
                severity = float(row.get(severity_col, 1.0))
            except ValueError:
                severity = 1.0

            events.append(AlarmEvent(ts=ts, alarm_type=alarm_type, severity=severity))

    events.sort(key=lambda e: e.ts)
    return events


def build_type_weights(events: List[AlarmEvent]) -> Dict[str, float]:
    """
    Assegna un peso base per tipo allarme.

    Strategia minimale:
        - ordina i tipi per frequenza,
        - assegna pesi crescenti: 1.0, 1.5, 2.0, ...

    Così i tipi più "rari" hanno un po' più peso (intuizione: segnali più insoliti).
    """
    from collections import Counter

    counter = Counter(e.alarm_type or "_" for e in events)
    types_sorted = sorted(counter.items(), key=lambda kv: (kv[1], kv[0]))

    weights: Dict[str, float] = {}
    base = 1.0
    step = 0.5

    for alarm_type, _count in types_sorted:
        weights[alarm_type] = base
        base += step

    return weights


def aggregate_to_timeseries(
    events: List[AlarmEvent],
    dt_seconds: float,
) -> tuple[List[float], datetime, float]:
    """
    Aggrega gli eventi su una griglia temporale uniforme.

    Ritorna:
        values: lista di intensità per ciascun bin
        t0:     timestamp del primo bin
        dt:     passo in secondi (uguale a dt_seconds)
    """
    if not events:
        from datetime import datetime as _dt

        return [], _dt.fromtimestamp(0), float(dt_seconds)

    dt = float(dt_seconds)
    t0 = events[0].ts
    t_last = events[-1].ts

    total_seconds = (t_last - t0).total_seconds()
    n_bins = int(total_seconds // dt) + 1

    values: List[float] = [0.0 for _ in range(n_bins)]

    # pesi per tipo
    type_weights = build_type_weights(events)

    for ev in events:
        delta = (ev.ts - t0).total_seconds()
        if delta < 0:
            idx = 0
        else:
            idx = int(delta // dt)
        if idx >= n_bins:
            extra = idx + 1 - n_bins
            values.extend([0.0] * extra)
            n_bins = idx + 1

        w_type = type_weights.get(ev.alarm_type or "_", 1.0)
        values[idx] += w_type * ev.severity

    return values, t0, dt


def write_series(path: Path, values: List[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["value"])
        for v in values:
            writer.writerow([f"{v:.6f}"])


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)

    in_path = Path(args.input_csv)
    out_path = Path(args.output_csv)

    events = load_events(
        in_path,
        time_col=args.time_column,
        type_col=args.type_column,
        severity_col=args.severity_column,
        time_fmt=args.time_format,
    )

    if not events:
        print("Nessun evento caricato, output vuoto.")
        write_series(out_path, [])
        return

    values, t0, dt = aggregate_to_timeseries(events, args.dt)
    write_series(out_path, values)

    # Info utili per l'encode Lasagna
    print(f"[prep_alarms] scritto {len(values)} punti in {out_path}")
    print(f"[prep_alarms] t0 suggerito per lasagna2 encode: {t0.isoformat()}")
    print(f"[prep_alarms] dt (s): {dt}")


if __name__ == "__main__":
    main()
