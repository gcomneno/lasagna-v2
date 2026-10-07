from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import struct
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "benchmark_local_model_value.py"

SPEC = importlib.util.spec_from_file_location(
    "benchmark_local_model_value",
    MODULE_PATH,
)

assert SPEC is not None
assert SPEC.loader is not None

benchmark = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = benchmark
SPEC.loader.exec_module(benchmark)


def test_frozen_architecture_matrix() -> None:
    assert [architecture.architecture for architecture in benchmark.ARCHITECTURES] == [
        "A0",
        "A1",
        "A2",
        "A3",
        "A4",
    ]

    assert benchmark.C_Q_VALUES == (
        0.0625,
        0.125,
        0.25,
        0.5,
        1.0,
        2.0,
        4.0,
    )


def test_v2_byte_accounting_reconciles_exactly() -> None:
    values = [float(index) for index in range(96)]
    ts = benchmark.make_timeseries(values)

    encoded = benchmark.encode_for_architecture(
        ts,
        benchmark.architecture_by_id("A4"),
        0.125,
    )

    accounting = benchmark.v2_byte_accounting(encoded)

    assert accounting["global_and_context_bytes"] + accounting[
        "segment_metadata_bytes"
    ] + accounting["residual_block_metadata_bytes"] + accounting[
        "residual_payload_bytes"
    ] == len(
        encoded
    )
    assert accounting["structural_bytes"] == (
        len(encoded) - accounting["residual_payload_bytes"]
    )


def test_frozen_boundary_pairs_are_equal() -> None:
    values = [math.sin(index / 10.0) + index * 0.001 for index in range(256)]
    ts = benchmark.make_timeseries(values)

    encoded = {
        architecture.architecture: benchmark.encode_for_architecture(
            ts,
            architecture,
            0.125,
        )
        for architecture in benchmark.ARCHITECTURES
    }

    assert benchmark.segment_signature(encoded["A1"]) == (
        benchmark.segment_signature(encoded["A2"])
    )
    assert benchmark.segment_signature(encoded["A3"]) == (
        benchmark.segment_signature(encoded["A4"])
    )


def _row(
    architecture: str,
    c_q: float,
    rmse: float,
    encoded_bytes: int,
) -> dict[str, object]:
    return {
        "point_id": f"sample.csv:{architecture}:{c_q}",
        "dataset": "sample.csv",
        "evidence_group": "external",
        "architecture": architecture,
        "architecture_name": architecture,
        "C_Q": c_q,
        "rmse": rmse,
        "max_abs_error": rmse * 2,
        "encoded_bytes": encoded_bytes,
        "bits_per_sample": encoded_bytes * 8 / 100,
        "n_samples": 100,
    }


def test_primary_targets_use_common_architecture_neutral_range() -> None:
    rows = [
        _row("A0", 0.125, 1.0, 100),
        _row("A0", 0.5, 3.0, 80),
        _row("A1", 0.125, 2.0, 90),
        _row("A1", 0.5, 4.0, 70),
        _row("A4", 0.125, 1.5, 85),
        _row("A4", 0.5, 3.5, 60),
    ]

    targets = benchmark.build_primary_targets(rows)

    assert [target for target, _aliases in targets] == [
        2.0,
        3.0,
    ]


def test_envelope_selection_uses_minimum_rate_within_budget() -> None:
    rows = [
        _row("A4", 0.0625, 0.5, 120),
        _row("A4", 0.125, 0.8, 100),
        _row("A4", 0.25, 1.0, 90),
        _row("A4", 0.5, 1.5, 70),
    ]

    selected = benchmark.select_envelope_point(
        rows,
        1.0,
    )

    assert selected is not None
    assert selected["encoded_bytes"] == 90
    assert selected["C_Q"] == 0.25


@pytest.mark.parametrize(
    ("ratio", "expected"),
    [
        (0.94, "MATERIAL_WIN"),
        (0.95, "MATERIAL_WIN"),
        (1.00, "PRACTICAL_TIE"),
        (1.049, "PRACTICAL_TIE"),
        (1.05, "MATERIAL_LOSS"),
        (1.20, "MATERIAL_LOSS"),
    ],
)
def test_rate_ratio_classification(
    ratio: float,
    expected: str,
) -> None:
    assert benchmark.classify_rate_ratio(ratio) == expected


def test_a0_is_exactly_one_segment() -> None:
    values = [float(index) for index in range(257)]
    ts = benchmark.make_timeseries(values)

    encoded = benchmark.encode_for_architecture(
        ts,
        benchmark.architecture_by_id("A0"),
        0.125,
    )

    (
        _context,
        _n_points,
        segments,
        _coding_type,
    ) = benchmark.read_lsg2_metadata_and_segments(encoded)

    assert len(segments) == 1
    assert segments[0].start_idx == 0
    assert segments[0].end_idx == len(values) - 1


