"""Experimental compact wire prototype for Lasagna issue #26.

This module is deliberately excluded from the public package API.

The encoder derives the prototype stream from canonical V2 bytes so
segmentation, predictor selection, binary32 metadata rounding, residual
integers and residual payload encoding remain V2-controlled.

The decoder parses the compact grammar strictly, expands it to the historical
V1 semantic representation, then delegates numerical reconstruction to the
existing V1 decoder path.
"""

from __future__ import annotations

import json
import math
import struct
from dataclasses import dataclass

from lasagna2 import core

FORMAT_VERSION_EXPERIMENTAL_COMPACT = 3

COMMON_PREFIX_STRUCT = struct.Struct("<IBfI")
MEAN_RECORD_STRUCT = struct.Struct("<IBfIf")
LINEAR_RECORD_STRUCT = struct.Struct("<IBfIff")
RANDOM_WALK_RECORD_STRUCT = struct.Struct("<IBfIf")

assert COMMON_PREFIX_STRUCT.size == 13
assert MEAN_RECORD_STRUCT.size == 17
assert LINEAR_RECORD_STRUCT.size == 21
assert RANDOM_WALK_RECORD_STRUCT.size == 17


@dataclass(frozen=True, slots=True)
class _V2Segment:
    start_idx: int
    end_idx: int
    predictor_type: int
    mean: float
    slope: float
    intercept: float
    quant_step_Q: float
    seed_value: float


