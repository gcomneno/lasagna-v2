#!/usr/bin/env python3
"""
generate_demo_data.py

Genera alcune serie temporali sintetiche per la demo di Lasagna v2.

Output (tutte con una colonna "value"):

- data/demo/trend.csv
- data/demo/sine_noise.csv
- data/demo/flat_spike.csv
- data/demo/ramp_then_burst.csv
- data/demo/multi_bump.csv
"""

from __future__ import annotations

import csv
import math
import random
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / "data" / "demo"


def write_csv(path: Path, values) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["value"])
        for v in values:
            w.writerow([f"{float(v):.6f}"])


def make_trend(
    n: int = 300, start: float = 0.0, slope: float = 0.05, noise: float = 0.0
):
    vals = []
    for i in range(n):
        v = start + slope * i
        if noise > 0.0:
            v += random.uniform(-noise, noise)
        vals.append(v)
    return vals


def make_sine_noise(
    n: int = 300,
    amplitude: float = 1.0,
    period: float = 60.0,
    trend_slope: float = 0.01,
    noise: float = 0.1,
):
    vals = []
    for i in range(n):
        sin_part = amplitude * math.sin(2 * math.pi * i / period)
        trend_part = trend_slope * i
        v = sin_part + trend_part + random.uniform(-noise, noise)
        vals.append(v)
    return vals


def make_flat_spike(
    n: int = 300,
    base: float = 1.5,
    spike_height: float = 1.5,
    spike_width: int = 30,
):
    vals = [base] * n
    center = n // 2
    half_w = spike_width // 2
    for i in range(center - half_w, center + half_w):
        if 0 <= i < n:
            vals[i] = base + spike_height
    return vals


def make_ramp_then_burst(
    n: int = 300,
    base: float = 0.0,
    ramp_slope: float = 0.03,
    noise_ramp: float = 0.1,
    burst_start_frac: float = 0.5,
    burst_amp: float = 6.0,
    burst_period: float = 10.0,
    noise_burst: float = 0.2,
):
    """Prima metà ~trend, seconda metà ~trend + oscillazioni grosse (burst)."""
    vals = []
    burst_start = int(n * burst_start_frac)
    for i in range(n):
        trend = base + ramp_slope * i
        if i < burst_start:
            v = trend + random.uniform(-noise_ramp, noise_ramp)
        else:
            osc = burst_amp * math.sin(2 * math.pi * (i - burst_start) / burst_period)
            v = trend + osc + random.uniform(-noise_burst, noise_burst)
        vals.append(v)
    return vals


def make_multi_bump(
    n: int = 300,
    base: float = 1.0,
    bump_height: float = 2.0,
    bump_width: int = 15,
    bump_positions: tuple[int, int, int] = (60, 150, 240),
    local_noise: float = 0.1,
):
    """Serie piatta con 3 spike separati (multi_bump)."""
    vals = [base + random.uniform(-local_noise, local_noise) for _ in range(n)]
    half_w = bump_width // 2
    for center in bump_positions:
        for i in range(center - half_w, center + half_w):
            if 0 <= i < n:
                vals[i] = base + bump_height + random.uniform(-local_noise, local_noise)
    return vals


def main() -> None:
    random.seed(42)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    trend_vals = make_trend()
    sine_vals = make_sine_noise()
    flat_spike_vals = make_flat_spike()
    ramp_then_burst_vals = make_ramp_then_burst()
    multi_bump_vals = make_multi_bump()

    write_csv(OUT_DIR / "trend.csv", trend_vals)
    write_csv(OUT_DIR / "sine_noise.csv", sine_vals)
    write_csv(OUT_DIR / "flat_spike.csv", flat_spike_vals)
    write_csv(OUT_DIR / "ramp_then_burst.csv", ramp_then_burst_vals)
    write_csv(OUT_DIR / "multi_bump.csv", multi_bump_vals)

    print(f"Demo CSV generati in {OUT_DIR}")


if __name__ == "__main__":
    main()
