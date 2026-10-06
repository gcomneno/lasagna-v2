from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import json
import math
import struct


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------
@dataclass
class TimeSeries:
    values: List[float]
    dt: float = 1.0
    t0: str = "1970-01-01T00:00:00Z"
    unit: str = "unknown"


@dataclass
class SegmentEntry:
    start_idx: int
    end_idx: int
    predictor_type: int
    mean: float
    slope: float
    intercept: float
    quant_step_Q: float
    seed_value: float


def classify_segment_pattern(seg: SegmentEntry) -> tuple[str, int, float]:
    """
    Classifica un segmento in (pattern_type, salience, energy).

    pattern_type ∈ {"flat", "trend", "oscillation", "noisy"}
    salience ∈ {0, 1, 2}
    energy è una misura grezza di "intensità" del segmento.
    """
    length = seg.end_idx - seg.start_idx + 1
    if length <= 0:
        return "flat", 0, 0.0

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

    # energia grezza (slope + rumore, pesati per la durata)
    energy = (a_slope * length) + (Q * length)

    # salienza discreta
    if energy < 1.0:
        salience = 0
    elif energy < 5.0:
        salience = 1
    else:
        salience = 2

    return pattern, salience, energy


@dataclass
class Motif:
    start_seg: int
    end_seg: int
    pattern: str
    total_len: int
    total_energy: float


def extract_motifs(segments: List[SegmentEntry]) -> List[Motif]:
    """
    Raggruppa segmenti consecutivi con lo stesso pattern_type
    in 'motifs' di livello più alto.

    Un motif ha:
      - start_seg / end_seg: indici di segmento (in segment-table)
      - pattern: flat / trend / oscillation / noisy
      - total_len: numero di punti complessivo
      - total_energy: somma delle energy dei segmenti
    """
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
            # continua lo stesso motif
            cur_len += length
            cur_energy += energy
        else:
            # chiudi il motif precedente
            motifs.append(
                Motif(
                    start_seg=cur_start,
                    end_seg=idx - 1,
                    pattern=cur_pattern,
                    total_len=cur_len,
                    total_energy=cur_energy,
                )
            )
            # inizia nuovo motif
            cur_start = idx
            cur_pattern = patt
            cur_len = length
            cur_energy = energy

    # ultimo motif
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
# Binary format structs
# ---------------------------------------------------------------------------

# File header:
# magic (4s) = b"LSG2"
# version (H) = 1
# flags (H)   = reserved
# header_len (I) = bytes of JSON context
# n_points (I)
# n_segments (I)
# reserved1 (I)
# reserved2 (I)
FORMAT_VERSION_V1 = 1
FORMAT_VERSION_V2 = 2

RESIDUAL_CODEC_RAW_INT32 = 0
RESIDUAL_CODEC_VARINT = 1
RESIDUAL_CODEC_ZERO_RUN_VARINT = 2

FILE_HEADER_STRUCT = struct.Struct("<4sHHIIIII")

# Segment entry:
# start_idx (I)
# end_idx   (I)
# predictor_type (I)
# pad1 (I)
# pad2 (I)
# pad3 (I)
# mean (d)
# slope (d)
# intercept (d)
# Q (d)
# seed_value (d)
# Version 1 segment entry: 64 bytes.
SEGMENT_ENTRY_STRUCT = struct.Struct("<6Iddddd")

# M2.3 candidate L32 ONLY — not yet the frozen V2 wire layout.
#
# Semantic field order frozen by M2.2A:
#   start_idx
#   end_idx
#   predictor_type
#   mean
#   slope
#   intercept
#   quant_step_Q
#   seed_value
#
# Exact semantic fields:
#   start_idx, end_idx, predictor_type
#
# Bounded-loss candidate fields in L32:
#   mean, slope, intercept, quant_step_Q, seed_value -> float32
#
# IMPORTANT:
#   - M2.2A freezes semantics, not these numeric widths.
#   - M2.3 must characterize the closed candidate-layout set.
#   - M2.4 must freeze exactly one physical V2 layout.
#   - No encoder may emit format_version=2 before that freeze.
#
# L32 size: 32 bytes.
SEGMENT_ENTRY_V2_STRUCT = struct.Struct("<IIIfffff")

# Residual section header:
# coding_type (I)
# reserved1 (I)
# reserved2 (I)
# reserved3 (I)
RESIDUAL_SECTION_HEADER_STRUCT = struct.Struct("<IIII")

# Residual block header:
# seg_id   (I)
# seg_len  (I)
# byte_len (I)
RESIDUAL_BLOCK_HEADER_STRUCT = struct.Struct("<III")

# ---------------------------------------------------------------------------
# Production resource limits
# ---------------------------------------------------------------------------
UINT32_MAX = (1 << 32) - 1

MAX_POINTS = 10_000_000
MAX_SEGMENTS = 1_000_000
MAX_SEGMENT_POINTS = MAX_POINTS

MAX_CONTEXT_BYTES = 65_536
MAX_CONTEXT_DEPTH = 64
MAX_VARINT_BYTES = 10

MAX_RESIDUAL_BLOCK_BYTES = MAX_VARINT_BYTES * MAX_SEGMENT_POINTS

MAX_INPUT_BYTES = (
    FILE_HEADER_STRUCT.size
    + MAX_CONTEXT_BYTES
    + (SEGMENT_ENTRY_STRUCT.size + RESIDUAL_BLOCK_HEADER_STRUCT.size) * MAX_SEGMENTS
    + MAX_VARINT_BYTES * MAX_POINTS
    + RESIDUAL_SECTION_HEADER_STRUCT.size
)


def _validate_context_depth(data: bytes) -> None:
    """Reject pathological JSON nesting before handing bytes to json.loads()."""
    depth = 0
    in_string = False
    escaped = False

    for byte in data:
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:  # backslash
                escaped = True
            elif byte == 0x22:  # double quote
                in_string = False
            continue

        if byte == 0x22:
            in_string = True
            continue

        if byte in (0x7B, 0x5B):  # { [
            depth += 1
            if depth > MAX_CONTEXT_DEPTH:
                raise ValueError(
                    "Context JSON exceeds maximum nesting depth " f"{MAX_CONTEXT_DEPTH}"
                )
        elif byte in (0x7D, 0x5D):  # } ]
            if depth > 0:
                depth -= 1


