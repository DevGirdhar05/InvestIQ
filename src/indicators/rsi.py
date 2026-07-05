import pandas as pd
import numpy as np


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """
    RSI — Relative Strength Index.

    Args:
        series : Close price Series
        window : Lookback period. 14 is the standard (Wilder's RSI)

    Returns:
        RSI Series, values between 0 and 100
    """
    # Step 1: Daily price change
    delta = series.diff()
    # delta.iloc[0] is NaN (no previous day)

    # Step 2: Separate gains and losses
    # clip(lower=0) sets all negatives to 0 → keeps only gains
    # clip(upper=0) sets all positives to 0 → keeps only losses (negative numbers)
    gains = delta.clip(lower=0)
    losses = (-delta).clip(lower=0)  # make losses positive

    # Step 3: Exponential moving average of gains and losses
    # min_periods=window means don't compute until we have `window` data points
    avg_gain = gains.ewm(
        com=window - 1,       # com = center of mass. com=13 → span=14 → alpha=1/14
        min_periods=window,
        adjust=False
    ).mean()

    avg_loss = losses.ewm(
        com=window - 1,
        min_periods=window,
        adjust=False
    ).mean()

    # Step 4 & 5: RS and RSI
    # Add tiny epsilon to avoid division by zero when avg_loss = 0
    rs = avg_gain / (avg_loss + 1e-10)
    rsi_values = 100 - (100 / (1 + rs))

    return rsi_values


def rsi_signal(rsi_series: pd.Series,
               overbought: int = 70,
               oversold: int = 30) -> pd.Series:
    """
    Generate signals from RSI thresholds.
    Returns: 1 (oversold = potential buy), -1 (overbought = potential sell), 0 (neutral)
    """
    signal = pd.Series(0, index=rsi_series.index)
    signal[rsi_series < oversold] = 1
    signal[rsi_series > overbought] = -1
    return signal