def test_v2_accounting_rejects_trailing_byte() -> None:
    values = [float(index) for index in range(64)]
    ts = benchmark.make_timeseries(values)

    encoded = benchmark.encode_for_architecture(
        ts,
        benchmark.architecture_by_id("A1"),
        0.125,
    )

    with pytest.raises(
        ValueError,
        match="stream length",
    ):
        benchmark.v2_byte_accounting(encoded + b"\x00")


def test_protocol_freeze_identity_is_exact() -> None:
    assert benchmark.PROTOCOL_FREEZE_COMMIT == (
        "198c8fd3434360c405d15a3e2a353dab039ca1ec"  # pragma: allowlist secret
    )


def test_all_frozen_controls_and_shared_context(monkeypatch) -> None:
    expected = [
        ("A0", "whole_linear", "fixed", "linear", None, None, None, None),
        ("A1", "fixed_linear", "fixed", "linear", 64, None, None, None),
        ("A2", "fixed_auto", "fixed", "auto", 64, None, None, None),
        ("A3", "adaptive_linear", "adaptive", "linear", None, 32, 128, 0.5),
        ("A4", "adaptive_auto", "adaptive", "auto", None, 32, 128, 0.5),
    ]
    assert [tuple(asdict(a).values()) for a in benchmark.ARCHITECTURES] == expected
    assert benchmark.Q_MIN == 1e-6
    assert benchmark.C_Q_VALUES == (0.0625, 0.125, 0.25, 0.5, 1, 2, 4)
    calls = []

    def capture(ts, **options):
        calls.append((benchmark.core.build_context_json(ts), options))
        return b"captured"

    monkeypatch.setattr(benchmark.core, "encode_timeseries_v2", capture)
    for architecture in benchmark.ARCHITECTURES:
        for c_q in benchmark.C_Q_VALUES:
            ts = benchmark.make_timeseries([float(i) for i in range(160)])
            assert (ts.dt, ts.t0, ts.unit) == (
                1.0,
                "1970-01-01T00:00:00Z",
                "local-model-value",
            )
            benchmark.encode_for_architecture(ts, architecture, c_q)
            options = calls[-1][1]
            assert options["Q_MIN"] == 1e-6
            assert options["C_Q"] == c_q
            assert options["residual_coding"] == "varint"
            assert options["predictor"] == architecture.predictor
            assert options["segment_mode"] == architecture.segment_mode
            assert options["segment_length"] == (
                160 if architecture.architecture == "A0" else 64
            )
            assert options["min_segment_length"] == 32
            assert options["max_segment_length"] == 128
            assert options["mse_threshold"] == 0.5
    assert len({context for context, _options in calls}) == 1


def test_timing_defaults_and_nondeterministic_rejection() -> None:
    args = benchmark.build_arg_parser().parse_args([])
    assert (args.warmup, args.repetitions) == (1, 3)
    outputs = iter([b"warmup", b"a", b"a", b"b"])
    with pytest.raises(ValueError, match="non-deterministic encoded bytes"):
        benchmark._measure_deterministic_encode(
            lambda: next(outputs),
            warmup=args.warmup,
            repetitions=args.repetitions,
        )


def test_v2_class_sizes_with_different_context_lengths_and_multiple_blocks() -> None:
    context_lengths = []
    for unit in ("x", "longer context with unicode é"):
        ts = benchmark.make_timeseries([math.sin(i / 3.0) for i in range(160)])
        ts.unit = unit
        encoded = benchmark.encode_for_architecture(
            ts,
            benchmark.architecture_by_id("A1"),
            0.125,
        )
        # Independent literal frozen layouts, not sizes imported from the codec.
        header = struct.unpack_from("<4sHHIIIII", encoded)
        assert header[1] == 2
        context_length, segments = header[3], header[5]
        context_lengths.append(context_length)
        assert segments == 3
        offset = 28 + context_length + 32 * segments + 16
        lengths = []
        for _ in range(segments):
            _segment_id, _samples, length = struct.unpack_from("<III", encoded, offset)
            lengths.append(length)
            offset += 12 + length
        assert offset == len(encoded)
        expected = {
            "global_and_context_bytes": 28 + context_length + 16,
            "segment_metadata_bytes": 32 * segments,
            "residual_block_metadata_bytes": 12 * segments,
            "residual_payload_bytes": sum(lengths),
            "structural_bytes": 28 + context_length + 16 + 44 * segments,
        }
        assert benchmark.v2_byte_accounting(encoded) == expected
        assert sum(
            expected[key]
            for key in (
                "global_and_context_bytes",
                "segment_metadata_bytes",
                "residual_block_metadata_bytes",
                "residual_payload_bytes",
            )
        ) == len(encoded)
    assert context_lengths[0] != context_lengths[1]


