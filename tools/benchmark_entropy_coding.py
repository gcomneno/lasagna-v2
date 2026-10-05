#!/usr/bin/env python3
"""Shadow entropy-coding benchmark for Lasagna 2 issue #9."""

from __future__ import annotations

import argparse
import csv
import heapq
import importlib.util
import math
import statistics
import struct
import sys
import time
import zlib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"

for import_path in (ROOT, TOOLS):
    value = str(import_path)
    if value not in sys.path:
        sys.path.insert(0, value)

from benchmark_codec import load_csv_values  # noqa: E402
from lasagna2 import core  # noqa: E402


HUFFMAN_FIXED_HEADER = struct.Struct("<HHH")
HUFFMAN_SYMBOL_ENTRY = struct.Struct("<BB")
DEFLATE_FIXED_HEADER = struct.Struct("<HH")

SELECTOR_BYTES_PER_BLOCK = 1
BENCHMARK_WARMUP = 1
BENCHMARK_RUNS = 7


RESULT_FIELDS = [
    "evidence_group",
    "dataset",
    "predictor",
    "base_residual_codec",
    "n_samples",
    "block_count",
    "source_payload_bytes",
    "current_v2_total_bytes",
    "huffman_forced_bytes",
    "huffman_forced_delta",
    "huffman_win_blocks",
    "huffman_tie_blocks",
    "huffman_loss_blocks",
    "huffman_selective_gross_bytes",
    "huffman_selector_bytes",
    "huffman_selective_bytes",
    "huffman_selective_delta",
    "huffman_projected_total_bytes",
    "huffman_projected_total_delta",
    "deflate_forced_bytes",
    "deflate_forced_delta",
    "deflate_win_blocks",
    "deflate_tie_blocks",
    "deflate_loss_blocks",
    "deflate_selective_gross_bytes",
    "deflate_selector_bytes",
    "deflate_selective_bytes",
    "deflate_selective_delta",
    "deflate_projected_total_bytes",
    "deflate_projected_total_delta",
    "huffman_encode_median_ms",
    "huffman_decode_median_ms",
    "deflate_encode_median_ms",
    "deflate_decode_median_ms",
]


BLOCK_FIELDS = [
    "evidence_group",
    "dataset",
    "predictor",
    "base_residual_codec",
    "segment_index",
    "segment_length",
    "source_payload_bytes",
    "source_symbol_count",
    "source_byte_entropy_bits_per_symbol",
    "huffman_bitstream_bytes",
    "huffman_codebook_bytes",
    "huffman_total_bytes",
    "huffman_delta_bytes",
    "deflate_stream_bytes",
    "deflate_total_bytes",
    "deflate_delta_bytes",
]


BUCKET_FIELDS = [
    "candidate",
    "bucket",
    "block_count",
    "win_blocks",
    "win_fraction",
    "median_delta_bytes",
    "p95_delta_bytes",
    "worst_delta_bytes",
]


@dataclass(order=True)
class HuffmanNode:
    frequency: int
    order: int
    symbol: int | None = None
    left: "HuffmanNode | None" = None
    right: "HuffmanNode | None" = None


def _load_residual_module():
    path = TOOLS / "analyze_residual_distributions.py"

    spec = importlib.util.spec_from_file_location(
        "analyze_residual_distributions_issue9",
        path,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load residual-distribution module")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


residuals = _load_residual_module()


def byte_entropy(data: bytes) -> float:
    if not data:
        return 0.0

    counts = Counter(data)
    total = len(data)

    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def _huffman_code_lengths(
    data: bytes,
) -> dict[int, int]:
    if not data:
        return {}

    frequencies = Counter(data)

    if len(frequencies) == 1:
        symbol = next(iter(frequencies))
        return {symbol: 1}

    heap: list[HuffmanNode] = []
    order = 0

    for symbol in sorted(frequencies):
        heapq.heappush(
            heap,
            HuffmanNode(
                frequency=frequencies[symbol],
                order=order,
                symbol=symbol,
            ),
        )
        order += 1

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)

        parent = HuffmanNode(
            frequency=(left.frequency + right.frequency),
            order=order,
            left=left,
            right=right,
        )
        order += 1
        heapq.heappush(heap, parent)

    lengths: dict[int, int] = {}

    def walk(
        node: HuffmanNode,
        depth: int,
    ) -> None:
        if node.symbol is not None:
            lengths[node.symbol] = max(
                1,
                depth,
            )
            return

        assert node.left is not None
        assert node.right is not None

        walk(node.left, depth + 1)
        walk(node.right, depth + 1)

    walk(heap[0], 0)
    return lengths


