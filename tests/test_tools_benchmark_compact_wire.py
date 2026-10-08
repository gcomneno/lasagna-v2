from __future__ import annotations

import copy
import importlib.util
import json
import math
import struct
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "benchmark_compact_wire", ROOT / "tools/benchmark_compact_wire.py"
)
assert SPEC is not None and SPEC.loader is not None
harness = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = harness
SPEC.loader.exec_module(harness)


def test_exact_frozen_execution_order_and_cardinality():
    expected_datasets = (
        ("internal", "data/examples/trend.csv"),
        ("internal", "data/examples/sine_noise.csv"),
        ("internal", "data/examples/flat_spike.csv"),
        ("external", "data/external-qualification/canonical/appliances-energy.csv"),
        ("external", "data/external-qualification/canonical/metro-traffic.csv"),
        ("external", "data/external-qualification/canonical/beijing-pm25.csv"),
        ("external", "data/external-qualification/canonical/seoul-bike-demand.csv"),
        ("external", "data/external-qualification/canonical/fan-vibration-x.csv"),
        (
            "external",
            "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        ),
        ("external", "data/external-qualification/canonical/room-occupancy-count.csv"),
        ("external", "data/external-qualification/canonical/tetouan-zone1-power.csv"),
    )
    expected_q = (0.0625, 0.125, 0.25, 0.5, 1.0, 2.0, 4.0)
    assert harness.INTERNAL_DATASETS is harness.frozen24.INTERNAL_DATASETS
    assert harness.EXTERNAL_DATASETS is harness.frozen24.EXTERNAL_DATASETS
    assert harness.ARCHITECTURES is harness.frozen24.ARCHITECTURES
    assert harness.C_Q_VALUES is harness.frozen24.C_Q_VALUES
    assert harness.Q_MIN == 1e-6
    expected = [
        (group, path, architecture, q)
        for group, path in expected_datasets
        for q in expected_q
        for architecture in ("A0", "A1", "A2", "A3", "A4")
    ]
    points = harness.execution_order()
    assert len(points) == len(expected) == 385
    assert [
        (p["evidence_group"], p["dataset_path"], p["architecture"], p["C_Q"])
        for p in points
    ] == expected
    frozen = harness.frozen24.execution_order(harness.corpus_order(), 3, 1)
    assert [p["point_id"] for p in points] == [p["point_id"] for p in frozen]


def test_cardinality_is_independently_asserted(monkeypatch):
    monkeypatch.setattr(harness, "C_Q_VALUES", harness.C_Q_VALUES[:-1])
    with pytest.raises(ValueError, match="385"):
        harness.execution_order()


@pytest.mark.parametrize("architecture", ("A0", "A1", "A2", "A3", "A4"))
@pytest.mark.parametrize("c_q", (0.0625, 0.125, 0.25, 0.5, 1.0, 2.0, 4.0))
def test_same_context_and_options_for_both_wires(monkeypatch, architecture, c_q):
    values = [math.sin(i / 9) + i / 100 for i in range(145)]
    monkeypatch.setattr(harness, "load_csv_values", lambda _: values)
    calls = {"v2": [], "compact": []}
    v2_encoder = harness.core.encode_timeseries_v2
    compact_encoder = harness.compact.encode_timeseries_compact_experimental

    def v2(ts, **options):
        calls["v2"].append((ts, options.copy()))
        return v2_encoder(ts, **options)

    def compact(ts, **options):
        calls["compact"].append((ts, options.copy()))
        return compact_encoder(ts, **options)

    monkeypatch.setattr(harness.core, "encode_timeseries_v2", v2)
    monkeypatch.setattr(
        harness.compact, "encode_timeseries_compact_experimental", compact
    )
    point = next(
        p
        for p in harness.execution_order()
        if p["architecture"] == architecture and p["C_Q"] == c_q
    )
    row, evidence = harness.evaluate_point(point)
    expected = harness.frozen24.architecture_options(
        harness.frozen24.architecture_by_id(architecture), len(values), c_q
    )
    assert len(calls["compact"]) == 5  # untimed + 1 warmup + 3 timed
    assert len(calls["v2"]) == 6  # direct canonical + compact's V2 control
    ts = calls["v2"][0][0]
    for series, options in calls["v2"] + calls["compact"]:
        assert series is ts
        assert options == expected
        assert (series.dt, series.t0, series.unit) == (
            1.0,
            "1970-01-01T00:00:00Z",
            "local-model-value",
        )
    assert all(evidence[f] is True for f in harness.SEMANTIC_FIELDS)
    assert evidence["compact_accounting_equal"] is True
    assert evidence["projection25_equal"] is True
    assert evidence["compact_timing_deterministic"] is True
    assert row["point_id"] == point["point_id"]
    assert (
        row["v2_encoded_bytes"] - row["compact_encoded_bytes"]
        == row["total_byte_reduction"]
    )
    assert (
        row["compact_structural_bytes"] + row["compact_residual_payload_bytes"]
        == row["compact_encoded_bytes"]
    )
    assert (
        row["compact_structural_fraction"]
        == row["compact_structural_bytes"] / row["compact_encoded_bytes"]
    )


def _varint(value):
    result = bytearray()
    while value >= 128:
        result.append((value & 127) | 128)
        value >>= 7
    result.append(value)
    return bytes(result)


def _payload(residuals, coding):
    if coding == 0:
        return struct.pack(f"<{len(residuals)}i", *residuals)
    result = bytearray()
    index = 0
    while index < len(residuals):
        if coding == 2 and residuals[index : index + 3] == [0, 0, 0]:
            end = index + 3
            while end < len(residuals) and residuals[end] == 0:
                end += 1
            result += b"\x00" + _varint(end - index)
            index = end
        else:
            value = residuals[index]
            zigzag = (value << 1) ^ (value >> 31)
            result += _varint(zigzag + (coding == 2))
            index += 1
    return bytes(result)


def _wire(version, coding=0, tags=(0, 1, 2), lengths=(1, 4, 2), *, parameters=None):
    """Literal independent serializer, including signed zero and int32 edges."""
    context = b'{"sampling":{"dt":0.25,"t0":"test"},"unit":"test"}'
    out = bytearray(
        struct.pack(
            "<4sHHIIIII",
            b"LSG2",
            version,
            0,
            len(context),
            sum(lengths),
            len(tags),
            0,
            0,
        )
    )
    out += context
    records, blocks, pairs = bytearray(), bytearray(), bytearray()
    start = 0
    for index, (tag, length) in enumerate(zip(tags, lengths, strict=True)):
        q = 0.125
        active = (
            parameters
            if parameters is not None
            else {0: (-0.0,), 1: (0.10000000149, -0.0), 2: (2.0,)}[tag]
        )
        mean = active[0] if tag == 0 else 0.0
        slope, intercept = active if tag == 1 else (0.0, 0.0)
        seed = active[0] if tag == 2 else 0.0
        residuals = [0, 0, 0, 0] if length == 4 else [-(2**31), 2**31 - 1][:length]
        payload = _payload(residuals, coding)
        records += struct.pack(
            "<IIIfffff", start, start + length - 1, tag, mean, slope, intercept, q, seed
        )
        blocks += struct.pack("<III", index, length, len(payload)) + payload
        pairs += struct.pack("<IBfI", length, tag, q, len(payload))
        pairs += struct.pack(f"<{len(active)}f", *active) + payload
        start += length
    coding_header = struct.pack("<IIII", coding, 0, 0, 0)
    return bytes(
        out
        + (records + coding_header + blocks if version == 2 else coding_header + pairs)
    )


@pytest.mark.parametrize("tag", (0, 1, 2))
@pytest.mark.parametrize("coding", (0, 1, 2))
def test_exact_oracle_all_predictors_and_codecs_and_accounting(tag, coding):
    v2 = _wire(2, coding, (tag,), (4,))
    compact = _wire(3, coding, (tag,), (4,))
    evidence = harness.equivalence(v2, compact)
    assert all(evidence[f] is True for f in harness.SEMANTIC_FIELDS)
    assert evidence["compact_accounting_equal"] is True
    wire = harness.read_wire(compact, 3)
    assert wire.segments[0].residuals == (0, 0, 0, 0)
    expected = (
        28
        + len(wire.context)
        + 16
        + (21 if tag == 1 else 17)
        + sum(len(s.payload) for s in wire.segments)
    )
    assert len(compact) == expected
    accounting = harness.frozen24.v2_byte_accounting(v2)
    row = {
        "point_id": "small:A4:cq=0.125",
        "dataset": "small",
        "evidence_group": "internal",
        "architecture": "A4",
        "architecture_name": "adaptive_auto",
        "C_Q": "0.125",
        "n_samples": "4",
        "segment_count": "1",
        "encoded_bytes": str(len(v2)),
        "mean_predictor_segments": str(tag == 0 and 1 or 0),
        "linear_predictor_segments": str(tag == 1 and 1 or 0),
        "rw_predictor_segments": str(tag == 2 and 1 or 0),
        **{k: str(v) for k, v in accounting.items()},
    }
    assert harness.projection25._project_row(row)["projected_encoded_bytes"] == len(
        compact
    )


@pytest.mark.parametrize("coding", (0, 1, 2))
def test_mixed_unequal_topology_signed_zero_and_int32_endpoints(coding):
    v2, compact = _wire(2, coding), _wire(3, coding)
    evidence = harness.equivalence(v2, compact)
    assert all(evidence[f] is True for f in harness.SEMANTIC_FIELDS)
    wire = harness.read_wire(compact, 3)
    assert [(s.start, s.end) for s in wire.segments] == [(0, 0), (1, 4), (5, 6)]
    assert wire.segments[0].parameter_bits == (b"\x00\x00\x00\x80",)
    assert wire.segments[2].residuals == (-(2**31), 2**31 - 1)
    assert len(compact) == 28 + len(wire.context) + 16 + 17 + 21 + 17 + sum(
        len(s.payload) for s in wire.segments
    )


@pytest.mark.parametrize(
    "field,offset",
    (("q_binary32_equal", 5), ("predictor_parameters_binary32_equal", 13)),
)
def test_oracle_detects_one_binary32_bit(field, offset):
    v2, compact = _wire(2), bytearray(_wire(3))
    context_len = struct.unpack_from("<I", compact, 8)[0]
    compact[28 + context_len + 16 + offset] ^= 1
    assert harness.equivalence(v2, bytes(compact))[field] is False


def test_oracle_detects_context_byte_difference():
    v2, compact = _wire(2), _wire(3)
    changed = compact.replace(b'"unit":"test"', b'"unit":"best"')
    evidence = harness.equivalence(v2, changed)
    assert evidence["context_bytes_equal"] is False
    assert evidence["reconstruction_binary64_equal"] is True


def test_oracle_detects_boundaries_even_with_equal_sample_and_segment_counts():
    v2 = _wire(2, lengths=(1, 4, 2))
    # All length-2 segments keep the builder's endpoint payloads valid.
    compact = _wire(3, lengths=(2, 4, 1))
    evidence = harness.equivalence(v2, compact)
    assert evidence["sample_count_equal"] is True
    assert evidence["segment_count_equal"] is True
    assert evidence["segment_boundaries_equal"] is False


def test_oracle_compares_payload_bytes_independently_of_residual_integers():
    v2 = _wire(2, 1, (0,), (4,))
    compact = bytearray(_wire(3, 1, (0,), (4,)))
    record = 28 + struct.unpack_from("<I", compact, 8)[0] + 16
    struct.pack_into("<I", compact, record + 9, 5)
    compact[record + 17 : record + 18] = b"\x80\x00"  # Same zero, distinct token bytes.
    evidence = harness.equivalence(v2, bytes(compact))
    assert evidence["residual_int32_equal"] is True
    assert evidence["residual_payload_equal"] is False
    assert evidence["compact_accounting_equal"] is True


def test_oracle_detects_coding_type_difference():
    evidence = harness.equivalence(_wire(2, 0), _wire(3, 1))
    assert evidence["coding_type_equal"] is False
    assert evidence["residual_int32_equal"] is True
    assert evidence["reconstruction_binary64_equal"] is True


def test_oracle_detects_single_binary64_bit(monkeypatch):
    decode = harness.compact.decode_timeseries_compact_experimental

    def changed(data):
        result = decode(data)
        result.values[0] = math.nextafter(result.values[0], math.inf)
        return result

    monkeypatch.setattr(
        harness.compact, "decode_timeseries_compact_experimental", changed
    )
    evidence = harness.equivalence(_wire(2), _wire(3))
    assert evidence["reconstruction_binary64_equal"] is False
    assert (
        evidence["v2_reconstruction_sha256"]
        != evidence["compact_reconstruction_sha256"]
    )


def test_compact_decode_failure_is_explicit(monkeypatch):
    def reject(_):
        raise ValueError("controlled failure")

    monkeypatch.setattr(
        harness.compact, "decode_timeseries_compact_experimental", reject
    )
    evidence = harness.equivalence(_wire(2), _wire(3))
    assert evidence["compact_decode_success"] is False
    assert evidence["reconstruction_binary64_equal"] is False
    assert evidence["compact_decode_error"] == "ValueError: controlled failure"


def _small_point(monkeypatch):
    monkeypatch.setattr(harness, "load_csv_values", lambda _: [1.0, 2.0, 1.5, 3.0])
    return harness.execution_order()[0]


def test_projection_disagreement_blocks_timing(monkeypatch):
    point = _small_point(monkeypatch)
    project = harness.projection25._project_row

    def changed(row):
        result = project(row)
        result["projected_encoded_bytes"] += 1
        return result

    monkeypatch.setattr(harness.projection25, "_project_row", changed)
    monkeypatch.setattr(
        harness,
        "_measure_deterministic_encode",
        lambda *a, **k: pytest.fail("timing on failed gate"),
    )
    row, evidence = harness.evaluate_point(point)
    assert evidence["projection25_equal"] is False
    assert row["encode_time_ms"] is None


def test_timing_exact_protocol_median_and_separate_oracle(monkeypatch):
    point = _small_point(monkeypatch)
    events = []
    oracle = harness.equivalence
    measure_encode, measure_decode = (
        harness._measure_deterministic_encode,
        harness._median_call_ms,
    )
    import benchmark_codec

    ticks = iter((0, 1_000_000, 10_000_000, 13_000_000, 20_000_000, 22_000_000) * 2)
    monkeypatch.setattr(benchmark_codec.time, "perf_counter_ns", lambda: next(ticks))

    def compare(*args):
        events.append("oracle")
        return oracle(*args)

    def encode(operation, **timing):
        assert timing == {"warmup": 1, "repetitions": 3}
        events.append("encode timing")
        return measure_encode(operation, **timing)

    def decode(operation, **timing):
        assert timing == {"warmup": 1, "repetitions": 3}
        events.append("decode timing")
        return measure_decode(operation, **timing)

    monkeypatch.setattr(harness, "equivalence", compare)
    monkeypatch.setattr(harness, "_measure_deterministic_encode", encode)
    monkeypatch.setattr(harness, "_median_call_ms", decode)
    row, evidence = harness.evaluate_point(point)
    assert events == ["oracle", "encode timing", "decode timing"]
    assert row["encode_time_ms"] == row["decode_time_ms"] == 2.0
    assert evidence["compact_timing_deterministic"] is True


@pytest.mark.parametrize("changed_call", (4, 5))
def test_timed_encodes_must_be_deterministic(monkeypatch, changed_call):
    point = _small_point(monkeypatch)
    encoder = harness.compact.encode_timeseries_compact_experimental
    calls = 0

    def changed(ts, **options):
        nonlocal calls
        calls += 1
        data = encoder(ts, **options)
        return data + b"x" if calls == changed_call else data

    monkeypatch.setattr(
        harness.compact, "encode_timeseries_compact_experimental", changed
    )
    row, evidence = harness.evaluate_point(point)
    assert evidence["compact_timing_deterministic"] is False
    assert "non-deterministic" in evidence["compact_timing_error"]
    assert all(evidence[f] is True for f in harness.SEMANTIC_FIELDS)
    assert row["encode_time_ms"] is None and row["decode_time_ms"] is None


def test_deterministic_timed_bytes_must_match_untimed_evidence(monkeypatch):
    point = _small_point(monkeypatch)
    encoder = harness.compact.encode_timeseries_compact_experimental
    calls = 0

    def changed(ts, **options):
        nonlocal calls
        calls += 1
        data = encoder(ts, **options)
        return data + b"x" if calls > 1 else data

    monkeypatch.setattr(
        harness.compact, "encode_timeseries_compact_experimental", changed
    )
    _, evidence = harness.evaluate_point(point)
    assert evidence["compact_timing_deterministic"] is False
    assert "differs from untimed evidence" in evidence["compact_timing_error"]


@pytest.fixture(scope="module")
def provenance():
    # Read-only identity capture; no corpus load, encoding, or measurement.
    return harness.capture_provenance(
        [sys.executable, "tools/benchmark_compact_wire.py", "--mode", "corpus"]
    )


def test_provenance_contains_frozen_and_prototype_identities(provenance):
    harness.validate_provenance(provenance)
    assert provenance["warmup"] == 1 and provenance["repetitions"] == 3
    assert (
        provenance["compact_prototype_identity"]["path"]
        == "lasagna2/experimental_compact.py"
    )
    assert provenance["compact_prototype_identity"][
        "sha256"
    ] == harness.frozen24.sha256_file(ROOT / "lasagna2/experimental_compact.py")
    assert provenance["v2_encoder_source_sha256"] == harness.frozen24.sha256_file(
        ROOT / "lasagna2/core.py"
    )
    assert provenance["baseline24_artifact_sha256"]
    assert (
        provenance["projection25_identity"]["implementation_path"]
        == "tools/analyze_segment_byte_anatomy.py"
    )
    assert "material_win_max" not in provenance["frozen_controls"]
    assert provenance["execution_order"] == harness.execution_order()


@pytest.mark.parametrize(
    "field,value",
    (
        ("repetitions", 2),
        ("warmup", 0),
        ("dataset_sha256", {}),
        ("protected_sha256", {}),
        ("v2_encoder_source_sha256", "bad"),
        ("baseline24_artifact_sha256", {}),
        ("execution_order", []),
        ("projection25_identity", {}),
        ("compact_prototype_identity", {}),
    ),
)
def test_invalid_provenance_fails_closed(provenance, field, value):
    changed = copy.deepcopy(provenance)
    changed[field] = value
    with pytest.raises((ValueError, KeyError)):
        harness.validate_provenance(changed)


def _artifacts(tmp_path):
    return harness.Artifacts(
        **{k: tmp_path / p.name for k, p in asdict(harness.Artifacts()).items()}
    )


def _no_corpus(monkeypatch):
    monkeypatch.setattr(harness, "preflight", lambda: None)
    monkeypatch.setattr(
        harness, "evaluate_point", lambda _: pytest.fail("evaluation must not start")
    )


@pytest.mark.parametrize("failure", ("capture", "validation", "write", "verification"))
def test_provenance_failure_blocks_evaluation(
    monkeypatch, tmp_path, provenance, failure
):
    _no_corpus(monkeypatch)
    monkeypatch.setattr(
        harness, "capture_provenance", lambda _: copy.deepcopy(provenance)
    )

    def reject(*a, **k):
        raise OSError("provenance failure")

    if failure == "capture":
        monkeypatch.setattr(harness, "capture_provenance", reject)
    elif failure == "validation":
        monkeypatch.setattr(harness, "validate_provenance", reject)
    elif failure == "write":
        monkeypatch.setattr(harness.frozen24, "write_json", reject)
    else:
        monkeypatch.setattr(
            harness.frozen24, "write_json", lambda _, p: p.write_text("{}")
        )
    with pytest.raises(OSError):
        harness.run_corpus(_artifacts(tmp_path), provenance["command_line"])


def test_provenance_is_persisted_before_first_evaluation(
    monkeypatch, tmp_path, provenance
):
    monkeypatch.setattr(harness, "preflight", lambda: None)
    monkeypatch.setattr(
        harness, "capture_provenance", lambda _: copy.deepcopy(provenance)
    )
    artifacts = _artifacts(tmp_path)
    before = {p: p.read_bytes() for p in harness.protected_paths()}

    class StopSyntheticEvaluation(Exception):
        pass

    def first(point):
        assert point == harness.execution_order()[0]
        assert json.loads(artifacts.provenance.read_text()) == provenance
        raise StopSyntheticEvaluation

    monkeypatch.setattr(harness, "evaluate_point", first)
    with pytest.raises(StopSyntheticEvaluation):
        harness.run_corpus(artifacts, provenance["command_line"])
    assert {p: p.read_bytes() for p in before} == before
    assert not artifacts.report.exists() and not artifacts.study.exists()


def test_failed_point_is_journaled_without_report(monkeypatch, tmp_path, provenance):
    monkeypatch.setattr(harness, "preflight", lambda: None)
    monkeypatch.setattr(
        harness, "capture_provenance", lambda _: copy.deepcopy(provenance)
    )
    artifacts = _artifacts(tmp_path)
    point = harness.execution_order()[0]
    row = {f: 0 for f in harness.RESULT_FIELDS}
    row["point_id"] = point["point_id"]
    comparison = {f: "" for f in harness.EQUIVALENCE_FIELDS}
    comparison.update({f: True for f in harness.SEMANTIC_FIELDS})
    comparison.update(
        {
            "point_id": point["point_id"],
            "context_bytes_equal": False,
            "compact_accounting_equal": True,
            "projection25_equal": True,
            "compact_timing_deterministic": False,
        }
    )
    visited = []

    def synthetic(p):
        visited.append(p["point_id"])
        return row, comparison

    def controls(row, evidence, baseline, projected):
        evidence["baseline24_equal"] = evidence["frozen_projection25_equal"] = True

    monkeypatch.setattr(harness, "evaluate_point", synthetic)
    monkeypatch.setattr(harness, "check_frozen_evidence", controls)
    with pytest.raises(ValueError, match="Wire qualification failed"):
        harness.run_corpus(artifacts, provenance["command_line"])
    assert visited == [point["point_id"]]
    persisted = harness.read_csv(artifacts.equivalence)
    assert len(persisted) == 1
    assert persisted[0]["context_bytes_equal"] == "False"
    assert persisted[0]["compact_accounting_equal"] == "True"
    assert len(harness.read_csv(artifacts.results)) == 1
    assert not artifacts.report.exists() and not artifacts.study.exists()


def test_runner_visits_exact_grid_using_only_synthetic_evaluations(
    monkeypatch, tmp_path, provenance
):
    """Exercise orchestration only; forbid all corpus loads and codec calls."""
    artifacts = _artifacts(tmp_path)
    before = {p: p.read_bytes() for p in harness.protected_paths()}
    monkeypatch.setattr(harness, "preflight", lambda: None)
    monkeypatch.setattr(
        harness, "capture_provenance", lambda _: copy.deepcopy(provenance)
    )
    monkeypatch.setattr(
        harness, "load_csv_values", lambda _: pytest.fail("corpus loaded")
    )
    monkeypatch.setattr(
        harness.core,
        "encode_timeseries_v2",
        lambda *a, **k: pytest.fail("corpus encoded"),
    )
    monkeypatch.setattr(harness, "public_compatibility", lambda: _canonical_public())
    baseline = {
        r["point_id"]: r
        for r in harness.read_csv(ROOT / "docs/local-model-value-results.csv")
    }
    projected = {
        r["point_id"]: r
        for r in harness.read_csv(ROOT / "docs/segment-byte-anatomy-results.csv")
    }
    visited, writes = [], []
    csv_writer = harness.frozen24.write_csv

    def journal(rows, path, fields):
        writes.append((path.name, len(rows)))
        # Only persist the completed metadata journals in this orchestration test.
        if len(rows) in (385, 55):
            csv_writer(rows, path, fields)

    def synthetic(point):
        assert json.loads(artifacts.provenance.read_text()) == provenance
        assert not artifacts.report.exists() and not artifacts.study.exists()
        visited.append(point["point_id"])
        b, p = baseline[point["point_id"]], projected[point["point_id"]]
        row = {f: 0 for f in harness.RESULT_FIELDS}
        row.update(
            {
                k: point[k]
                for k in (
                    "point_id",
                    "dataset",
                    "evidence_group",
                    "architecture",
                    "C_Q",
                )
            }
        )
        for key in (
            "n_samples",
            "segment_count",
            "mean_predictor_segments",
            "linear_predictor_segments",
            "rw_predictor_segments",
            "global_and_context_bytes",
        ):
            row[key] = int(b[key])
        row.update(
            {
                "v2_encoded_bytes": int(b["encoded_bytes"]),
                "v2_structural_bytes": int(b["structural_bytes"]),
                "v2_residual_payload_bytes": int(b["residual_payload_bytes"]),
                "compact_encoded_bytes": int(p["projected_encoded_bytes"]),
                "total_byte_reduction": int(p["total_byte_reduction"]),
                "total_reduction_fraction": float(p["total_reduction_fraction"]),
            }
        )
        comparison = {f: "" for f in harness.EQUIVALENCE_FIELDS}
        comparison.update({f: True for f in harness.SEMANTIC_FIELDS})
        comparison.update(
            {
                "point_id": point["point_id"],
                "compact_accounting_equal": True,
                "projection25_equal": True,
                "compact_timing_deterministic": True,
            }
        )
        return row, comparison

    monkeypatch.setattr(harness, "evaluate_point", synthetic)
    monkeypatch.setattr(harness.frozen24, "write_csv", journal)
    report = harness.run_corpus(artifacts, provenance["command_line"])
    assert visited == [p["point_id"] for p in harness.execution_order()]
    assert report["gates"]["full_grid_execution_gate"] is True
    assert len(harness.read_csv(artifacts.results)) == 385
    assert len(harness.read_csv(artifacts.equivalence)) == 385
    assert len(writes) == 385 * 2 + 1
    assert artifacts.study.read_text() == harness.render_study(report)
    assert {p: p.read_bytes() for p in before} == before


def test_public_compatibility_frozen_fixtures():
    assert harness.public_compatibility() == {
        "v1_fixture_byte_identical": True,
        "v2_fixture_byte_identical": True,
        "public_default_v2": True,
        "public_decoder_rejects_v3": True,
    }


@pytest.mark.parametrize("field", tuple(asdict(harness.Artifacts())))
def test_artifact_paths_cannot_overwrite_24(field, tmp_path):
    artifacts = _artifacts(tmp_path)
    changed = asdict(artifacts)
    changed[field] = ROOT / "docs/local-model-value-results.csv"
    with pytest.raises(ValueError, match="Unsafe"):
        harness.Artifacts(**changed).validate()


def test_artifact_symlink_cannot_overwrite_24(tmp_path):
    artifacts = _artifacts(tmp_path)
    artifacts.results.symlink_to(ROOT / "docs/local-model-value-results.csv")
    with pytest.raises(ValueError, match="Unsafe"):
        artifacts.validate()


def _synthetic_grid():
    rows, evidence = [], []
    for point in harness.execution_order():
        rows.append(
            {
                **point,
                "v2_encoded_bytes": 200,
                "compact_encoded_bytes": 177,
                "total_byte_reduction": 23,
                "total_reduction_fraction": 23 / 200,
                "compact_structural_fraction": 100 / 177,
                "v2_structural_fraction": 123 / 200,
            }
        )
        evidence.append(
            {
                "point_id": point["point_id"],
                **{f: True for f in harness.SEMANTIC_FIELDS},
                "compact_accounting_equal": True,
                "projection25_equal": True,
                "baseline24_equal": True,
                "frozen_projection25_equal": True,
                "compact_timing_deterministic": True,
            }
        )
    return rows, evidence


def _canonical_public():
    return {
        "v1_fixture_byte_identical": True,
        "v2_fixture_byte_identical": True,
        "public_default_v2": True,
        "public_decoder_rejects_v3": True,
    }


def test_report_and_study_are_pure_and_deterministic(monkeypatch, provenance):
    _no_corpus(monkeypatch)
    monkeypatch.setattr(
        harness.core,
        "encode_timeseries_v2",
        lambda *a, **k: pytest.fail("report encodes"),
    )
    monkeypatch.setattr(
        harness.compact,
        "decode_timeseries_compact_experimental",
        lambda *a, **k: pytest.fail("report decodes"),
    )
    rows, evidence = _synthetic_grid()
    public = {
        f: True
        for f in (
            "v1_fixture_byte_identical",
            "v2_fixture_byte_identical",
            "public_default_v2",
            "public_decoder_rejects_v3",
        )
    }
    report = harness.build_report(rows, evidence, provenance, public)
    assert all(report["gates"].values())
    assert report["outcome"] == "PASS"
    assert report["compact_byte_reduction_summary"]["total_byte_reduction"] == 23 * 385
    assert len(report["summary"]) == 11 * 5
    assert harness.render_study(report) == harness.render_study(copy.deepcopy(report))
    assert "claim_supported" not in report


@pytest.mark.parametrize(
    "field,gate",
    (
        ("context_bytes_equal", "semantic_equivalence_gate"),
        ("compact_accounting_equal", "exact_byte_accounting_gate"),
        ("projection25_equal", "projection25_agreement_gate"),
        ("frozen_projection25_equal", "projection25_agreement_gate"),
        ("baseline24_equal", "baseline24_agreement_gate"),
        ("compact_timing_deterministic", "compact_timing_determinism_gate"),
    ),
)
def test_report_calculates_independent_gates(provenance, field, gate):
    rows, evidence = _synthetic_grid()
    evidence[17][field] = False
    report = harness.build_report(rows, evidence, provenance, _canonical_public())
    assert report["gates"][gate] is False
    assert report["gates"]["full_grid_execution_gate"] is True
    if gate != "semantic_equivalence_gate":
        assert report["gates"]["semantic_equivalence_gate"] is True


@pytest.mark.parametrize(
    "failure", ("missing", "duplicate", "reordered", "missing_equivalence")
)
def test_report_requires_complete_ordered_evidence(provenance, failure):
    rows, evidence = _synthetic_grid()
    if failure == "missing":
        rows.pop()
    elif failure == "duplicate":
        rows[-1] = rows[0]
    elif failure == "reordered":
        rows[0], rows[1] = rows[1], rows[0]
    else:
        evidence.pop()
    with pytest.raises(ValueError, match="complete ordered"):
        harness.build_report(rows, evidence, provenance, {})


def test_preflight_is_default_and_never_runs_corpus(monkeypatch):
    calls = []
    monkeypatch.setattr(harness, "preflight", lambda: calls.append("tests"))
    monkeypatch.setattr(harness, "run_corpus", lambda *a: pytest.fail("corpus started"))
    assert harness.main([]) == 0
    assert harness.main(["--mode", "preflight"]) == 0
    assert calls == ["tests", "tests"]


def test_preflight_runs_both_small_suites(monkeypatch):
    calls = []
    monkeypatch.setattr(
        harness.subprocess,
        "run",
        lambda command, **options: calls.append((command, options)),
    )
    harness.preflight()
    assert calls == [
        (
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "tests/test_tools_benchmark_compact_wire.py",
                "tests/test_experimental_compact_wire.py",
            ],
            {"cwd": ROOT, "check": True},
        )
    ]


