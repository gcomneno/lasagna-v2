import lasagna2.core as core


def test_format_versions_are_explicit() -> None:
    assert core.FORMAT_VERSION_V1 == 1
    assert core.FORMAT_VERSION_V2 == 2


def test_residual_codec_ids_are_explicit_and_distinct() -> None:
    assert core.RESIDUAL_CODEC_RAW_INT32 == 0
    assert core.RESIDUAL_CODEC_VARINT == 1
    assert core.RESIDUAL_CODEC_ZERO_RUN_VARINT == 2

    assert (
        len(
            {
                core.RESIDUAL_CODEC_RAW_INT32,
                core.RESIDUAL_CODEC_VARINT,
                core.RESIDUAL_CODEC_ZERO_RUN_VARINT,
            }
        )
        == 3
    )


def test_v1_segment_entry_size_is_unchanged() -> None:
    assert core.SEGMENT_ENTRY_STRUCT.size == 64


def test_v2_segment_entry_size_is_32_bytes() -> None:
    assert core.SEGMENT_ENTRY_V2_STRUCT.size == 32


def test_v2_segment_entry_roundtrip() -> None:
    sample = (
        0,
        79,
        1,
        3.95,
        0.1,
        0.0,
        1e-6,
        0.0,
    )

    packed = core.SEGMENT_ENTRY_V2_STRUCT.pack(*sample)
    decoded = core.SEGMENT_ENTRY_V2_STRUCT.unpack(packed)

    assert len(packed) == 32

    assert decoded[0] == 0
    assert decoded[1] == 79
    assert decoded[2] == 1

    assert abs(decoded[3] - 3.95) < 1e-6
    assert abs(decoded[4] - 0.1) < 1e-6
    assert abs(decoded[5] - 0.0) < 1e-6
    assert abs(decoded[6] - 1e-6) < 1e-10
    assert abs(decoded[7] - 0.0) < 1e-6