def test_target_full_precision_aliases_and_descriptive_exclusion() -> None:
    nearby = math.nextafter(1.0, math.inf)
    rows = [
        _row(a, q, d, 100)
        for a in ("A0", "A1", "A4")
        for q, d in ((0.0625, 0.0), (0.125, 1.0), (0.25, nearby), (4.0, 2.0))
    ]
    rows += [_row("A2", 0.5, 1.5, 1), _row("A3", 0.5, 1.7, 1)]
    targets = benchmark.build_primary_targets(rows)
    assert [d for d, _ in targets] == [0.0, 1.0, nearby, 2.0]
    assert targets[1][1] == tuple(
        sorted(
            row["point_id"]
            for row in rows
            if row["architecture"] in ("A0", "A1", "A4") and row["rmse"] == 1.0
        )
    )
    assert len(targets[1][1]) == 3
    assert targets == benchmark.build_primary_targets(list(reversed(rows)))


def test_target_closed_boundaries_disjoint_and_missing_architecture() -> None:
    rows = [
        _row("A0", 0.125, 1.0, 100),
        _row("A0", 4, 3.0, 80),
        _row("A1", 0.125, 2.0, 100),
        _row("A1", 4, 4.0, 80),
        _row("A4", 0.125, 1.5, 100),
        _row("A4", 4, 3.5, 80),
    ]
    assert [d for d, _ in benchmark.build_primary_targets(rows)] == [2.0, 3.0]
    for architecture in ("A0", "A1", "A4"):
        assert (
            benchmark.build_primary_targets(
                [row for row in rows if row["architecture"] != architecture]
            )
            == []
        )
    disjoint = [_row(a, 0.125, d, 100) for a, d in (("A0", 1), ("A1", 2), ("A4", 3))]
    assert benchmark.build_primary_targets(disjoint) == []


@pytest.mark.parametrize(
    "field,better,worse",
    [
        ("encoded_bytes", 99, 100),
        ("rmse", 0.5, 0.6),
        ("max_abs_error", 0.5, 0.6),
        ("C_Q", 0.125, 0.25),
        ("point_id", "a", "z"),
    ],
)
def test_envelope_each_tie_break_and_input_order(field, better, worse) -> None:
    first = _row("A4", 0.25, 0.8, 100)
    second = dict(first)
    first[field], second[field] = better, worse
    first["encode_time_ms"], second["encode_time_ms"] = 1000, 0
    first["decode_time_ms"], second["decode_time_ms"] = 1000, 0
    for rows in ([first, second], [second, first]):
        assert benchmark.select_envelope_point(rows, 1.0) is first
    assert benchmark.select_envelope_point([first, second], 0.1) is None


def test_baseline_architecture_final_tie_break() -> None:
    rows = [_row(a, 0.125, 1.0, 100) for a in ("A1", "A0", "A4")]
    matched, _summary = benchmark.match_dataset(rows)
    assert (
        next(row for row in matched if row["architecture"] == "A4")["selected_baseline"]
        == "A0"
    )


def test_integrated_envelope_baseline_family_and_integer_rate() -> None:
    rows = [
        _row("A0", 0.125, 0.5, 110),
        _row("A0", 4, 1.0, 105),
        _row("A1", 0.125, 0.5, 100),
        _row("A1", 4, 1.0, 100),
        _row("A4", 0.125, 0.5, 90),
        _row("A4", 4, 1.0, 95),
        _row("A2", 0.125, 0.5, 1),
        _row("A3", 0.125, 0.5, 1),
    ]
    for row in rows:
        row["bits_per_sample"] = -1  # matcher must derive rates from integer bytes
    matched, summary = benchmark.match_dataset(rows)
    a4_rows = [row for row in matched if row["architecture"] == "A4"]
    assert len(a4_rows) == 2
    assert all(row["selected_C_Q"] == 0.125 for row in a4_rows)
    assert all(row["selected_baseline"] == "A1" for row in a4_rows)
    assert all(row["rate_ratio"] == 0.9 for row in a4_rows)
    assert all(row["selected_bits_per_sample"] == 7.2 for row in a4_rows)
    assert summary["complete_primary_coverage"] == 2
    assert summary["coverage_status"] == "COMPLETE"
    primary_only = [row for row in rows if row["architecture"] in ("A0", "A1", "A4")]
    assert benchmark.match_dataset(primary_only)[1] == summary


