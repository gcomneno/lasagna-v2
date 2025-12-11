# lasagna2/cli.py
from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .core import (
    TimeSeries,
    SegmentEntry,
    FILE_HEADER_STRUCT,
    SEGMENT_ENTRY_STRUCT,
    RESIDUAL_SECTION_HEADER_STRUCT,
    encode_timeseries,
    decode_timeseries,
)

import json


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------
def _load_csv_values(path: Path) -> List[float]:
    """Carica la prima colonna numerica da un CSV (ignorando righe vuote / commenti)."""
    values: List[float] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            try:
                values.append(float(parts[0]))
            except ValueError:
                continue
    return values


def load_timeseries_from_csv(path: Path, dt: float, t0: str, unit: str) -> TimeSeries:
    values = _load_csv_values(path)
    return TimeSeries(values=values, dt=dt, t0=t0, unit=unit)


def save_timeseries_to_csv(ts: TimeSeries, path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for v in ts.values:
            f.write(f"{v:.10g}\n")


# ---------------------------------------------------------------------------
# Pattern classification per segmento
# ---------------------------------------------------------------------------
def classify_segment_pattern(seg: SegmentEntry) -> tuple[str, int, float]:
    """
    Classifica un segmento in (pattern_type, salience, energy).

    pattern_type ∈ {"flat", "trend", "oscillation", "noisy"}
    salience ∈ {0, 1, 2}
    energy ~ (|slope| + Q) * length
    """
    length = seg.end_idx - seg.start_idx + 1
    if length <= 0:
        return "noisy", 0, 0.0

    a_slope = abs(seg.slope)
    Q = seg.quant_step_Q
    predictor_type = seg.predictor_type

    # soglie empiriche MVP (tarabili)
    SLOPE_FLAT = 0.002
    SLOPE_TREND = 0.01
    Q_LOW = 0.05
    Q_OSC_MIN = 0.2  # nuova: abbastanza "energetico" da sembrare oscillazione
    Q_NOISY_MIN = 0.4  # sopra questo consideriamo davvero "noisy"

    # 1) Flat: praticamente piatto e poco rumore
    if a_slope < SLOPE_FLAT and Q < Q_LOW:
        pattern = "flat"

    # 2) Trend: retta evidente, anche se c'è rumore
    elif predictor_type == 1 and a_slope >= SLOPE_TREND:
        pattern = "trend"

    # 3) Oscillation: slope medio basso, ma Q significativo
    elif (
        predictor_type in (1, 2)
        and a_slope < SLOPE_TREND
        and Q >= Q_OSC_MIN
        and Q < Q_NOISY_MIN
    ):
        pattern = "oscillation"

    # 4) Noisy: tutto il resto, soprattutto Q molto alto
    else:
        pattern = "noisy"

    # salience: energia grezza
    energy = (a_slope * length) + (Q * length)
    if energy < 1.0:
        salience = 0
    elif energy < 5.0:
        salience = 1
    else:
        salience = 2

    return pattern, salience, energy


# ---------------------------------------------------------------------------
# Motifs (layer 2)
# ---------------------------------------------------------------------------
@dataclass
class Motif:
    start_seg: int
    end_seg: int
    pattern: str
    total_len: int
    total_energy: float


def extract_motifs(segments: List[SegmentEntry]) -> List[Motif]:
    """Raggruppa segmenti consecutivi con lo stesso pattern in motifs."""
    if not segments:
        return []

    motifs: List[Motif] = []

    # primo segmento
    cur_start = 0
    cur_pattern, _sal, cur_energy = classify_segment_pattern(segments[0])
    cur_len = segments[0].end_idx - segments[0].start_idx + 1

    for idx, seg in enumerate(segments[1:], start=1):
        patt, _sal, energy = classify_segment_pattern(seg)
        length = seg.end_idx - seg.start_idx + 1

        if patt == cur_pattern:
            cur_len += length
            cur_energy += energy
        else:
            motifs.append(
                Motif(
                    start_seg=cur_start,
                    end_seg=idx - 1,
                    pattern=cur_pattern,
                    total_len=cur_len,
                    total_energy=cur_energy,
                )
            )
            cur_start = idx
            cur_pattern = patt
            cur_len = length
            cur_energy = energy

    motifs.append(
        Motif(
            start_seg=cur_start,
            end_seg=len(segments) - 1,
            pattern=cur_pattern,
            total_len=cur_len,
            total_energy=cur_energy,
        )
    )

    return motifs


# ---------------------------------------------------------------------------
# Lettura metadata + segmenti da .lsg2 (senza decodificare residui)
# ---------------------------------------------------------------------------
def read_lsg2_metadata_and_segments(
    data: bytes,
) -> tuple[dict, int, List[SegmentEntry], int]:
    """
    Ritorna (ctx, n_points, segments, coding_type) da un buffer .lsg2.

    Legge header + context JSON + tabella segmenti + header sezione residui.
    Non decodifica i blocchi di residui.
    """
    offset = 0
    if len(data) < FILE_HEADER_STRUCT.size:
        raise ValueError("Data too short to contain header")

    (
        magic,
        version,
        flags,
        header_len,
        n_points,
        n_segments,
        reserved1,
        reserved2,
    ) = FILE_HEADER_STRUCT.unpack_from(data, offset)
    offset += FILE_HEADER_STRUCT.size

    if magic != b"LSG2":
        raise ValueError("Invalid magic, not an LSG2 file")
    if version != 1:
        raise ValueError(f"Unsupported LSG2 version {version} (expected 1 for MVP)")

    # sanity check basica per evitare allocazioni folli
    if n_points < 0 or n_points > 10_000_000:
        raise ValueError(f"Suspicious n_points={n_points}")
    if n_segments < 0 or n_segments > 1_000_000:
        raise ValueError(f"Suspicious n_segments={n_segments}")
    if header_len < 0 or header_len > len(data) - offset:
        raise ValueError("header_len is inconsistent with data size")

    # Context JSON
    if len(data) < offset + header_len:
        raise ValueError("Data too short for context JSON")
    ctx_bytes = data[offset : offset + header_len]
    offset += header_len

    ctx = json.loads(ctx_bytes.decode("utf-8"))

    # Segment table
    segments: List[SegmentEntry] = []
    for _ in range(n_segments):
        if len(data) < offset + SEGMENT_ENTRY_STRUCT.size:
            raise ValueError("Data too short for segment table")
        (
            start_idx,
            end_idx,
            predictor_type,
            _pad1,
            _pad2,
            _pad3,
            mean,
            slope,
            intercept,
            Q,
            seed_value,
        ) = SEGMENT_ENTRY_STRUCT.unpack_from(data, offset)
        offset += SEGMENT_ENTRY_STRUCT.size
        segments.append(
            SegmentEntry(
                start_idx=start_idx,
                end_idx=end_idx,
                predictor_type=predictor_type,
                mean=mean,
                slope=slope,
                intercept=intercept,
                quant_step_Q=Q,
                seed_value=seed_value,
            )
        )

    # Residual section header (solo coding_type)
    if len(data) < offset + RESIDUAL_SECTION_HEADER_STRUCT.size:
        raise ValueError("Data too short for residual section header")
    coding_type, _, _, _ = RESIDUAL_SECTION_HEADER_STRUCT.unpack_from(data, offset)

    return ctx, n_points, segments, coding_type


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lasagna",
        description="Lasagna v2 – univariate time series codec (MVP)",
    )
    sub = p.add_subparsers(dest="command")

    # encode
    p_enc = sub.add_parser("encode", help="encode CSV into .lsg2")
    p_enc.add_argument("input", type=str, help="input CSV file")
    p_enc.add_argument("output", type=str, help="output .lsg2 file")
    p_enc.add_argument(
        "--dt", type=float, required=True, help="sampling interval (seconds)"
    )
    p_enc.add_argument("--t0", type=str, required=True, help="start timestamp")
    p_enc.add_argument("--unit", type=str, required=True, help="unit of measure")
    p_enc.add_argument(
        "--segment-mode",
        type=str,
        default="adaptive",
        choices=["fixed", "adaptive"],
        help="segmentation mode (fixed/adaptive)",
    )
    p_enc.add_argument(
        "--segment-length",
        type=int,
        default=64,
        help="segment length for fixed mode",
    )
    p_enc.add_argument(
        "--min-segment-length",
        type=int,
        default=32,
        help="min segment length for adaptive mode",
    )
    p_enc.add_argument(
        "--max-segment-length",
        type=int,
        default=128,
        help="max segment length for adaptive mode",
    )
    p_enc.add_argument(
        "--mse-threshold",
        type=float,
        default=0.5,
        help="max allowed MSE per segment in adaptive mode",
    )
    p_enc.add_argument(
        "--predictor",
        type=str,
        default="linear",
        help="predictor (mean/linear/rw/auto)",
    )
    p_enc.add_argument(
        "--residual-coding",
        type=str,
        default="varint",
        choices=["raw", "varint"],
        help="residual coding type",
    )
    p_enc.set_defaults(func=cli_encode)

    # decode
    p_dec = sub.add_parser("decode", help="decode .lsg2 into CSV")
    p_dec.add_argument("input", type=str, help="input .lsg2 file")
    p_dec.add_argument("output", type=str, help="output CSV file")
    p_dec.set_defaults(func=cli_decode)

    # info
    p_info = sub.add_parser(
        "info",
        help="inspect .lsg2 file metadata and segments",
    )
    p_info.add_argument("input", type=str, help="input .lsg2 file")
    p_info.add_argument(
        "-v", "--verbose", action="store_true", help="show detailed stats"
    )
    p_info.set_defaults(func=cli_info)

    # export-tags
    p_tags = sub.add_parser("export-tags", help="export segment tags to CSV")
    p_tags.add_argument("input", type=str, help="input .lsg2 file")
    p_tags.add_argument("output", type=str, help="output CSV file with segment tags")
    p_tags.set_defaults(func=cli_export_tags)

    # export-motifs
    p_motifs = sub.add_parser("export-motifs", help="export motifs to CSV")
    p_motifs.add_argument("input", type=str, help="input .lsg2 file")
    p_motifs.add_argument("output", type=str, help="output CSV file with motifs")
    p_motifs.set_defaults(func=cli_export_motifs)

    # export-profile
    p_profile = sub.add_parser(
        "export-profile",
        help="export a compact semantic profile to CSV",
    )
    p_profile.add_argument("input", type=str, help="input .lsg2 file")
    p_profile.add_argument("output", type=str, help="output CSV file with profile")
    p_profile.set_defaults(func=cli_export_profile)

    return p


