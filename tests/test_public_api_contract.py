from __future__ import annotations

import inspect

import lasagna2
from lasagna2 import cli, core

EXPECTED_PUBLIC_NAMES = {
    "TimeSeries",
    "encode_timeseries",
    "encode_timeseries_v1",
    "encode_timeseries_v2",
    "decode_timeseries",
}


def _parameter_contract(callable_object) -> tuple[tuple[str, object], ...]:
    signature = inspect.signature(callable_object)

    return tuple(
        (
            name,
            parameter.default,
        )
        for name, parameter in signature.parameters.items()
    )


def test_public_package_surface_is_explicit() -> None:
    assert set(lasagna2.__all__) == EXPECTED_PUBLIC_NAMES

    for name in EXPECTED_PUBLIC_NAMES:
        assert getattr(lasagna2, name) is getattr(
            core,
            name,
        )


def test_timeseries_constructor_contract() -> None:
    signature = inspect.signature(lasagna2.TimeSeries)

    assert tuple(signature.parameters) == (
        "values",
        "dt",
        "t0",
        "unit",
    )

    assert signature.parameters["values"].default is inspect.Parameter.empty
    assert signature.parameters["dt"].default == 1.0
    assert signature.parameters["t0"].default == "1970-01-01T00:00:00Z"
    assert signature.parameters["unit"].default == "unknown"


def test_default_encoder_signature_contract() -> None:
    assert _parameter_contract(lasagna2.encode_timeseries) == (
        ("ts", inspect.Parameter.empty),
        ("segment_length", 64),
        ("predictor", "linear"),
        ("C_Q", 0.125),
        ("Q_MIN", 1e-6),
        ("segment_mode", "fixed"),
        ("min_segment_length", 32),
        ("max_segment_length", 128),
        ("mse_threshold", 0.5),
        ("residual_coding", "raw"),
    )


def test_v1_encoder_signature_contract() -> None:
    assert _parameter_contract(lasagna2.encode_timeseries_v1) == (
        ("ts", inspect.Parameter.empty),
        ("segment_length", 64),
        ("predictor", "linear"),
        ("C_Q", 0.5),
        ("Q_MIN", 1e-6),
        ("segment_mode", "fixed"),
        ("min_segment_length", 32),
        ("max_segment_length", 128),
        ("mse_threshold", 0.5),
        ("residual_coding", "raw"),
    )


def test_v2_encoder_signature_contract() -> None:
    assert _parameter_contract(lasagna2.encode_timeseries_v2) == (
        ("ts", inspect.Parameter.empty),
        ("segment_length", 64),
        ("predictor", "linear"),
        ("C_Q", 0.125),
        ("Q_MIN", 1e-6),
        ("segment_mode", "fixed"),
        ("min_segment_length", 32),
        ("max_segment_length", 128),
        ("mse_threshold", 0.5),
        ("residual_coding", "raw"),
    )


def test_decoder_signature_contract() -> None:
    signature = inspect.signature(lasagna2.decode_timeseries)

    assert tuple(signature.parameters) == ("data",)


def test_public_return_contracts() -> None:
    ts = lasagna2.TimeSeries(
        values=[1.0, 2.0, 3.0, 4.0],
    )

    encoded_default = lasagna2.encode_timeseries(
        ts,
        segment_length=4,
    )
    encoded_v1 = lasagna2.encode_timeseries_v1(
        ts,
        segment_length=4,
    )
    encoded_v2 = lasagna2.encode_timeseries_v2(
        ts,
        segment_length=4,
    )

    assert isinstance(encoded_default, bytes)
    assert isinstance(encoded_v1, bytes)
    assert isinstance(encoded_v2, bytes)

    assert isinstance(
        lasagna2.decode_timeseries(encoded_default),
        lasagna2.TimeSeries,
    )
    assert isinstance(
        lasagna2.decode_timeseries(encoded_v1),
        lasagna2.TimeSeries,
    )
    assert isinstance(
        lasagna2.decode_timeseries(encoded_v2),
        lasagna2.TimeSeries,
    )


def test_cli_command_surface_contract() -> None:
    parser = cli.build_arg_parser()

    subparser_action = next(
        action
        for action in parser._actions
        if isinstance(
            action,
            __import__("argparse")._SubParsersAction,
        )
    )

    assert set(subparser_action.choices) == {
        "encode",
        "decode",
        "info",
        "export-tags",
        "export-motifs",
        "export-profile",
    }


def test_cli_encode_defaults_contract() -> None:
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

    assert args.segment_mode == "adaptive"
    assert args.segment_length == 64
    assert args.min_segment_length == 32
    assert args.max_segment_length == 128
    assert args.mse_threshold == 0.5
    assert args.predictor == "linear"
    assert args.residual_coding == "varint"
    assert args.format_version == core.FORMAT_VERSION_V2


def test_cli_encode_choice_contract() -> None:
    parser = cli.build_arg_parser()

    encode_parser = next(
        action
        for action in parser._actions
        if isinstance(
            action,
            __import__("argparse")._SubParsersAction,
        )
    ).choices["encode"]

    actions = {action.dest: action for action in encode_parser._actions}

    assert set(actions["segment_mode"].choices) == {
        "fixed",
        "adaptive",
    }

    assert set(actions["residual_coding"].choices) == {
        "raw",
        "varint",
        "zero-run",
        "auto",
    }

    assert set(actions["format_version"].choices) == {
        core.FORMAT_VERSION_V1,
        core.FORMAT_VERSION_V2,
    }


def test_cli_info_verbose_default_contract() -> None:
    parser = cli.build_arg_parser()

    args = parser.parse_args(
        [
            "info",
            "input.lsg2",
        ]
    )

    assert args.verbose is False