def _validate_context_bytes(data: bytes) -> None:
    if len(data) > MAX_CONTEXT_BYTES:
        raise ValueError(
            "Context JSON exceeds maximum size " f"{MAX_CONTEXT_BYTES} bytes"
        )

    _validate_context_depth(data)


def _parse_context_json(data: bytes) -> dict:
    """Parse and validate the common LSG2 context shape."""
    _validate_context_bytes(data)

    try:
        ctx = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid context JSON") from exc

    if not isinstance(ctx, dict):
        raise ValueError("Context JSON must be an object")

    sampling = ctx.get("sampling", {})

    if not isinstance(sampling, dict):
        raise ValueError("Context sampling must be an object")

    try:
        float(sampling.get("dt", 1.0))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Context sampling.dt must be float-convertible") from exc

    return ctx


def _validate_input_size(data: bytes) -> None:
    if len(data) > MAX_INPUT_BYTES:
        raise ValueError("LSG2 input exceeds maximum size " f"{MAX_INPUT_BYTES} bytes")


def _validate_header_resources(
    *,
    header_len: int,
    n_points: int,
    n_segments: int,
) -> None:
    if n_points > MAX_POINTS:
        raise ValueError(f"n_points={n_points} exceeds maximum {MAX_POINTS}")

    if n_segments > MAX_SEGMENTS:
        raise ValueError(f"n_segments={n_segments} exceeds maximum {MAX_SEGMENTS}")

    if header_len > MAX_CONTEXT_BYTES:
        raise ValueError(
            "Context JSON exceeds maximum size " f"{MAX_CONTEXT_BYTES} bytes"
        )


def _preflight_lsg2(data: bytes) -> None:
    """
    Validate resource-bearing LSG2 structure before decoder amplification.

    This check intentionally preserves frozen V1/V2 wire semantics. It bounds
    work and allocation but does not reinterpret valid predictor semantics.
    """
    _validate_input_size(data)

    if len(data) < FILE_HEADER_STRUCT.size:
        raise ValueError("Data too short to contain header")

    (
        magic,
        version,
        _flags,
        header_len,
        n_points,
        n_segments,
        _reserved1,
        _reserved2,
    ) = FILE_HEADER_STRUCT.unpack_from(data, 0)

    if magic != b"LSG2":
        raise ValueError("Invalid magic, not an LSG2 file")

    if version not in (
        FORMAT_VERSION_V1,
        FORMAT_VERSION_V2,
    ):
        raise ValueError(
            f"Unsupported LSG2 version {version}; " "supported versions are 1 and 2"
        )

    _validate_header_resources(
        header_len=header_len,
        n_points=n_points,
        n_segments=n_segments,
    )

    offset = FILE_HEADER_STRUCT.size
    context_end = offset + header_len

    if context_end > len(data):
        raise ValueError("Data too short for context JSON")

    context_bytes = data[offset:context_end]
    _validate_context_bytes(context_bytes)
    offset = context_end

    if version == FORMAT_VERSION_V1:
        segment_struct = SEGMENT_ENTRY_STRUCT
    else:
        segment_struct = SEGMENT_ENTRY_V2_STRUCT

    segment_table_bytes = n_segments * segment_struct.size
    segment_table_end = offset + segment_table_bytes

    if segment_table_end > len(data):
        raise ValueError("Data too short for segment table")

    segment_lengths: list[int] = []
    total_segment_samples = 0
    expected_v2_start = 0

    for _ in range(n_segments):
        if version == FORMAT_VERSION_V1:
            (
                start_idx,
                end_idx,
                predictor_type,
                _pad1,
                _pad2,
                _pad3,
                _mean,
                _slope,
                _intercept,
                _Q,
                _seed_value,
            ) = SEGMENT_ENTRY_STRUCT.unpack_from(
                data,
                offset,
            )
        else:
            (
                start_idx,
                end_idx,
                predictor_type,
                _mean,
                _slope,
                _intercept,
                _Q,
                _seed_value,
            ) = SEGMENT_ENTRY_V2_STRUCT.unpack_from(
                data,
                offset,
            )

        offset += segment_struct.size

        if predictor_type not in (0, 1, 2):
            raise ValueError(f"Unsupported predictor_type {predictor_type}")

        if end_idx < start_idx:
            raise ValueError("Invalid segment extent")

        if n_points == 0 or end_idx >= n_points:
            raise ValueError("Segment extent exceeds declared point count")

        length = end_idx - start_idx + 1

        if length > MAX_SEGMENT_POINTS:
            raise ValueError("Segment length exceeds maximum " f"{MAX_SEGMENT_POINTS}")

        total_segment_samples += length

        if total_segment_samples > MAX_POINTS:
            raise ValueError(
                "Aggregate segment sample count exceeds maximum " f"{MAX_POINTS}"
            )

        if version == FORMAT_VERSION_V2:
            if start_idx != expected_v2_start:
                raise ValueError("Non-contiguous V2 segment table")
            expected_v2_start = end_idx + 1

        segment_lengths.append(length)

    if version == FORMAT_VERSION_V2:
        if n_segments == 0 and n_points != 0:
            raise ValueError("Non-empty V2 series has no segments")

        if n_segments and expected_v2_start != n_points:
            raise ValueError(
                "V2 segment table does not cover " "the declared point count"
            )

    residual_header_end = offset + RESIDUAL_SECTION_HEADER_STRUCT.size

    if residual_header_end > len(data):
        raise ValueError("Data too short for residual section header")

    (
        coding_type,
        _res1,
        _res2,
        _res3,
    ) = RESIDUAL_SECTION_HEADER_STRUCT.unpack_from(
        data,
        offset,
    )

    offset = residual_header_end

    if coding_type not in (
        RESIDUAL_CODEC_RAW_INT32,
        RESIDUAL_CODEC_VARINT,
        RESIDUAL_CODEC_ZERO_RUN_VARINT,
    ):
        raise ValueError(f"Unsupported coding_type {coding_type} in decoder")

    seen_segment_ids: set[int] = set()
    total_residual_samples = 0

    for _ in range(n_segments):
        block_header_end = offset + RESIDUAL_BLOCK_HEADER_STRUCT.size

        if block_header_end > len(data):
            raise ValueError("Data too short for residual block header")

        (
            seg_id,
            seg_len,
            byte_len,
        ) = RESIDUAL_BLOCK_HEADER_STRUCT.unpack_from(
            data,
            offset,
        )

        offset = block_header_end

        if seg_id >= n_segments:
            raise ValueError(f"Invalid seg_id {seg_id} in residual block")

        if seg_id in seen_segment_ids:
            raise ValueError(f"Duplicate residual block for seg_id={seg_id}")

        seen_segment_ids.add(seg_id)

        expected_length = segment_lengths[seg_id]

        if seg_len != expected_length:
            raise ValueError(
                "Residual sample count does not match "
                f"segment length for seg_id={seg_id}"
            )

        if seg_len > MAX_SEGMENT_POINTS:
            raise ValueError(
                "Residual sample count exceeds maximum " f"{MAX_SEGMENT_POINTS}"
            )

        total_residual_samples += seg_len

        if total_residual_samples > MAX_POINTS:
            raise ValueError(
                "Aggregate residual sample count exceeds maximum " f"{MAX_POINTS}"
            )

        if byte_len > MAX_RESIDUAL_BLOCK_BYTES:
            raise ValueError(
                "Residual block exceeds maximum size "
                f"{MAX_RESIDUAL_BLOCK_BYTES} bytes"
            )

        if coding_type == RESIDUAL_CODEC_RAW_INT32 and byte_len != seg_len * 4:
            raise ValueError("byte_len != seg_len * 4 for raw residuals")

        block_end = offset + byte_len

        if block_end > len(data):
            raise ValueError("Data too short for residual block data")

        offset = block_end

    if len(seen_segment_ids) != n_segments:
        raise ValueError("Missing residual block")


