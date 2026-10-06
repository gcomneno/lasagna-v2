#!/usr/bin/env python3
"""Deterministic adversarial qualification harness for Lasagna decoders."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import struct
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from lasagna2 import core

DEFAULT_SEED = 20261006
DEFAULT_ITERATIONS = 25_000
MAX_DIRECT_PAYLOAD = 256
MAX_DIRECT_LENGTH = 256

CORPUS_DIR = Path("tests/fuzz_corpus")


@dataclass(frozen=True)
class CorpusCase:
    name: str
    data: bytes


@dataclass
class TargetStats:
    cases: int = 0
    accepted: int = 0
    rejected: int = 0
    crashes: int = 0


class UnexpectedCrash(RuntimeError):
    def __init__(
        self,
        *,
        target: str,
        iteration: int,
        seed: int,
        payload: bytes,
        exc: BaseException,
    ) -> None:
        self.target = target
        self.iteration = iteration
        self.seed = seed
        self.payload = payload
        self.exc = exc

        super().__init__(
            f"{target} iteration={iteration} seed={seed}: "
            f"{type(exc).__name__}: {exc}"
        )


def build_seed_corpus() -> list[CorpusCase]:
    values = [
        1.0,
        1.1,
        1.2,
        4.0,
        4.0,
        4.0,
        2.5,
        2.6,
        2.7,
        2.8,
        8.0,
        8.0,
        8.0,
        3.0,
        3.1,
        3.2,
    ]

    ts = core.TimeSeries(
        values=values,
        dt=1.0,
        t0="2026-10-06T00:00:00Z",
        unit="fuzz-seed",
    )

    return [
        CorpusCase(
            "v1-raw.lsg2",
            core.encode_timeseries_v1(
                ts,
                segment_length=4,
                predictor="mean",
                residual_coding="raw",
            ),
        ),
        CorpusCase(
            "v1-varint.lsg2",
            core.encode_timeseries_v1(
                ts,
                segment_length=4,
                predictor="linear",
                residual_coding="varint",
            ),
        ),
        CorpusCase(
            "v2-raw.lsg2",
            core.encode_timeseries_v2(
                ts,
                segment_length=4,
                predictor="mean",
                residual_coding="raw",
            ),
        ),
        CorpusCase(
            "v2-varint.lsg2",
            core.encode_timeseries_v2(
                ts,
                segment_length=4,
                predictor="linear",
                residual_coding="varint",
            ),
        ),
        CorpusCase(
            "v2-zero-run.lsg2",
            core.encode_timeseries_v2(
                ts,
                segment_length=4,
                predictor="rw",
                residual_coding="zero-run",
            ),
        ),
    ]


def write_seed_corpus(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)

    expected = {case.name for case in build_seed_corpus()}

    for existing in directory.glob("*.lsg2"):
        if existing.name not in expected:
            existing.unlink()

    for case in build_seed_corpus():
        (directory / case.name).write_bytes(case.data)


def load_seed_corpus(directory: Path) -> list[CorpusCase]:
    cases = [
        CorpusCase(path.name, path.read_bytes())
        for path in sorted(directory.glob("*.lsg2"))
    ]

    if not cases:
        raise ValueError(f"No .lsg2 corpus files found in {directory}")

    return cases


def _header_layout(data: bytes) -> tuple[int, int, int]:
    (
        _magic,
        version,
        _flags,
        header_len,
        _n_points,
        n_segments,
        _r1,
        _r2,
    ) = core.FILE_HEADER_STRUCT.unpack_from(data, 0)

    segment_size = (
        core.SEGMENT_ENTRY_STRUCT.size
        if version == core.FORMAT_VERSION_V1
        else core.SEGMENT_ENTRY_V2_STRUCT.size
    )

    segment_offset = core.FILE_HEADER_STRUCT.size + header_len
    residual_offset = segment_offset + n_segments * segment_size

    return segment_offset, segment_size, residual_offset


def structured_mutations(data: bytes) -> list[tuple[str, bytes]]:
    """Return deterministic wire-aware mutations for one valid stream."""
    mutations: list[tuple[str, bytes]] = []

    if len(data) < core.FILE_HEADER_STRUCT.size:
        return mutations

    # Truncation boundaries.
    for size in (
        0,
        1,
        core.FILE_HEADER_STRUCT.size - 1,
        core.FILE_HEADER_STRUCT.size,
        max(0, len(data) - 1),
    ):
        mutations.append((f"truncate-{size}", data[:size]))

    header = list(core.FILE_HEADER_STRUCT.unpack_from(data, 0))

    def header_variant(name: str, index: int, value) -> None:
        mutated = bytearray(data)
        fields = list(header)
        fields[index] = value
        core.FILE_HEADER_STRUCT.pack_into(mutated, 0, *fields)
        mutations.append((name, bytes(mutated)))

    header_variant("bad-magic", 0, b"NOPE")
    header_variant("unknown-version", 1, 0xFFFF)
    header_variant(
        "context-over-limit",
        3,
        core.MAX_CONTEXT_BYTES + 1,
    )
    header_variant(
        "points-over-limit",
        4,
        core.MAX_POINTS + 1,
    )
    header_variant(
        "segments-over-limit",
        5,
        core.MAX_SEGMENTS + 1,
    )
    header_variant("zero-points", 4, 0)

    try:
        segment_offset, segment_size, residual_offset = _header_layout(data)
    except (ValueError, struct.error):
        return mutations

    # Context mutations.
    context_start = core.FILE_HEADER_STRUCT.size
    context_end = segment_offset

    if context_end > context_start:
        mutated = bytearray(data)
        mutated[context_start] = 0xFF
        mutations.append(("context-invalid-utf8", bytes(mutated)))

        mutated = bytearray(data)
        mutated[context_start:context_end] = (
            b"[" * min(core.MAX_CONTEXT_DEPTH + 1, context_end - context_start)
        ).ljust(context_end - context_start, b" ")
        mutations.append(("context-deep-json", bytes(mutated)))

        malformed_contexts = (
            ("context-root-array", b"[]"),
            ("context-root-null", b"null"),
            ("context-sampling-array", b'{"sampling":[]}'),
            ("context-dt-array", b'{"sampling":{"dt":[]}}'),
            ("context-dt-null", b'{"sampling":{"dt":null}}'),
            (
                "context-dt-huge-integer",
                b'{"sampling":{"dt":' + b"9" * 1000 + b"}}",
            ),
        )

        for name, replacement in malformed_contexts:
            header = list(
                core.FILE_HEADER_STRUCT.unpack_from(
                    data,
                    0,
                )
            )

            old_context_len = int(header[3])
            old_context_end = core.FILE_HEADER_STRUCT.size + old_context_len

            header[3] = len(replacement)

            mutated = (
                core.FILE_HEADER_STRUCT.pack(*header)
                + replacement
                + data[old_context_end:]
            )

            mutations.append(
                (
                    name,
                    mutated,
                )
            )

    # Segment table mutations.
    if residual_offset >= segment_offset + segment_size:
        mutated = bytearray(data)
        struct.pack_into(
            "<I",
            mutated,
            segment_offset,
            core.UINT32_MAX,
        )
        mutations.append(("segment-start-max", bytes(mutated)))

        mutated = bytearray(data)
        struct.pack_into(
            "<I",
            mutated,
            segment_offset + 4,
            core.UINT32_MAX,
        )
        mutations.append(("segment-end-max", bytes(mutated)))

        mutated = bytearray(data)
        struct.pack_into(
            "<I",
            mutated,
            segment_offset + 8,
            core.UINT32_MAX,
        )
        mutations.append(("segment-predictor-max", bytes(mutated)))

    # Residual section / first block mutations.
    block_offset = residual_offset + core.RESIDUAL_SECTION_HEADER_STRUCT.size

    if len(data) >= block_offset + core.RESIDUAL_BLOCK_HEADER_STRUCT.size:
        mutated = bytearray(data)
        struct.pack_into(
            "<I",
            mutated,
            residual_offset,
            core.UINT32_MAX,
        )
        mutations.append(("residual-codec-max", bytes(mutated)))

        for field_name, field_offset, value in (
            ("block-segid-max", 0, core.UINT32_MAX),
            ("block-seglen-max", 4, core.UINT32_MAX),
            (
                "block-bytelen-over-limit",
                8,
                core.MAX_RESIDUAL_BLOCK_BYTES + 1,
            ),
        ):
            mutated = bytearray(data)
            struct.pack_into(
                "<I",
                mutated,
                block_offset + field_offset,
                value,
            )
            mutations.append((field_name, bytes(mutated)))

        payload_offset = block_offset + core.RESIDUAL_BLOCK_HEADER_STRUCT.size

        if payload_offset < len(data):
            mutated = bytearray(data)
            mutated[payload_offset] ^= 0x80
            mutations.append(("payload-high-bit-flip", bytes(mutated)))

            mutated = bytearray(data)
            mutated[-1] ^= 0xFF
            mutations.append(("payload-tail-flip", bytes(mutated)))

    return mutations


def random_mutation(
    rng: random.Random,
    corpus: list[CorpusCase],
) -> tuple[str, bytes]:
    case = corpus[rng.randrange(len(corpus))]
    base = case.data
    structured = structured_mutations(base)

    mode = rng.randrange(5)

    if mode == 0 and structured:
        name, mutated = structured[rng.randrange(len(structured))]
        return f"{case.name}:{name}", mutated

    if mode == 1:
        cut = rng.randrange(len(base) + 1)
        return f"{case.name}:random-truncate-{cut}", base[:cut]

    if mode == 2:
        mutated = bytearray(base)

        # Avoid randomizing the n_points/n_segments uint32 fields: arbitrary
        # in-policy values can deliberately request multi-million-element
        # allocations. Those fields are fuzzed structurally with over-limit
        # values instead.
        protected = set(range(12, 20))
        positions = [index for index in range(len(mutated)) if index not in protected]

        if positions:
            position = positions[rng.randrange(len(positions))]
            mutated[position] ^= 1 << rng.randrange(8)

        return f"{case.name}:bit-flip", bytes(mutated)

    if mode == 3:
        mutated = bytearray(base)
        if mutated:
            position = rng.randrange(len(mutated))
            mutated[position] = rng.randrange(256)
        return f"{case.name}:byte-replace", bytes(mutated)

    suffix_length = rng.randrange(1, 33)
    suffix = bytes(rng.randrange(256) for _ in range(suffix_length))
    return f"{case.name}:trailing-bytes", base + suffix


def _run_decoder_case(
    *,
    payload: bytes,
    target: str,
    iteration: int,
    seed: int,
    stats: TargetStats,
) -> None:
    stats.cases += 1

    try:
        core.decode_timeseries(payload)
    except ValueError:
        stats.rejected += 1
    except Exception as exc:
        stats.crashes += 1
        raise UnexpectedCrash(
            target=target,
            iteration=iteration,
            seed=seed,
            payload=payload,
            exc=exc,
        ) from exc
    else:
        stats.accepted += 1


def run_decoder_target(
    *,
    rng: random.Random,
    corpus: list[CorpusCase],
    iterations: int,
    seed: int,
) -> TargetStats:
    stats = TargetStats()

    # Every named structured mutation is always exercised once.
    iteration = 0
    for case in corpus:
        for mutation_name, payload in structured_mutations(case.data):
            _run_decoder_case(
                payload=payload,
                target=f"decoder:{case.name}:{mutation_name}",
                iteration=iteration,
                seed=seed,
                stats=stats,
            )
            iteration += 1

    while iteration < iterations:
        mutation_name, payload = random_mutation(rng, corpus)
        _run_decoder_case(
            payload=payload,
            target=f"decoder:{mutation_name}",
            iteration=iteration,
            seed=seed,
            stats=stats,
        )
        iteration += 1

    return stats


def _bounded_direct_parameters(data: bytes) -> tuple[bytes, int]:
    payload = data[:MAX_DIRECT_PAYLOAD]

    if not payload:
        return payload, 0

    length_seed = int.from_bytes(
        payload[: min(4, len(payload))],
        "little",
    )

    return payload, length_seed % (MAX_DIRECT_LENGTH + 1)


def run_residual_target(
    *,
    rng: random.Random,
    iterations: int,
    seed: int,
    name: str,
    decoder: Callable[[bytes, int], list[int]],
) -> TargetStats:
    stats = TargetStats()

    deterministic = [
        b"",
        b"\x00",
        b"\x80",
        b"\x80" * core.MAX_VARINT_BYTES,
        b"\x80" * (core.MAX_VARINT_BYTES + 1),
        b"\xff" * core.MAX_VARINT_BYTES,
        core._encode_varint(0),
        core._encode_varint(1),
        core._encode_varint(127),
        core._encode_varint(128),
    ]

    iteration = 0

    while iteration < iterations:
        if iteration < len(deterministic):
            data = deterministic[iteration]
        else:
            size = rng.randrange(MAX_DIRECT_PAYLOAD + 1)
            data = bytes(rng.randrange(256) for _ in range(size))

        payload, length = _bounded_direct_parameters(data)
        stats.cases += 1

        try:
            decoder(payload, length)
        except ValueError:
            stats.rejected += 1
        except Exception as exc:
            stats.crashes += 1
            raise UnexpectedCrash(
                target=name,
                iteration=iteration,
                seed=seed,
                payload=payload,
                exc=exc,
            ) from exc
        else:
            stats.accepted += 1

        iteration += 1

    return stats


def write_crash_artifact(
    directory: Path,
    crash: UnexpectedCrash,
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)

    digest = hashlib.sha256(crash.payload).hexdigest()
    stem = (
        f"{crash.target.replace('/', '_').replace(':', '_')}"
        f"-seed-{crash.seed}"
        f"-iter-{crash.iteration}"
        f"-{digest[:16]}"
    )

    payload_path = directory / f"{stem}.bin"
    metadata_path = directory / f"{stem}.json"

    payload_path.write_bytes(crash.payload)
    metadata_path.write_text(
        json.dumps(
            {
                "target": crash.target,
                "iteration": crash.iteration,
                "seed": crash.seed,
                "sha256": digest,
                "exception_type": type(crash.exc).__name__,
                "exception": str(crash.exc),
                "payload_file": payload_path.name,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return metadata_path


def replay_payload(
    *,
    target: str,
    payload: bytes,
) -> None:
    if target.startswith("decoder"):
        core.decode_timeseries(payload)
        return

    _, length = _bounded_direct_parameters(payload)

    if target == "residual-varint":
        core.decode_int_list_varint(payload, length)
        return

    if target == "residual-zero-run":
        core.decode_int_list_zero_run_varint(payload, length)
        return

    raise ValueError(f"Unknown replay target: {target}")


def _stats_dict(stats: TargetStats) -> dict[str, int]:
    return {
        "cases": stats.cases,
        "accepted": stats.accepted,
        "rejected": stats.rejected,
        "crashes": stats.crashes,
    }


def run_campaign(
    *,
    corpus_dir: Path,
    iterations: int,
    seed: int,
    crash_dir: Path,
) -> dict[str, object]:
    corpus = load_seed_corpus(corpus_dir)

    started = time.perf_counter()

    decoder_stats = run_decoder_target(
        rng=random.Random(seed),
        corpus=corpus,
        iterations=iterations,
        seed=seed,
    )

    varint_stats = run_residual_target(
        rng=random.Random(seed ^ 0xA51C),
        iterations=iterations,
        seed=seed,
        name="residual-varint",
        decoder=core.decode_int_list_varint,
    )

    zero_run_stats = run_residual_target(
        rng=random.Random(seed ^ 0xBEEF),
        iterations=iterations,
        seed=seed,
        name="residual-zero-run",
        decoder=core.decode_int_list_zero_run_varint,
    )

    elapsed = time.perf_counter() - started

    result = {
        "schema_version": 1,
        "seed": seed,
        "iterations_per_target": iterations,
        "corpus_files": [case.name for case in corpus],
        "targets": {
            "decoder": _stats_dict(decoder_stats),
            "residual-varint": _stats_dict(varint_stats),
            "residual-zero-run": _stats_dict(zero_run_stats),
        },
        "total_cases": (
            decoder_stats.cases + varint_stats.cases + zero_run_stats.cases
        ),
        "total_crashes": (
            decoder_stats.crashes + varint_stats.crashes + zero_run_stats.crashes
        ),
        "elapsed_seconds": round(elapsed, 6),
        "crash_directory": str(crash_dir),
    }

    return result


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run deterministic Lasagna fuzz qualification",
    )

    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help="cases per fuzz target",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="deterministic RNG seed",
    )
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=CORPUS_DIR,
    )
    parser.add_argument(
        "--crash-dir",
        type=Path,
        default=Path("artifacts/fuzz-crashes"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="optional JSON result path",
    )
    parser.add_argument(
        "--write-corpus",
        action="store_true",
        help="write canonical seed corpus and exit",
    )
    parser.add_argument(
        "--replay",
        type=Path,
        default=None,
        help="replay one crash payload",
    )
    parser.add_argument(
        "--target",
        type=str,
        default="decoder",
        help="target used with --replay",
    )

    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)

    if args.iterations <= 0:
        raise ValueError("--iterations must be > 0")

    if args.write_corpus:
        write_seed_corpus(args.corpus_dir)
        print(f"FUZZ_CORPUS_WRITE_GATE=PASS files={len(build_seed_corpus())}")
        return 0

    if args.replay is not None:
        replay_payload(
            target=args.target,
            payload=args.replay.read_bytes(),
        )
        print("FUZZ_REPLAY_GATE=PASS")
        return 0

    try:
        result = run_campaign(
            corpus_dir=args.corpus_dir,
            iterations=args.iterations,
            seed=args.seed,
            crash_dir=args.crash_dir,
        )
    except UnexpectedCrash as crash:
        artifact = write_crash_artifact(
            args.crash_dir,
            crash,
        )
        print(f"FUZZ_CRASH_GATE=FAIL artifact={artifact}")
        print(str(crash), file=sys.stderr)
        return 1

    rendered = json.dumps(
        result,
        indent=2,
        sort_keys=True,
    )

    print(rendered)

    if args.report is not None:
        args.report.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        args.report.write_text(
            rendered + "\n",
            encoding="utf-8",
        )

    if result["total_crashes"] != 0:
        return 1

    print("FUZZ_QUALIFICATION_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