def _canonical_codes(
    lengths: dict[int, int],
) -> dict[int, tuple[int, int]]:
    ordered = sorted(
        (
            length,
            symbol,
        )
        for symbol, length in lengths.items()
    )

    codes: dict[int, tuple[int, int]] = {}

    code = 0
    previous_length = 0

    for length, symbol in ordered:
        code <<= length - previous_length

        codes[symbol] = (
            code,
            length,
        )

        code += 1
        previous_length = length

    return codes


def encode_huffman_sparse(
    data: bytes,
) -> bytes:
    if len(data) > 0xFFFF:
        raise ValueError("Huffman benchmark block exceeds uint16 length")

    lengths = _huffman_code_lengths(data)

    codes = _canonical_codes(lengths)

    bit_length = sum(codes[byte][1] for byte in data)

    if bit_length > 0xFFFF:
        raise ValueError("Huffman benchmark bitstream exceeds uint16 length")

    if len(lengths) > 0xFFFF:
        raise ValueError("Huffman symbol count exceeds uint16")

    out = bytearray(
        HUFFMAN_FIXED_HEADER.pack(
            len(data),
            bit_length,
            len(lengths),
        )
    )

    for symbol in sorted(lengths):
        length = lengths[symbol]

        if length > 0xFF:
            raise ValueError("Huffman code length exceeds uint8")

        out += HUFFMAN_SYMBOL_ENTRY.pack(
            symbol,
            length,
        )

    accumulator = 0
    accumulator_bits = 0

    for byte in data:
        code, code_length = codes[byte]

        accumulator = (accumulator << code_length) | code

        accumulator_bits += code_length

        while accumulator_bits >= 8:
            shift = accumulator_bits - 8
            out.append((accumulator >> shift) & 0xFF)

            accumulator &= (1 << shift) - 1 if shift else 0

            accumulator_bits = shift

    if accumulator_bits:
        out.append((accumulator << (8 - accumulator_bits)) & 0xFF)

    return bytes(out)


def decode_huffman_sparse(
    encoded: bytes,
) -> bytes:
    if len(encoded) < HUFFMAN_FIXED_HEADER.size:
        raise ValueError("Truncated Huffman header")

    (
        original_length,
        bit_length,
        symbol_count,
    ) = HUFFMAN_FIXED_HEADER.unpack_from(
        encoded,
        0,
    )

    offset = HUFFMAN_FIXED_HEADER.size

    codebook_bytes = symbol_count * HUFFMAN_SYMBOL_ENTRY.size

    if offset + codebook_bytes > len(encoded):
        raise ValueError("Truncated Huffman codebook")

    lengths: dict[int, int] = {}

    for _ in range(symbol_count):
        symbol, length = HUFFMAN_SYMBOL_ENTRY.unpack_from(
            encoded,
            offset,
        )
        offset += HUFFMAN_SYMBOL_ENTRY.size

        if length == 0:
            raise ValueError("Invalid zero-length Huffman code")

        if symbol in lengths:
            raise ValueError("Duplicate Huffman symbol")

        lengths[symbol] = length

    bitstream_bytes = (bit_length + 7) // 8

    if offset + bitstream_bytes != len(encoded):
        raise ValueError("Malformed Huffman payload length")

    if original_length == 0:
        if bit_length != 0 or symbol_count != 0:
            raise ValueError("Malformed empty Huffman block")
        return b""

    if not lengths:
        raise ValueError("Missing Huffman codebook")

    codes = _canonical_codes(lengths)

    decode_table = {
        (length, code): symbol
        for symbol, (
            code,
            length,
        ) in codes.items()
    }

    payload = encoded[offset:]

    out = bytearray()
    code = 0
    code_length = 0
    consumed_bits = 0

    for byte in payload:
        for shift in range(7, -1, -1):
            if consumed_bits >= bit_length:
                break

            bit = (byte >> shift) & 1

            code = (code << 1) | bit
            code_length += 1
            consumed_bits += 1

            symbol = decode_table.get(
                (
                    code_length,
                    code,
                )
            )

            if symbol is not None:
                out.append(symbol)
                code = 0
                code_length = 0

                if len(out) > original_length:
                    raise ValueError("Huffman output exceeds declared length")

    if consumed_bits != bit_length:
        raise ValueError("Truncated Huffman bitstream")

    if code_length != 0:
        raise ValueError("Incomplete Huffman terminal code")

    if len(out) != original_length:
        raise ValueError("Huffman output length mismatch")

    return bytes(out)