def _validate_encoded_size(size: int) -> None:
    if size > MAX_INPUT_BYTES:
        raise ValueError(
            "Encoded LSG2 output exceeds maximum size " f"{MAX_INPUT_BYTES} bytes"
        )


# ---------------------------------------------------------------------------
# Varint / ZigZag helpers
# ---------------------------------------------------------------------------
def zigzag_encode(n: int) -> int:
    """Map signed int -> unsigned for varint."""
    return (n << 1) ^ (n >> 31)


def zigzag_decode(z: int) -> int:
    """Inverse of zigzag_encode."""
    return (z >> 1) ^ -(z & 1)


def _encode_varint(value: int) -> bytes:
    """Encode an unsigned int as varint (7-bit payload, MSB=continuation)."""
    if value < 0:
        raise ValueError("varint expects non-negative integers")
    out = bytearray()
    while True:
        if len(out) >= MAX_VARINT_BYTES:
            raise ValueError(
                "Varint exceeds maximum encoded length " f"{MAX_VARINT_BYTES} bytes"
            )

        to_write = value & 0x7F
        value >>= 7
        if value:
            out.append(to_write | 0x80)
        else:
            out.append(to_write)
            break
    return bytes(out)


def _decode_varint(data: bytes, offset: int) -> Tuple[int, int]:
    """Decode one varint starting at offset. Returns (value, new_offset)."""
    shift = 0
    result = 0
    while True:
        if offset >= len(data):
            raise ValueError("Truncated varint")
        b = data[offset]
        offset += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
        if shift > 63:
            raise ValueError("Varint too long")
    return result, offset


def encode_int_list_varint(values: List[int]) -> bytes:
    """Encode a list of signed ints with ZigZag + varint."""
    out = bytearray()
    for v in values:
        z = zigzag_encode(int(v))
        out += _encode_varint(z)
    return bytes(out)


def decode_int_list_varint(data: bytes, length: int) -> List[int]:
    """Decode exactly `length` signed ints from ZigZag+varint buffer."""
    out: List[int] = []
    offset = 0
    for _ in range(length):
        z, offset = _decode_varint(data, offset)
        out.append(zigzag_decode(z))
    if offset != len(data):
        # Non-fatal, ma è un segnale che il blocco ha extra bytes
        # (potrebbe essere malware / file corrotto)
        # Al momento lo ignoriamo, ma il caller può decidere cosa fare.
        pass
    return out


ZERO_RUN_MIN_LENGTH = 3


def encode_int_list_zero_run_varint(values: List[int]) -> bytes:
    """Encode signed ints using shifted ZigZag literals plus zero runs."""
    out = bytearray()
    index = 0

    while index < len(values):
        if values[index] == 0:
            run_end = index + 1

            while run_end < len(values) and values[run_end] == 0:
                run_end += 1

            run_length = run_end - index

            if run_length >= ZERO_RUN_MIN_LENGTH:
                out += _encode_varint(0)
                out += _encode_varint(run_length)
                index = run_end
                continue

        token = zigzag_encode(int(values[index])) + 1
        out += _encode_varint(token)
        index += 1

    return bytes(out)


def decode_int_list_zero_run_varint(
    data: bytes,
    length: int,
) -> List[int]:
    """Decode exactly `length` residuals from zero-run + varint."""
    out: List[int] = []
    offset = 0

    while offset < len(data):
        token, offset = _decode_varint(
            data,
            offset,
        )

        if token == 0:
            run_length, offset = _decode_varint(
                data,
                offset,
            )

            if run_length < ZERO_RUN_MIN_LENGTH:
                raise ValueError("Invalid zero-run length")

            if len(out) + run_length > length:
                raise ValueError("Zero-run exceeds declared residual count")

            out.extend([0] * run_length)
        else:
            out.append(zigzag_decode(token - 1))

            if len(out) > length:
                raise ValueError("Decoded residual count exceeds declaration")

    if len(out) != length:
        raise ValueError("Decoded residual count does not match declaration")

    return out


# ---------------------------------------------------------------------------
# Stats, predittori, quantizzazione
# ---------------------------------------------------------------------------
def compute_stats(x: List[float]) -> Tuple[float, float, float, float]:
    """
    Calcola (mean, slope, intercept, variance) su x con regressione lineare
    rispetto a t = 0..len(x)-1.
    """
    n = len(x)
    if n == 0:
        return 0.0, 0.0, 0.0, 0.0
    mean = sum(x) / n
    if n == 1:
        return mean, 0.0, mean, 0.0

    # Regressione lineare semplice
    # t = 0..n-1
    t_vals = range(n)
    sum_t = (n - 1) * n / 2.0
    sum_t2 = (n - 1) * n * (2 * n - 1) / 6.0
    sum_x = float(sum(x))
    sum_tx = sum(t * v for t, v in zip(t_vals, x))

    denom = n * sum_t2 - sum_t * sum_t
    if denom == 0:
        slope = 0.0
    else:
        slope = (n * sum_tx - sum_t * sum_x) / denom
    intercept = mean - slope * (sum_t / n)

    # Varianza
    var = sum((v - mean) ** 2 for v in x) / n
    return mean, slope, intercept, var


