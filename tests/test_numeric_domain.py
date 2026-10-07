import math
from collections.abc import Callable

import pytest

from lasagna2 import core

Encoder = Callable[..., bytes]


def _encoders() -> tuple[Encoder, ...]:
    return (
        core.encode_timeseries,
        core.encode_timeseries_v1,
        core.encode_timeseries_v2,
    )


@pytest.mark.parametrize(
    "sample",
    (
        math.nan,
        math.inf,
        -math.inf,
    ),
)
@pytest.mark.parametrize(
    "encoder",
    _encoders(),
)
def test_public_encoders_reject_non_finite_samples(
    sample: float,
    encoder: Encoder,
) -> None:
    ts = core.TimeSeries(
        values=[
            0.0,
            sample,
        ],
    )

    with pytest.raises(
        ValueError,
        match="finite",
    ):
        encoder(
            ts,
            segment_length=2,
            predictor="rw",
        )


@pytest.mark.parametrize(
    "values",
    (
        [1e200, -1e200],
        [1e308, 1e308],
    ),
)
@pytest.mark.parametrize(
    "encoder",
    _encoders(),
)
def test_public_encoders_normalize_extreme_numeric_failure(
    values: list[float],
    encoder: Encoder,
) -> None:
    ts = core.TimeSeries(
        values=values,
    )

    with pytest.raises(ValueError):
        encoder(
            ts,
            segment_length=2,
            predictor="linear",
        )


@pytest.mark.parametrize(
    "dt",
    (
        math.nan,
        math.inf,
        -math.inf,
        0.0,
        -1.0,
    ),
)
@pytest.mark.parametrize(
    "encoder",
    _encoders(),
)
def test_public_encoders_reject_invalid_dt(
    dt: float,
    encoder: Encoder,
) -> None:
    ts = core.TimeSeries(
        values=[
            1.0,
            2.0,
        ],
        dt=dt,
    )

    with pytest.raises(
        ValueError,
        match="dt",
    ):
        encoder(
            ts,
            segment_length=2,
        )


@pytest.mark.parametrize(
    "C_Q",
    (
        math.nan,
        math.inf,
        -math.inf,
        -0.1,
    ),
)
def test_quantizer_rejects_invalid_cq(
    C_Q: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="C_Q",
    ):
        core.quantize_residuals(
            [0.0, 1.0],
            C_Q=C_Q,
            Q_MIN=1.0,
        )


@pytest.mark.parametrize(
    "Q_MIN",
    (
        math.nan,
        math.inf,
        -math.inf,
        0.0,
        -1.0,
    ),
)
def test_quantizer_rejects_invalid_qmin(
    Q_MIN: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="Q_MIN",
    ):
        core.quantize_residuals(
            [0.0, 1.0],
            C_Q=0.0,
            Q_MIN=Q_MIN,
        )


def test_quantizer_accepts_zero_cq_with_positive_qmin() -> None:
    residuals, Q = core.quantize_residuals(
        [0.0, 1.0],
        C_Q=0.0,
        Q_MIN=1.0,
    )

    assert Q == 1.0
    assert residuals == [0, 1]


@pytest.mark.parametrize(
    "mse_threshold",
    (
        math.nan,
        math.inf,
        -math.inf,
        -0.1,
    ),
)
@pytest.mark.parametrize(
    "segment_mode",
    (
        "fixed",
        "adaptive",
    ),
)
def test_public_encoder_rejects_invalid_mse_threshold(
    mse_threshold: float,
    segment_mode: str,
) -> None:
    ts = core.TimeSeries(
        values=[
            0.0,
            1.0,
        ],
    )

    with pytest.raises(
        ValueError,
        match="mse_threshold",
    ):
        core.encode_timeseries(
            ts,
            segment_mode=segment_mode,
            segment_length=2,
            min_segment_length=1,
            max_segment_length=2,
            mse_threshold=mse_threshold,
        )


@pytest.mark.parametrize(
    "value",
    (
        core.INT32_MIN,
        core.INT32_MAX,
    ),
)
def test_zigzag_accepts_signed_int32_boundaries(
    value: int,
) -> None:
    encoded = core.zigzag_encode(value)

    assert core.zigzag_decode(encoded) == value


@pytest.mark.parametrize(
    "value",
    (
        core.INT32_MIN - 1,
        core.INT32_MAX + 1,
    ),
)
def test_zigzag_rejects_out_of_range_values(
    value: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="signed int32",
    ):
        core.zigzag_encode(value)


ENCODING_CASES = (
    (
        core.encode_timeseries_v1,
        "raw",
    ),
    (
        core.encode_timeseries_v1,
        "varint",
    ),
    (
        core.encode_timeseries_v2,
        "raw",
    ),
    (
        core.encode_timeseries_v2,
        "varint",
    ),
    (
        core.encode_timeseries_v2,
        "zero-run",
    ),
    (
        core.encode_timeseries_v2,
        "auto",
    ),
    (
        core.encode_timeseries,
        "raw",
    ),
    (
        core.encode_timeseries,
        "varint",
    ),
    (
        core.encode_timeseries,
        "zero-run",
    ),
    (
        core.encode_timeseries,
        "auto",
    ),
)