def test_render_mode_only_renders_persisted_report(monkeypatch, tmp_path, provenance):
    _no_corpus(monkeypatch)
    rows, evidence = _synthetic_grid()
    report = harness.build_report(rows, evidence, provenance, _canonical_public())
    artifacts = _artifacts(tmp_path)
    artifacts.report.write_text(json.dumps(report))
    monkeypatch.setattr(
        harness,
        "capture_provenance",
        lambda _: pytest.fail("render captured execution provenance"),
    )
    assert (
        harness.main(
            [
                "--mode",
                "render",
                "--report",
                str(artifacts.report),
                "--study",
                str(artifacts.study),
            ]
        )
        == 0
    )
    assert artifacts.study.read_text() == harness.render_study(report)


def test_import_never_executes_measurement(monkeypatch):
    monkeypatch.setattr(
        harness.core,
        "encode_timeseries_v2",
        lambda *a, **k: pytest.fail("import encodes"),
    )
    monkeypatch.setattr(
        harness.frozen24,
        "provenance",
        lambda *a, **k: pytest.fail("import captures provenance"),
    )
    SPEC.loader.exec_module(harness)


@pytest.fixture
def saved_reporting_evidence(tmp_path):
    """Persist typed metadata only; never evaluate or encode a dataset point."""
    rows, evidence = _synthetic_grid()
    for row in rows:
        row.pop("dataset_path")
        row.pop("operations")
        row.update(
            {
                "architecture_name": harness.frozen24.architecture_by_id(
                    row["architecture"]
                ).name,
                "Q_MIN": 1e-6,
                "n_samples": 4,
                "projected_encoded_bytes": 177,
                "compact_structural_bytes": 100,
                "compact_residual_payload_bytes": 77,
                "segment_count": 1,
                "mean_segment_length": 4.0,
                "min_segment_length": 4,
                "max_segment_length": 4,
                "mean_predictor_segments": 0,
                "linear_predictor_segments": 1,
                "rw_predictor_segments": 0,
                "global_and_context_bytes": 79,
                "v2_structural_bytes": 123,
                "v2_residual_payload_bytes": 77,
                "encode_time_ms": 0.125,
                "decode_time_ms": None,
            }
        )
    for comparison in evidence:
        comparison.update(
            {
                "v2_stream_sha256": "a" * 64,
                "compact_stream_sha256": "b" * 64,
                "v2_reconstruction_sha256": "c" * 64,
                "compact_reconstruction_sha256": "c" * 64,
                "compact_decode_error": "",
                "compact_timing_error": "",
            }
        )
    artifacts = _artifacts(tmp_path)
    harness.frozen24.write_csv(rows, artifacts.results, harness.RESULT_FIELDS)
    harness.frozen24.write_csv(
        evidence, artifacts.equivalence, harness.EQUIVALENCE_FIELDS
    )
    harness.frozen24.write_csv(
        harness.summarize(rows), artifacts.summary, harness.SUMMARY_FIELDS
    )
    artifacts.provenance.write_bytes(harness.Artifacts().provenance.read_bytes())
    provenance = json.loads(artifacts.provenance.read_text())
    return artifacts, rows, evidence, provenance