def predict_mean_const(length: int, mean: float) -> List[float]:
    return [mean] * length


def predict_linear(length: int, slope: float, intercept: float) -> List[float]:
    return [intercept + slope * i for i in range(length)]


def predict_random_walk(x: List[float], seed: float) -> List[float]:
    """
    Predittore random-walk: per encode side, usiamo x[i-1] come predizione,
    con seed per il primo valore (anche se di solito seed = x[0]).
    """
    n = len(x)
    if n == 0:
        return []
    preds = [0.0] * n
    preds[0] = seed
    for i in range(1, n):
        preds[i] = x[i - 1]
    return preds


def quantize_residuals(
    residuals: List[float],
    C_Q: float = 0.5,
    Q_MIN: float = 1e-6,
) -> Tuple[List[int], float]:
    """
    Quantizza residui float in interi usando passo Q = max(C_Q * sigma, Q_MIN).
    Restituisce (q_residuals, Q).
    """
    if not residuals:
        return [], Q_MIN
    n = len(residuals)
    mean = sum(residuals) / n
    var = sum((r - mean) ** 2 for r in residuals) / n
    sigma = math.sqrt(var)
    Q = max(C_Q * sigma, Q_MIN)
    if Q == 0.0:
        Q = Q_MIN
    q_res = [int(round(r / Q)) for r in residuals]
    return q_res, Q


# ---------------------------------------------------------------------------
# Segmentazione
# ---------------------------------------------------------------------------
def segment_series_fixed_length(
    n_points: int, segment_length: int
) -> List[Tuple[int, int]]:
    """
    Segmentazione a lunghezza fissa. Indici [start, end] inclusivi.
    """
    if segment_length <= 0:
        raise ValueError("segment_length must be > 0")

    segment_count = (n_points + segment_length - 1) // segment_length if n_points else 0

    if segment_count > MAX_SEGMENTS:
        raise ValueError("Segment count exceeds maximum " f"{MAX_SEGMENTS}")

    segments: List[Tuple[int, int]] = []
    start = 0
    while start < n_points:
        end = min(start + segment_length, n_points) - 1
        segments.append((start, end))
        start = end + 1
    return segments


def _build_preds_for_segmentation(
    x_seg: List[float],
    predictor_type: int,
    mean: float,
    slope: float,
    intercept: float,
    seed_value: float,
) -> List[float]:
    length = len(x_seg)
    if predictor_type == 0:  # mean
        return predict_mean_const(length, mean)
    if predictor_type == 1:  # linear
        return predict_linear(length, slope, intercept)
    if predictor_type == 2:  # random-walk
        return predict_random_walk(x_seg, seed_value)
    raise ValueError(f"Unknown predictor_type {predictor_type} for segmentation")


def segment_series_adaptive(
    values: List[float],
    predictor_type: int,
    min_len: int,
    max_len: int,
    mse_threshold: float,
) -> List[Tuple[int, int]]:
    """
    Segmentazione adattiva: estende il segmento finché il MSE del modello
    scelto resta sotto soglia o finché raggiunge max_len.
    """
    n = len(values)
    if n == 0:
        return []
    if min_len <= 0 or max_len < min_len:
        raise ValueError("Invalid min_len / max_len")

    segments: List[Tuple[int, int]] = []
    i = 0
    while i < n:
        start = i
        end = min(start + min_len, n) - 1
        best_end = end

        # Prova ad allungare finché il MSE resta sotto soglia
        while True:
            x_seg = values[start : end + 1]
            length = len(x_seg)
            mean, slope, intercept, _var = compute_stats(x_seg)
            seed_value = x_seg[0] if x_seg else 0.0

            preds = _build_preds_for_segmentation(
                x_seg,
                predictor_type=predictor_type,
                mean=mean,
                slope=slope,
                intercept=intercept,
                seed_value=seed_value,
            )
            if length > 0:
                mse = sum((v - p) ** 2 for v, p in zip(x_seg, preds)) / length
            else:
                mse = 0.0

            if mse <= mse_threshold:
                best_end = end
                # prova ad allungare ancora
                if (end + 1) < n and (end - start + 1) < max_len:
                    end += 1
                    continue
            # se MSE supera soglia o abbiamo raggiunto max_len / fine serie
            break

        if len(segments) >= MAX_SEGMENTS:
            raise ValueError("Segment count exceeds maximum " f"{MAX_SEGMENTS}")

        segments.append((start, best_end))
        i = best_end + 1

    return segments


# ---------------------------------------------------------------------------
# Context JSON
# ---------------------------------------------------------------------------
def build_context_json(ts: TimeSeries) -> bytes:
    for name, value in (
        ("t0", str(ts.t0)),
        ("unit", str(ts.unit)),
    ):
        if len(value.encode("utf-8")) > MAX_CONTEXT_BYTES:
            raise ValueError(f"Context field {name} exceeds resource limit")

    ctx = {
        "sampling": {
            "dt": ts.dt,
            "t0": ts.t0,
        },
        "unit": ts.unit,
    }

    encoder = json.JSONEncoder(
        separators=(",", ":"),
    )

    out = bytearray()

    for chunk in encoder.iterencode(ctx):
        encoded = chunk.encode("utf-8")

        if len(out) + len(encoded) > MAX_CONTEXT_BYTES:
            raise ValueError(
                "Context JSON exceeds maximum size " f"{MAX_CONTEXT_BYTES} bytes"
            )

        out.extend(encoded)

    result = bytes(out)
    _validate_context_depth(result)
    return result