@pytest.mark.parametrize("missing", ["A0", "A1", "A4"])
def test_incomplete_target_never_enters_primary_statistics(
    monkeypatch, missing
) -> None:
    # Exercise the defensive invariant even though normal target construction
    # guarantees eligibility from the primary architectures' common interval.
    monkeypatch.setattr(
        benchmark,
        "build_primary_targets",
        lambda _rows: [(1.0, ()), (2.0, ())],
    )
    rows = [
        _row(a, 0.125, 2.0 if a == missing else 0.5, 90 if a == "A4" else 100)
        for a in ("A0", "A1", "A4")
    ]
    matched, summary = benchmark.match_dataset(rows)
    first = [row for row in matched if row["target_rmse"] == 1.0]
    assert len(first) == 5
    assert (
        next(row for row in first if row["architecture"] == missing)["match_status"]
        == "INELIGIBLE"
    )
    assert all(row["rate_ratio"] == row["classification"] == "" for row in first)
    assert (
        next(row for row in first if row["architecture"] == "A4")["selected_baseline"]
        == ""
    )
    assert summary["coverage_status"] == "INSUFFICIENT_COVERAGE"
    assert summary["primary_target_count"] == 2
    assert summary["complete_primary_coverage"] == 1
    assert summary[f"{missing}_covered"] == 1
    assert all(summary[f"{a}_covered"] == 2 for a in ("A0", "A1", "A4") if a != missing)
    assert summary["material_wins"] == 1
    assert summary["practical_ties"] == summary["material_losses"] == 0
    assert (
        summary["median_rate_ratio"]
        == summary["best_rate_ratio"]
        == summary["worst_rate_ratio"]
        == 0.9
    )
    assert summary["non_loss_fraction"] == 1.0


def test_dataset_summary_even_median_counts_and_non_losses() -> None:
    rows = []
    for q, distortion, base, full in (
        (0.125, 1, 1000, 900),
        (0.25, 2, 800, 800),
        (0.5, 3, 600, 660),
        (1.0, 4, 500, 600),
    ):
        rows.extend([_row("A0", q, distortion, base), _row("A1", q, distortion, base)])
        rows.append(_row("A4", q, distortion, full))
    _matched, summary = benchmark.match_dataset(rows)
    assert summary["primary_target_count"] == summary["complete_primary_coverage"] == 4
    assert summary["material_wins"] == 1
    assert summary["practical_ties"] == 1
    assert summary["material_losses"] == 2
    assert summary["non_loss_fraction"] == 0.5
    assert summary["median_rate_ratio"] == (1.0 + 1.1) / 2
    assert summary["best_rate_ratio"] == 0.9
    assert summary["worst_rate_ratio"] == 1.2


def _summaries(medians=None):
    medians = [0.9] * 8 if medians is None else medians
    return [
        {
            "dataset": path.name,
            "evidence_group": "external",
            "coverage_status": "COMPLETE",
            "primary_target_count": 4,
            "A0_covered": 4,
            "A1_covered": 4,
            "A4_covered": 4,
            "complete_primary_coverage": 4,
            "median_rate_ratio": median,
            "material_wins": 3,
            "practical_ties": 0,
            "material_losses": 1,
            "non_loss_fraction": 0.75,
        }
        for path, median in zip(benchmark.EXTERNAL_DATASETS, medians)
    ]


def _decision(summaries):
    return benchmark.external_decision(summaries, byte_accounting_verified=True)


@pytest.mark.parametrize("count", [7, 9])
def test_external_exact_dataset_count(count) -> None:
    rows = _summaries()
    rows = rows[:count] if count == 7 else rows + [dict(rows[0])]
    assert _decision(rows)["reason"] == "EXTERNAL_DATASET_COUNT"


def test_external_internal_exclusion_identity_and_byte_accounting_gate() -> None:
    rows = _summaries()
    internal = {**rows[0], "evidence_group": "internal", "median_rate_ratio": math.nan}
    assert _decision(rows + [internal]) == _decision(rows)
    assert _decision(rows)["claim_supported"]
    assert not benchmark.external_decision(rows)["claim_supported"]
    assert not benchmark.external_decision(rows)["gate_5"]
    rows[-1]["dataset"] = rows[0]["dataset"]
    assert _decision(rows)["reason"] == "EXTERNAL_DATASET_IDENTITY"


@pytest.mark.parametrize(
    "field,value",
    [
        ("coverage_status", "INSUFFICIENT_COVERAGE"),
        ("complete_primary_coverage", 3),
        ("primary_target_count", 0),
        ("A0_covered", 3),
        ("A1_covered", 3),
        ("A4_covered", 3),
    ],
)
def test_external_rejects_incomplete_coverage(field, value) -> None:
    rows = _summaries()
    rows[0][field] = value
    assert _decision(rows)["reason"] == "INSUFFICIENT_COVERAGE"


