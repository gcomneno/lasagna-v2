from __future__ import annotations

import csv
import hashlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RESULTS = ROOT / "docs" / "external-qualification-results.csv"

REPORT = ROOT / "docs" / "external-qualification.md"

CANONICAL = ROOT / "data" / "external-qualification" / "canonical-manifest.tsv"

EXPECTED_RESULTS_SHA256 = (
    "d5af5be4e474aa906d0000b6d40b94e1" "db208524ddff72d9e914c499c8fb31be"
)


def _results() -> list[dict[str, str]]:
    with RESULTS.open(
        encoding="utf-8",
        newline="",
    ) as stream:
        return list(csv.DictReader(stream))


def test_machine_readable_result_hash_is_frozen() -> None:
    actual = hashlib.sha256(RESULTS.read_bytes()).hexdigest()

    assert actual == EXPECTED_RESULTS_SHA256


def test_results_cover_eight_datasets_and_five_codecs() -> None:
    rows = _results()

    assert len(rows) == 40

    counts = Counter(row["dataset"] for row in rows)

    assert len(counts) == 8
    assert set(counts.values()) == {5}

    for dataset in counts:
        codecs = {row["codec"] for row in rows if row["dataset"] == dataset}

        assert codecs == {
            "raw",
            "gzip",
            "zstd",
            "gorilla",
            "lasagna",
        }


def test_one_lasagna_result_exists_per_dataset() -> None:
    rows = _results()

    lasagna = [row for row in rows if row["codec"] == "lasagna"]

    assert len(lasagna) == 8

    assert {row["configuration"] for row in lasagna} == {
        "adaptive_auto_varint",
    }


def test_result_sample_counts_match_canonical_manifest() -> None:
    rows = _results()

    with CANONICAL.open(
        encoding="utf-8",
        newline="",
    ) as stream:
        canonical = list(
            csv.DictReader(
                stream,
                delimiter="\t",
            )
        )

    expected = {row["canonical_file"]: int(row["samples"]) for row in canonical}

    for dataset, samples in expected.items():
        dataset_rows = [row for row in rows if row["dataset"] == dataset]

        assert dataset_rows

        assert {int(row["n_samples"]) for row in dataset_rows} == {
            samples,
        }


def test_failure_cases_are_retained() -> None:
    rows = _results()

    worse_than_best_lossless = 0

    for dataset in {row["dataset"] for row in rows}:
        dataset_rows = [row for row in rows if row["dataset"] == dataset]

        lasagna = next(row for row in dataset_rows if row["codec"] == "lasagna")

        best_lossless = min(
            int(row["encoded_bytes"])
            for row in dataset_rows
            if row["comparison_class"] == "lossless"
        )

        if int(lasagna["encoded_bytes"]) > best_lossless:
            worse_than_best_lossless += 1

    assert worse_than_best_lossless == 6


def test_report_records_interpretation_boundary() -> None:
    text = REPORT.read_text(encoding="utf-8")

    for expected in (
        "PRODUCTION_READINESS_GATE_13=PASS",
        "UNIVERSAL_SUPERIORITY_CLAIM=NO",
        "FAILURE_CASE_RETENTION_GATE=PASS",
        "NO_POST_HOC_SELECTION_GATE=PASS",
        EXPECTED_RESULTS_SHA256,
    ):
        assert expected in text