@pytest.mark.parametrize(
    ("encoder", "residual_coding"),
    ENCODING_CASES,
)
@pytest.mark.parametrize(
    "value",
    (
        core.INT32_MIN,
        core.INT32_MAX,
    ),
)
def test_all_residual_codings_accept_int32_boundaries(
    encoder: Encoder,
    residual_coding: str,
    value: int,
) -> None:
    ts = core.TimeSeries(
        values=[
            0.0,
            float(value),
        ],
    )

    encoded = encoder(
        ts,
        segment_length=2,
        predictor="rw",
        C_Q=0.0,
        Q_MIN=1.0,
        residual_coding=residual_coding,
    )

    decoded = core.decode_timeseries(encoded)

    assert decoded.values == pytest.approx(
        ts.values,
    )


@pytest.mark.parametrize(
    ("encoder", "residual_coding"),
    ENCODING_CASES,
)
@pytest.mark.parametrize(
    "value",
    (
        core.INT32_MIN - 1,
        core.INT32_MAX + 1,
    ),
)
def test_all_residual_codings_reject_out_of_range_residuals(
    encoder: Encoder,
    residual_coding: str,
    value: int,
) -> None:
    ts = core.TimeSeries(
        values=[
            0.0,
            float(value),
        ],
    )

    with pytest.raises(
        ValueError,
        match="signed int32",
    ):
        encoder(
            ts,
            segment_length=2,
            predictor="rw",
            C_Q=0.0,
            Q_MIN=1.0,
            residual_coding=residual_coding,
        )


def test_v2_post_rounding_residual_cannot_bypass_int32_guard() -> None:
    mean = 1.0 + 1e-8
    amplitude = (core.INT32_MAX + 0.25) * 1e-10

    ts = core.TimeSeries(
        values=[
            mean - amplitude,
            mean + amplitude,
        ],
    )

    for residual_coding in (
        "raw",
        "varint",
        "zero-run",
        "auto",
    ):
        with pytest.raises(
            ValueError,
            match="signed int32",
        ):
            core.encode_timeseries_v2(
                ts,
                segment_length=2,
                predictor="mean",
                C_Q=0.0,
                Q_MIN=1e-10,
                residual_coding=residual_coding,
            )


@pytest.mark.parametrize(
    ("segment_length", "segment_mode"),
    (
        (0, "fixed"),
        (-1, "fixed"),
    ),
)
def test_fixed_mode_rejects_invalid_active_segment_length(
    segment_length: int,
    segment_mode: str,
) -> None:
    ts = core.TimeSeries(
        values=[
            1.0,
            2.0,
        ],
    )

    with pytest.raises(
        ValueError,
        match="segment_length",
    ):
        core.encode_timeseries(
            ts,
            segment_mode=segment_mode,
            segment_length=segment_length,
        )


@pytest.mark.parametrize(
    ("minimum", "maximum"),
    (
        (0, 2),
        (-1, 2),
        (3, 2),
    ),
)
def test_adaptive_mode_rejects_invalid_active_segment_lengths(
    minimum: int,
    maximum: int,
) -> None:
    ts = core.TimeSeries(
        values=[
            1.0,
            2.0,
            3.0,
        ],
    )

    with pytest.raises(ValueError):
        core.encode_timeseries(
            ts,
            segment_mode="adaptive",
            min_segment_length=minimum,
            max_segment_length=maximum,
        )


def test_empty_quantizer_still_validates_controls() -> None:
    with pytest.raises(
        ValueError,
        match="Q_MIN",
    ):
        core.quantize_residuals(
            [],
            C_Q=0.0,
            Q_MIN=0.0,
        )


def test_adaptive_mse_overflow_is_normalized_to_valueerror() -> None:
    ts = core.TimeSeries(
        values=[
            7e153,
            -7e153,
        ],
    )

    with pytest.raises(
        ValueError,
        match="Adaptive segmentation MSE",
    ):
        core.encode_timeseries(
            ts,
            predictor="rw",
            segment_mode="adaptive",
            min_segment_length=2,
            max_segment_length=2,
            mse_threshold=1.0,
        )


def test_auto_predictor_mse_overflow_is_normalized_to_valueerror() -> None:
    ts = core.TimeSeries(
        values=(
            [
                0.0,
                1e153,
                5e152,
            ]
            * 64
        ),
    )

    with pytest.raises(
        ValueError,
        match="Auto predictor MSE",
    ):
        core.encode_timeseries(
            ts,
            segment_length=len(ts.values),
            predictor="auto",
            C_Q=1.0,
            Q_MIN=1e-6,
            segment_mode="fixed",
        )


