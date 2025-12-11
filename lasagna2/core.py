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
SEGMENT_ENTRY_STRUCT = struct.Struct("<6Iddddd")

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

        segments.append((start, best_end))
        i = best_end + 1

    return segments


# ---------------------------------------------------------------------------
# Context JSON
# ---------------------------------------------------------------------------
def build_context_json(ts: TimeSeries) -> bytes:
    ctx = {
        "sampling": {
            "dt": ts.dt,
            "t0": ts.t0,
        },
        "unit": ts.unit,
    }
    return json.dumps(ctx, separators=(",", ":")).encode("utf-8")


# ---------------------------------------------------------------------------
# Codec: encode / decode
# ---------------------------------------------------------------------------
def encode_timeseries(
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
    """
    Encode a TimeSeries into Lasagna MVP bytes (.lsg2).

    Args:
        ts: TimeSeries object.
        segment_length: fixed segment length (used if segment_mode='fixed').
        predictor: 'mean', 'linear', 'rw', or 'auto' (choose per segment).
        C_Q: coefficient for quantization step Q.
        Q_MIN: minimum Q to avoid zero.
        segment_mode: 'fixed' or 'adaptive'.
        min_segment_length: min length for adaptive segmentation.
        max_segment_length: max length for adaptive segmentation.
        mse_threshold: max allowed MSE to extend a segment (adaptive).
        residual_coding: 'raw' (int32) or 'varint' (ZigZag+varint).
    """
    values = ts.values
    n_points = len(values)
    if n_points == 0:
        raise ValueError("TimeSeries is empty")

    predictor_map = {
        "mean": 0,
        "linear": 1,
        "rw": 2,
    }

    if predictor == "auto":
        default_predictor_type = None
        predictor_type_for_segmentation = 1  # linear come modello di fondo
    else:
        if predictor not in predictor_map:
            raise ValueError(
                f"Unknown predictor '{predictor}', "
                f"expected one of {list(predictor_map) + ['auto']}"
            )
        default_predictor_type = predictor_map[predictor]
        predictor_type_for_segmentation = default_predictor_type

    # 1) Segmentazione
    if segment_mode == "fixed":
        segment_ranges = segment_series_fixed_length(n_points, segment_length)
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

    segments: List[SegmentEntry] = []
    q_resid_segments: List[List[int]] = []

    # 2) Costruzione segmenti
    for start, end in segment_ranges:
        x_seg = values[start : end + 1]
        length = len(x_seg)
        mean, slope, intercept, _var = compute_stats(x_seg)
        seed_value = x_seg[0] if x_seg else 0.0

        # Scegli il predittore per questo segmento
        if predictor == "auto":
            best_type = None
            best_mse = float("inf")

            # prova mean, linear, rw
            for cand_type in (0, 1, 2):
                # 1) predizioni
                preds_c = _build_preds_for_segmentation(
                    x_seg,
                    predictor_type=cand_type,
                    mean=mean,
                    slope=slope,
                    intercept=intercept,
                    seed_value=seed_value,
                )

                # 2) residui + quantizzazione
                residuals_c = [v - p for v, p in zip(x_seg, preds_c)]
                q_res_c, Q_c = quantize_residuals(residuals_c, C_Q=C_Q, Q_MIN=Q_MIN)

                # 3) decode locale e MSE finale
                x_hat_c = [0.0] * length
                if cand_type in (0, 1):
                    # mean / linear: predizioni indipendenti
                    preds_dec = preds_c
                    for i in range(length):
                        x_hat_c[i] = preds_dec[i] + q_res_c[i] * Q_c
                elif cand_type == 2:
                    # random-walk: ricostruzione iterativa
                    if length > 0:
                        preds_dec = [0.0] * length
                        preds_dec[0] = seed_value
                        x_hat_c[0] = preds_dec[0] + q_res_c[0] * Q_c
                        for i in range(1, length):
                            preds_dec[i] = x_hat_c[i - 1]
                            x_hat_c[i] = preds_dec[i] + q_res_c[i] * Q_c

                if length > 0:
                    mse_c = sum((v - h) ** 2 for v, h in zip(x_seg, x_hat_c)) / length
                else:
                    mse_c = 0.0

                if mse_c < best_mse:
                    best_mse = mse_c
                    best_type = cand_type

            if best_type is None:
                best_type = 0  # fallback paranoico

            predictor_type_seg = best_type
            # predizioni "buone" per l'encode reale
            preds = _build_preds_for_segmentation(
                x_seg,
                predictor_type=predictor_type_seg,
                mean=mean,
                slope=slope,
                intercept=intercept,
                seed_value=seed_value,
            )
        else:
            predictor_type_seg = default_predictor_type  # type: ignore[assignment]
            preds = _build_preds_for_segmentation(
                x_seg,
                predictor_type=predictor_type_seg,
                mean=mean,
                slope=slope,
                intercept=intercept,
                seed_value=seed_value,
            )

        residuals = [v - p for v, p in zip(x_seg, preds)]
        q_res, Q = quantize_residuals(residuals, C_Q=C_Q, Q_MIN=Q_MIN)

        seg = SegmentEntry(
            start_idx=start,
            end_idx=end,
            predictor_type=predictor_type_seg,
            mean=mean,
            slope=slope,
            intercept=intercept,
            quant_step_Q=Q,
            seed_value=seed_value,
        )
        segments.append(seg)
        q_resid_segments.append(q_res)

    # 3) Costruzione buffer binario
    buf = bytearray()

    ctx_bytes = build_context_json(ts)
    header_len = len(ctx_bytes)

    magic = b"LSG2"
    version = 1
    flags = 0
    n_segments = len(segments)
    reserved1 = 0
    reserved2 = 0

    buf += FILE_HEADER_STRUCT.pack(
        magic,
        version,
        flags,
        header_len,
        n_points,
        n_segments,
        reserved1,
        reserved2,
    )

    buf += ctx_bytes

    # Tabella segmenti
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

    # Header sezione residui
    if residual_coding == "raw":
        coding_type = 0
    elif residual_coding == "varint":
        coding_type = 1
    else:
        raise ValueError(
            f"Unknown residual_coding '{residual_coding}', expected 'raw' or 'varint'"
        )

    buf += RESIDUAL_SECTION_HEADER_STRUCT.pack(
        coding_type,
        0,
        0,
        0,
    )

    # Blocchi residui
    for seg_id, q_res in enumerate(q_resid_segments):
        seg_len = len(q_res)
        if coding_type == 0:
            byte_len = seg_len * 4
            buf += RESIDUAL_BLOCK_HEADER_STRUCT.pack(seg_id, seg_len, byte_len)
            if seg_len > 0:
                buf += struct.pack(f"<{seg_len}i", *q_res)
        else:
            data_bytes = encode_int_list_varint(q_res)
            byte_len = len(data_bytes)
            buf += RESIDUAL_BLOCK_HEADER_STRUCT.pack(seg_id, seg_len, byte_len)
            buf += data_bytes

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

    ctx = json.loads(ctx_bytes.decode("utf-8"))
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

    if coding_type not in (0, 1):
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

        if coding_type == 0:
            if seg_len * 4 != byte_len:
                raise ValueError("byte_len != seg_len * 4 for raw residuals")
            if seg_len > 0:
                q_res = list(struct.unpack(f"<{seg_len}i", block_bytes))
            else:
                q_res = []
        else:
            q_res = decode_int_list_varint(block_bytes, seg_len)

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