# ---------------------------------------------------------------------------
# Codec: encode / decode
# ---------------------------------------------------------------------------
def _build_encoding_model(
    ts: TimeSeries,
    segment_length: int = 64,
    predictor: str = "linear",
    C_Q: float = 0.5,
    Q_MIN: float = 1e-6,
    segment_mode: str = "fixed",
    min_segment_length: int = 32,
    max_segment_length: int = 128,
    mse_threshold: float = 0.5,
) -> tuple[bytes, list[SegmentEntry], list[list[int]]]:
    """
    Build the format-independent encoding model shared by V1 and V2.

    Returns:
        context bytes,
        segment metadata,
        V1-semantic quantized residuals.
    """
    values = ts.values
    n_points = len(values)

    if n_points == 0:
        raise ValueError("TimeSeries is empty")

    if n_points > MAX_POINTS:
        raise ValueError(f"n_points={n_points} exceeds maximum {MAX_POINTS}")

    predictor_map = {
        "mean": 0,
        "linear": 1,
        "rw": 2,
    }

    if predictor == "auto":
        default_predictor_type = None
        predictor_type_for_segmentation = 1
    else:
        if predictor not in predictor_map:
            raise ValueError(
                f"Unknown predictor '{predictor}', "
                f"expected one of {list(predictor_map) + ['auto']}"
            )

        default_predictor_type = predictor_map[predictor]
        predictor_type_for_segmentation = default_predictor_type

    if segment_mode == "fixed":
        segment_ranges = segment_series_fixed_length(
            n_points,
            segment_length,
        )
    elif segment_mode == "adaptive":
        segment_ranges = segment_series_adaptive(
            values,
            predictor_type=predictor_type_for_segmentation,
            min_len=min_segment_length,
            max_len=max_segment_length,
            mse_threshold=mse_threshold,
        )
    else:
        raise ValueError("segment_mode must be 'fixed' or 'adaptive'")

    segments: list[SegmentEntry] = []
    q_resid_segments: list[list[int]] = []

    for start, end in segment_ranges:
        x_seg = values[start : end + 1]
        length = len(x_seg)

        mean, slope, intercept, _var = compute_stats(x_seg)
        seed_value = x_seg[0] if x_seg else 0.0

        if predictor == "auto":
            best_type = None
            best_mse = float("inf")

            for cand_type in (0, 1, 2):
                preds_c = _build_preds_for_segmentation(
                    x_seg,
                    predictor_type=cand_type,
                    mean=mean,
                    slope=slope,
                    intercept=intercept,
                    seed_value=seed_value,
                )

                residuals_c = [
                    value - pred
                    for value, pred in zip(
                        x_seg,
                        preds_c,
                    )
                ]

                q_res_c, Q_c = quantize_residuals(
                    residuals_c,
                    C_Q=C_Q,
                    Q_MIN=Q_MIN,
                )

                x_hat_c = [0.0] * length

                if cand_type in (0, 1):
                    for index in range(length):
                        x_hat_c[index] = preds_c[index] + q_res_c[index] * Q_c
                else:
                    if length > 0:
                        preds_dec = [0.0] * length
                        preds_dec[0] = seed_value

                        x_hat_c[0] = preds_dec[0] + q_res_c[0] * Q_c

                        for index in range(1, length):
                            preds_dec[index] = x_hat_c[index - 1]

                            x_hat_c[index] = preds_dec[index] + q_res_c[index] * Q_c

                if length > 0:
                    mse_c = (
                        sum(
                            (value - reconstructed) ** 2
                            for value, reconstructed in zip(
                                x_seg,
                                x_hat_c,
                            )
                        )
                        / length
                    )
                else:
                    mse_c = 0.0

                if mse_c < best_mse:
                    best_mse = mse_c
                    best_type = cand_type

            if best_type is None:
                best_type = 0

            predictor_type_seg = best_type

            preds = _build_preds_for_segmentation(
                x_seg,
                predictor_type=predictor_type_seg,
                mean=mean,
                slope=slope,
                intercept=intercept,
                seed_value=seed_value,
            )
        else:
            predictor_type_seg = default_predictor_type

            preds = _build_preds_for_segmentation(
                x_seg,
                predictor_type=predictor_type_seg,
                mean=mean,
                slope=slope,
                intercept=intercept,
                seed_value=seed_value,
            )

        residuals = [
            value - pred
            for value, pred in zip(
                x_seg,
                preds,
            )
        ]

        q_res, Q = quantize_residuals(
            residuals,
            C_Q=C_Q,
            Q_MIN=Q_MIN,
        )

        segments.append(
            SegmentEntry(
                start_idx=start,
                end_idx=end,
                predictor_type=predictor_type_seg,
                mean=mean,
                slope=slope,
                intercept=intercept,
                quant_step_Q=Q,
                seed_value=seed_value,
            )
        )

        q_resid_segments.append(q_res)

    return (
        build_context_json(ts),
        segments,
        q_resid_segments,
    )


