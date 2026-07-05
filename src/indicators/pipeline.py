
import pandas as pd
from .moving_averages import add_moving_averages
from .rsi import rsi, rsi_signal
from .macd import macd, macd_crossover_signal
from .bollinger import bollinger_bands
from .atr import add_atr


def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Take a raw OHLCV DataFrame and return it enriched with
    all technical indicators. This is what the ML model uses
    as its feature set.
    """
    df = df.copy()

    # Moving Averages
    df = add_moving_averages(df)

    # RSI
    df["RSI"]        = rsi(df["Close"], window=14)
    df["RSI_Signal"] = rsi_signal(df["RSI"])

    # MACD
    macd_df          = macd(df["Close"])
    df["MACD"]       = macd_df["MACD"]
    df["MACD_Signal"]= macd_df["Signal"]
    df["MACD_Hist"]  = macd_df["Histogram"]

    # Bollinger Bands
    bb_df            = bollinger_bands(df["Close"])
    df["BB_Upper"]   = bb_df["BB_Upper"]
    df["BB_Lower"]   = bb_df["BB_Lower"]
    df["BB_Width"]   = bb_df["BB_Width"]
    df["BB_Pct"]     = bb_df["BB_Pct"]

    # Volume ratio — how unusual is today's volume?
    df["Volume_Ratio"] = df["Volume"] / df["Volume"].rolling(20).mean()

    # ATR — volatility measure                        ← NEW
    df = add_atr(df, window=14)

    # Drop rows where any indicator is NaN
    # SMA50 needs 50 days, so first ~50 rows are always dropped
    df = df.dropna()

    return df