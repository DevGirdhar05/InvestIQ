import pandas as pd
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.database import load_features


def build_dataset(ticker: str, horizon: int = 5, threshold: float = 0.0) -> tuple:
    """
    Build the (X, y) dataset for ML training.

    Args:
        ticker    : e.g. "RELIANCE.NS"
        horizon   : predict price movement N days into the future. Default 5.
        threshold : minimum % move to count as "up". Default 0.0 (any rise).
                    Use 0.02 to predict "rises by at least 2%".

    Returns:
        X         : DataFrame of features (indicators)
        y         : Series of labels (0=down, 1=up)
        dates     : DatetimeIndex — needed for time-series split later
    """
    df = load_features(ticker)

    # ── Step 1: Create the target variable ───────────────────────
    # "What is the return N days from today?"
    # shift(-horizon) moves future values to today's row
    # e.g. with horizon=5, today's row gets the close price from 5 days later
    future_close = df["close"].shift(-horizon)
    future_return = (future_close - df["close"]) / df["close"]

    # Binary label: 1 if future return > threshold, else 0
    y = (future_return > threshold).astype(int)

    # ── Step 2: Select feature columns ───────────────────────────
    feature_cols = [
        "rsi",
        "macd", "macd_signal", "macd_hist",
        "bb_pct", "bb_width",
        "sma_20", "sma_50", "ema_20",
        "volume_ratio"
    ]

    # Add derived features — these are more informative than raw values
    df["price_vs_sma20"] = df["close"] / df["sma_20"] - 1  # how far above/below SMA20
    df["price_vs_sma50"] = df["close"] / df["sma_50"] - 1
    df["macd_vs_signal"] = df["macd"] - df["macd_signal"]   # already have this as hist
    df["rsi_normalized"] = (df["rsi"] - 50) / 50            # centre RSI at 0

    extended_features = feature_cols + [
        "price_vs_sma20", "price_vs_sma50", "rsi_normalized"
    ]

    X = df[extended_features].copy()

    # ── Step 3: Drop the last `horizon` rows ─────────────────────
    # These rows have NaN in y because there's no future data yet
    # (we can't know what happens 5 days after the most recent day)
    X = X.iloc[:-horizon]
    y = y.iloc[:-horizon]

    # ── Step 4: Drop any remaining NaN rows ──────────────────────
    # Align X and y — drop rows where either has NaN
    valid_mask = X.notna().all(axis=1) & y.notna()
    X = X[valid_mask]
    y = y[valid_mask]

    dates = X.index

    print(f"Dataset built for {ticker}")
    print(f"  Total samples : {len(X)}")
    print(f"  Features      : {len(X.columns)}")
    print(f"  UP days       : {y.sum()} ({y.mean():.1%})")
    print(f"  DOWN days     : {(1-y).sum()} ({(1-y.mean()):.1%})")
    print(f"  Date range    : {dates[0].date()} → {dates[-1].date()}")

    return X, y, dates

def time_series_split(X: pd.DataFrame, y: pd.Series, test_size: float = 0.2):
    split_idx = int(len(X) * (1 - test_size))

    X_train = X.iloc[:split_idx]
    X_test  = X.iloc[split_idx:]
    y_train = y.iloc[:split_idx]
    y_test  = y.iloc[split_idx:]

    print(f"Train: {len(X_train)} days ({X_train.index[0].date()} → {X_train.index[-1].date()})")
    print(f"Test:  {len(X_test)} days  ({X_test.index[0].date()} → {X_test.index[-1].date()})")

    return X_train, X_test, y_train, y_test