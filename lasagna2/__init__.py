"""
Lasagna v2 – Brain-inspired time series compressor (univariate MVP).
"""

from .core import TimeSeries, encode_timeseries, decode_timeseries

__all__ = [
    "TimeSeries",
    "encode_timeseries",
    "decode_timeseries",
]
