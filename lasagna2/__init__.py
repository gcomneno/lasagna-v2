"""
Lasagna 2 – Time Series Predictive Codec (experimental univariate MVP).
"""

from .core import TimeSeries, encode_timeseries, decode_timeseries

__all__ = [
    "TimeSeries",
    "encode_timeseries",
    "decode_timeseries",
]
