from fastapi import APIRouter, HTTPException
from src.api.models import SentimentResponse
from src.data.database import load_features_with_sentiment
from src.sentiment.aggregator import sentiment_to_text

router = APIRouter(prefix="/sentiment", tags=["Sentiment"])

WATCHLIST = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS",
    "HDFCBANK.NS", "WIPRO.NS"
]


@router.get("/{ticker}", response_model=SentimentResponse)
async def get_sentiment(ticker: str):
    """
    Get latest news sentiment scores for a ticker.

    Returns 1-day, 3-day, 7-day sentiment scores
    and momentum (is sentiment improving or worsening?).
    """
    ticker = ticker.upper()

    if ticker not in WATCHLIST:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker {ticker} not in watchlist."
        )

    try:
        df   = load_features_with_sentiment(ticker)
        last = df.iloc[-1]
        date = df.index[-1].strftime("%Y-%m-%d")

        s3d = float(last.get("sentiment_3d", 0) or 0)

        return SentimentResponse(
            ticker             = ticker,
            date               = date,
            sentiment_1d       = float(last.get("sentiment_1d", 0) or 0),
            sentiment_3d       = s3d,
            sentiment_7d       = float(last.get("sentiment_7d", 0) or 0),
            sentiment_momentum = float(last.get("sentiment_momentum", 0) or 0),
            sentiment_label    = sentiment_to_text(s3d),
            error              = None
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Sentiment fetch failed: {str(e)}"
        )