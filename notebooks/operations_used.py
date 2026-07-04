# ── Adding a new column ───────────────────────────────────────────
df["Daily_Return"] = (df["Close"] - df["Close"].shift(1)) / df["Close"].shift(1) * 100
# .shift(1) moves the column DOWN by 1 row — so each row has yesterday's Close
# Row 0 will be NaN (no yesterday)

# ── Filtering rows ────────────────────────────────────────────────
high_volume_days = df[df["Volume"] > 5000000]
positive_days = df[df["Daily_Return"] > 0]

# ── Applying functions ────────────────────────────────────────────
df["Price_Range"] = df["High"] - df["Low"]   # daily trading range
df["Body_Size"] = abs(df["Close"] - df["Open"])  # candle body size

# ── Rolling windows — critical for indicators ────────────────────
# "What was the 3-day average close price up to today?"
df["MA3"] = df["Close"].rolling(window=3).mean()
# First 2 rows are NaN (not enough data yet)

# ── Handling missing values ───────────────────────────────────────
print(df.isnull().sum())         # count NaNs per column
df_clean = df.dropna()           # drop any row with a NaN
df_filled = df.fillna(method="ffill")  # fill NaN with previous valid value
# "forward fill" — standard practice for missing price data


df["Daily_return"]=()