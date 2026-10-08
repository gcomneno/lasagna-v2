"""Issue #26 wire validation. Default mode runs only small pre-corpus tests.

Corpus execution requires --mode corpus. Rendering persisted evidence with
--mode render never encodes, decodes, or measures a dataset. Timing is separate
from the byte-level equivalence oracle and has no semantic tolerance.
Report-only recovery with --mode recover reads saved CSV evidence and original
provenance, and runs only the small canonical public compatibility fixtures.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import shlex
import statistics
import struct
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / "tools"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import analyze_segment_byte_anatomy as projection25  # noqa: E402
import benchmark_local_model_value as frozen24  # noqa: E402
from benchmark_codec import (  # noqa: E402
    _measure_deterministic_encode,
    _median_call_ms,
    canonical_float64_bytes,
    load_csv_values,
)

from lasagna2 import core  # noqa: E402
from lasagna2 import experimental_compact as compact  # noqa: E402

INTERNAL_DATASETS = frozen24.INTERNAL_DATASETS
EXTERNAL_DATASETS = frozen24.EXTERNAL_DATASETS
ARCHITECTURES = frozen24.ARCHITECTURES
C_Q_VALUES = frozen24.C_Q_VALUES
Q_MIN = frozen24.Q_MIN
EXPECTED_POINTS = 385  # Independent frozen cardinality: 11 * 7 * 5.
WARMUP = 1
REPETITIONS = 3
PROTOCOL_PATH = ROOT / "docs/compact-wire-layout-protocol.md"
PROJECTION_PROTOCOL_PATH = ROOT / "docs/segment-byte-anatomy-protocol.md"

SEMANTIC_FIELDS = (
    "context_bytes_equal",
    "sample_count_equal",
    "segment_count_equal",
    "segment_boundaries_equal",
    "predictor_types_equal",
    "q_binary32_equal",
    "predictor_parameters_binary32_equal",
    "coding_type_equal",
    "residual_int32_equal",
    "residual_payload_equal",
    "reconstruction_binary64_equal",
    "compact_decode_success",
)
BOOLEAN_FIELDS = (
    *SEMANTIC_FIELDS,
    "compact_accounting_equal",
    "projection25_equal",
    "baseline24_equal",
    "frozen_projection25_equal",
    "compact_timing_deterministic",
)
PUBLIC_COMPATIBILITY_FIELDS = (
    "v1_fixture_byte_identical",
    "v2_fixture_byte_identical",
    "public_default_v2",
    "public_decoder_rejects_v3",
)
EQUIVALENCE_FIELDS = (
    "point_id",
    *BOOLEAN_FIELDS,
    "v2_stream_sha256",
    "compact_stream_sha256",
    "v2_reconstruction_sha256",
    "compact_reconstruction_sha256",
    "compact_decode_error",
    "compact_timing_error",
)
RESULT_FIELDS = (
    "point_id",
    "dataset",
    "evidence_group",
    "architecture",
    "architecture_name",
    "C_Q",
    "Q_MIN",
    "n_samples",
    "v2_encoded_bytes",
    "compact_encoded_bytes",
    "projected_encoded_bytes",
    "compact_structural_bytes",
    "compact_residual_payload_bytes",
    "compact_structural_fraction",
    "v2_structural_fraction",
    "total_byte_reduction",
    "total_reduction_fraction",
    "segment_count",
    "mean_segment_length",
    "min_segment_length",
    "max_segment_length",
    "mean_predictor_segments",
    "linear_predictor_segments",
    "rw_predictor_segments",
    "global_and_context_bytes",
    "v2_structural_bytes",
    "v2_residual_payload_bytes",
    "encode_time_ms",
    "decode_time_ms",
)
SUMMARY_FIELDS = (
    "dataset",
    "evidence_group",
    "architecture",
    "point_count",
    "median_total_byte_reduction",
    "median_total_reduction_fraction",
    "min_total_reduction_fraction",
    "max_total_reduction_fraction",
    "median_compact_structural_fraction",
    "median_v2_structural_fraction",
)
# CSV types are explicit: integer counts/bytes never pass through float.
RESULT_TEXT_FIELDS = (
    "point_id",
    "dataset",
    "evidence_group",
    "architecture",
    "architecture_name",
)
RESULT_FLOAT_FIELDS = (
    "C_Q",
    "Q_MIN",
    "compact_structural_fraction",
    "v2_structural_fraction",
    "total_reduction_fraction",
    "mean_segment_length",
    "encode_time_ms",
    "decode_time_ms",
)
OPTIONAL_TIMING_FIELDS = ("encode_time_ms", "decode_time_ms")
RESULT_INTEGER_FIELDS = tuple(
    f for f in RESULT_FIELDS if f not in (*RESULT_TEXT_FIELDS, *RESULT_FLOAT_FIELDS)
)
SUMMARY_INTEGER_FIELDS = ("point_count", "median_total_byte_reduction")
SUMMARY_FLOAT_FIELDS = SUMMARY_FIELDS[5:]


@dataclass(frozen=True)
class Artifacts:
    results: Path = ROOT / "docs/compact-wire-results.csv"
    summary: Path = ROOT / "docs/compact-wire-summary.csv"
    equivalence: Path = ROOT / "docs/compact-wire-equivalence.csv"
    provenance: Path = ROOT / "docs/compact-wire-provenance.json"
    report: Path = ROOT / "docs/compact-wire-report.json"
    study: Path = ROOT / "docs/compact-wire-study.md"

    def validate(self) -> None:
        defaults = Artifacts()
        resolved = []
        for field, path in asdict(self).items():
            # Custom directories are supported; artifact names remain #26-only.
            if path.name != getattr(defaults, field).name or path.is_symlink():
                raise ValueError(f"Unsafe #26 artifact path: {path}")
            resolved.append(path.resolve())
        if len(set(resolved)) != len(resolved):
            raise ValueError("Artifact paths must be distinct")


def corpus_order() -> tuple[tuple[str, Path], ...]:
    return tuple(("internal", p) for p in INTERNAL_DATASETS) + tuple(
        ("external", p) for p in EXTERNAL_DATASETS
    )


def execution_order() -> list[dict[str, object]]:
    points = [
        {
            "dataset": path.name,
            "dataset_path": path.as_posix(),
            "evidence_group": group,
            "architecture": architecture.architecture,
            "C_Q": c_q,
            "point_id": frozen24.point_id(path.name, architecture.architecture, c_q),
            "operations": [
                "canonical_v2_encode",
                "compact_encode",
                "untimed_equivalence",
                "compact_encode_warmup",
                "compact_encode_timed",
                "compact_decode_warmup",
                "compact_decode_timed",
            ],
        }
        for group, path in corpus_order()
        for c_q in C_Q_VALUES
        for architecture in ARCHITECTURES
    ]
    if (
        len(INTERNAL_DATASETS) != 3
        or len(EXTERNAL_DATASETS) != 8
        or len(C_Q_VALUES) != 7
        or [a.architecture for a in ARCHITECTURES] != ["A0", "A1", "A2", "A3", "A4"]
        or len(points) != EXPECTED_POINTS
        or len({p["point_id"] for p in points}) != EXPECTED_POINTS
    ):
        raise ValueError("Frozen matrix must contain exactly 11 * 7 * 5 = 385 points")
    return points


@dataclass(frozen=True)
class WireSegment:
    start: int
    end: int
    predictor: int
    q_bits: bytes
    parameter_bits: tuple[bytes, ...]
    payload: bytes
    residuals: tuple[int, ...]


@dataclass(frozen=True)
class Wire:
    context: bytes
    n_samples: int
    coding: int
    segments: tuple[WireSegment, ...]


def read_residuals(payload: bytes, coding: int, count: int) -> tuple[int, ...]:
    """Independent bounded signed-int32 oracle for all three frozen codecs."""
    if coding == 0:
        if len(payload) != 4 * count:
            raise ValueError("RAW_INT32 length mismatch")
        return struct.unpack(f"<{count}i", payload)
    if coding not in (1, 2) or len(payload) > 10 * count:
        raise ValueError("Invalid residual coding or payload bound")
    cursor = 0

    def token() -> int:
        nonlocal cursor
        value = 0
        for index in range(10):
            if cursor == len(payload):
                raise ValueError("Truncated residual token")
            byte = payload[cursor]
            cursor += 1
            value |= (byte & 127) << (7 * index)
            if not byte & 128:
                return value
        raise ValueError("Oversized residual token")

    values = []
    while cursor < len(payload):
        unsigned = token()
        if coding == 2 and unsigned == 0:
            run = token()
            if not 3 <= run <= count - len(values):
                raise ValueError("Invalid zero run")
            values.extend([0] * run)
        else:
            if coding == 2:
                unsigned -= 1
            value = (unsigned >> 1) ^ -(unsigned & 1)
            if not -(2**31) <= value < 2**31:
                raise ValueError("Residual outside signed int32")
            values.append(value)
        if len(values) > count:
            raise ValueError("Extra residuals")
    if len(values) != count:
        raise ValueError("Residual count mismatch")
    return tuple(values)


def read_wire(data: bytes, version: int) -> Wire:
    """Read literal frozen grammar; never use the prototype's parsing helpers."""
    cursor = 0

    def take(size: int) -> bytes:
        nonlocal cursor
        if size < 0 or cursor + size > len(data):
            raise ValueError("Truncated wire evidence")
        value = data[cursor : cursor + size]
        cursor += size
        return value

    magic, actual, flags, context_len, points, count, r1, r2 = struct.unpack(
        "<4sHHIIIII", take(28)
    )
    if (magic, actual, flags, r1, r2) != (b"LSG2", version, 0, 0, 0):
        raise ValueError("Unexpected wire envelope")
    if version not in (2, 3) or points > 10_000_000 or count > 1_000_000:
        raise ValueError("Invalid version or resource declaration")
    if (points == 0) != (count == 0) or count > points:
        raise ValueError("Invalid point/segment declaration")
    context = take(context_len)
    records = [take(32) for _ in range(count)] if version == 2 else []
    coding, *reserved = struct.unpack("<IIII", take(16))
    if coding not in (0, 1, 2) or any(reserved):
        raise ValueError("Unexpected coding header")
    segments = []
    start = 0
    for index in range(count):
        if version == 2:
            record = records[index]
            actual_start, end, tag = struct.unpack_from("<III", record)
            if actual_start != start or end < start:
                raise ValueError("Non-contiguous V2 topology")
            length = end - start + 1
            if tag not in (0, 1, 2):
                raise ValueError("Unknown predictor")
            q_bits = record[24:28]
            offsets = {0: (12,), 1: (16, 20), 2: (28,)}[tag]
            parameters = tuple(record[o : o + 4] for o in offsets)
            seg_id, seg_len, payload_len = struct.unpack("<III", take(12))
            if (seg_id, seg_len) != (index, length):
                raise ValueError("Residual block topology mismatch")
        else:
            prefix = take(13)
            length, tag, _q, payload_len = struct.unpack("<IBfI", prefix)
            if tag not in (0, 1, 2):
                raise ValueError("Unknown predictor")
            q_bits = prefix[5:9]
            parameters = tuple(take(4) for _ in range(2 if tag == 1 else 1))
        if length <= 0 or length > points - start:
            raise ValueError("Invalid segment coverage")
        payload = take(payload_len)
        segments.append(
            WireSegment(
                start,
                start + length - 1,
                tag,
                q_bits,
                parameters,
                payload,
                read_residuals(payload, coding, length),
            )
        )
        start += length
    if start != points or cursor != len(data):
        raise ValueError("Coverage or EOF mismatch")
    return Wire(context, points, coding, tuple(segments))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def equivalence(v2: bytes, encoded: bytes) -> dict[str, object]:
    baseline, experimental = read_wire(v2, 2), read_wire(encoded, 3)
    left, right = baseline.segments, experimental.segments

    def column(segments: tuple[WireSegment, ...], field: str) -> tuple:
        return tuple(getattr(segment, field) for segment in segments)

    decoded_v2 = canonical_float64_bytes(core.decode_timeseries(v2).values)
    error = ""
    try:
        decoded = compact.decode_timeseries_compact_experimental(encoded)
        decoded_compact = canonical_float64_bytes(decoded.values)
        decode_success = len(decoded.values) == experimental.n_samples
    except (ValueError, TypeError, OverflowError, struct.error) as exc:
        decoded_compact = b""
        decode_success = False
        error = f"{type(exc).__name__}: {exc}"
    counts = [sum(s.predictor == tag for s in right) for tag in (0, 1, 2)]
    expected_bytes = (
        28
        + len(experimental.context)
        + 16
        + 17 * counts[0]
        + 21 * counts[1]
        + 17 * counts[2]
        + sum(len(s.payload) for s in right)
    )
    return {
        "context_bytes_equal": baseline.context == experimental.context,
        "sample_count_equal": baseline.n_samples == experimental.n_samples,
        "segment_count_equal": len(left) == len(right),
        "segment_boundaries_equal": tuple((s.start, s.end) for s in left)
        == tuple((s.start, s.end) for s in right),
        "predictor_types_equal": column(left, "predictor")
        == column(right, "predictor"),
        "q_binary32_equal": column(left, "q_bits") == column(right, "q_bits"),
        "predictor_parameters_binary32_equal": column(left, "parameter_bits")
        == column(right, "parameter_bits"),
        "coding_type_equal": baseline.coding == experimental.coding,
        "residual_int32_equal": column(left, "residuals") == column(right, "residuals"),
        "residual_payload_equal": column(left, "payload") == column(right, "payload"),
        "reconstruction_binary64_equal": decode_success
        and decoded_v2 == decoded_compact,
        "compact_decode_success": decode_success,
        "compact_accounting_equal": len(encoded) == expected_bytes,
        "v2_stream_sha256": sha256_bytes(v2),
        "compact_stream_sha256": sha256_bytes(encoded),
        "v2_reconstruction_sha256": sha256_bytes(decoded_v2),
        "compact_reconstruction_sha256": sha256_bytes(decoded_compact),
        "compact_decode_error": error,
    }