@pytest.mark.parametrize(
    "median", [math.nan, math.inf, -math.inf, 0, -1, "", None, "invalid"]
)
def test_external_rejects_invalid_median(median) -> None:
    rows = _summaries()
    rows[0]["median_rate_ratio"] = median
    assert _decision(rows)["reason"] == "INVALID_DATASET_MEDIAN"


def test_external_gate_boundaries_and_geometric_mean() -> None:
    rows = _summaries([0.8] * 6 + [1.0, 1.05])
    decision = _decision(rows)
    assert decision["claim_supported"]
    assert decision["dataset_median_win_count"] == 6
    assert decision["dataset_median_loss_count"] == 1
    assert decision["pooled_non_loss_fraction"] == 0.75
    assert decision["geometric_mean_dataset_medians"] == math.exp(
        sum(math.log(value) for value in [0.8] * 6 + [1.0, 1.05]) / 8
    )
    rows[6]["median_rate_ratio"] = 1.05
    assert not _decision(rows)["gate_3"]
    rows = _summaries([0.95] * 8)
    assert _decision(rows)["gate_1"]
    assert _decision(rows)["gate_2"] == (
        math.exp(sum(math.log(0.95) for _ in range(8)) / 8) <= 0.95
    )
    assert not _decision(_summaries([0.96] * 8))["gate_2"]
    assert not _decision(_summaries([0.8] * 5 + [1.0] * 3))["gate_1"]


def test_external_pooled_denominator_uses_unequal_unique_target_counts() -> None:
    rows = _summaries()
    for row in rows:
        row.update(
            {
                "primary_target_count": 1,
                "complete_primary_coverage": 1,
                "A0_covered": 1,
                "A1_covered": 1,
                "A4_covered": 1,
                "material_wins": 1,
                "practical_ties": 0,
                "material_losses": 0,
                "non_loss_fraction": 1,
            }
        )
    rows[0].update(
        {
            "primary_target_count": 9,
            "complete_primary_coverage": 9,
            "A0_covered": 9,
            "A1_covered": 9,
            "A4_covered": 9,
            "material_wins": 5,
            "material_losses": 4,
            "non_loss_fraction": 5 / 9,
        }
    )
    assert _decision(rows)["pooled_non_loss_fraction"] == (5 + 7) / (9 + 7)
    assert _decision(rows)["gate_4"]
    rows[0].update({"material_wins": 4, "material_losses": 5})
    assert not _decision(rows)["gate_4"]


def test_pareto_dominance_equal_coordinates_and_architecture_identity() -> None:
    rows = [
        _row("A0", 0.125, 1, 100),
        _row("A1", 0.125, 1, 100),  # equal coordinates retain both IDs
        _row("A2", 0.125, 2, 100),  # strictly worse RMSE
        _row("A3", 0.125, 1, 110),  # strictly worse rate
        _row("A4", 0.125, 0.5, 120),  # rate/distortion tradeoff
    ]
    for i, row in enumerate(rows):
        row["encode_time_ms"] = 1000 - i
    expected = [rows[0], rows[1], rows[4]]
    assert benchmark.pareto_frontier(rows) == expected
    assert benchmark.pareto_frontier(list(reversed(rows))) == expected
    report = benchmark.pareto_report(rows)
    assert [point["architecture"] for point in report["pooled"]] == ["A0", "A1", "A4"]
    assert [point["point_id"] for point in report["pooled"]] == [
        row["point_id"] for row in expected
    ]
    assert list(report["per_architecture"]) == ["A0", "A1", "A2", "A3", "A4"]
    assert report == benchmark.pareto_report(list(reversed(rows)))


def test_descriptive_pairs_use_envelopes_and_leave_primary_gates_unchanged() -> None:
    rows = [
        _row(a, q, d, rate)
        for a, rate in (
            ("A0", 100),
            ("A1", 100),
            ("A2", 80),
            ("A3", 70),
            ("A4", 60),
        )
        for q, d in ((0.125, 0.5), (4.0, 1.0))
    ]
    before = benchmark.match_dataset(rows)[1]
    comparisons = benchmark.descriptive_comparisons(rows)
    assert [pair["comparison"] for pair in comparisons] == [
        "A2/A1",
        "A3/A1",
        "A4/A2",
        "A4/A3",
    ]
    for pair, expected_ratio in zip(comparisons, (0.8, 0.7, 0.75, 60 / 70)):
        assert pair["interpretation"] == "DESCRIPTIVE_ONLY"
        assert pair["coverage_status"] == "COMPLETE"
        assert len(pair["observations"]) == 2
        for observation in pair["observations"]:
            assert observation["rate_ratio"] == expected_ratio
            assert observation["numerator"]["C_Q"] == 0.125
            assert observation["denominator"]["C_Q"] == 0.125
    assert before == benchmark.match_dataset(rows)[1]
    primary = [row for row in rows if row["architecture"] in ("A0", "A1", "A4")]
    assert before == benchmark.match_dataset(primary)[1]
    assert comparisons == benchmark.descriptive_comparisons(list(reversed(rows)))
    assert all(
        pair["coverage_status"] == "INSUFFICIENT_COVERAGE"
        for pair in benchmark.descriptive_comparisons([])
    )