def test_saved_csv_reconstructs_typed_report(saved_reporting_evidence):
    artifacts, rows, evidence, provenance = saved_reporting_evidence
    loaded_rows = harness.load_saved_results(artifacts.results)
    loaded_evidence = harness.load_saved_equivalence(artifacts.equivalence)
    assert loaded_rows == rows
    assert loaded_evidence == evidence
    assert type(loaded_rows[0]["n_samples"]) is int
    assert type(loaded_rows[0]["C_Q"]) is float
    assert loaded_rows[0]["decode_time_ms"] is None
    assert harness.build_report(
        loaded_rows, loaded_evidence, provenance, _canonical_public()
    ) == (harness.build_report(rows, evidence, provenance, _canonical_public()))


@pytest.mark.parametrize(
    "field,gate",
    (
        ("context_bytes_equal", "semantic_equivalence_gate"),
        ("compact_accounting_equal", "exact_byte_accounting_gate"),
        ("projection25_equal", "projection25_agreement_gate"),
        ("frozen_projection25_equal", "projection25_agreement_gate"),
        ("baseline24_equal", "baseline24_agreement_gate"),
        ("compact_timing_deterministic", "compact_timing_determinism_gate"),
    ),
)
def test_saved_false_remains_false(saved_reporting_evidence, field, gate):
    artifacts, rows, evidence, provenance = saved_reporting_evidence
    evidence[17][field] = False
    harness.frozen24.write_csv(
        evidence, artifacts.equivalence, harness.EQUIVALENCE_FIELDS
    )
    loaded = harness.load_saved_equivalence(artifacts.equivalence)
    assert loaded[17][field] is False
    report = harness.build_report(rows, loaded, provenance, _canonical_public())
    assert report["gates"][gate] is False
    assert report["outcome"] == "FAIL"


