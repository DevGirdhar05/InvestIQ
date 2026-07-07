import pandas as pd
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.database import load_features


def build_dataset(
    ticker   : str,
    horizon  : int = 10,      # changed from 5 to 10
    threshold: float = 0.0
) -> tuple:
    """
    Build (X, y) dataset for ML training.

    Args:
        ticker    : e.g. "RELIANCE.NS"
        horizon   : predict price movement N days into future
        threshold : minimum % move to count as UP (0.0 = any rise)

    Returns:
        X     : DataFrame of features
        y     : Series of labels (0=DOWN, 1=UP)
        dates : DatetimeIndex
    """
    df = load_features(ticker)

    # Target: will price be higher N days from now?
    future_close  = df["close"].shift(-horizon)
    future_return = (future_close - df["close"]) / df["close"]
    y = (future_return > threshold).astype(int)

    # Derived features — more informative than raw values
    df["price_vs_sma20"]  = df["close"] / df["sma_20"] - 1
    df["price_vs_sma50"]  = df["close"] / df["sma_50"] - 1
    df["rsi_normalized"]  = (df["rsi"] - 50) / 50

    feature_cols = [
        "rsi", "macd", "macd_signal", "macd_hist",
        "bb_pct", "bb_width", "sma_20", "sma_50",
        "ema_20", "volume_ratio",
        "price_vs_sma20", "price_vs_sma50", "rsi_normalized"
    ]

    X = df[feature_cols].copy()

    # Drop last horizon rows — no future data exists for them
    X = X.iloc[:-horizon]
    y = y.iloc[:-horizon]

    # Remove any NaN rows
    valid = X.notna().all(axis=1) & y.notna()
    X, y  = X[valid], y[valid]

    print(f"Dataset built for {ticker}")
    print(f"  Total samples : {len(X)}")
    print(f"  Features      : {len(X.columns)}")
    print(f"  UP days       : {y.sum()} ({y.mean():.1%})")
    print(f"  DOWN days     : {(1-y).sum()} ({(1-y.mean()):.1%})")
    print(f"  Date range    : {X.index[0].date()} → {X.index[-1].date()}")

    return X, y, X.index


def time_series_split(
    X        : pd.DataFrame,
    y        : pd.Series,
    test_size: float = 0.2
):
    """
    Chronological split — train on past, test on future.
    NEVER use sklearn's train_test_split with shuffle on time-series.
    """
    split_idx = int(len(X) * (1 - test_size))

    X_train = X.iloc[:split_idx]
    X_test  = X.iloc[split_idx:]
    y_train = y.iloc[:split_idx]
    y_test  = y.iloc[split_idx:]

    print(f"Train: {len(X_train)} days "
          f"({X_train.index[0].date()} → {X_train.index[-1].date()})")
    print(f"Test:  {len(X_test)} days  "
          f"({X_test.index[0].date()} → {X_test.index[-1].date()})")

    return X_train, X_test, y_train, y_test