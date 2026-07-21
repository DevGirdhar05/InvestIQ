import pandas as pd
import numpy as np


def aggregate_daily_sentiment(
    news_df: pd.DataFrame,
    method: str = "mean"
) -> pd.Series:

    df = news_df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()

    if method == "mean":
        daily = df.groupby("date")["sentiment_score"].mean()

    elif method == "weighted":
        df["weight"] = df["sentiment_score"].abs()
        df["weighted_score"] = df["sentiment_score"] * df["weight"]
        daily = (
            df.groupby("date")["weighted_score"].sum()
            / df.groupby("date")["weight"].sum()
        )

    return daily.sort_index().round(4)


def build_sentiment_features(
    daily_sentiment: pd.Series,
    price_index: pd.DatetimeIndex,
    windows: list = [1, 3, 7]
) -> pd.DataFrame:

    # Align to trading days
    aligned = daily_sentiment.reindex(price_index)

    # Carry latest available sentiment forward
    aligned = aligned.ffill()

    # If initial rows are NaN, fill with first available sentiment
    aligned = aligned.bfill()

    # If still NaN (no news at all), use neutral sentiment
    aligned = aligned.fillna(0)

    features = pd.DataFrame(index=price_index)

    for w in windows:
        features[f"sentiment_{w}d"] = (
            aligned
            .rolling(window=w, min_periods=1)
            .mean()
            .round(4)
        )

    features["sentiment_momentum"] = (
        features["sentiment_1d"] - features["sentiment_7d"]
    ).fillna(0).round(4)

    return features


def sentiment_to_text(score: float) -> str:
    if score > 0.3:
        return "STRONGLY POSITIVE"
    if score > 0.1:
        return "MILDLY POSITIVE"
    if score > -0.1:
        return "NEUTRAL"
    if score > -0.3:
        return "MILDLY NEGATIVE"
    return "STRONGLY NEGATIVE"