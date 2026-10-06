from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs" / "external-qualification-protocol.md"
SELECTION = ROOT / "data" / "external-qualification" / "selection.tsv"


EXPECTED_IDS = {
    "Q01",
    "Q02",
    "Q03",
    "Q04",
    "Q05",
    "Q06",
    "Q07",
    "Q08",
}

EXPECTED_DOMAINS = {
    "building-appliance-energy",
    "road-traffic-volume",
    "urban-particulate-pollution",
    "urban-bicycle-demand",
    "mechanical-vibration",
    "financial-market-returns",
    "room-occupancy",
    "electrical-distribution-load",
}


def _rows() -> list[dict[str, str]]:
    with SELECTION.open(
        encoding="utf-8",
        newline="",
    ) as stream:
        return list(
            csv.DictReader(
                stream,
                delimiter="\t",
            )
        )


def test_protocol_is_frozen_before_measurement() -> None:
    text = PROTOCOL.read_text(encoding="utf-8")

    assert "PROTOCOL = FROZEN BEFORE MEASUREMENT" in text
    assert "CODEC RESULTS = NOT YET EXECUTED" in text
    assert (
        "NEW_DATASET_CODEC_EXECUTION_GATE=" "BLOCKED_UNTIL_SOURCE_MANIFEST_FREEZE"
    ) in text


def test_selection_has_exactly_eight_frozen_series() -> None:
    rows = _rows()

    assert len(rows) == 8

    assert {row["qualification_id"] for row in rows} == EXPECTED_IDS


def test_selection_covers_eight_declared_domains() -> None:
    rows = _rows()

    assert {row["domain"] for row in rows} == EXPECTED_DOMAINS


def test_every_source_has_doi_and_license() -> None:
    for row in _rows():
        assert row["source"] == "UCI"
        assert row["doi"].startswith("10.")
        assert row["license"] == "CC-BY-4.0"


def test_new_selection_is_frozen_before_execution() -> None:
    rows = _rows()

    new_rows = [row for row in rows if row["qualification_id"] >= "Q04"]

    assert len(new_rows) == 5

    assert {row["status"] for row in new_rows} == {"frozen-new"}