def _validate_context_bytes(context_bytes: bytes) -> None:
    if len(context_bytes) > core.MAX_CONTEXT_BYTES:
        raise ValueError(
            f"Context JSON exceeds maximum size {core.MAX_CONTEXT_BYTES} bytes"
        )

    core._validate_context_depth(context_bytes)

    try:
        decoded = json.loads(context_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid context JSON") from exc

    if not isinstance(decoded, dict):
        raise TypeError("Context JSON must decode to an object")


def _decode_varint_strict(data: bytes, offset: int) -> tuple[int, int]:
    result = 0

    for index in range(core.MAX_VARINT_BYTES):
        if offset >= len(data):
            raise ValueError("Truncated varint")

        byte = data[offset]
        offset += 1
        result |= (byte & 0x7F) << (7 * index)

        if not (byte & 0x80):
            return result, offset

    raise ValueError("Varint exceeds maximum encoded length")


def _zigzag_decode_int32(value: int) -> int:
    decoded = core.zigzag_decode(value)

    if decoded < core.INT32_MIN or decoded > core.INT32_MAX:
        raise ValueError("Decoded residual exceeds signed int32 range")

    return decoded


def _decode_varint_payload_strict(
    payload: bytes,
    segment_length: int,
) -> list[int]:
    residuals: list[int] = []
    offset = 0

    for _ in range(segment_length):
        value, offset = _decode_varint_strict(payload, offset)
        residuals.append(_zigzag_decode_int32(value))

    if offset != len(payload):
        raise ValueError("Extra bytes inside varint payload")

    return residuals


def _decode_zero_run_payload_strict(
    payload: bytes,
    segment_length: int,
) -> list[int]:
    residuals: list[int] = []
    offset = 0

    while offset < len(payload):
        token, offset = _decode_varint_strict(payload, offset)

        if token == 0:
            run_length, offset = _decode_varint_strict(payload, offset)

            if run_length < core.ZERO_RUN_MIN_LENGTH:
                raise ValueError("Invalid zero-run length")

            remaining = segment_length - len(residuals)

            if run_length > remaining:
                raise ValueError("Zero-run exceeds declared residual count")

            residuals.extend([0] * run_length)
            continue

        residuals.append(_zigzag_decode_int32(token - 1))

        if len(residuals) > segment_length:
            raise ValueError("Decoded residual count exceeds declaration")

    if len(residuals) != segment_length:
        raise ValueError("Decoded residual count does not match declaration")

    return residuals


def _decode_payload_strict(
    coding_type: int,
    payload: bytes,
    segment_length: int,
) -> list[int]:
    if coding_type == core.RESIDUAL_CODEC_RAW_INT32:
        expected_length = 4 * segment_length

        if len(payload) != expected_length:
            raise ValueError("RAW_INT32 payload length does not match segment length")

        if not segment_length:
            return []

        return list(
            struct.unpack(
                f"<{segment_length}i",
                payload,
            )
        )

    if len(payload) > core.MAX_VARINT_BYTES * segment_length:
        raise ValueError("Variable-length residual payload exceeds bound")

    if coding_type == core.RESIDUAL_CODEC_VARINT:
        return _decode_varint_payload_strict(
            payload,
            segment_length,
        )

    if coding_type == core.RESIDUAL_CODEC_ZERO_RUN_VARINT:
        return _decode_zero_run_payload_strict(
            payload,
            segment_length,
        )

    raise ValueError(f"Unsupported residual coding type {coding_type}")


def _read_v2_segments(
    data: bytes,
    offset: int,
    n_points: int,
    n_segments: int,
) -> tuple[list[_V2Segment], int]:
    segments: list[_V2Segment] = []
    expected_start = 0

    for _ in range(n_segments):
        end = offset + core.SEGMENT_ENTRY_V2_STRUCT.size

        if end > len(data):
            raise ValueError("Truncated V2 segment table")

        values = core.SEGMENT_ENTRY_V2_STRUCT.unpack_from(data, offset)
        offset = end

        segment = _V2Segment(*values)

        if segment.predictor_type not in (0, 1, 2):
            raise ValueError(f"Unsupported V2 predictor_type {segment.predictor_type}")

        if segment.end_idx < segment.start_idx:
            raise ValueError("Invalid V2 segment extent")

        if segment.start_idx != expected_start:
            raise ValueError("Non-contiguous V2 segment table")

        real_values = (
            segment.mean,
            segment.slope,
            segment.intercept,
            segment.quant_step_Q,
            segment.seed_value,
        )

        if any(not math.isfinite(value) for value in real_values):
            raise ValueError("V2 segment metadata must be finite")

        if segment.quant_step_Q <= 0.0:
            raise ValueError("V2 quantization step Q must be > 0")

        expected_start = segment.end_idx + 1
        segments.append(segment)

    if expected_start != n_points and n_segments:
        raise ValueError("V2 segment table does not cover the declared point count")

    if n_segments == 0 and n_points != 0:
        raise ValueError("Non-empty V2 series has no segments")

    return segments, offset


def compact_from_v2(data: bytes) -> bytes:
    """Repack one canonical valid V2 stream into the frozen #26 grammar."""
    core._preflight_lsg2(data)

    (
        magic,
        version,
        flags,
        header_len,
        n_points,
        n_segments,
        reserved1,
        reserved2,
    ) = core.FILE_HEADER_STRUCT.unpack_from(data, 0)

    if magic != b"LSG2":
        raise ValueError("Invalid magic, not an LSG2 file")

    if version != core.FORMAT_VERSION_V2:
        raise ValueError(f"Expected LSG2 version 2, got {version}")

    offset = core.FILE_HEADER_STRUCT.size
    context_end = offset + header_len

    if context_end > len(data):
        raise ValueError("Truncated LSG2 context")

    context_bytes = data[offset:context_end]
    offset = context_end

    segments, offset = _read_v2_segments(
        data,
        offset,
        n_points,
        n_segments,
    )

    coding_header_end = offset + core.RESIDUAL_SECTION_HEADER_STRUCT.size

    if coding_header_end > len(data):
        raise ValueError("Truncated residual coding header")

    (
        coding_type,
        coding_reserved1,
        coding_reserved2,
        coding_reserved3,
    ) = core.RESIDUAL_SECTION_HEADER_STRUCT.unpack_from(data, offset)

    if coding_type not in (
        core.RESIDUAL_CODEC_RAW_INT32,
        core.RESIDUAL_CODEC_VARINT,
        core.RESIDUAL_CODEC_ZERO_RUN_VARINT,
    ):
        raise ValueError(f"Unsupported residual coding type {coding_type}")

    offset = coding_header_end

    payloads: list[bytes | None] = [None] * n_segments

    for _ in range(n_segments):
        block_end = offset + core.RESIDUAL_BLOCK_HEADER_STRUCT.size

        if block_end > len(data):
            raise ValueError("Truncated residual block header")

        seg_id, seg_len, payload_length = core.RESIDUAL_BLOCK_HEADER_STRUCT.unpack_from(
            data, offset
        )
        offset = block_end

        if seg_id >= n_segments:
            raise ValueError(f"Invalid residual segment id {seg_id}")

        if payloads[seg_id] is not None:
            raise ValueError(f"Duplicate residual block for seg_id={seg_id}")

        expected_length = segments[seg_id].end_idx - segments[seg_id].start_idx + 1

        if seg_len != expected_length:
            raise ValueError("Residual sample count does not match segment length")

        payload_end = offset + payload_length

        if payload_end > len(data):
            raise ValueError("Truncated residual payload")

        payload = data[offset:payload_end]
        offset = payload_end

        _decode_payload_strict(
            coding_type,
            payload,
            seg_len,
        )

        payloads[seg_id] = payload

    if any(payload is None for payload in payloads):
        raise ValueError("Missing residual block")

    out = bytearray()

    out += core.FILE_HEADER_STRUCT.pack(
        b"LSG2",
        FORMAT_VERSION_EXPERIMENTAL_COMPACT,
        flags,
        header_len,
        n_points,
        n_segments,
        reserved1,
        reserved2,
    )

    out += context_bytes
    out += core.RESIDUAL_SECTION_HEADER_STRUCT.pack(
        coding_type,
        coding_reserved1,
        coding_reserved2,
        coding_reserved3,
    )

    for segment, payload_optional in zip(
        segments,
        payloads,
        strict=True,
    ):
        assert payload_optional is not None
        payload = payload_optional

        segment_length = segment.end_idx - segment.start_idx + 1
        payload_length = len(payload)

        if segment.predictor_type == 0:
            out += MEAN_RECORD_STRUCT.pack(
                segment_length,
                segment.predictor_type,
                segment.quant_step_Q,
                payload_length,
                segment.mean,
            )
        elif segment.predictor_type == 1:
            out += LINEAR_RECORD_STRUCT.pack(
                segment_length,
                segment.predictor_type,
                segment.quant_step_Q,
                payload_length,
                segment.slope,
                segment.intercept,
            )
        else:
            out += RANDOM_WALK_RECORD_STRUCT.pack(
                segment_length,
                segment.predictor_type,
                segment.quant_step_Q,
                payload_length,
                segment.seed_value,
            )

        out += payload

    core._validate_encoded_size(len(out))

    return bytes(out)


def encode_timeseries_compact_experimental(
    ts: core.TimeSeries,
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
    """Encode through canonical V2, then repack into experimental compact V3."""
    v2 = core.encode_timeseries_v2(
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

    return compact_from_v2(v2)


def decode_timeseries_compact_experimental(
    data: bytes,
) -> core.TimeSeries:
    """Strictly decode one #26 compact prototype stream."""
    if len(data) > core.MAX_INPUT_BYTES:
        raise ValueError(f"Input exceeds maximum size {core.MAX_INPUT_BYTES} bytes")

    if len(data) < core.FILE_HEADER_STRUCT.size:
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
    ) = core.FILE_HEADER_STRUCT.unpack_from(data, 0)

    if magic != b"LSG2":
        raise ValueError("Invalid magic, not an LSG2 file")

    if version != FORMAT_VERSION_EXPERIMENTAL_COMPACT:
        raise ValueError(f"Expected experimental compact LSG2 version 3, got {version}")

    if flags != 0 or reserved1 != 0 or reserved2 != 0:
        raise ValueError("Experimental compact header reserved fields must be zero")

    if n_points > core.MAX_POINTS:
        raise ValueError(f"n_points={n_points} exceeds maximum {core.MAX_POINTS}")

    if n_segments > core.MAX_SEGMENTS:
        raise ValueError(f"n_segments={n_segments} exceeds maximum {core.MAX_SEGMENTS}")

    if (n_points == 0) != (n_segments == 0):
        raise ValueError(
            "n_points and n_segments must either both be zero or both be nonzero"
        )

    if n_points and n_segments > n_points:
        raise ValueError("n_segments cannot exceed n_points")

    if header_len > core.MAX_CONTEXT_BYTES:
        raise ValueError(
            f"Context JSON exceeds maximum size {core.MAX_CONTEXT_BYTES} bytes"
        )

    offset = core.FILE_HEADER_STRUCT.size
    context_end = offset + header_len

    if context_end > len(data):
        raise ValueError("Truncated LSG2 context")

    context_bytes = data[offset:context_end]
    _validate_context_bytes(context_bytes)
    offset = context_end

    coding_end = offset + core.RESIDUAL_SECTION_HEADER_STRUCT.size

    if coding_end > len(data):
        raise ValueError("Truncated residual coding header")

    (
        coding_type,
        coding_reserved1,
        coding_reserved2,
        coding_reserved3,
    ) = core.RESIDUAL_SECTION_HEADER_STRUCT.unpack_from(data, offset)

    if any(
        value != 0
        for value in (
            coding_reserved1,
            coding_reserved2,
            coding_reserved3,
        )
    ):
        raise ValueError("Experimental compact coding reserved fields must be zero")

    if coding_type not in (
        core.RESIDUAL_CODEC_RAW_INT32,
        core.RESIDUAL_CODEC_VARINT,
        core.RESIDUAL_CODEC_ZERO_RUN_VARINT,
    ):
        raise ValueError(f"Unsupported residual coding type {coding_type}")

    offset = coding_end
    cumulative_length = 0

    v1_segments = bytearray()
    v1_residual_blocks = bytearray()

    for seg_id in range(n_segments):
        prefix_end = offset + COMMON_PREFIX_STRUCT.size

        if prefix_end > len(data):
            raise ValueError("Truncated compact segment prefix")

        (
            segment_length,
            predictor_type,
            quant_step_Q,
            payload_length,
        ) = COMMON_PREFIX_STRUCT.unpack_from(data, offset)

        if predictor_type == 0:
            record_struct = MEAN_RECORD_STRUCT
        elif predictor_type == 1:
            record_struct = LINEAR_RECORD_STRUCT
        elif predictor_type == 2:
            record_struct = RANDOM_WALK_RECORD_STRUCT
        else:
            raise ValueError(f"Unsupported compact predictor_type {predictor_type}")

        record_end = offset + record_struct.size

        if record_end > len(data):
            raise ValueError("Truncated compact predictor record")

        record = record_struct.unpack_from(data, offset)
        offset = record_end

        if segment_length == 0:
            raise ValueError("Compact segment length must be positive")

        if segment_length > core.MAX_SEGMENT_POINTS:
            raise ValueError(
                f"Compact segment length exceeds maximum {core.MAX_SEGMENT_POINTS}"
            )

        remaining_points = n_points - cumulative_length

        if segment_length > remaining_points:
            raise ValueError("Compact segment coverage exceeds n_points")

        if payload_length == 0:
            raise ValueError("Compact residual payload must be non-empty")

        if payload_length > core.MAX_RESIDUAL_BLOCK_BYTES:
            raise ValueError(
                "Compact residual payload exceeds maximum "
                f"{core.MAX_RESIDUAL_BLOCK_BYTES} bytes"
            )

        if (
            coding_type != core.RESIDUAL_CODEC_RAW_INT32
            and payload_length > core.MAX_VARINT_BYTES * segment_length
        ):
            raise ValueError("Compact variable-length residual payload exceeds bound")

        payload_end = offset + payload_length

        if payload_end > len(data):
            raise ValueError("Truncated compact residual payload")

        payload = data[offset:payload_end]
        offset = payload_end

        residuals = _decode_payload_strict(
            coding_type,
            payload,
            segment_length,
        )

        if len(residuals) != segment_length:
            raise ValueError("Decoded residual count does not match segment length")

        values = tuple(float(value) for value in record[4:])

        if any(not math.isfinite(value) for value in values):
            raise ValueError("Compact segment metadata must be finite")

        if not math.isfinite(quant_step_Q) or quant_step_Q <= 0.0:
            raise ValueError("Compact quantization step Q must be finite and > 0")

        mean = 0.0
        slope = 0.0
        intercept = 0.0
        seed_value = 0.0

        if predictor_type == 0:
            mean = values[0]
        elif predictor_type == 1:
            slope, intercept = values
        else:
            seed_value = values[0]

        start_idx = cumulative_length
        end_idx = start_idx + segment_length - 1
        cumulative_length += segment_length

        v1_segments += core.SEGMENT_ENTRY_STRUCT.pack(
            start_idx,
            end_idx,
            predictor_type,
            0,
            0,
            0,
            mean,
            slope,
            intercept,
            float(quant_step_Q),
            seed_value,
        )

        v1_residual_blocks += core.RESIDUAL_BLOCK_HEADER_STRUCT.pack(
            seg_id,
            segment_length,
            payload_length,
        )
        v1_residual_blocks += payload

    if cumulative_length != n_points:
        raise ValueError("Compact segments do not cover the declared point count")

    if offset != len(data):
        raise ValueError("Trailing bytes after compact stream")

    expanded = bytearray()

    expanded += core.FILE_HEADER_STRUCT.pack(
        b"LSG2",
        core.FORMAT_VERSION_V1,
        0,
        header_len,
        n_points,
        n_segments,
        0,
        0,
    )
    expanded += context_bytes
    expanded += v1_segments
    expanded += core.RESIDUAL_SECTION_HEADER_STRUCT.pack(
        coding_type,
        0,
        0,
        0,
    )
    expanded += v1_residual_blocks

    return core._decode_timeseries_v1(bytes(expanded))
