from fastapi import APIRouter, HTTPException
from src.api.models import AnalysisResponse
from src.api.dependencies import get_model_and_explainer
from src.models.features import build_dataset, time_series_split
from src.models.xgboost_model import get_prediction_explanation
from src.data.database import (
    load_features, get_connection
)
from sqlalchemy import text
import pandas as pd
from src.api.cache import cache_get, cache_set, TTL_ANALYSIS
from datetime import date as date_module


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
    df = load_features(ticker)   # 13 features only

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
        "price_vs_sma20", "price_vs_sma50", "rsi_normalized"
    ]

    X = df[feature_cols].copy()
    X = X.iloc[:-HORIZON]
    y = y.iloc[:-HORIZON]

    valid = X.notna().all(axis=1) & y.notna()
    return X[valid], y[valid]

    


@router.get("/{ticker}", response_model=AnalysisResponse)
async def analyze_ticker(ticker: str):
    ticker = ticker.upper()

    if ticker not in WATCHLIST:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker {ticker} not in watchlist."
        )

    # ── Check cache first ─────────────────────────────────────
    cache_key    = f"analyze:{ticker}"
    cached_result= cache_get(cache_key)

    if cached_result:
        # Cache hit — return immediately, no computation
        return AnalysisResponse(**cached_result)

    # ── Cache miss — run full analysis ────────────────────────
    try:
        X, y = build_features_for_ticker(ticker)

        if len(X) < 100:
            raise HTTPException(status_code=422,
                detail=f"Insufficient data for {ticker}.")

        X_train, X_test, y_train, y_test = time_series_split(
            X, y, test_size=0.2
        )

        model, explainer = get_model_and_explainer()
        latest_row       = X.iloc[[-1]]
        prediction       = get_prediction_explanation(
            model, explainer, latest_row
        )

        company_name = get_company_name(ticker)

        result = AnalysisResponse(
            ticker          = ticker,
            company_name    = company_name,
            date            = date_module.today().strftime("%Y-%m-%d"),  # today not data date
            probability_up  = prediction["probability_up"],
            probability_down= prediction["probability_down"],
            confidence      = prediction["confidence"],
            top_features    = prediction["top_features"],
            horizon_days    = HORIZON,
            training_samples= len(X_train),
            error           = None
        )

        # Store in cache — subsequent requests are instant
        cache_set(cache_key, result.dict(), ttl=TTL_ANALYSIS)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
            detail=f"Analysis failed for {ticker}: {str(e)}")