def test_recovery_persists_failed_gate(saved_reporting_evidence, monkeypatch):
    artifacts, _, evidence, _ = saved_reporting_evidence
    evidence[17]["context_bytes_equal"] = False
    harness.frozen24.write_csv(
        evidence, artifacts.equivalence, harness.EQUIVALENCE_FIELDS
    )
    monkeypatch.setattr(harness, "run_corpus", lambda *a: pytest.fail("corpus started"))
    monkeypatch.setattr(
        harness, "evaluate_point", lambda *a: pytest.fail("point evaluated")
    )
    report = harness.recover_report(artifacts, ["report-only"])
    assert report["gates"]["semantic_equivalence_gate"] is False
    assert report["outcome"] == "FAIL"
    assert json.loads(artifacts.report.read_text())["outcome"] == "FAIL"
    assert artifacts.study.read_text() == harness.render_study(report)


@pytest.mark.parametrize("field", harness.BOOLEAN_FIELDS)
@pytest.mark.parametrize(
    "invalid", ("", "true", "FALSE", "1", "0", " True", "False ", "null")
)
def test_saved_malformed_boolean_rejected(saved_reporting_evidence, field, invalid):
    artifacts, _, evidence, _ = saved_reporting_evidence
    evidence[0][field] = invalid
    harness.frozen24.write_csv(
        evidence, artifacts.equivalence, harness.EQUIVALENCE_FIELDS
    )
    with pytest.raises(ValueError, match="Invalid saved boolean"):
        harness.load_saved_equivalence(artifacts.equivalence)