def encode_timeseries_v1(
    ts: TimeSeries,
    segment_length: int = 64,
    predictor: str = "linear",
    C_Q: float = 0.5,
    Q_MIN: float = 1e-6,
    segment_mode: str = "fixed",
    min_segment_length: int = 32,
    max_segment_length: int = 128,
    mse_threshold: float = 0.5,
    residual_coding: str = "raw",
) -> bytes:
    """Encode a TimeSeries using the legacy V1 wire format."""
    (
        ctx_bytes,
        segments,
        q_resid_segments,
    ) = _build_encoding_model(
        ts,
        segment_length=segment_length,
        predictor=predictor,
        C_Q=C_Q,
        Q_MIN=Q_MIN,
        segment_mode=segment_mode,
        min_segment_length=min_segment_length,
        max_segment_length=max_segment_length,
        mse_threshold=mse_threshold,
    )

    n_points = len(ts.values)
    n_segments = len(segments)

    buf = bytearray()

    buf += FILE_HEADER_STRUCT.pack(
        b"LSG2",
        FORMAT_VERSION_V1,
        0,
        len(ctx_bytes),
        n_points,
        n_segments,
        0,
        0,
    )

    buf += ctx_bytes

    for seg in segments:
        buf += SEGMENT_ENTRY_STRUCT.pack(
            seg.start_idx,
            seg.end_idx,
            seg.predictor_type,
            0,
            0,
            0,
            seg.mean,
            seg.slope,
            seg.intercept,
            seg.quant_step_Q,
            seg.seed_value,
        )

    encoded_payloads: list[bytes] | None

    if residual_coding == "raw":
        coding_type = RESIDUAL_CODEC_RAW_INT32
        encoded_payloads = None
        payload_bytes = sum(len(q_res) * 4 for q_res in q_resid_segments)
    elif residual_coding == "varint":
        coding_type = RESIDUAL_CODEC_VARINT
        encoded_payloads = [encode_int_list_varint(q_res) for q_res in q_resid_segments]
        payload_bytes = sum(len(payload) for payload in encoded_payloads)
    else:
        raise ValueError(
            f"Unknown residual_coding '{residual_coding}', "
            "expected 'raw' or 'varint'"
        )

    for q_res in q_resid_segments:
        if len(q_res) > MAX_SEGMENT_POINTS:
            raise ValueError("Segment length exceeds maximum " f"{MAX_SEGMENT_POINTS}")

    for payload in encoded_payloads or []:
        if len(payload) > MAX_RESIDUAL_BLOCK_BYTES:
            raise ValueError(
                "Residual block exceeds maximum size "
                f"{MAX_RESIDUAL_BLOCK_BYTES} bytes"
            )

    encoded_size = (
        FILE_HEADER_STRUCT.size
        + len(ctx_bytes)
        + n_segments * SEGMENT_ENTRY_STRUCT.size
        + RESIDUAL_SECTION_HEADER_STRUCT.size
        + n_segments * RESIDUAL_BLOCK_HEADER_STRUCT.size
        + payload_bytes
    )
    _validate_encoded_size(encoded_size)

    buf += RESIDUAL_SECTION_HEADER_STRUCT.pack(
        coding_type,
        0,
        0,
        0,
    )

    for seg_id, q_res in enumerate(q_resid_segments):
        seg_len = len(q_res)

        if coding_type == RESIDUAL_CODEC_RAW_INT32:
            byte_len = seg_len * 4

            buf += RESIDUAL_BLOCK_HEADER_STRUCT.pack(
                seg_id,
                seg_len,
                byte_len,
            )

            if seg_len:
                buf += struct.pack(
                    f"<{seg_len}i",
                    *q_res,
                )
        else:
            assert encoded_payloads is not None
            payload = encoded_payloads[seg_id]

            buf += RESIDUAL_BLOCK_HEADER_STRUCT.pack(
                seg_id,
                seg_len,
                len(payload),
            )

            buf += payload

    return bytes(buf)