@pytest.mark.parametrize(
    "encoder",
    (
        core.encode_int_list_varint,
        core.encode_int_list_zero_run_varint,
    ),
)
@pytest.mark.parametrize(
    "value",
    (
        core.INT32_MIN,
        core.INT32_MAX,
    ),
)
def test_integer_list_helpers_accept_signed_int32_boundaries(
    encoder: Callable[[list[int]], bytes],
    value: int,
) -> None:
    payload = encoder([value])

    if encoder is core.encode_int_list_varint:
        decoded = core.decode_int_list_varint(
            payload,
            1,
        )
    else:
        decoded = core.decode_int_list_zero_run_varint(
            payload,
            1,
        )

    assert decoded == [value]


@pytest.mark.parametrize(
    "encoder",
    (
        core.encode_int_list_varint,
        core.encode_int_list_zero_run_varint,
    ),
)
@pytest.mark.parametrize(
    "value",
    (
        core.INT32_MIN - 1,
        core.INT32_MAX + 1,
    ),
)
def test_integer_list_helpers_reject_out_of_range_values(
    encoder: Callable[[list[int]], bytes],
    value: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="signed int32",
    ):
        encoder([value])


@pytest.mark.parametrize(
    "mse_threshold",
    (
        0.0,
        1.0,
    ),
)
def test_zero_and_positive_mse_threshold_are_supported(
    mse_threshold: float,
) -> None:
    ts = core.TimeSeries(
        values=[
            0.0,
            0.0,
        ],
    )

    encoded = core.encode_timeseries(
        ts,
        segment_mode="adaptive",
        min_segment_length=1,
        max_segment_length=2,
        mse_threshold=mse_threshold,
    )

    assert core.decode_timeseries(encoded).values == pytest.approx(ts.values)


def test_large_active_segment_lengths_are_clipped_to_series() -> None:
    ts = core.TimeSeries(
        values=[
            1.0,
            2.0,
            3.0,
        ],
    )

    encoded = core.encode_timeseries(
        ts,
        segment_mode="fixed",
        segment_length=1_000_000,
    )

    decoded = core.decode_timeseries(encoded)

    assert len(decoded.values) == 3


def test_timeseries_container_remains_lightweight_for_nonfinite_values() -> None:
    ts = core.TimeSeries(
        values=[
            math.nan,
            math.inf,
            -math.inf,
        ],
        dt=math.nan,
    )

    assert math.isnan(ts.values[0])
    assert math.isinf(ts.values[1])
    assert math.isinf(ts.values[2])
    assert math.isnan(ts.dt)


@pytest.mark.parametrize(
    "token",
    (
        "nan",
        "inf",
        "-inf",
        "1e9999",
    ),
)
@pytest.mark.parametrize(
    "format_version",
    (
        core.FORMAT_VERSION_V1,
        core.FORMAT_VERSION_V2,
    ),
)
def test_cli_encode_rejects_nonfinite_csv_values_without_writing_output(
    tmp_path,
    token: str,
    format_version: int,
) -> None:
    from argparse import Namespace

    from lasagna2 import cli

    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "output.lsg2"

    input_path.write_text(
        f"0.0\n{token}\n",
        encoding="utf-8",
    )

    args = Namespace(
        input=str(input_path),
        output=str(output_path),
        dt=1.0,
        t0="1970-01-01T00:00:00Z",
        unit="test",
        segment_mode="fixed",
        segment_length=2,
        min_segment_length=1,
        max_segment_length=2,
        mse_threshold=0.5,
        predictor="rw",
        residual_coding="raw",
        format_version=format_version,
    )

    with pytest.raises(ValueError):
        cli.cli_encode(args)

    assert not output_path.exists()


@pytest.mark.parametrize(
    ("dt", "mse_threshold"),
    (
        (math.nan, 0.5),
        (math.inf, 0.5),
        (-math.inf, 0.5),
        (1.0, math.nan),
        (1.0, math.inf),
        (1.0, -math.inf),
    ),
)
def test_cli_encode_rejects_nonfinite_controls_without_overwriting_output(
    tmp_path,
    dt: float,
    mse_threshold: float,
) -> None:
    from argparse import Namespace

    from lasagna2 import cli

    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "output.lsg2"

    input_path.write_text(
        "0.0\n1.0\n",
        encoding="utf-8",
    )

    sentinel = b"do-not-overwrite"
    output_path.write_bytes(sentinel)

    args = Namespace(
        input=str(input_path),
        output=str(output_path),
        dt=dt,
        t0="1970-01-01T00:00:00Z",
        unit="test",
        segment_mode="fixed",
        segment_length=2,
        min_segment_length=1,
        max_segment_length=2,
        mse_threshold=mse_threshold,
        predictor="rw",
        residual_coding="raw",
        format_version=core.FORMAT_VERSION_V2,
    )

    with pytest.raises(ValueError):
        cli.cli_encode(args)

    assert output_path.read_bytes() == sentinel
