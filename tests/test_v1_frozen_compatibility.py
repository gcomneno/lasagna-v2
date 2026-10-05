import csv
import struct
from pathlib import Path

from lasagna2 import core


CORPUS_ROOT = Path("data/m2-3")
MANIFEST = CORPUS_ROOT / "manifest.tsv"


def _reference_encoding_parameters(
    reference: bytes,
) -> tuple[int, str]:
    (
        _magic,
        _version,
        _flags,
        header_len,
        _n_points,
        n_segments,
        _reserved1,
        _reserved2,
    ) = core.FILE_HEADER_STRUCT.unpack_from(
        reference,
        0,
    )

    offset = core.FILE_HEADER_STRUCT.size + header_len
    segment_lengths: list[int] = []

    for _ in range(n_segments):
        (
            start_idx,
            end_idx,
            *_rest,
        ) = core.SEGMENT_ENTRY_STRUCT.unpack_from(
            reference,
            offset,
        )

        segment_lengths.append(
            end_idx - start_idx + 1
        )

        offset += core.SEGMENT_ENTRY_STRUCT.size

    assert segment_lengths

    segment_length = segment_lengths[0]

    assert all(
        length == segment_length
        for length in segment_lengths[:-1]
    )
    assert segment_lengths[-1] <= segment_length

    coding_type = (
        core.RESIDUAL_SECTION_HEADER_STRUCT.unpack_from(
            reference,
            offset,
        )[0]
    )

    residual_coding = {
        core.RESIDUAL_CODEC_RAW_INT32: "raw",
        core.RESIDUAL_CODEC_VARINT: "varint",
    }[coding_type]

    return segment_length, residual_coding


def test_frozen_v1_corpus_remains_decodable_and_byte_identical() -> None:
    with MANIFEST.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        rows = list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )

    assert len(rows) == 1575

    total_reference_bytes = 0

    for row in rows:
        raw = (
            CORPUS_ROOT
            / row["case_path"]
        ).read_bytes()

        assert len(raw) % 8 == 0

        values = list(
            struct.unpack(
                f"<{len(raw) // 8}d",
                raw,
            )
        )

        reference = (
            CORPUS_ROOT
            / row["reference_path"]
        ).read_bytes()

        decoded = core.decode_timeseries(
            reference
        )

        segment_length, residual_coding = (
            _reference_encoding_parameters(
                reference
            )
        )

        ts = core.TimeSeries(
            values=values,
            dt=decoded.dt,
            t0=decoded.t0,
            unit=decoded.unit,
        )

        reproduced = core.encode_timeseries_v1(
            ts,
            segment_length=segment_length,
            predictor=row["predictor"],
            residual_coding=residual_coding,
        )

        assert reproduced == reference, row["case_id"]

        total_reference_bytes += len(reference)

    assert total_reference_bytes == 1_875_150