@pytest.mark.parametrize("field", harness.BOOLEAN_FIELDS)
def test_saved_missing_boolean_column_rejected(saved_reporting_evidence, field):
    artifacts, _, evidence, _ = saved_reporting_evidence
    fields = tuple(f for f in harness.EQUIVALENCE_FIELDS if f != field)
    evidence = [{f: row[f] for f in fields} for row in evidence]
    harness.frozen24.write_csv(evidence, artifacts.equivalence, fields)
    with pytest.raises(ValueError, match="schema"):
        harness.load_saved_equivalence(artifacts.equivalence)


@pytest.mark.parametrize("fault", ("truncated", "extra", "duplicate_header"))
def test_saved_csv_row_shape_rejected(saved_reporting_evidence, fault):
    artifacts, _, _, _ = saved_reporting_evidence
    lines = artifacts.equivalence.read_text().splitlines()
    if fault == "truncated":
        lines[1] = ",".join(lines[1].split(",")[:-1])
    elif fault == "extra":
        lines[1] += ",extra"
    else:
        lines[0] = lines[0].replace("compact_accounting_equal", "context_bytes_equal")
    artifacts.equivalence.write_text("\n".join(lines) + "\n")
    with pytest.raises(ValueError, match="schema|fields"):
        harness.load_saved_equivalence(artifacts.equivalence)