def decode_timeseries(data: bytes) -> TimeSeries:
    """
    Decode Lasagna MVP bytes (.lsg2) back to a TimeSeries.
    Supporta:
      - coding_type = 0 (int32 raw)
      - coding_type = 1 (ZigZag + varint)
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

    ctx = _parse_context_json(ctx_bytes)
    dt = float(ctx.get("sampling", {}).get("dt", 1.0))
    t0 = str(ctx.get("sampling", {}).get("t0", "1970-01-01T00:00:00Z"))
    unit = str(ctx.get("unit", "unknown"))

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

    # Residual section header
    if len(data) < offset + RESIDUAL_SECTION_HEADER_STRUCT.size:
        raise ValueError("Data too short for residual section header")
    coding_type, _, _, _ = RESIDUAL_SECTION_HEADER_STRUCT.unpack_from(data, offset)
    offset += RESIDUAL_SECTION_HEADER_STRUCT.size

    if coding_type not in (
        RESIDUAL_CODEC_RAW_INT32,
        RESIDUAL_CODEC_VARINT,
        RESIDUAL_CODEC_ZERO_RUN_VARINT,
    ):
        raise ValueError(f"Unsupported coding_type {coding_type} in decoder")

    # Residual blocks
    q_res_segments: List[List[int]] = [[] for _ in range(n_segments)]
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

        block_bytes = data[offset : offset + byte_len]
        offset += byte_len

        if coding_type == RESIDUAL_CODEC_RAW_INT32:
            if seg_len * 4 != byte_len:
                raise ValueError("byte_len != seg_len * 4 for raw residuals")
            if seg_len > 0:
                q_res = list(
                    struct.unpack(
                        f"<{seg_len}i",
                        block_bytes,
                    )
                )
            else:
                q_res = []
        elif coding_type == RESIDUAL_CODEC_VARINT:
            q_res = decode_int_list_varint(
                block_bytes,
                seg_len,
            )
        else:
            q_res = decode_int_list_zero_run_varint(
                block_bytes,
                seg_len,
            )

        q_res_segments[seg_id] = q_res

    # Ricostruzione
    x_hat = [0.0] * n_points

    for seg_id, seg in enumerate(segments):
        q_res = q_res_segments[seg_id]
        start = seg.start_idx
        end = seg.end_idx
        length = end - start + 1
        if length != len(q_res):
            raise ValueError(
                f"Segment length mismatch for seg_id={seg_id}: length={length}, "
                f"len(q_res)={len(q_res)}"
            )

        Q = seg.quant_step_Q
        residuals = [q * Q for q in q_res]

        if seg.predictor_type == 0:  # mean
            preds = predict_mean_const(length, seg.mean)
            for i in range(length):
                x_hat[start + i] = preds[i] + residuals[i]
        elif seg.predictor_type == 1:  # linear
            preds = predict_linear(length, seg.slope, seg.intercept)
            for i in range(length):
                x_hat[start + i] = preds[i] + residuals[i]
        elif seg.predictor_type == 2:  # random-walk
            if length > 0:
                preds = [0.0] * length
                preds[0] = seg.seed_value
                x_hat[start] = preds[0] + residuals[0]
                for i in range(1, length):
                    preds[i] = x_hat[start + i - 1]
                    x_hat[start + i] = preds[i] + residuals[i]
        else:
            raise ValueError(f"Unknown predictor_type {seg.predictor_type}")

    return TimeSeries(values=x_hat, dt=dt, t0=t0, unit=unit)


# ---------------------------------------------------------------------------
# Version 2 frozen L32 wire path
# ---------------------------------------------------------------------------
#
# M2.4 freezes the V2 segment-entry representation as:
#
#     <IIIfffff>
#
# The V1 encoder and decoder implementation above remain unchanged.
# V2 encoding deliberately derives segmentation and predictor selection from
# the V1 encoder, then re-quantizes residuals using the binary32 metadata that
# is actually serialized on the V2 wire.
#
# The historical public decoder is retained as _decode_timeseries_v1 before
# decode_timeseries is rebound to the version dispatcher below.


_decode_timeseries_v1 = decode_timeseries


def _round_segment_entry_v2(seg: SegmentEntry) -> SegmentEntry:
    """Round all V2 real metadata through the frozen binary32 wire layout."""
    try:
        packed = SEGMENT_ENTRY_V2_STRUCT.pack(
            seg.start_idx,
            seg.end_idx,
            seg.predictor_type,
            seg.mean,
            seg.slope,
            seg.intercept,
            seg.quant_step_Q,
            seg.seed_value,
        )
    except (OverflowError, struct.error) as exc:
        raise ValueError(
            "Segment metadata is not representable in frozen V2 L32 layout"
        ) from exc

    (
        start_idx,
        end_idx,
        predictor_type,
        mean,
        slope,
        intercept,
        quant_step_Q,
        seed_value,
    ) = SEGMENT_ENTRY_V2_STRUCT.unpack(packed)

    real_values = (
        mean,
        slope,
        intercept,
        quant_step_Q,
        seed_value,
    )

    if any(not math.isfinite(value) for value in real_values):
        raise ValueError("V2 segment metadata must be finite")

    if not math.isfinite(quant_step_Q) or quant_step_Q <= 0.0:
        raise ValueError("V2 quantization step Q must be finite and > 0")

    if predictor_type not in (0, 1, 2):
        raise ValueError(f"Unsupported V2 predictor_type {predictor_type}")

    return SegmentEntry(
        start_idx=start_idx,
        end_idx=end_idx,
        predictor_type=predictor_type,
        mean=mean,
        slope=slope,
        intercept=intercept,
        quant_step_Q=quant_step_Q,
        seed_value=seed_value,
    )


def encode_timeseries_v2(
    ts: TimeSeries,
    segment_length: int = 64,
    predictor: str = "linear",
    C_Q: float = 0.125,
    Q_MIN: float = 1e-6,
    segment_mode: str = "fixed",
    min_segment_length: int = 32,
    max_segment_length: int = 128,
    mse_threshold: float = 0.5,
    residual_coding: str = "raw",
) -> bytes:
    """
    Encode a TimeSeries using the frozen Version 2 L32 segment layout.

    Segmentation, statistics and predictor selection are obtained from the
    shared format-independent encoding model. Segment metadata is then rounded
    exactly through the frozen <IIIfffff> representation before residuals are
    recomputed.

    Random-walk encoding preserves the frozen semantic rule: samples after
    the seed are predicted from the previous ORIGINAL sample.
    """
    (
        context_bytes,
        model_segments,
        _,
    ) = _build_encoding_model(
        ts,
        segment_length=segment_length,
        predictor=predictor,
        C_Q=C_Q,
        Q_MIN=Q_MIN,
        segment_mode=segment_mode,
        min_segment_length=min_segment_length,
        max_segment_length=max_segment_length,
        mse_threshold=mse_threshold,
    )

    n_points = len(ts.values)
    n_segments = len(model_segments)
    header_len = len(context_bytes)

    v2_segments = [_round_segment_entry_v2(seg) for seg in model_segments]

    q_resid_segments: list[list[int]] = []

    for seg in v2_segments:
        if seg.end_idx < seg.start_idx:
            raise ValueError("Invalid V2 segment extent")

        x_seg = list(ts.values[seg.start_idx : seg.end_idx + 1])

        expected_length = seg.end_idx - seg.start_idx + 1

        if len(x_seg) != expected_length:
            raise ValueError("V2 segment lies outside TimeSeries")

        preds = _build_preds_for_segmentation(
            x_seg,
            predictor_type=seg.predictor_type,
            mean=seg.mean,
            slope=seg.slope,
            intercept=seg.intercept,
            seed_value=seg.seed_value,
        )

        Q = seg.quant_step_Q

        q_res = [round((value - pred) / Q) for value, pred in zip(x_seg, preds)]

        q_resid_segments.append(q_res)

    encoded_payloads: list[bytes] | None

    if residual_coding == "raw":
        coding_type = RESIDUAL_CODEC_RAW_INT32
        encoded_payloads = None
        payload_bytes = sum(len(q_res) * 4 for q_res in q_resid_segments)
    elif residual_coding == "varint":
        coding_type = RESIDUAL_CODEC_VARINT
        encoded_payloads = [encode_int_list_varint(q_res) for q_res in q_resid_segments]
        payload_bytes = sum(len(payload) for payload in encoded_payloads)
    elif residual_coding == "zero-run":
        coding_type = RESIDUAL_CODEC_ZERO_RUN_VARINT
        encoded_payloads = [
            encode_int_list_zero_run_varint(q_res) for q_res in q_resid_segments
        ]
        payload_bytes = sum(len(payload) for payload in encoded_payloads)
    elif residual_coding == "auto":
        varint_payloads = [encode_int_list_varint(q_res) for q_res in q_resid_segments]
        zero_run_payloads = [
            encode_int_list_zero_run_varint(q_res) for q_res in q_resid_segments
        ]

        varint_size = sum(len(payload) for payload in varint_payloads)
        zero_run_size = sum(len(payload) for payload in zero_run_payloads)

        if zero_run_size < varint_size:
            coding_type = RESIDUAL_CODEC_ZERO_RUN_VARINT
            encoded_payloads = zero_run_payloads
            payload_bytes = zero_run_size
        else:
            coding_type = RESIDUAL_CODEC_VARINT
            encoded_payloads = varint_payloads
            payload_bytes = varint_size
    else:
        raise ValueError(
            f"Unknown residual_coding '{residual_coding}', "
            "expected 'raw', 'varint', 'zero-run' or 'auto'"
        )

    for q_res in q_resid_segments:
        if len(q_res) > MAX_SEGMENT_POINTS:
            raise ValueError("Segment length exceeds maximum " f"{MAX_SEGMENT_POINTS}")

    for payload in encoded_payloads or []:
        if len(payload) > MAX_RESIDUAL_BLOCK_BYTES:
            raise ValueError(
                "Residual block exceeds maximum size "
                f"{MAX_RESIDUAL_BLOCK_BYTES} bytes"
            )

    encoded_size = (
        FILE_HEADER_STRUCT.size
        + header_len
        + n_segments * SEGMENT_ENTRY_V2_STRUCT.size
        + RESIDUAL_SECTION_HEADER_STRUCT.size
        + n_segments * RESIDUAL_BLOCK_HEADER_STRUCT.size
        + payload_bytes
    )
    _validate_encoded_size(encoded_size)

    buf = bytearray()

    buf += FILE_HEADER_STRUCT.pack(
        b"LSG2",
        FORMAT_VERSION_V2,
        0,
        header_len,
        n_points,
        n_segments,
        0,
        0,
    )

    buf += context_bytes

    for seg in v2_segments:
        buf += SEGMENT_ENTRY_V2_STRUCT.pack(
            seg.start_idx,
            seg.end_idx,
            seg.predictor_type,
            seg.mean,
            seg.slope,
            seg.intercept,
            seg.quant_step_Q,
            seg.seed_value,
        )

    buf += RESIDUAL_SECTION_HEADER_STRUCT.pack(
        coding_type,
        0,
        0,
        0,
    )

    for seg_id, q_res in enumerate(q_resid_segments):
        seg_len = len(q_res)

        if coding_type == RESIDUAL_CODEC_RAW_INT32:
            byte_len = seg_len * 4

            buf += RESIDUAL_BLOCK_HEADER_STRUCT.pack(
                seg_id,
                seg_len,
                byte_len,
            )

            if seg_len:
                buf += struct.pack(
                    f"<{seg_len}i",
                    *q_res,
                )
        else:
            assert encoded_payloads is not None
            payload = encoded_payloads[seg_id]

            buf += RESIDUAL_BLOCK_HEADER_STRUCT.pack(
                seg_id,
                seg_len,
                len(payload),
            )

            buf += payload

    return bytes(buf)


def _decode_timeseries_v2(data: bytes) -> TimeSeries:
    """
    Decode Version 2 by losslessly widening L32 metadata to the V1 semantic
    representation, then invoking the unchanged V1 reconstruction path.
    """
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
    ) = FILE_HEADER_STRUCT.unpack_from(
        data,
        0,
    )

    if magic != b"LSG2":
        raise ValueError("Invalid magic, not an LSG2 file")

    if version != FORMAT_VERSION_V2:
        raise ValueError(f"Expected LSG2 version 2, got {version}")

    offset = FILE_HEADER_STRUCT.size

    context_end = offset + header_len

    if context_end > len(data):
        raise ValueError("Truncated LSG2 context")

    context_bytes = data[offset:context_end]

    offset = context_end

    expanded = bytearray()

    expanded += FILE_HEADER_STRUCT.pack(
        magic,
        FORMAT_VERSION_V1,
        flags,
        header_len,
        n_points,
        n_segments,
        reserved1,
        reserved2,
    )

    expanded += context_bytes

    expected_start = 0

    for _ in range(n_segments):
        segment_end = offset + SEGMENT_ENTRY_V2_STRUCT.size

        if segment_end > len(data):
            raise ValueError("Truncated V2 segment table")

        (
            start_idx,
            end_idx,
            predictor_type,
            mean,
            slope,
            intercept,
            quant_step_Q,
            seed_value,
        ) = SEGMENT_ENTRY_V2_STRUCT.unpack_from(
            data,
            offset,
        )

        offset = segment_end

        if predictor_type not in (0, 1, 2):
            raise ValueError(f"Unsupported V2 predictor_type " f"{predictor_type}")

        if end_idx < start_idx:
            raise ValueError("Invalid V2 segment extent")

        if start_idx != expected_start:
            raise ValueError("Non-contiguous V2 segment table")

        expected_start = end_idx + 1

        real_values = (
            mean,
            slope,
            intercept,
            quant_step_Q,
            seed_value,
        )

        if any(not math.isfinite(value) for value in real_values):
            raise ValueError("V2 segment metadata must be finite")

        if not math.isfinite(quant_step_Q) or quant_step_Q <= 0.0:
            raise ValueError("V2 quantization step Q must " "be finite and > 0")

        expanded += SEGMENT_ENTRY_STRUCT.pack(
            start_idx,
            end_idx,
            predictor_type,
            0,
            0,
            0,
            float(mean),
            float(slope),
            float(intercept),
            float(quant_step_Q),
            float(seed_value),
        )

    if expected_start != n_points and n_segments:
        raise ValueError("V2 segment table does not cover " "the declared point count")

    if n_segments == 0 and n_points != 0:
        raise ValueError("Non-empty V2 series has no segments")

    expanded += data[offset:]

    return _decode_timeseries_v1(bytes(expanded))


def encode_timeseries(
    ts: TimeSeries,
    segment_length: int = 64,
    predictor: str = "linear",
    C_Q: float = 0.125,
    Q_MIN: float = 1e-6,
    segment_mode: str = "fixed",
    min_segment_length: int = 32,
    max_segment_length: int = 128,
    mse_threshold: float = 0.5,
    residual_coding: str = "raw",
) -> bytes:
    """Encode a TimeSeries using the current default V2 wire format."""
    return encode_timeseries_v2(
        ts,
        segment_length=segment_length,
        predictor=predictor,
        C_Q=C_Q,
        Q_MIN=Q_MIN,
        segment_mode=segment_mode,
        min_segment_length=min_segment_length,
        max_segment_length=max_segment_length,
        mse_threshold=mse_threshold,
        residual_coding=residual_coding,
    )


def decode_timeseries(data: bytes) -> TimeSeries:
    """
    Decode a supported LSG2 stream.

    Version 1 is delegated byte-for-byte to the historical decoder.
    Version 2 uses the frozen 32-byte L32 segment-entry representation.
    Unknown versions fail closed.
    """
    _preflight_lsg2(data)

    if len(data) < FILE_HEADER_STRUCT.size:
        raise ValueError("Data too short to contain header")

    (
        magic,
        version,
        _flags,
        _header_len,
        _n_points,
        _n_segments,
        _reserved1,
        _reserved2,
    ) = FILE_HEADER_STRUCT.unpack_from(
        data,
        0,
    )

    if magic != b"LSG2":
        raise ValueError("Invalid magic, not an LSG2 file")

    if version == FORMAT_VERSION_V1:
        return _decode_timeseries_v1(data)

    if version == FORMAT_VERSION_V2:
        return _decode_timeseries_v2(data)

    raise ValueError(
        f"Unsupported LSG2 version {version}; " "supported versions are 1 and 2"
    )
