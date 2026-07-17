from fastapi import APIRouter, HTTPException
from src.data.database import load_features

router = APIRouter(prefix="/prices", tags=["Prices"])

WATCHLIST = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "WIPRO.NS",
]


@router.get("/{ticker}")
async def get_prices(ticker: str, days: int = 90):
    """
    Get historical prices with indicator overlays.

    Returns:
    - Price
    - SMA20
    - SMA50
    """

    ticker = ticker.upper()

    if ticker not in WATCHLIST:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker {ticker} not in watchlist."
        )

    try:
        # load_features() already joins prices + indicators
        df = load_features(ticker)

        # Keep only latest N trading days
        df = df.tail(days)

        records = []

        for date, row in df.iterrows():
            records.append({
                "date": date.strftime("%d %b"),
                "Price": round(float(row["close"]), 2),
                "SMA20": round(float(row["sma_20"]), 2),
                "SMA50": round(float(row["sma_50"]), 2),
                "Volume": int(row["volume"]),
            })

        return {
            "ticker": ticker,
            "days": days,
            "data": records
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Price fetch failed: {str(e)}"
        )