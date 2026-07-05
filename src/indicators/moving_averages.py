import pandas as pd
import numpy as np


def sma(series: pd.Series, window: int) -> pd.Series:
    """
    Simple Moving Average — unweighted mean of last `window` values.

    Rolling window slides one day at a time:
    Day 20: mean(day1..day20)
    Day 21: mean(day2..day21)   ← drops day1, adds day21
    ...

    First (window - 1) values are NaN — not enough history yet.
    """
    return series.rolling(window=window).mean()


def ema(series: pd.Series, window: int) -> pd.Series:
    """
    Exponential Moving Average — weights recent prices more heavily.

    pandas ewm() implements the recursive formula efficiently.
    adjust=False means it uses the true recursive formula:
        EMA_t = alpha * price_t + (1 - alpha) * EMA_{t-1}
    """
    return series.ewm(span=window, adjust=False).mean()


def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add SMA and EMA columns to an OHLCV DataFrame.
    Standard periods used by traders: 20-day (short), 50-day (medium)
    """
    df = df.copy()

    df["SMA_20"] = sma(df["Close"], window=20)
    df["SMA_50"] = sma(df["Close"], window=50)
    df["EMA_20"] = ema(df["Close"], window=20)

    return df

def sma_crossover_signal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate buy/sell signals from SMA20 vs SMA50 crossover.
    Signal = +1 (bullish), -1 (bearish), 0 (no change)
    """
    df = df.copy()

    # +1 when SMA20 is above SMA50, -1 when below
    df["MA_Position"] = np.where(df["SMA_20"] > df["SMA_50"], 1, -1)

    # Signal fires only when position CHANGES (the actual crossover moment)
    df["MA_Signal"] = df["MA_Position"].diff()
    # diff() = today - yesterday. Value of 2 means went from -1 to +1 (buy signal)

    return df