# src/indicators/atr.py

import pandas as pd
import numpy as np


def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """
    Average True Range — measures volatility.

    True Range on any given day is the LARGEST of these three:
        1. High - Low          (today's trading range)
        2. |High - PrevClose|  (gap up then volatile day)
        3. |Low  - PrevClose|  (gap down then volatile day)

    Cases 2 and 3 handle overnight gaps — when a stock closes
    at ₹100 but opens at ₹110 the next day, the "true" range
    includes that gap. Plain High-Low would miss it.

    ATR = EMA of True Range over `window` days (14 is standard)

    Args:
        df     : OHLCV DataFrame with High, Low, Close columns
        window : lookback period, default 14

    Returns:
        ATR Series — same index as df
        Higher ATR = more volatile stock
        Lower ATR  = calmer, tighter trading range
    """
    high      = df["High"]
    low       = df["Low"]
    prev_close = df["Close"].shift(1)   # yesterday's close

    # Compute all three components of True Range
    range1 = high - low                    # today's high-low range
    range2 = (high - prev_close).abs()     # gap up scenario
    range3 = (low  - prev_close).abs()     # gap down scenario

    # True Range = max of the three, element-wise across all rows
    true_range = pd.concat([range1, range2, range3], axis=1).max(axis=1)
    # pd.concat creates a 3-column DataFrame, .max(axis=1) picks
    # the largest value in each row across all 3 columns

    # ATR = exponential moving average of True Range
    atr_values = true_range.ewm(span=window, adjust=False).mean()

    return atr_values


def add_atr(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """
    Add ATR column to an OHLCV DataFrame.
    Also adds ATR% — ATR as a percentage of Close price.
    This normalises ATR so you can compare volatility across
    stocks at different price levels.

    ATR of ₹50 means nothing alone.
    ATR% of 2.1% means the stock moves ~2.1% per day on average.
    """
    df = df.copy()
    df["ATR"]   = atr(df, window=window).round(2)
    df["ATR_Pct"] = (df["ATR"] / df["Close"] * 100).round(3)
    return df