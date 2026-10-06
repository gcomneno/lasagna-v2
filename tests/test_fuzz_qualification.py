from __future__ import annotations

import sys
from pathlib import Path

import pytest

from lasagna2 import core

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import fuzz_qualification as fuzz  # noqa: E402


def test_seed_corpus_contains_v1_and_v2_codecs() -> None:
    names = {case.name for case in fuzz.build_seed_corpus()}

    assert names == {
        "v1-raw.lsg2",
        "v1-varint.lsg2",
        "v2-raw.lsg2",
        "v2-varint.lsg2",
        "v2-zero-run.lsg2",
    }


def test_seed_corpus_is_deterministic(
    tmp_path: Path,
) -> None:
    left = tmp_path / "left"
    right = tmp_path / "right"

    fuzz.write_seed_corpus(left)
    fuzz.write_seed_corpus(right)

    assert {path.name: path.read_bytes() for path in left.iterdir()} == {
        path.name: path.read_bytes() for path in right.iterdir()
    }


@pytest.mark.parametrize(
    "case",
    fuzz.build_seed_corpus(),
    ids=lambda case: case.name,
)
def test_seed_corpus_decodes(case) -> None:
    decoded = core.decode_timeseries(case.data)
    assert decoded.values


def test_structured_mutations_cover_required_wire_regions() -> None:
    case = next(
        case for case in fuzz.build_seed_corpus() if case.name == "v2-zero-run.lsg2"
    )

    names = {name for name, _payload in fuzz.structured_mutations(case.data)}

    assert {
        "bad-magic",
        "unknown-version",
        "context-over-limit",
        "points-over-limit",
        "segments-over-limit",
        "context-invalid-utf8",
        "context-deep-json",
        "segment-start-max",
        "segment-end-max",
        "segment-predictor-max",
        "residual-codec-max",
        "block-segid-max",
        "block-seglen-max",
        "block-bytelen-over-limit",
        "payload-high-bit-flip",
        "payload-tail-flip",
    } <= names


def test_small_campaign_has_no_unexpected_crash(
    tmp_path: Path,
) -> None:
    corpus = tmp_path / "corpus"
    fuzz.write_seed_corpus(corpus)

    result = fuzz.run_campaign(
        corpus_dir=corpus,
        iterations=250,
        seed=fuzz.DEFAULT_SEED,
        crash_dir=tmp_path / "crashes",
    )

    assert result["total_crashes"] == 0
    assert result["total_cases"] >= 750


def test_crash_artifact_is_replayable_metadata(
    tmp_path: Path,
) -> None:
    crash = fuzz.UnexpectedCrash(
        target="decoder:test",
        iteration=7,
        seed=123,
        payload=b"abc",
        exc=RuntimeError("boom"),
    )

    metadata_path = fuzz.write_crash_artifact(
        tmp_path,
        crash,
    )

    assert metadata_path.exists()
    assert metadata_path.with_suffix(".bin").exists()


@pytest.mark.parametrize(
    ("target", "decoder"),
    [
        (
            "residual-varint",
            core.decode_int_list_varint,
        ),
        (
            "residual-zero-run",
            core.decode_int_list_zero_run_varint,
        ),
    ],
)
def test_residual_target_runs_without_unexpected_crash(
    target,
    decoder,
) -> None:
    stats = fuzz.run_residual_target(
        rng=__import__("random").Random(123),
        iterations=250,
        seed=123,
        name=target,
        decoder=decoder,
    )

    assert stats.crashes == 0
    assert stats.cases == 250
