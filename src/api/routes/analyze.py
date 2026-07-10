from fastapi import APIRouter, HTTPException
from src.api.models import AnalysisResponse
from src.api.dependencies import get_model_and_explainer
from src.models.features import build_dataset, time_series_split
from src.models.xgboost_model import get_prediction_explanation
from src.data.database import (
    load_features_with_sentiment, get_connection
)
from sqlalchemy import text
import pandas as pd

router = APIRouter(prefix="/analyze", tags=["Analysis"])

HORIZON = 10
WATCHLIST = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS",
    "HDFCBANK.NS", "WIPRO.NS"
]


def get_company_name(ticker: str) -> str:
    """Fetch company name from metadata table."""
    NAMES = {
        "RELIANCE.NS" : "Reliance Industries",
        "TCS.NS"      : "Tata Consultancy Services",
        "INFY.NS"     : "Infosys",
        "HDFCBANK.NS" : "HDFC Bank",
        "WIPRO.NS"    : "Wipro",
    }
    try:
        with get_connection() as conn:
            result = conn.execute(text("""
                SELECT company_name FROM stock_metadata
                WHERE ticker = :ticker
            """), {"ticker": ticker})
            row = result.fetchone()
        return row[0] if row else NAMES.get(ticker, ticker)
    except Exception:
        return NAMES.get(ticker, ticker)


def build_features_for_ticker(ticker: str):
    """
    Build feature dataset for prediction.
    Uses load_features_with_sentiment for 17-feature set.
    """
    df = load_features_with_sentiment(ticker)

    future_close  = df["close"].shift(-HORIZON)
    future_return = (future_close - df["close"]) / df["close"]
    y = (future_return > 0).astype(int)

    df["price_vs_sma20"] = df["close"] / df["sma_20"] - 1
    df["price_vs_sma50"] = df["close"] / df["sma_50"] - 1
    df["rsi_normalized"] = (df["rsi"] - 50) / 50

    feature_cols = [
        "rsi", "macd", "macd_signal", "macd_hist",
        "bb_pct", "bb_width", "sma_20", "sma_50",
        "ema_20", "volume_ratio",
        "price_vs_sma20", "price_vs_sma50", "rsi_normalized",
        "sentiment_1d", "sentiment_3d",
        "sentiment_7d", "sentiment_momentum"
    ]

    X = df[feature_cols].copy()
    X = X.iloc[:-HORIZON]
    y = y.iloc[:-HORIZON]

    valid = X.notna().all(axis=1) & y.notna()
    return X[valid], y[valid]


@router.get("/{ticker}", response_model=AnalysisResponse)
async def analyze_ticker(ticker: str):
    """
    Get ML prediction for a ticker.

    Returns probability of price rise in 10 trading days,
    confidence level, and top SHAP feature contributions.

    Ticker format:
    - NSE stocks: RELIANCE.NS, TCS.NS
    - BSE stocks: RELIANCE.BO
    - US stocks: AAPL, TSLA
    """
    ticker = ticker.upper()

    if ticker not in WATCHLIST:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker {ticker} not in watchlist. "
                   f"Available: {WATCHLIST}"
        )

    try:
        # Build features
        X, y = build_features_for_ticker(ticker)

        if len(X) < 100:
            raise HTTPException(
                status_code=422,
                detail=f"Insufficient data for {ticker}. "
                       f"Need at least 100 samples."
            )

        # Split — use all data, predict on latest row
        X_train, X_test, y_train, y_test = time_series_split(
            X, y, test_size=0.2
        )

        # Get model and explainer (cached)
        model, explainer = get_model_and_explainer()

        # Predict on the most recent row
        latest_row = X.iloc[[-1]]
        prediction = get_prediction_explanation(
            model, explainer, latest_row
        )

        company_name = get_company_name(ticker)

        return AnalysisResponse(
            ticker          = ticker,
            company_name    = company_name,
            date            = X.index[-1].strftime("%Y-%m-%d"),
            probability_up  = prediction["probability_up"],
            probability_down= prediction["probability_down"],
            confidence      = prediction["confidence"],
            top_features    = prediction["top_features"],
            horizon_days    = HORIZON,
            training_samples= len(X_train),
            error           = None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed for {ticker}: {str(e)}"
        )