def test_execution_order_is_exact_cq_major_architecture_minor() -> None:
    corpus = [("internal", Path("first.csv")), ("external", Path("second.csv"))]
    order = benchmark.execution_order(corpus, 5, 2)
    assert [
        (item["dataset_path"], item["C_Q"], item["architecture"]) for item in order
    ] == [
        (str(path), q, a.architecture)
        for _group, path in corpus
        for q in benchmark.C_Q_VALUES
        for a in benchmark.ARCHITECTURES
    ]
    assert order[0]["operations"] == [
        {"operation": "encode_warmup", "calls": 2},
        {"operation": "encode_timed", "calls": 5},
        {"operation": "decode_warmup", "calls": 2},
        {"operation": "decode_timed", "calls": 5},
        {"operation": "encode_for_boundary_check", "calls": 1},
    ]
    assert order[4]["boundary_checks_after_point"] == ["A1=A2", "A3=A4"]
    assert order[0]["boundary_checks_after_point"] == []


def test_provenance_required_fields_hashes_and_actual_timing(
    tmp_path, monkeypatch
) -> None:
    dataset = tmp_path / "input.csv"
    dataset.write_bytes(b"value\n1\n2\n")
    corpus = [("external", dataset)]
    monkeypatch.setattr(
        benchmark, "verify_protocol_freeze", lambda: benchmark.PROTOCOL_FREEZE_COMMIT
    )
    monkeypatch.setattr(
        benchmark,
        "git_output",
        lambda *args: "current-head" if args[0] == "rev-parse" else " M tracked",
    )
    first = benchmark.provenance(
        corpus,
        repetitions=5,
        warmup=2,
        command_line=["python", "tool", "--warmup", "2"],
    )
    second = benchmark.provenance(
        corpus,
        repetitions=5,
        warmup=2,
        command_line=["python", "tool", "--warmup", "2"],
    )
    assert first == second
    assert set(first) >= {
        "protocol_freeze_commit",
        "verified_protocol_freeze_commit",
        "implementation_commit",
        "codec_source_identity",
        "dirty_tree",
        "dataset_sha256",
        "architecture_matrix",
        "frozen_controls",
        "timeseries_context",
        "repetitions",
        "warmup",
        "command_line",
        "execution_order",
        "python_version",
        "platform",
        "cpu_identity",
        "dependency_versions",
    }
    assert first["implementation_commit"] == "current-head"
    assert first["dirty_tree"] is True
    assert (first["repetitions"], first["warmup"]) == (5, 2)
    assert first["frozen_controls"]["repetitions"] == 3
    assert first["frozen_controls"]["warmup"] == 1
    assert (
        first["dataset_sha256"][str(dataset)]
        == hashlib.sha256(dataset.read_bytes()).hexdigest()
    )
    source = Path(benchmark.core.__file__).resolve()
    assert first["codec_source_identity"] == {
        "path": source.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }
    assert first["timeseries_context"] == {
        "dt": 1.0,
        "t0": "1970-01-01T00:00:00Z",
        "unit": "local-model-value",
    }
    assert first["dependency_versions"]["project"] == {
        "name": "lasagna-v2",
        "version": "0.3.0",
    }
    assert "gorillacompression" in first["dependency_versions"]
    path = tmp_path / "provenance.json"
    benchmark.write_json(first, path)
    assert json.loads(path.read_text()) == first


@pytest.mark.parametrize("dirty", ["", "?? untracked"])
def test_provenance_records_actual_dirty_state(tmp_path, monkeypatch, dirty) -> None:
    dataset = tmp_path / "input.csv"
    dataset.write_bytes(b"value\n1\n")
    monkeypatch.setattr(
        benchmark, "verify_protocol_freeze", lambda: benchmark.PROTOCOL_FREEZE_COMMIT
    )
    monkeypatch.setattr(
        benchmark,
        "git_output",
        lambda *args: "head" if args[0] == "rev-parse" else dirty,
    )
    value = benchmark.provenance(
        [("internal", dataset)], repetitions=3, warmup=1, command_line=["tool"]
    )
    assert value["dirty_tree"] is bool(dirty)


def test_cpu_linux_model_and_deterministic_fallback(monkeypatch) -> None:
    monkeypatch.setattr(benchmark.platform, "system", lambda: "Linux")
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda self, **kwargs: "processor : 0\nmodel name : Test CPU 123\n",
    )
    assert benchmark.cpu_identity() == "Test CPU 123"
    monkeypatch.setattr(Path, "read_text", lambda self, **kwargs: "")
    monkeypatch.setattr(benchmark.platform, "processor", lambda: "")
    monkeypatch.setattr(benchmark.platform, "machine", lambda: "test-machine")
    assert benchmark.cpu_identity() == "test-machine"