@pytest.mark.parametrize(
    "field,invalid",
    (
        ("n_samples", "4.0"),
        ("v2_encoded_bytes", "1e3"),
        ("segment_count", "NaN"),
        ("total_byte_reduction", ""),
        ("C_Q", "nan"),
        ("Q_MIN", "inf"),
        ("total_reduction_fraction", "-Infinity"),
        ("compact_structural_fraction", "1e999"),
        ("mean_segment_length", "bad"),
        ("encode_time_ms", "nan"),
        ("decode_time_ms", "inf"),
        ("encode_time_ms", "1_0"),
        ("decode_time_ms", " 1.0"),
    ),
)
def test_saved_malformed_or_nonfinite_number_rejected(
    saved_reporting_evidence, field, invalid
):
    artifacts, rows, _, _ = saved_reporting_evidence
    rows[0][field] = invalid
    harness.frozen24.write_csv(rows, artifacts.results, harness.RESULT_FIELDS)
    with pytest.raises(ValueError, match="saved number"):
        harness.load_saved_results(artifacts.results)


@pytest.mark.parametrize("which", ("results", "equivalence"))
@pytest.mark.parametrize("fault", ("incomplete", "duplicate", "reordered"))
def test_saved_incomplete_duplicate_reordered_rejected(
    saved_reporting_evidence, monkeypatch, which, fault
):
    artifacts, rows, evidence, _ = saved_reporting_evidence
    changed = rows if which == "results" else evidence
    if fault == "incomplete":
        changed.pop()
    elif fault == "duplicate":
        changed[-1] = changed[0]
    else:
        changed[0], changed[1] = changed[1], changed[0]
    fields = harness.RESULT_FIELDS if which == "results" else harness.EQUIVALENCE_FIELDS
    harness.frozen24.write_csv(changed, getattr(artifacts, which), fields)
    monkeypatch.setattr(
        harness,
        "public_compatibility",
        lambda: pytest.fail("fixtures before validation"),
    )
    with pytest.raises(ValueError, match="complete ordered"):
        harness.recover_report(artifacts, ["report-only"])
    assert not artifacts.report.exists() and not artifacts.study.exists()


