# lasagna/cli.py
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import List

from .core import (
    TimeSeries,
    SegmentEntry,
    FILE_HEADER_STRUCT,
    SEGMENT_ENTRY_STRUCT,
    RESIDUAL_SECTION_HEADER_STRUCT,
    RESIDUAL_BLOCK_HEADER_STRUCT,
    encode_timeseries,
    decode_timeseries,
)

import json


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------
def _load_csv_values(path: Path) -> List[float]:
    values: List[float] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # prima colonna
            parts = line.split(",")
            try:
                values.append(float(parts[0]))
            except ValueError:
                continue
    return values


def load_csv_timeseries(path: Path, dt: float, t0: str, unit: str) -> TimeSeries:
    values = _load_csv_values(path)
    return TimeSeries(values=values, dt=dt, t0=t0, unit=unit)


def save_timeseries_to_csv(ts: TimeSeries, path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for v in ts.values:
            f.write(f"{v:.10g}\n")


# ---------------------------------------------------------------------------
# Pattern classification per segmento
# ---------------------------------------------------------------------------
def classify_segment_pattern(seg: SegmentEntry) -> tuple[str, int]:
    """
    Classifica un segmento in (pattern_type, salience).

    pattern_type ∈ {"flat", "trend", "oscillation", "noisy"}
    salience ∈ {0, 1, 2}
    """
    length = seg.end_idx - seg.start_idx + 1
    if length <= 0:
        return "flat", 0

    a_slope = abs(seg.slope)
    Q = seg.quant_step_Q
    predictor_type = seg.predictor_type

    # soglie empiriche MVP (tarabili)
    SLOPE_FLAT = 0.002
    SLOPE_TREND = 0.01
    Q_LOW = 0.05
    Q_HIGH = 0.3

    # pattern_type
    if a_slope < SLOPE_FLAT and Q < Q_LOW:
        # praticamente piatto e poco rumore
        pattern = "flat"
    elif predictor_type == 1 and a_slope >= SLOPE_TREND:
        # retta evidente -> trend
        pattern = "trend"
    elif predictor_type in (1, 2) and Q_LOW <= Q <= Q_HIGH:
        # un po' di struttura + energia media -> oscillazione
        pattern = "oscillation"
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

    return pattern, salience


# ---------------------------------------------------------------------------
# Lettura metadata + segmenti da .lsg2 (senza decodificare tutto)
# ---------------------------------------------------------------------------
def read_lsg2_metadata_and_segments(
    data: bytes,
) -> tuple[dict, int, List[SegmentEntry], int]:
    """
    Ritorna (ctx, n_points, segments, coding_type) da un buffer .lsg2.
    Non legge i blocchi residui (solo salta).
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
        raise ValueError(f"Unsupported LSG2 version {version}")

    if n_points < 0 or n_points > 10_000_000:
        raise ValueError(f"Suspicious n_points={n_points}")
    if n_segments < 0 or n_segments > 1_000_000:
        raise ValueError(f"Suspicious n_segments={n_segments}")
    if header_len < 0 or header_len > len(data) - offset:
        raise ValueError("header_len is inconsistent with data size")

    if len(data) < offset + header_len:
        raise ValueError("Data too short for context JSON")
    ctx_bytes = data[offset : offset + header_len]
    offset += header_len
    ctx = json.loads(ctx_bytes.decode("utf-8"))

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

    if len(data) < offset + RESIDUAL_SECTION_HEADER_STRUCT.size:
        raise ValueError("Data too short for residual section header")
    coding_type, _, _, _ = RESIDUAL_SECTION_HEADER_STRUCT.unpack_from(data, offset)
    offset += RESIDUAL_SECTION_HEADER_STRUCT.size

    # Non leggiamo i blocchi residui, ma controlliamo grossolanamente
    for _ in range(n_segments):
        if len(data) < offset + RESIDUAL_BLOCK_HEADER_STRUCT.size:
            raise ValueError("Data too short for residual block header")
        seg_id, seg_len, byte_len = RESIDUAL_BLOCK_HEADER_STRUCT.unpack_from(
            data, offset
        )
        offset += RESIDUAL_BLOCK_HEADER_STRUCT.size

        if seg_id < 0 or seg_id >= n_segments:
            raise ValueError(f"Invalid seg_id {seg_id} in residual block")
        if seg_len < 0 or byte_len < 0:
            raise ValueError("Negative seg_len/byte_len in residual block")
        if len(data) < offset + byte_len:
            raise ValueError("Data too short for residual block data")

        # salta il blocco
        offset += byte_len

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
    p_enc.add_argument(
        "--t0", type=str, required=True, help="start timestamp (ISO string)"
    )
    p_enc.add_argument("--unit", type=str, required=True, help="unit (string)")

    p_enc.add_argument(
        "--segment-mode",
        type=str,
        default="fixed",
        choices=["fixed", "adaptive"],
        help="segmentation mode (fixed or adaptive)",
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
        choices=["mean", "linear", "rw", "auto"],
        help="predictor type (mean, linear, rw=random-walk, auto=per-segment selection)",
    )
    p_enc.add_argument(
        "--residual-coding",
        type=str,
        default="raw",
        choices=["raw", "varint"],
        help="residual coding: raw int32 or ZigZag+varint",
    )
    p_enc.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="verbose",
    )

    p_enc.set_defaults(func=cli_encode)

    # decode
    p_dec = sub.add_parser("decode", help="decode .lsg2 into CSV")
    p_dec.add_argument("input", type=str, help="input .lsg2 file")
    p_dec.add_argument("output", type=str, help="output CSV file")
    p_dec.set_defaults(func=cli_decode)

    # info
    p_info = sub.add_parser("info", help="inspect .lsg2 file")
    p_info.add_argument("input", type=str, help="input .lsg2 file")
    p_info.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="show stats",
    )
    p_info.set_defaults(func=cli_info)

    return p


def cli_encode(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    output_path = Path(args.output)

    ts = load_csv_timeseries(input_path, dt=args.dt, t0=args.t0, unit=args.unit)

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
    if getattr(args, "verbose", False):
        print(f"Encoded {len(ts.values)} points into {len(data)} bytes.")


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

    print("Segments overview:")
    print("  id  start   end   len  pred  patt  sal   mean        slope       Q")
    print(
        "  --- ------- ----- ---- ----- ----- --- ----------- ----------- -----------"
    )

    for seg_id, seg in enumerate(segments):
        length = seg.end_idx - seg.start_idx + 1
        lengths.append(length)
        slopes.append(seg.slope)
        Qs.append(seg.quant_step_Q)

        pred_name = predictor_names.get(seg.predictor_type, f"#{seg.predictor_type}")
        pattern, sal = classify_segment_pattern(seg)
        patterns.append(pattern)
        saliences.append(sal)

        print(
            f"  {seg_id:3d} {seg.start_idx:7d} {seg.end_idx:5d} {length:4d} "
            f"{pred_name:5s} {pattern:5s}  {sal:d} "
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
        c_patterns = Counter(patterns)
        print("  patterns: " + ", ".join(f"{k}={v}" for k, v in c_patterns.items()))
        if saliences:
            print(
                f"  salience: min={min(saliences)}, max={max(saliences)}, "
                f"avg={sum(saliences)/len(saliences):.2f}"
            )


def main(argv: List[str] | None = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return
    args.func(args)
