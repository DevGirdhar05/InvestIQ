# src/data/pipeline.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.fetch import fetch_stock_data
from src.data.database import (
    initialise_database,
    save_prices,
    save_indicators
)
from src.indicators.pipeline import compute_all_indicators

WATCHLIST = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "WIPRO.NS",
]


def run_pipeline(tickers: list = None, period: str = "2y"):
    """
    Full pipeline: fetch → compute indicators → save to PostgreSQL.
    Safe to run multiple times — upserts never create duplicates.
    """
    if tickers is None:
        tickers = WATCHLIST

    initialise_database()

    results = {"success": [], "failed": []}

    for ticker in tickers:
        print(f"\n{'─' * 45}")
        print(f"Processing {ticker}...")

        try:
            # Step 1: Fetch raw OHLCV from Yahoo Finance
            raw_df = fetch_stock_data(ticker, period=period, save=True)

            # Step 2: Save raw prices to DB
            save_prices(ticker, raw_df)

            # Step 3: Compute all technical indicators
            indicator_df = compute_all_indicators(raw_df)

            # Step 4: Save indicators to DB
            save_indicators(ticker, indicator_df)

            results["success"].append(ticker)
            print(f"✓ {ticker} complete")

        except Exception as e:
            results["failed"].append(ticker)
            print(f"✗ {ticker} failed: {e}")

    print(f"\n{'═' * 45}")
    print(f"Pipeline complete.")
    print(f"Success : {results['success']}")
    if results["failed"]:
        print(f"Failed  : {results['failed']}")

    return results


if __name__ == "__main__":
    run_pipeline()