def encode_deflate_raw(
    data: bytes,
) -> bytes:
    if len(data) > 0xFFFF:
        raise ValueError("DEFLATE benchmark block exceeds uint16 length")

    compressor = zlib.compressobj(
        level=1,
        wbits=-15,
    )

    stream = compressor.compress(data) + compressor.flush()

    if len(stream) > 0xFFFF:
        raise ValueError("DEFLATE benchmark stream exceeds uint16 length")

    return (
        DEFLATE_FIXED_HEADER.pack(
            len(data),
            len(stream),
        )
        + stream
    )


def decode_deflate_raw(
    encoded: bytes,
) -> bytes:
    if len(encoded) < DEFLATE_FIXED_HEADER.size:
        raise ValueError("Truncated DEFLATE header")

    (
        original_length,
        compressed_length,
    ) = DEFLATE_FIXED_HEADER.unpack_from(
        encoded,
        0,
    )

    stream = encoded[DEFLATE_FIXED_HEADER.size :]

    if len(stream) != compressed_length:
        raise ValueError("Malformed DEFLATE payload length")

    decompressor = zlib.decompressobj(wbits=-15)

    decoded = decompressor.decompress(stream) + decompressor.flush()

    if decompressor.unused_data:
        raise ValueError("Unexpected trailing DEFLATE data")

    if len(decoded) != original_length:
        raise ValueError("DEFLATE output length mismatch")

    return decoded


def median_runtime_ms(
    operation: Callable[[], object],
) -> float:
    for _ in range(BENCHMARK_WARMUP):
        operation()

    samples: list[float] = []

    for _ in range(BENCHMARK_RUNS):
        start = time.perf_counter_ns()
        operation()
        samples.append((time.perf_counter_ns() - start) / 1_000_000.0)

    return statistics.median(samples)


def _source_payloads(
    q_blocks: list[list[int]],
    base_residual_codec: str,
) -> tuple[str, list[bytes]]:
    varint_payloads = [core.encode_int_list_varint(block) for block in q_blocks]

    if base_residual_codec == "varint":
        return (
            "varint",
            varint_payloads,
        )

    if base_residual_codec != "auto":
        raise ValueError("Unsupported benchmark base residual codec")

    zero_payloads = [core.encode_int_list_zero_run_varint(block) for block in q_blocks]

    if sum(len(payload) for payload in zero_payloads) < sum(
        len(payload) for payload in varint_payloads
    ):
        return (
            "zero-run",
            zero_payloads,
        )

    return (
        "varint",
        varint_payloads,
    )


def _current_v2_size(
    values: list[float],
    predictor: str,
    residual_coding: str,
) -> int:
    ts = core.TimeSeries(
        values=values,
        dt=1.0,
        t0="1970-01-01T00:00:00Z",
        unit="entropy-study",
    )

    encoded = core.encode_timeseries_v2(
        ts,
        segment_length=64,
        predictor=predictor,
        C_Q=0.125,
        Q_MIN=1e-6,
        segment_mode="adaptive",
        min_segment_length=32,
        max_segment_length=128,
        mse_threshold=0.5,
        residual_coding=residual_coding,
    )

    return len(encoded)


