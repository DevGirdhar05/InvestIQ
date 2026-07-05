import sys
from pathlib import Path
import pandas as pd

# Add project root to Python path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.data.database import (
    load_prices,
    load_features,
    get_latest_signals,
)

TICKER = "RELIANCE.NS"

print("TEST 1: Load raw prices from PostgreSQL")
print("─" * 45)

prices = load_prices(TICKER)

print(prices.tail())
print(f"Shape: {prices.shape}")

print("\nTEST 2: Load ML features (prices + indicators joined)")
print("─" * 45)

features = load_features(TICKER)

print(features.tail())
print(f"\nFeature columns : {list(features.columns)}")
print(f"Total ML rows   : {len(features)}")

print("\nTEST 3: Date-filtered query")
print("─" * 45)

# Use a valid date range from the downloaded data
start_date = prices.index.min()
end_date = start_date + pd.DateOffset(months=3)

filtered = load_prices(
    TICKER,
    start=start_date.strftime("%Y-%m-%d"),
    end=end_date.strftime("%Y-%m-%d")
)

print(filtered.head())
print(f"\nRows returned: {len(filtered)}")

print("\nTEST 4: Latest market signals")
print("─" * 45)

signals = get_latest_signals([
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "WIPRO.NS",
])

print(signals)

print("\n✅ All Week 3 tests passed successfully!")