def test_protocol_freeze_binary_content_validation(monkeypatch) -> None:
    current = benchmark.PROTOCOL_PATH.read_bytes()
    monkeypatch.setattr(
        benchmark, "git_output", lambda *args: benchmark.PROTOCOL_FREEZE_COMMIT
    )
    monkeypatch.setattr(
        benchmark.subprocess, "check_output", lambda *args, **kwargs: current
    )
    assert benchmark.verify_protocol_freeze() == benchmark.PROTOCOL_FREEZE_COMMIT
    monkeypatch.setattr(
        benchmark.subprocess, "check_output", lambda *args, **kwargs: current + b"\n"
    )
    with pytest.raises(ValueError, match="content mismatch"):
        benchmark.verify_protocol_freeze()


def test_main_persists_provenance_before_first_evaluation(
    tmp_path, monkeypatch
) -> None:
    dataset = tmp_path / "input.csv"
    dataset.write_bytes(b"value\n1\n2\n")
    artifact = tmp_path / "provenance.json"
    monkeypatch.setattr(benchmark, "INTERNAL_DATASETS", (dataset,))
    monkeypatch.setattr(benchmark, "EXTERNAL_DATASETS", ())
    monkeypatch.setattr(benchmark, "PROVENANCE_PATH", artifact)
    monkeypatch.setattr(
        sys,
        "argv",
        ["benchmark_local_model_value.py", "--warmup", "2", "--repetitions", "5"],
    )
    monkeypatch.setattr(sys, "orig_argv", [sys.executable, "-B", *sys.argv])
    monkeypatch.setattr(
        benchmark, "verify_protocol_freeze", lambda: benchmark.PROTOCOL_FREEZE_COMMIT
    )
    calls = []

    def first_evaluation(path, group, **timing):
        saved = json.loads(artifact.read_text())
        assert saved["dataset_sha256"][str(path)] == benchmark.sha256_file(path)
        assert saved["execution_order"][0]["dataset_path"] == str(path)
        assert saved["command_line"] == [sys.executable, "-B", *sys.argv]
        assert (saved["repetitions"], saved["warmup"]) == (5, 2)
        assert timing == {"repetitions": 5, "warmup": 2}
        calls.append((path, group))
        raise RuntimeError("stop before any evaluation point")

    monkeypatch.setattr(benchmark, "evaluate_dataset", first_evaluation)
    with pytest.raises(RuntimeError, match="stop before"):
        benchmark.main()
    assert calls == [(dataset, "internal")]


@pytest.mark.parametrize("failure", ["mismatch", "capture", "persist"])
def test_provenance_failures_prevent_any_evaluation(
    tmp_path, monkeypatch, failure
) -> None:
    dataset = tmp_path / "input.csv"
    dataset.write_bytes(b"value\n1\n")
    monkeypatch.setattr(benchmark, "INTERNAL_DATASETS", (dataset,))
    monkeypatch.setattr(benchmark, "EXTERNAL_DATASETS", ())
    monkeypatch.setattr(benchmark, "PROVENANCE_PATH", tmp_path / "provenance.json")
    monkeypatch.setattr(sys, "argv", ["benchmark_local_model_value.py"])
    called = []
    monkeypatch.setattr(
        benchmark, "evaluate_dataset", lambda *args, **kwargs: called.append("dataset")
    )
    monkeypatch.setattr(
        benchmark, "evaluate_point", lambda *args, **kwargs: called.append("point")
    )
    if failure == "mismatch":
        monkeypatch.setattr(
            benchmark.subprocess,
            "check_output",
            lambda *args, **kwargs: b"mismatched protocol",
        )
        monkeypatch.setattr(
            benchmark, "git_output", lambda *args: benchmark.PROTOCOL_FREEZE_COMMIT
        )
    else:
        monkeypatch.setattr(
            benchmark,
            "verify_protocol_freeze",
            lambda: benchmark.PROTOCOL_FREEZE_COMMIT,
        )

        def fail(*args, **kwargs):
            raise OSError("provenance unavailable")

        monkeypatch.setattr(
            benchmark,
            "dependency_versions" if failure == "capture" else "write_json",
            fail,
        )
    with pytest.raises((ValueError, OSError), match="mismatch|unavailable"):
        benchmark.main()
    assert called == []