def cli_encode(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    output_path = Path(args.output)

    ts = load_timeseries_from_csv(input_path, dt=args.dt, t0=args.t0, unit=args.unit)

    data = encode_timeseries(
        ts,
        segment_length=args.segment_length,
        predictor=args.predictor,
        segment_mode=args.segment_mode,
        min_segment_length=args.min_segment_length,
        max_segment_length=args.max_segment_length,
        mse_threshold=args.mse_threshold,
        residual_coding=args.residual_coding,
    )

    output_path.write_bytes(data)


def cli_decode(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    output_path = Path(args.output)

    data = input_path.read_bytes()
    ts = decode_timeseries(data)
    save_timeseries_to_csv(ts, output_path)


def cli_info(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    data = input_path.read_bytes()

    ctx, n_points, segments, coding_type = read_lsg2_metadata_and_segments(data)

    # header
    print(f"File        : {input_path.name}")
    print(f"Size        : {len(data)} bytes")
    print("Format      : LSG2 (MVP v1, univariate)")
    print()

    print("Time series :")
    dt = float(ctx.get("sampling", {}).get("dt", 1.0))
    t0 = str(ctx.get("sampling", {}).get("t0", "1970-01-01T00:00:00Z"))
    unit = str(ctx.get("unit", "unknown"))
    print(f"  points    : {n_points}")
    print(f"  dt        : {dt} s")
    print(f"  t0        : {t0}")
    print(f"  unit      : {unit}")
    print(f"  segments  : {len(segments)}")
    print()

    # Compression estimate (vs float64)
    raw_size = n_points * 8
    ratio = raw_size / len(data) if len(data) > 0 else 0.0
    print("Compression (vs raw float64):")
    print(f"  raw_size  : {raw_size} bytes")
    print(f"  ratio     : {ratio:.3f}x  (raw/ls g2)")
    print()

    predictor_names = {
        0: "mean",
        1: "linear",
        2: "rw",
    }

    patterns: List[str] = []
    saliences: List[int] = []
    lengths: List[int] = []
    slopes: List[float] = []
    Qs: List[float] = []
    energies: List[float] = []

    print("Segments overview:")
    print(
        "  id  start   end   len  pred  patt  sal   energy      mean        slope       Q"
    )
    print(
        "  --- ------- ----- ---- ----- ----- --- ---------- ----------- ----------- -----------"
    )

    for seg_id, seg in enumerate(segments):
        length = seg.end_idx - seg.start_idx + 1
        lengths.append(length)
        slopes.append(seg.slope)
        Qs.append(seg.quant_step_Q)

        pred_name = predictor_names.get(seg.predictor_type, f"#{seg.predictor_type}")
        pattern, sal, energy = classify_segment_pattern(seg)
        patterns.append(pattern)
        saliences.append(sal)
        energies.append(energy)

        print(
            f"  {seg_id:3d} {seg.start_idx:7d} {seg.end_idx:5d} {length:4d} "
            f"{pred_name:5s} {pattern:5s}  {sal:d} {energy:10.3f} "
            f"{seg.mean:11.6f} {seg.slope:11.6f} {seg.quant_step_Q:11.6g}"
        )

    if args.verbose and segments:
        print()
        print("Stats:")
        print(
            f"  seg_len : min={min(lengths)}, max={max(lengths)}, "
            f"avg={sum(lengths)/len(lengths):.2f}"
        )
        if slopes:
            print(f"  slope   : min={min(slopes):.6f}, max={max(slopes):.6f}")
        if Qs:
            print(f"  Q       : min={min(Qs):g}, max={max(Qs):g}")
        if energies:
            print(
                f"  energy  : min={min(energies):.3f}, max={max(energies):.3f}, "
                f"avg={sum(energies)/len(energies):.3f}"
            )

        c_patterns = Counter(patterns)
        print("  patterns: " + ", ".join(f"{k}={v}" for k, v in c_patterns.items()))
        if saliences:
            print(
                f"  salience: min={min(saliences)}, max={max(saliences)}, "
                f"avg={sum(saliences)/len(saliences):.2f}"
            )

        # Motifs + profilo alto livello
        motifs = extract_motifs(segments)
        if motifs:
            print("Motifs:")
            print(
                "  id  seg_start  seg_end  n_segs  patt        total_len  total_energy"
            )
            print(
                "  --- --------- -------- ------- ----------- ----------  ------------"
            )
            for mid, m in enumerate(motifs):
                n_segs = m.end_seg - m.start_seg + 1
                print(
                    f"  {mid:3d} {m.start_seg:9d} {m.end_seg:8d} {n_segs:7d} "
                    f"{m.pattern:11s} {m.total_len:10d} {m.total_energy:12.3f}"
                )

            total_points = n_points
            by_pattern_points: dict[str, int] = {}
            for seg, patt in zip(segments, patterns):
                length = seg.end_idx - seg.start_idx + 1
                by_pattern_points[patt] = by_pattern_points.get(patt, 0) + length

            by_pattern_motifs: dict[str, int] = {}
            for m in motifs:
                by_pattern_motifs[m.pattern] = by_pattern_motifs.get(m.pattern, 0) + 1

            print("Profile:")
            print("  pattern       points   frac_pts   segs  motifs")
            print("  ----------- -------- ---------- ----- -------")
            for patt, pts in sorted(
                by_pattern_points.items(), key=lambda kv: kv[1], reverse=True
            ):
                frac = pts / total_points if total_points > 0 else 0.0
                segs = c_patterns.get(patt, 0)
                mot = by_pattern_motifs.get(patt, 0)
                print(f"  {patt:11s} {pts:8d} {frac:10.3f} {segs:5d} {mot:7d}")


def cli_export_tags(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    output_path = Path(args.output)
    data = input_path.read_bytes()
    ctx, n_points, segments, coding_type = read_lsg2_metadata_and_segments(data)

    predictor_names = {
        0: "mean",
        1: "linear",
        2: "rw",
    }

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "seg_id",
                "start",
                "end",
                "len",
                "pred",
                "patt",
                "sal",
                "energy",
                "mean",
                "slope",
                "Q",
            ]
        )
        for seg_id, seg in enumerate(segments):
            length = seg.end_idx - seg.start_idx + 1
            pred_name = predictor_names.get(
                seg.predictor_type, f"#{seg.predictor_type}"
            )
            pattern, sal, energy = classify_segment_pattern(seg)
            writer.writerow(
                [
                    seg_id,
                    seg.start_idx,
                    seg.end_idx,
                    length,
                    pred_name,
                    pattern,
                    sal,
                    f"{energy:.6g}",
                    f"{seg.mean:.6g}",
                    f"{seg.slope:.6g}",
                    f"{seg.quant_step_Q:.6g}",
                ]
            )


def cli_export_motifs(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    output_path = Path(args.output)
    data = input_path.read_bytes()
    ctx, n_points, segments, coding_type = read_lsg2_metadata_and_segments(data)
    motifs = extract_motifs(segments)

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "motif_id",
                "seg_start",
                "seg_end",
                "n_segs",
                "pattern",
                "total_len",
                "total_energy",
            ]
        )
        for mid, m in enumerate(motifs):
            n_segs = m.end_seg - m.start_seg + 1
            writer.writerow(
                [
                    mid,
                    m.start_seg,
                    m.end_seg,
                    n_segs,
                    m.pattern,
                    m.total_len,
                    f"{m.total_energy:.6g}",
                ]
            )


def cli_export_profile(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    output_path = Path(args.output)

    data = input_path.read_bytes()
    ctx, n_points, segments, coding_type = read_lsg2_metadata_and_segments(data)

    # meta base
    dt = float(ctx.get("sampling", {}).get("dt", 1.0))
    unit = str(ctx.get("unit", "unknown"))
    n_segments = len(segments)

    # se non ci sono segmenti, scrivi solo lo scheletro
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

    # punti per pattern (non solo numero di segmenti)
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
    n_motifs_osc = by_pattern_motifs.get("oscillation", 0)
    n_motifs_noisy = by_pattern_motifs.get("noisy", 0)

    # scrivi CSV: una riga per file
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "file",
                "n_points",
                "dt",
                "unit",
                "n_segments",
                # pattern fractions
                "frac_flat",
                "frac_trend",
                "frac_oscillation",
                "frac_noisy",
                # salience
                "sal_min",
                "sal_max",
                "sal_avg",
                # energy
                "energy_min",
                "energy_max",
                "energy_avg",
                # motifs
                "n_motifs_flat",
                "n_motifs_trend",
                "n_motifs_oscillation",
                "n_motifs_noisy",
            ]
        )
        writer.writerow(
            [
                input_path.name,
                n_points,
                f"{dt:g}",
                unit,
                n_segments,
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
                n_motifs_flat,
                n_motifs_trend,
                n_motifs_osc,
                n_motifs_noisy,
            ]
        )


def main(argv: List[str] | None = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return
    args.func(args)