@pytest.mark.parametrize("invalid", ("True", "False", 1, 0, None))
def test_report_requires_native_boolean_equivalence(saved_reporting_evidence, invalid):
    _, rows, evidence, provenance = saved_reporting_evidence
    evidence[0]["context_bytes_equal"] = invalid
    with pytest.raises(ValueError, match="actual boolean"):
        harness.build_report(rows, evidence, provenance, _canonical_public())


@pytest.mark.parametrize(
    "fault", ("missing", "wrong", "extra", "old_map", "string", "integer")
)
def test_report_rejects_noncanonical_compatibility(saved_reporting_evidence, fault):
    _, rows, evidence, provenance = saved_reporting_evidence
    public = _canonical_public()
    if fault == "missing":
        public.pop("public_decoder_rejects_v3")
    elif fault == "wrong":
        public["wrong"] = public.pop("public_decoder_rejects_v3")
    elif fault == "extra":
        public["extra"] = True
    elif fault == "old_map":
        public = {"v1": True, "v2": True, "experimental_v3": True}
    else:
        public["public_decoder_rejects_v3"] = "True" if fault == "string" else 1
    with pytest.raises(ValueError, match="canonical four boolean"):
        harness.build_report(rows, evidence, provenance, public)


@pytest.mark.parametrize("field", tuple(_canonical_public()))
def test_report_public_false_fails(saved_reporting_evidence, field):
    _, rows, evidence, provenance = saved_reporting_evidence
    public = _canonical_public()
    public[field] = False
    report = harness.build_report(rows, evidence, provenance, public)
    assert report["gates"]["public_compatibility_gate"] is False
    assert report["outcome"] == "FAIL"