@pytest.mark.parametrize(
    "status,median,outcome",
    [
        ("COMPLETE", 0.95, "FAVORABLE"),
        ("COMPLETE", 1.0, "NEUTRAL"),
        ("COMPLETE", 1.05, "UNFAVORABLE"),
        ("INSUFFICIENT_COVERAGE", 0.5, "INSUFFICIENT_COVERAGE"),
    ],
)
def test_study_dataset_outcomes_preserve_negative_results(
    status, median, outcome
) -> None:
    assert (
        benchmark.dataset_outcome(
            {
                "coverage_status": status,
                "median_rate_ratio": median,
            }
        )
        == outcome
    )


def test_study_renderer_is_deterministic_and_does_not_evaluate(monkeypatch) -> None:
    def forbidden(*args, **kwargs):
        pytest.fail("Study rendering must not evaluate points")

    monkeypatch.setattr(benchmark, "evaluate_dataset", forbidden)
    monkeypatch.setattr(benchmark, "evaluate_point", forbidden)
    report = {
        "execution_completed": True,
        "primary_claim_supported": False,
        "outcome": "MIXED",
        "frozen_gates": {gate: False for gate in benchmark.REPRODUCIBILITY_GATES},
        "decision": {"claim_supported": False, "gate_0": False, "gate_5": True},
        "datasets": [
            {
                "summary": {"coverage_status": "INSUFFICIENT_COVERAGE"},
                "outcome": "INSUFFICIENT_COVERAGE",
                "pareto": {"pooled": []},
                "descriptive_comparisons": [],
            }
        ],
        "provenance": {"dirty_tree": True},
    }
    rendered = benchmark.render_study(report)
    assert rendered == benchmark.render_study(report)
    assert "Primary claim supported: False" in rendered
    assert "INSUFFICIENT_COVERAGE" in rendered
    assert "pareto" in rendered and "descriptive_comparisons" in rendered
    assert "dirty_tree" in rendered
    assert all(gate in rendered for gate in benchmark.REPRODUCIBILITY_GATES)
    with pytest.raises(ValueError, match="completed execution evidence"):
        benchmark.render_study({**report, "execution_completed": False})


def test_report_complete_evidence_and_internal_coverage_do_not_change_primary_claim() -> (
    None
):
    corpus = [("internal", path) for path in benchmark.INTERNAL_DATASETS] + [
        ("external", path) for path in benchmark.EXTERNAL_DATASETS
    ]
    rows, matched, summaries = [], [], []
    for group, path in corpus:
        dataset_rows = []
        for q in benchmark.C_Q_VALUES:
            for architecture in benchmark.ARCHITECTURES:
                encoded = 300 if architecture.architecture != "A4" else 270
                row = _row(architecture.architecture, q, q, encoded)
                row.update(
                    {
                        "dataset": path.name,
                        "evidence_group": group,
                        "point_id": benchmark.point_id(
                            path.name, architecture.architecture, q
                        ),
                        "Q_MIN": 1e-6,
                        "segment_count": 3,
                        "global_and_context_bytes": 50,
                        "segment_metadata_bytes": 96,
                        "residual_block_metadata_bytes": 36,
                        "residual_payload_bytes": encoded - 182,
                        "structural_bytes": 182,
                        "encode_time_ms": 1.0,
                        "decode_time_ms": 1.0,
                    }
                )
                dataset_rows.append(row)
        dataset_matched, summary = benchmark.match_dataset(dataset_rows)
        rows.extend(dataset_rows)
        matched.extend(dataset_matched)
        summaries.append(summary)
    provenance = {
        "execution_order": benchmark.execution_order(corpus, 3, 1),
        "verified_protocol_freeze_commit": benchmark.PROTOCOL_FREEZE_COMMIT,
        "repetitions": 3,
        "warmup": 1,
    }
    report = benchmark.build_report(
        rows, matched, summaries, provenance, execution_completed=True
    )
    assert report["primary_claim_supported"]
    assert report["outcome"] == "FAVORABLE"
    assert all(report["frozen_gates"].values())
    assert set(report["decision"]) >= {f"gate_{i}" for i in range(6)}
    assert len(report["datasets"]) == 11
    summaries[0] = {**summaries[0], "coverage_status": "INSUFFICIENT_COVERAGE"}
    report = benchmark.build_report(
        rows, matched, summaries, provenance, execution_completed=True
    )
    assert report["primary_claim_supported"]  # internal evidence is secondary
    assert report["datasets"][0]["outcome"] == "INSUFFICIENT_COVERAGE"
    altered = [dict(row) for row in rows]
    altered[0]["residual_payload_bytes"] += 1
    report = benchmark.build_report(
        altered, matched, summaries, provenance, execution_completed=True
    )
    assert not report["primary_claim_supported"]
    assert not report["decision"]["gate_5"]
    assert not report["frozen_gates"]["EXACT_BYTE_ACCOUNTING_GATE"]
