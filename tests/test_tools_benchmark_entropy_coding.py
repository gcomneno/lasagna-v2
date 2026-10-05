import importlib.util
import sys
from pathlib import Path

import pytest


PATH = Path("tools/benchmark_entropy_coding.py")

SPEC = importlib.util.spec_from_file_location(
    "benchmark_entropy_coding_test",
    PATH,
)

assert SPEC is not None
assert SPEC.loader is not None

entropy = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = entropy
SPEC.loader.exec_module(entropy)


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"\x00",
        b"\x00" * 32,
        bytes(range(32)),
        b"banana banana banana",
        bytes(value % 7 for value in range(128)),
    ],
)
def test_huffman_roundtrip(
    payload: bytes,
) -> None:
    encoded = entropy.encode_huffman_sparse(payload)

    assert entropy.decode_huffman_sparse(encoded) == payload


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"\x00",
        b"\x00" * 32,
        bytes(range(32)),
        b"banana banana banana",
        bytes(value % 7 for value in range(128)),
    ],
)
def test_deflate_roundtrip(
    payload: bytes,
) -> None:
    encoded = entropy.encode_deflate_raw(payload)

    assert entropy.decode_deflate_raw(encoded) == payload


def test_huffman_one_symbol_is_deterministic() -> None:
    payload = b"\x07" * 32

    first = entropy.encode_huffman_sparse(payload)

    second = entropy.encode_huffman_sparse(payload)

    assert first == second

    (
        original_length,
        bit_length,
        symbol_count,
    ) = entropy.HUFFMAN_FIXED_HEADER.unpack_from(
        first,
        0,
    )

    assert original_length == 32
    assert bit_length == 32
    assert symbol_count == 1


def test_huffman_overhead_is_fully_framed() -> None:
    payload = bytes(
        [
            0,
            1,
            0,
            1,
        ]
    )

    encoded = entropy.encode_huffman_sparse(payload)

    (
        _original_length,
        bit_length,
        symbol_count,
    ) = entropy.HUFFMAN_FIXED_HEADER.unpack_from(
        encoded,
        0,
    )

    expected = 6 + 2 * symbol_count + (bit_length + 7) // 8

    assert len(encoded) == expected


def test_deflate_overhead_is_fully_framed() -> None:
    payload = b"\x00" * 32

    encoded = entropy.encode_deflate_raw(payload)

    (
        original_length,
        compressed_length,
    ) = entropy.DEFLATE_FIXED_HEADER.unpack_from(
        encoded,
        0,
    )

    assert original_length == len(payload)

    assert len(encoded) == (4 + compressed_length)


def test_bucket_boundaries() -> None:
    assert entropy.bucket_name(1) == "1..16"
    assert entropy.bucket_name(16) == "1..16"
    assert entropy.bucket_name(17) == "17..32"
    assert entropy.bucket_name(32) == "17..32"
    assert entropy.bucket_name(33) == "33..64"
    assert entropy.bucket_name(64) == "33..64"
    assert entropy.bucket_name(65) == "65..128"
    assert entropy.bucket_name(128) == "65..128"
    assert entropy.bucket_name(129) == ">128"