@pytest.mark.parametrize("fault", ("provenance", "summary", "configuration"))
def test_recovery_rejects_inconsistent_saved_context(
    saved_reporting_evidence, monkeypatch, fault
):
    artifacts, rows, _, provenance = saved_reporting_evidence
    if fault == "provenance":
        provenance["compact_prototype_identity"]["sha256"] = "changed"
        artifacts.provenance.write_text(json.dumps(provenance))
    elif fault == "summary":
        summary = harness.summarize(rows)
        summary[0]["point_count"] = 6
        harness.frozen24.write_csv(summary, artifacts.summary, harness.SUMMARY_FIELDS)
    else:
        rows[0]["C_Q"] = 1.0
        harness.frozen24.write_csv(rows, artifacts.results, harness.RESULT_FIELDS)
    monkeypatch.setattr(
        harness,
        "public_compatibility",
        lambda: pytest.fail("fixtures before validation"),
    )
    with pytest.raises(ValueError, match="identity mismatch|summary|configuration"):
        harness.recover_report(artifacts, ["report-only"])
    assert not artifacts.report.exists() and not artifacts.study.exists()


def test_recovery_only_runs_canonical_fixtures(saved_reporting_evidence, monkeypatch):
    artifacts, rows, evidence, provenance = saved_reporting_evidence
    inputs = (
        artifacts.results,
        artifacts.summary,
        artifacts.equivalence,
        artifacts.provenance,
    )
    before = {
        p: p.read_bytes()
        for p in (*inputs, *harness.protected_paths(), Path(harness.compact.__file__))
    }

    def forbidden(*args, **kwargs):
        pytest.fail(
            "report recovery attempted corpus execution, data loading or measurement"
        )

    for name in (
        "run_corpus",
        "evaluate_point",
        "preflight",
        "capture_provenance",
        "load_csv_values",
        "_measure_deterministic_encode",
        "_median_call_ms",
    ):
        monkeypatch.setattr(harness, name, forbidden)
    monkeypatch.setattr(harness.frozen24, "provenance", forbidden)
    monkeypatch.setattr(harness.frozen24, "load_csv_values", forbidden)
    calls = []

    def fixture_encoder(name, original):
        def checked(ts, *args, **options):
            assert ts.values == [1.0, 2.0, 3.0, 4.0]
            assert (ts.dt, ts.t0, ts.unit) == (1.0, "1970-01-01T00:00:00Z", "test")
            assert options["segment_length"] == 4
            assert options["predictor"] == "linear"
            assert options["C_Q"] == 0.5
            assert options["residual_coding"] == "raw"
            calls.append(name)
            return original(ts, *args, **options)

        return checked

    for module, name in (
        (harness.core, "encode_timeseries_v1"),
        (harness.core, "encode_timeseries_v2"),
        (harness.core, "encode_timeseries"),
        (harness.compact, "encode_timeseries_compact_experimental"),
    ):
        monkeypatch.setattr(module, name, fixture_encoder(name, getattr(module, name)))
    command = ["--mode", "recover"]
    for field, path in asdict(artifacts).items():
        command.extend((f"--{field}", str(path)))
    assert harness.main(command) == 0
    report = json.loads(artifacts.report.read_text())
    repair = report.pop("reporting_repair")
    assert report == harness.build_report(
        rows, evidence, provenance, _canonical_public()
    )
    assert repair["command_line"][-len(command) :] == command
    assert repair["input_sha256"] == {
        f: harness.frozen24.sha256_file(getattr(artifacts, f))
        for f in ("results", "summary", "equivalence", "provenance")
    }
    assert report["provenance"] == provenance
    assert calls == [
        "encode_timeseries_v1",
        "encode_timeseries_v2",
        "encode_timeseries_compact_experimental",
        "encode_timeseries_v2",
        "encode_timeseries",
        "encode_timeseries_v2",
    ]
    assert {p: p.read_bytes() for p in before} == before
    persisted = json.loads(artifacts.report.read_text())
    assert artifacts.study.read_text() == harness.render_study(persisted)
    assert "Original corpus provenance is unchanged" in artifacts.study.read_text()
