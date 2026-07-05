import pandas as pd


def macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> pd.DataFrame:
    """
    MACD — Moving Average Convergence Divergence.

    Standard parameters: fast=12, slow=26, signal=9
    These were chosen by Gerald Appel in the 1970s and remain standard.

    Returns DataFrame with three columns:
        MACD      : fast EMA − slow EMA
        Signal    : EMA of MACD (trigger line)
        Histogram : MACD − Signal (momentum strength and direction)
    """
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return pd.DataFrame({
        "MACD": macd_line,
        "Signal": signal_line,
        "Histogram": histogram
    }, index=series.index)


def macd_crossover_signal(macd_df: pd.DataFrame) -> pd.Series:
    """
    Signal fires when MACD line crosses the Signal line.
    +1 = MACD crossed above Signal (bullish)
    -1 = MACD crossed below Signal (bearish)
     0 = no crossover today
    """
    position = (macd_df["MACD"] > macd_df["Signal"]).astype(int)
    # astype(int) converts True/False → 1/0
    signal = position.diff()
    # diff() = 1 when crossed up (0→1), -1 when crossed down (1→0)
    return signal