def evaluate_stream(
    evidence_group: str,
    dataset: Path,
    predictor: str,
    base_residual_codec: str,
) -> tuple[
    dict[str, object],
    list[dict[str, object]],
]:
    values = load_csv_values(dataset)

    segments, q_blocks = residuals.build_v2_residual_stream(
        values,
        predictor,
    )

    (
        selected_base,
        source_payloads,
    ) = _source_payloads(
        q_blocks,
        base_residual_codec,
    )

    huffman_payloads = [encode_huffman_sparse(payload) for payload in source_payloads]

    deflate_payloads = [encode_deflate_raw(payload) for payload in source_payloads]

    if [
        decode_huffman_sparse(payload) for payload in huffman_payloads
    ] != source_payloads:
        raise ValueError("Huffman roundtrip mismatch")

    if [decode_deflate_raw(payload) for payload in deflate_payloads] != source_payloads:
        raise ValueError("DEFLATE roundtrip mismatch")

    source_sizes = [len(payload) for payload in source_payloads]

    huffman_sizes = [len(payload) for payload in huffman_payloads]

    deflate_sizes = [len(payload) for payload in deflate_payloads]

    source_total = sum(source_sizes)

    huffman_forced = sum(huffman_sizes)

    deflate_forced = sum(deflate_sizes)

    huffman_gross = sum(
        min(source, candidate)
        for source, candidate in zip(
            source_sizes,
            huffman_sizes,
        )
    )

    deflate_gross = sum(
        min(source, candidate)
        for source, candidate in zip(
            source_sizes,
            deflate_sizes,
        )
    )

    selector_bytes = SELECTOR_BYTES_PER_BLOCK * len(source_payloads)

    huffman_selective = huffman_gross + selector_bytes

    deflate_selective = deflate_gross + selector_bytes

    current_total = _current_v2_size(
        values,
        predictor,
        base_residual_codec,
    )

    block_rows: list[dict[str, object]] = []

    for index, (
        segment,
        source,
        huffman,
        deflate,
    ) in enumerate(
        zip(
            segments,
            source_payloads,
            huffman_payloads,
            deflate_payloads,
        )
    ):
        (
            _original_length,
            bit_length,
            symbol_count,
        ) = HUFFMAN_FIXED_HEADER.unpack_from(
            huffman,
            0,
        )

        huffman_bitstream_bytes = (bit_length + 7) // 8

        huffman_codebook_bytes = 2 * symbol_count

        deflate_stream_bytes = len(deflate) - DEFLATE_FIXED_HEADER.size

        block_rows.append(
            {
                "evidence_group": evidence_group,
                "dataset": dataset.name,
                "predictor": predictor,
                "base_residual_codec": (selected_base),
                "segment_index": index,
                "segment_length": (segment.end_idx - segment.start_idx + 1),
                "source_payload_bytes": (len(source)),
                "source_symbol_count": (len(set(source))),
                "source_byte_entropy_bits_per_symbol": (byte_entropy(source)),
                "huffman_bitstream_bytes": (huffman_bitstream_bytes),
                "huffman_codebook_bytes": (huffman_codebook_bytes),
                "huffman_total_bytes": (len(huffman)),
                "huffman_delta_bytes": (len(huffman) - len(source)),
                "deflate_stream_bytes": (deflate_stream_bytes),
                "deflate_total_bytes": (len(deflate)),
                "deflate_delta_bytes": (len(deflate) - len(source)),
            }
        )

    result = {
        "evidence_group": evidence_group,
        "dataset": dataset.name,
        "predictor": predictor,
        "base_residual_codec": selected_base,
        "n_samples": len(values),
        "block_count": len(source_payloads),
        "source_payload_bytes": source_total,
        "current_v2_total_bytes": current_total,
        "huffman_forced_bytes": huffman_forced,
        "huffman_forced_delta": (huffman_forced - source_total),
        "huffman_win_blocks": sum(
            candidate < source
            for source, candidate in zip(
                source_sizes,
                huffman_sizes,
            )
        ),
        "huffman_tie_blocks": sum(
            candidate == source
            for source, candidate in zip(
                source_sizes,
                huffman_sizes,
            )
        ),
        "huffman_loss_blocks": sum(
            candidate > source
            for source, candidate in zip(
                source_sizes,
                huffman_sizes,
            )
        ),
        "huffman_selective_gross_bytes": (huffman_gross),
        "huffman_selector_bytes": (selector_bytes),
        "huffman_selective_bytes": (huffman_selective),
        "huffman_selective_delta": (huffman_selective - source_total),
        "huffman_projected_total_bytes": (
            current_total - source_total + huffman_selective
        ),
        "huffman_projected_total_delta": (huffman_selective - source_total),
        "deflate_forced_bytes": (deflate_forced),
        "deflate_forced_delta": (deflate_forced - source_total),
        "deflate_win_blocks": sum(
            candidate < source
            for source, candidate in zip(
                source_sizes,
                deflate_sizes,
            )
        ),
        "deflate_tie_blocks": sum(
            candidate == source
            for source, candidate in zip(
                source_sizes,
                deflate_sizes,
            )
        ),
        "deflate_loss_blocks": sum(
            candidate > source
            for source, candidate in zip(
                source_sizes,
                deflate_sizes,
            )
        ),
        "deflate_selective_gross_bytes": (deflate_gross),
        "deflate_selector_bytes": (selector_bytes),
        "deflate_selective_bytes": (deflate_selective),
        "deflate_selective_delta": (deflate_selective - source_total),
        "deflate_projected_total_bytes": (
            current_total - source_total + deflate_selective
        ),
        "deflate_projected_total_delta": (deflate_selective - source_total),
        "huffman_encode_median_ms": "",
        "huffman_decode_median_ms": "",
        "deflate_encode_median_ms": "",
        "deflate_decode_median_ms": "",
    }

    if predictor == "auto":
        result["huffman_encode_median_ms"] = median_runtime_ms(
            lambda: [encode_huffman_sparse(payload) for payload in source_payloads]
        )

        result["huffman_decode_median_ms"] = median_runtime_ms(
            lambda: [decode_huffman_sparse(payload) for payload in huffman_payloads]
        )

        result["deflate_encode_median_ms"] = median_runtime_ms(
            lambda: [encode_deflate_raw(payload) for payload in source_payloads]
        )

        result["deflate_decode_median_ms"] = median_runtime_ms(
            lambda: [decode_deflate_raw(payload) for payload in deflate_payloads]
        )

    return result, block_rows


