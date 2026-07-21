import pandas as pd
import numpy as np


def aggregate_daily_sentiment(
    news_df: pd.DataFrame,
    method : str = "mean"
) -> pd.Series:
    """
    Aggregate article-level scores to one score per day.

    Individual articles are noisy. One clickbait negative
    headline during a positive news cycle shouldn't tank
    the score. A daily average smooths this out.

    Args:
        method: "mean" or "weighted"
                weighted gives more weight to extreme scores
                (very positive or very negative articles)
    """
    df         = news_df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()

    if method == "mean":
        daily = df.groupby("date")["sentiment_score"].mean()

    elif method == "weighted":
        df["weight"]        = df["sentiment_score"].abs()
        df["weighted_score"]= df["sentiment_score"] * df["weight"]
        daily = (
            df.groupby("date")["weighted_score"].sum()
            / df.groupby("date")["weight"].sum()
        )

    return daily.round(4)

def build_sentiment_features(
    daily_sentiment: pd.Series,
    price_index    : pd.DatetimeIndex,
    windows        : list = [1, 3, 7]
) -> pd.DataFrame:
    """
    Build rolling sentiment features aligned to price data.

    Why rolling windows?
    A single day's sentiment is noisy. A 3-day rolling average
    captures sustained news trends. A 7-day window captures the
    broader sentiment cycle over a trading week.

    Why forward-fill on weekends?
    News is published on weekends but price data has no
    Saturday/Sunday rows. We carry Friday's sentiment into
    Monday — the market prices in weekend news at open.
    """
    # Reindex to trading days, forward-fill gaps
    aligned  = daily_sentiment.reindex(price_index, method="ffill")
    features = pd.DataFrame(index=price_index)

    for w in windows:
        features[f"sentiment_{w}d"] = (
            aligned.rolling(window=w, min_periods=1)
            .mean()
            .round(4)
        )

    # Sentiment momentum: is news improving or deteriorating?
    # Positive = sentiment getting better recently
    # Negative = sentiment getting worse
    features["sentiment_momentum"] = (
        features["sentiment_1d"] - features["sentiment_7d"]
    ).round(4)

    return features


def sentiment_to_text(score: float) -> str:
    """
    Convert numeric score to human-readable label.
    Used by LLM explanation layer in Week 8.
    """
    if score >  0.3:  return "STRONGLY POSITIVE"
    if score >  0.1:  return "MILDLY POSITIVE"
    if score > -0.1:  return "NEUTRAL"
    if score > -0.3:  return "MILDLY NEGATIVE"
    return "STRONGLY NEGATIVE"