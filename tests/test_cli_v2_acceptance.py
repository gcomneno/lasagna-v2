from pathlib import Path

import lasagna2
import pytest
from lasagna2 import cli, core


def _encode_args(
    input_path: Path,
    output_path: Path,
    *extra: str,
) -> list[str]:
    return [
        "encode",
        str(input_path),
        str(output_path),
        "--dt",
        "1",
        "--t0",
        "1970-01-01T00:00:00Z",
        "--unit",
        "test",
        "--segment-mode",
        "fixed",
        "--segment-length",
        "64",
        "--predictor",
        "linear",
        "--residual-coding",
        "varint",
        *extra,
    ]


def _write_linear_csv(
    path: Path,
) -> list[float]:
    values = [
        1.0 + 0.5 * index
        for index in range(64)
    ]

    path.write_text(
        "".join(
            f"{value:.17g}\n"
            for value in values
        ),
        encoding="utf-8",
    )

    return values


def _read_csv_values(
    path: Path,
) -> list[float]:
    return [
        float(line)
        for line in path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]


def _version(data: bytes) -> int:
    return (
        core.FILE_HEADER_STRUCT
        .unpack_from(data, 0)[1]
    )


def test_encode_parser_defaults_to_v1() -> None:
    parser = cli.build_arg_parser()

    args = parser.parse_args(
        [
            "encode",
            "input.csv",
            "output.lsg2",
            "--dt",
            "1",
            "--t0",
            "0",
            "--unit",
            "u",
        ]
    )

    assert args.format_version == (
        core.FORMAT_VERSION_V1
    )


def test_encode_parser_accepts_explicit_v2() -> None:
    parser = cli.build_arg_parser()

    args = parser.parse_args(
        [
            "encode",
            "input.csv",
            "output.lsg2",
            "--dt",
            "1",
            "--t0",
            "0",
            "--unit",
            "u",
            "--format-version",
            "2",
        ]
    )

    assert args.format_version == (
        core.FORMAT_VERSION_V2
    )


def test_encode_parser_rejects_unknown_version() -> None:
    parser = cli.build_arg_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "encode",
                "input.csv",
                "output.lsg2",
                "--dt",
                "1",
                "--t0",
                "0",
                "--unit",
                "u",
                "--format-version",
                "3",
            ]
        )


def test_public_api_exports_v2_encoder() -> None:
    assert (
        lasagna2.encode_timeseries_v2
        is core.encode_timeseries_v2
    )

    assert "encode_timeseries_v2" in (
        lasagna2.__all__
    )

    assert (
        lasagna2.encode_timeseries
        is core.encode_timeseries
    )


def test_cli_v1_default_and_explicit_v1_are_identical(
    tmp_path: Path,
) -> None:
    source = tmp_path / "input.csv"
    default_output = (
        tmp_path / "default.lsg2"
    )
    explicit_output = (
        tmp_path / "explicit-v1.lsg2"
    )

    _write_linear_csv(source)

    cli.main(
        _encode_args(
            source,
            default_output,
        )
    )

    cli.main(
        _encode_args(
            source,
            explicit_output,
            "--format-version",
            "1",
        )
    )

    default_bytes = (
        default_output.read_bytes()
    )

    explicit_bytes = (
        explicit_output.read_bytes()
    )

    assert (
        default_bytes
        == explicit_bytes
    )

    assert _version(
        default_bytes
    ) == core.FORMAT_VERSION_V1


def test_cli_v2_encode_decode_and_info(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "input.csv"
    encoded = tmp_path / "output-v2.lsg2"
    decoded = tmp_path / "decoded.csv"

    original = _write_linear_csv(
        source
    )

    cli.main(
        _encode_args(
            source,
            encoded,
            "--format-version",
            "2",
        )
    )

    data = encoded.read_bytes()

    assert _version(data) == (
        core.FORMAT_VERSION_V2
    )

    (
        _ctx,
        n_points,
        segments,
        coding_type,
    ) = (
        cli.read_lsg2_metadata_and_segments(
            data
        )
    )

    assert n_points == 64
    assert len(segments) == 1

    assert coding_type == (
        core.RESIDUAL_CODEC_VARINT
    )

    cli.main(
        [
            "decode",
            str(encoded),
            str(decoded),
        ]
    )

    reconstructed = (
        _read_csv_values(decoded)
    )

    assert reconstructed == (
        pytest.approx(
            original,
            rel=0.0,
            abs=2e-6,
        )
    )

    cli.main(
        [
            "info",
            str(encoded),
        ]
    )

    output = capsys.readouterr().out

    assert (
        "Format      : "
        "LSG2 (v2 L32, univariate)"
        in output
    )

    assert "points    : 64" in output
    assert "segments  : 1" in output


def test_cli_info_preserves_v1_label(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "input.csv"
    encoded = tmp_path / "output-v1.lsg2"

    _write_linear_csv(source)

    cli.main(
        _encode_args(
            source,
            encoded,
        )
    )

    cli.main(
        [
            "info",
            str(encoded),
        ]
    )

    output = capsys.readouterr().out

    assert (
        "Format      : "
        "LSG2 (MVP v1, univariate)"
        in output
    )