def evaluate_point(point: dict[str, object]) -> tuple[dict, dict]:
    ts = frozen24.make_timeseries(load_csv_values(ROOT / str(point["dataset_path"])))
    architecture = frozen24.architecture_by_id(str(point["architecture"]))
    options = frozen24.architecture_options(architecture, len(ts.values), point["C_Q"])
    v2 = core.encode_timeseries_v2(ts, **options)
    encoded = compact.encode_timeseries_compact_experimental(ts, **options)
    evidence = {"point_id": point["point_id"], **equivalence(v2, encoded)}
    count, mean_length, min_length, max_length, predictors = frozen24.segment_metrics(
        v2
    )
    accounting = frozen24.v2_byte_accounting(v2)
    projection_input = {
        **point,
        "architecture_name": architecture.name,
        "n_samples": len(ts.values),
        "segment_count": count,
        "mean_predictor_segments": predictors[0],
        "linear_predictor_segments": predictors[1],
        "rw_predictor_segments": predictors[2],
        **accounting,
        "encoded_bytes": len(v2),
    }
    projected = projection25._project_row(
        {k: str(v) for k, v in projection_input.items()}
    )
    payload_bytes = sum(len(s.payload) for s in read_wire(encoded, 3).segments)
    structural_bytes = len(encoded) - payload_bytes
    evidence["projection25_equal"] = (
        len(encoded) == projected["projected_encoded_bytes"]
    )
    evidence["compact_timing_deterministic"] = False
    evidence["compact_timing_error"] = ""
    encode_ms = decode_ms = None
    # The oracle runs outside every timed region. Failed semantics are persisted
    # without measuring a stream that already fails qualification.
    if all(
        evidence[f]
        for f in (*SEMANTIC_FIELDS, "compact_accounting_equal", "projection25_equal")
    ):
        try:
            timed, encode_ms = _measure_deterministic_encode(
                lambda: compact.encode_timeseries_compact_experimental(ts, **options),
                warmup=WARMUP,
                repetitions=REPETITIONS,
            )
            if timed != encoded:
                raise ValueError("Compact timed encoding differs from untimed evidence")
            _, decode_ms = _median_call_ms(
                lambda: compact.decode_timeseries_compact_experimental(encoded),
                warmup=WARMUP,
                repetitions=REPETITIONS,
            )
            evidence["compact_timing_deterministic"] = True
        except ValueError as exc:
            # Preserve timing failures independently of the semantic evidence.
            encode_ms = decode_ms = None
            evidence["compact_timing_error"] = str(exc)
    row = {
        k: projection_input[k]
        for k in (
            "point_id",
            "dataset",
            "evidence_group",
            "architecture",
            "architecture_name",
            "C_Q",
            "n_samples",
            "segment_count",
            "mean_predictor_segments",
            "linear_predictor_segments",
            "rw_predictor_segments",
        )
    }
    row.update(
        {
            "Q_MIN": Q_MIN,
            "v2_encoded_bytes": len(v2),
            "compact_encoded_bytes": len(encoded),
            "projected_encoded_bytes": projected["projected_encoded_bytes"],
            "compact_structural_bytes": structural_bytes,
            "compact_residual_payload_bytes": payload_bytes,
            "compact_structural_fraction": structural_bytes / len(encoded),
            "v2_structural_fraction": accounting["structural_bytes"] / len(v2),
            "total_byte_reduction": len(v2) - len(encoded),
            "total_reduction_fraction": 1 - len(encoded) / len(v2),
            "mean_segment_length": mean_length,
            "min_segment_length": min_length,
            "max_segment_length": max_length,
            "global_and_context_bytes": accounting["global_and_context_bytes"],
            "v2_structural_bytes": accounting["structural_bytes"],
            "v2_residual_payload_bytes": accounting["residual_payload_bytes"],
            "encode_time_ms": encode_ms,
            "decode_time_ms": decode_ms,
        }
    )
    return row, evidence


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_saved_csv(path: Path, fields: Sequence[str]) -> list[dict[str, str]]:
    """Reject changed schemas, extra cells and truncated rows before parsing."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, strict=True)
        if reader.fieldnames != list(fields):
            raise ValueError(f"Invalid saved CSV schema: {path}")
        rows = list(reader)
    if any(
        set(row) != set(fields) or any(v is None for v in row.values()) for row in rows
    ):
        raise ValueError(f"Missing or extra saved CSV fields: {path}")
    return rows


def parse_saved_number(value: str, field: str, *, integer: bool) -> int | float:
    pattern = (
        r"-?[0-9]+"
        if integer
        else r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"
    )
    if re.fullmatch(pattern, value) is None:
        raise ValueError(f"Invalid saved number for {field}: {value!r}")
    number = int(value) if integer else float(value)
    if not integer and not math.isfinite(number):
        raise ValueError(f"Nonfinite saved number for {field}: {value!r}")
    return number


def load_saved_results(path: Path) -> list[dict]:
    rows = read_saved_csv(path, RESULT_FIELDS)
    for row in rows:
        for field in (*RESULT_INTEGER_FIELDS, *RESULT_FLOAT_FIELDS):
            value = row[field]
            row[field] = (
                None
                if field in OPTIONAL_TIMING_FIELDS and value == ""
                else parse_saved_number(
                    value, field, integer=field in RESULT_INTEGER_FIELDS
                )
            )
    return rows


def load_saved_equivalence(path: Path) -> list[dict]:
    rows = read_saved_csv(path, EQUIVALENCE_FIELDS)
    for row in rows:
        for field in BOOLEAN_FIELDS:
            value = row[field]
            if value not in ("True", "False"):
                raise ValueError(f"Invalid saved boolean for {field}: {value!r}")
            row[field] = value == "True"
    return rows


def load_saved_summary(path: Path) -> list[dict]:
    rows = read_saved_csv(path, SUMMARY_FIELDS)
    for row in rows:
        for field in (*SUMMARY_INTEGER_FIELDS, *SUMMARY_FLOAT_FIELDS):
            row[field] = parse_saved_number(
                row[field], field, integer=field in SUMMARY_INTEGER_FIELDS
            )
    return rows


def verify_committed(path: Path) -> None:
    relative = path.relative_to(ROOT).as_posix()
    committed = frozen24.git_output("rev-parse", f"HEAD:{relative}")
    # Honor Git's checkout/clean attributes (notably CSV CRLF conversion).
    # Provenance separately hashes the exact physical bytes used in this run.
    current = frozen24.git_output("hash-object", f"--path={relative}", str(path))
    if current != committed:
        raise ValueError(f"Frozen identity changed: {path}")


def protected_paths() -> list[Path]:
    return sorted(
        {
            *ROOT.glob("docs/local-model-value-*"),
            *ROOT.glob("docs/segment-byte-anatomy-*"),
            ROOT / "tools/benchmark_local_model_value.py",
            ROOT / "tools/analyze_segment_byte_anatomy.py",
            ROOT / "lasagna2/core.py",
            ROOT / "lasagna2/__init__.py",
            PROTOCOL_PATH,
        }
    )


def capture_provenance(command_line: Sequence[str]) -> dict[str, object]:
    order = execution_order()
    for path in protected_paths():
        verify_committed(path)
    baseline_rows = read_csv(ROOT / "docs/local-model-value-results.csv")
    projection_rows = read_csv(ROOT / "docs/segment-byte-anatomy-results.csv")
    baseline_provenance = json.loads(
        (ROOT / "docs/local-model-value-provenance.json").read_text(encoding="utf-8")
    )
    if (
        frozen24.sha256_file(Path(core.__file__))
        != baseline_provenance["codec_source_identity"]["sha256"]
    ):
        raise ValueError("V2 encoder differs from the frozen #24 execution source")
    if baseline_provenance["dataset_sha256"] != {
        str(path): frozen24.sha256_file(ROOT / path) for _, path in corpus_order()
    }:
        raise ValueError("Corpus bytes differ from the frozen #24 execution")
    expected_ids = [p["point_id"] for p in order]
    for rows in (baseline_rows, projection_rows):
        if [r["point_id"] for r in rows] != expected_ids:
            raise ValueError("Frozen evidence does not match the exact 385-point order")
    for baseline, projected in zip(baseline_rows, projection_rows, strict=True):
        if projection25._project_row(baseline)["projected_encoded_bytes"] != int(
            projected["projected_encoded_bytes"]
        ):
            raise ValueError("Frozen #25 projection mismatch")
    provenance = frozen24.provenance(
        corpus_order(),
        repetitions=REPETITIONS,
        warmup=WARMUP,
        command_line=command_line,
    )
    # Retain environment/context/configuration identities, discard #24's claim
    # thresholds and reporting policy: they answer a different research question.
    provenance["frozen_controls"] = {
        "wire_formats": ["canonical V2", "experimental compact V3"],
        "residual_coding": "varint",
        "Q_MIN": Q_MIN,
        "C_Q": list(C_Q_VALUES),
        "warmup": WARMUP,
        "repetitions": REPETITIONS,
        "timing_statistic": "median wall-clock time",
    }
    provenance["baseline24_protocol_sha256"] = provenance["protocol_sha256"]
    provenance.update(
        {
            "schema_version": 26,
            "protocol_sha256": frozen24.sha256_file(PROTOCOL_PATH),
            "protocol_path": PROTOCOL_PATH.relative_to(ROOT).as_posix(),
            "baseline24_protocol_freeze_commit": provenance.pop(
                "protocol_freeze_commit"
            ),
            "baseline24_verified_protocol_freeze_commit": provenance.pop(
                "verified_protocol_freeze_commit"
            ),
            "execution_order": order,
            "compact_prototype_identity": {
                "path": Path(compact.__file__).resolve().relative_to(ROOT).as_posix(),
                "sha256": frozen24.sha256_file(Path(compact.__file__)),
            },
            "v2_encoder_source_sha256": frozen24.sha256_file(Path(core.__file__)),
            "baseline24_artifact_sha256": {
                p.relative_to(ROOT).as_posix(): frozen24.sha256_file(p)
                for p in ROOT.glob("docs/local-model-value-*")
            },
            "projection25_identity": {
                "protocol_path": PROJECTION_PROTOCOL_PATH.relative_to(ROOT).as_posix(),
                "protocol_sha256": frozen24.sha256_file(PROJECTION_PROTOCOL_PATH),
                "implementation_path": "tools/analyze_segment_byte_anatomy.py",
                "implementation_sha256": frozen24.sha256_file(
                    Path(projection25.__file__)
                ),
            },
            "protected_sha256": {
                p.relative_to(ROOT).as_posix(): frozen24.sha256_file(p)
                for p in protected_paths()
            },
            "precorpus_tests_passed": True,
        }
    )
    validate_provenance(provenance)
    return provenance


def validate_provenance(provenance: dict[str, object]) -> None:
    if (
        provenance["schema_version"] != 26
        or provenance["warmup"] != WARMUP
        or provenance["repetitions"] != REPETITIONS
        or provenance["execution_order"] != execution_order()
        or provenance["dataset_order"]
        != [{"evidence_group": g, "path": str(p)} for g, p in corpus_order()]
        or provenance["command"] != shlex.join(provenance["command_line"])
        or provenance["architecture_matrix"] != [asdict(a) for a in ARCHITECTURES]
        or provenance["precorpus_tests_passed"] is not True
        or not provenance["command_line"]
        or provenance["configurations"]
        != {
            a.architecture: [
                frozen24.architecture_options(a, "n_samples", q) for q in C_Q_VALUES
            ]
            for a in ARCHITECTURES
        }
    ):
        raise ValueError("Invalid #26 provenance")
    identities = provenance["protected_sha256"]
    expected_paths = {p.relative_to(ROOT).as_posix() for p in protected_paths()}
    if set(identities) != expected_paths:
        raise ValueError("Incomplete protected provenance identities")
    for relative, digest in identities.items():
        if frozen24.sha256_file(ROOT / relative) != digest:
            raise ValueError(f"Provenance identity mismatch: {relative}")
    identity = provenance["compact_prototype_identity"]
    prototype_path = Path(compact.__file__).resolve()
    if identity != {
        "path": prototype_path.relative_to(ROOT).as_posix(),
        "sha256": frozen24.sha256_file(prototype_path),
    }:
        raise ValueError("Compact prototype identity mismatch")
    if set(provenance["dataset_sha256"]) != {str(p) for _, p in corpus_order()}:
        raise ValueError("Incomplete dataset identities")
    for relative, digest in provenance["dataset_sha256"].items():
        if frozen24.sha256_file(ROOT / relative) != digest:
            raise ValueError(f"Dataset identity mismatch: {relative}")
    if provenance["v2_encoder_source_sha256"] != identities["lasagna2/core.py"]:
        raise ValueError("V2 encoder identity mismatch")
    if (
        provenance["protocol_sha256"]
        != identities["docs/compact-wire-layout-protocol.md"]
    ):
        raise ValueError("#26 protocol identity mismatch")
    if provenance["baseline24_artifact_sha256"] != {
        p: h for p, h in identities.items() if p.startswith("docs/local-model-value-")
    }:
        raise ValueError("#24 artifact identities mismatch")
    projection = provenance["projection25_identity"]
    if projection != {
        "protocol_path": "docs/segment-byte-anatomy-protocol.md",
        "protocol_sha256": identities["docs/segment-byte-anatomy-protocol.md"],
        "implementation_path": "tools/analyze_segment_byte_anatomy.py",
        "implementation_sha256": identities["tools/analyze_segment_byte_anatomy.py"],
    }:
        raise ValueError("#25 identity mismatch")


def public_compatibility() -> dict[str, bool]:
    """Small explicit frozen linear/raw fixtures for both production versions."""
    ts = core.TimeSeries([1.0, 2.0, 3.0, 4.0], 1.0, "1970-01-01T00:00:00Z", "test")
    context = b'{"sampling":{"dt":1.0,"t0":"1970-01-01T00:00:00Z"},"unit":"test"}'
    tail = struct.pack("<IIIIIII4i", 0, 0, 0, 0, 0, 4, 16, 0, 0, 0, 0)
    expected = {}
    for version in (1, 2):
        record = (
            struct.pack("<6I5d", 0, 3, 1, 0, 0, 0, 2.5, 1.0, 1.0, 1e-6, 1.0)
            if version == 1
            else struct.pack("<IIIfffff", 0, 3, 1, 2.5, 1.0, 1.0, 1e-6, 1.0)
        )
        expected[version] = (
            struct.pack("<4sHHIIIII", b"LSG2", version, 0, len(context), 4, 1, 0, 0)
            + context
            + record
            + tail
        )
    options = {
        "segment_length": 4,
        "predictor": "linear",
        "C_Q": 0.5,
        "residual_coding": "raw",
    }
    v1 = core.encode_timeseries_v1(ts, **options)
    v2 = core.encode_timeseries_v2(ts, **options)
    experimental = compact.encode_timeseries_compact_experimental(ts, **options)
    try:
        core.decode_timeseries(experimental)
    except ValueError:
        rejects_compact = True
    else:
        rejects_compact = False
    return {
        "v1_fixture_byte_identical": v1 == expected[1],
        "v2_fixture_byte_identical": v2 == expected[2],
        "public_default_v2": core.encode_timeseries(ts, **options) == expected[2],
        "public_decoder_rejects_v3": rejects_compact,
    }


def preflight() -> None:
    execution_order()
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_tools_benchmark_compact_wire.py",
            "tests/test_experimental_compact_wire.py",
        ],
        cwd=ROOT,
        check=True,
    )


def check_frozen_evidence(
    row: dict, evidence: dict, baseline: dict, projected: dict
) -> None:
    fields = {
        "v2_encoded_bytes": "encoded_bytes",
        "n_samples": "n_samples",
        "segment_count": "segment_count",
        "mean_predictor_segments": "mean_predictor_segments",
        "linear_predictor_segments": "linear_predictor_segments",
        "rw_predictor_segments": "rw_predictor_segments",
        "global_and_context_bytes": "global_and_context_bytes",
        "v2_structural_bytes": "structural_bytes",
        "v2_residual_payload_bytes": "residual_payload_bytes",
    }
    evidence["baseline24_equal"] = all(
        int(row[k]) == int(baseline[v]) for k, v in fields.items()
    )
    evidence["frozen_projection25_equal"] = row["compact_encoded_bytes"] == int(
        projected["projected_encoded_bytes"]
    )


def summarize(rows: Sequence[dict]) -> list[dict]:
    output = []
    groups = sorted(
        {(r["dataset"], r["evidence_group"], r["architecture"]) for r in rows}
    )
    for dataset, group, architecture in groups:
        points = [
            r
            for r in rows
            if (r["dataset"], r["evidence_group"], r["architecture"])
            == (dataset, group, architecture)
        ]
        fractions = [r["total_reduction_fraction"] for r in points]
        output.append(
            {
                "dataset": dataset,
                "evidence_group": group,
                "architecture": architecture,
                "point_count": len(points),
                "median_total_byte_reduction": statistics.median(
                    r["total_byte_reduction"] for r in points
                ),
                "median_total_reduction_fraction": statistics.median(fractions),
                "min_total_reduction_fraction": min(fractions),
                "max_total_reduction_fraction": max(fractions),
                "median_compact_structural_fraction": statistics.median(
                    r["compact_structural_fraction"] for r in points
                ),
                "median_v2_structural_fraction": statistics.median(
                    r["v2_structural_fraction"] for r in points
                ),
            }
        )
    return output


def validate_report_evidence(
    rows: Sequence[dict], evidence: Sequence[dict], provenance: dict
) -> bool:
    expected = execution_order()
    ids = [p["point_id"] for p in expected]
    complete = (
        len(rows) == len(evidence) == EXPECTED_POINTS
        and [r["point_id"] for r in rows] == ids
        and [e["point_id"] for e in evidence] == ids
        and provenance["execution_order"] == expected
    )
    if not complete:
        raise ValueError("Report requires complete ordered 385-point evidence")
    if any(type(e.get(f)) is not bool for e in evidence for f in BOOLEAN_FIELDS):
        raise ValueError("Report requires actual boolean equivalence fields")
    return complete


def build_report(
    rows: Sequence[dict], evidence: Sequence[dict], provenance: dict, public: dict
) -> dict:
    complete = validate_report_evidence(rows, evidence, provenance)
    if set(public) != set(PUBLIC_COMPATIBILITY_FIELDS) or any(
        type(value) is not bool for value in public.values()
    ):
        raise ValueError(
            "Report requires the canonical four boolean compatibility checks"
        )
    gates = {
        "semantic_equivalence_gate": all(
            e[f] is True for e in evidence for f in SEMANTIC_FIELDS
        ),
        "exact_byte_accounting_gate": all(
            e["compact_accounting_equal"] is True for e in evidence
        ),
        "projection25_agreement_gate": all(
            e[f] is True
            for e in evidence
            for f in ("projection25_equal", "frozen_projection25_equal")
        ),
        "public_compatibility_gate": all(
            public[f] is True for f in PUBLIC_COMPATIBILITY_FIELDS
        ),
        "full_grid_execution_gate": complete,
        "baseline24_agreement_gate": all(
            e["baseline24_equal"] is True for e in evidence
        ),
        "compact_timing_determinism_gate": all(
            e["compact_timing_deterministic"] is True for e in evidence
        ),
    }
    return {
        "schema_version": 26,
        "question": "Does compact wire preserve V2 semantics while materially reducing actual serialized bytes?",
        "scope": "Wire-layout validation; no codec-superiority claim or public format promotion.",
        "execution_completed": True,
        "point_count": len(rows),
        "gates": gates,
        "outcome": "PASS" if all(gates.values()) else "FAIL",
        "public_compatibility": public,
        "provenance": provenance,
        "compact_byte_reduction_summary": {
            "v2_total_bytes": sum(r["v2_encoded_bytes"] for r in rows),
            "compact_total_bytes": sum(r["compact_encoded_bytes"] for r in rows),
            "total_byte_reduction": sum(r["total_byte_reduction"] for r in rows),
            "median_total_reduction_fraction": statistics.median(
                r["total_reduction_fraction"] for r in rows
            ),
            "min_total_reduction_fraction": min(
                r["total_reduction_fraction"] for r in rows
            ),
            "max_total_reduction_fraction": max(
                r["total_reduction_fraction"] for r in rows
            ),
        },
        "summary": summarize(rows),
    }


def render_study(report: dict) -> str:
    if (
        report.get("execution_completed") is not True
        or report.get("point_count") != EXPECTED_POINTS
    ):
        raise ValueError("Study requires complete evidence")
    return (
        "# Compact Wire Study (#26)\n\n"
        + report["question"]
        + "\n\n"
        + report["scope"]
        + "\n\n"
        + (
            "Reporting repair: strict saved CSV parsing and canonical public compatibility "
            "fixtures; no corpus rerun. Original corpus provenance is unchanged. "
            "The separate `reporting_repair` entry records recovery inputs and command.\n\n"
            if "reporting_repair" in report
            else ""
        )
        + "```json\n"
        + json.dumps(report, sort_keys=True, indent=2, allow_nan=False)
        + "\n```\n"
    )


def recover_report(artifacts: Artifacts, command_line: Sequence[str]) -> dict:
    """Rebuild only report/study; never capture or write corpus provenance."""
    artifacts.validate()
    provenance = json.loads(artifacts.provenance.read_text(encoding="utf-8"))
    validate_provenance(provenance)
    rows = load_saved_results(artifacts.results)
    evidence = load_saved_equivalence(artifacts.equivalence)
    validate_report_evidence(rows, evidence, provenance)
    for row, point in zip(rows, execution_order(), strict=True):
        if (
            any(
                row[f] != point[f]
                for f in ("dataset", "evidence_group", "architecture", "C_Q")
            )
            or row["Q_MIN"] != Q_MIN
            or row["architecture_name"]
            != (frozen24.architecture_by_id(str(point["architecture"])).name)
        ):
            raise ValueError(
                f"Saved result configuration mismatch: {point['point_id']}"
            )
    if load_saved_summary(artifacts.summary) != summarize(rows):
        raise ValueError("Saved summary differs from result evidence")
    report = build_report(rows, evidence, provenance, public_compatibility())
    report["reporting_repair"] = {
        "mode": "report-only recovery; canonical public compatibility fixtures only",
        "command_line": list(command_line),
        "command": shlex.join(command_line),
        "input_sha256": {
            field: frozen24.sha256_file(getattr(artifacts, field))
            for field in ("results", "summary", "equivalence", "provenance")
        },
        "reporting_source_sha256": frozen24.sha256_file(Path(__file__)),
    }
    study = render_study(report)
    frozen24.write_json(report, artifacts.report)
    artifacts.study.parent.mkdir(parents=True, exist_ok=True)
    artifacts.study.write_text(study, encoding="utf-8")
    return report


def run_corpus(artifacts: Artifacts, command_line: Sequence[str]) -> dict:
    artifacts.validate()
    preflight()
    provenance = capture_provenance(command_line)
    validate_provenance(provenance)
    frozen24.write_json(provenance, artifacts.provenance)
    if json.loads(artifacts.provenance.read_text(encoding="utf-8")) != provenance:
        raise OSError("Provenance persistence verification failed")
    public = public_compatibility()
    if not all(public.values()):
        raise ValueError("Public compatibility pre-corpus gate failed")
    baseline = {
        r["point_id"]: r for r in read_csv(ROOT / "docs/local-model-value-results.csv")
    }
    projected = {
        r["point_id"]: r
        for r in read_csv(ROOT / "docs/segment-byte-anatomy-results.csv")
    }
    rows, evidence = [], []
    for point in execution_order():
        row, comparison = evaluate_point(point)
        check_frozen_evidence(
            row, comparison, baseline[point["point_id"]], projected[point["point_id"]]
        )
        rows.append(row)
        evidence.append(comparison)
        # Preserve a failing point; never publish a complete report for a prefix.
        frozen24.write_csv(rows, artifacts.results, RESULT_FIELDS)
        frozen24.write_csv(evidence, artifacts.equivalence, EQUIVALENCE_FIELDS)
        checks = (
            *SEMANTIC_FIELDS,
            "compact_accounting_equal",
            "projection25_equal",
            "baseline24_equal",
            "frozen_projection25_equal",
            "compact_timing_deterministic",
        )
        if not all(comparison[f] is True for f in checks):
            raise ValueError(f"Wire qualification failed at {point['point_id']}")
    validate_provenance(provenance)
    report = build_report(rows, evidence, provenance, public)
    frozen24.write_csv(report["summary"], artifacts.summary, SUMMARY_FIELDS)
    frozen24.write_json(report, artifacts.report)
    artifacts.study.parent.mkdir(parents=True, exist_ok=True)
    artifacts.study.write_text(render_study(report), encoding="utf-8")
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("preflight", "corpus", "render", "recover"),
        default="preflight",
    )
    for field, default in asdict(Artifacts()).items():
        parser.add_argument(f"--{field}", type=Path, default=default)
    args = parser.parse_args(argv)
    artifacts = Artifacts(**{f: getattr(args, f) for f in asdict(Artifacts())})
    artifacts.validate()
    if args.mode == "preflight":
        preflight()
    elif args.mode == "corpus":
        run_corpus(
            artifacts,
            sys.orig_argv if argv is None else [sys.executable, __file__, *argv],
        )
    elif args.mode == "recover":
        recover_report(
            artifacts,
            sys.orig_argv if argv is None else [sys.executable, __file__, *argv],
        )
    else:
        report = json.loads(artifacts.report.read_text(encoding="utf-8"))
        artifacts.study.parent.mkdir(parents=True, exist_ok=True)
        artifacts.study.write_text(render_study(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