def bucket_name(
    size: int,
) -> str:
    if size <= 16:
        return "1..16"
    if size <= 32:
        return "17..32"
    if size <= 64:
        return "33..64"
    if size <= 128:
        return "65..128"
    return ">128"


def percentile_nearest_rank(
    values: list[int],
    percentile: float,
) -> int:
    if not values:
        return 0

    ordered = sorted(values)
    rank = max(
        1,
        math.ceil(percentile * len(ordered)),
    )

    return ordered[rank - 1]


def summarize_buckets(
    block_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []

    for candidate, delta_field in (
        (
            "huffman_sparse",
            "huffman_delta_bytes",
        ),
        (
            "deflate_raw",
            "deflate_delta_bytes",
        ),
    ):
        grouped: dict[
            str,
            list[int],
        ] = {}

        for row in block_rows:
            bucket = bucket_name(int(row["source_payload_bytes"]))

            grouped.setdefault(
                bucket,
                [],
            ).append(int(row[delta_field]))

        for bucket in (
            "1..16",
            "17..32",
            "33..64",
            "65..128",
            ">128",
        ):
            deltas = grouped.get(
                bucket,
                [],
            )

            if not deltas:
                continue

            wins = sum(delta < 0 for delta in deltas)

            output.append(
                {
                    "candidate": candidate,
                    "bucket": bucket,
                    "block_count": len(deltas),
                    "win_blocks": wins,
                    "win_fraction": (wins / len(deltas)),
                    "median_delta_bytes": (statistics.median(deltas)),
                    "p95_delta_bytes": (
                        percentile_nearest_rank(
                            deltas,
                            0.95,
                        )
                    ),
                    "worst_delta_bytes": (max(deltas)),
                }
            )

    return output


def write_csv(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, object]],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--matrix",
        type=Path,
        default=Path("docs/residual-distribution-matrix.tsv"),
    )

    parser.add_argument(
        "--results",
        type=Path,
        default=Path("/tmp/lasagna-v2-issue9-entropy-results.csv"),
    )

    parser.add_argument(
        "--blocks",
        type=Path,
        default=Path("/tmp/lasagna-v2-issue9-entropy-blocks.csv"),
    )

    parser.add_argument(
        "--buckets",
        type=Path,
        default=Path("/tmp/lasagna-v2-issue9-entropy-buckets.csv"),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    matrix = residuals.load_matrix(args.matrix)

    results: list[dict[str, object]] = []

    blocks: list[dict[str, object]] = []

    total_cases = len(matrix) * 2

    case_index = 0

    for row in matrix:
        for base_codec in (
            "varint",
            "auto",
        ):
            case_index += 1

            result, case_blocks = evaluate_stream(
                row.evidence_group,
                row.dataset,
                row.predictor,
                base_codec,
            )

            results.append(result)
            blocks.extend(case_blocks)

            print(
                f"CASE={case_index}/{total_cases} "
                f"DATASET={result['dataset']} "
                f"PREDICTOR={result['predictor']} "
                f"CONTROL={base_codec} "
                f"BASE_SELECTED="
                f"{result['base_residual_codec']} "
                f"SOURCE={result['source_payload_bytes']} "
                f"HUFFMAN_FORCED_DELTA="
                f"{result['huffman_forced_delta']} "
                f"HUFFMAN_SELECTIVE_DELTA="
                f"{result['huffman_selective_delta']} "
                f"DEFLATE_FORCED_DELTA="
                f"{result['deflate_forced_delta']} "
                f"DEFLATE_SELECTIVE_DELTA="
                f"{result['deflate_selective_delta']}"
            )

    buckets = summarize_buckets(blocks)

    write_csv(
        args.results,
        RESULT_FIELDS,
        results,
    )

    write_csv(
        args.blocks,
        BLOCK_FIELDS,
        blocks,
    )

    write_csv(
        args.buckets,
        BUCKET_FIELDS,
        buckets,
    )

    print(f"RESULT_ROWS={len(results)}")
    print(f"BLOCK_ROWS={len(blocks)}")
    print(f"BUCKET_ROWS={len(buckets)}")
    print(f"RESULTS={args.results}")
    print(f"BLOCKS={args.blocks}")
    print(f"BUCKETS={args.buckets}")
    print("ENTROPY_BENCHMARK_GATE=PASS")


if __name__ == "__main__":
    main()
