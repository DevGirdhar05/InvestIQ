# src/data/database.py
import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager

# Load .env using absolute path — never breaks regardless of run location
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def _build_db_url() -> str:
    required = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]
    missing  = [v for v in required if not os.getenv(v)]
    if missing:
        raise EnvironmentError(
            f"Missing .env variables: {missing}\n"
            f"Check that .env exists at your project root."
        )
    return (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}"
        f"/{os.getenv('DB_NAME')}"
    )


engine = create_engine(
    _build_db_url(),
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False
)


@contextmanager
def get_connection():
    with engine.connect() as conn:
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def initialise_database():
    with get_connection() as conn:

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS prices (
                ticker   VARCHAR(20)      NOT NULL,
                date     DATE             NOT NULL,
                open     DOUBLE PRECISION,
                high     DOUBLE PRECISION,
                low      DOUBLE PRECISION,
                close    DOUBLE PRECISION NOT NULL,
                volume   BIGINT,
                PRIMARY KEY (ticker, date)
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS indicators (
                ticker        VARCHAR(20)      NOT NULL,
                date          DATE             NOT NULL,
                sma_20        DOUBLE PRECISION,
                sma_50        DOUBLE PRECISION,
                ema_20        DOUBLE PRECISION,
                rsi           DOUBLE PRECISION,
                macd          DOUBLE PRECISION,
                macd_signal   DOUBLE PRECISION,
                macd_hist     DOUBLE PRECISION,
                bb_upper      DOUBLE PRECISION,
                bb_lower      DOUBLE PRECISION,
                bb_width      DOUBLE PRECISION,
                bb_pct        DOUBLE PRECISION,
                volume_ratio  DOUBLE PRECISION,
                PRIMARY KEY (ticker, date)
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS fetch_log (
                ticker        VARCHAR(20) PRIMARY KEY,
                last_fetched  TIMESTAMP   NOT NULL DEFAULT NOW()
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS stock_metadata (
                ticker       VARCHAR(20) PRIMARY KEY,
                company_name VARCHAR(100),
                sector       VARCHAR(50),
                market_cap   VARCHAR(20),
                exchange     VARCHAR(10)
            )
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_prices_ticker_date
            ON prices (ticker, date DESC)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_indicators_ticker_date
            ON indicators (ticker, date DESC)
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sentiment (
                ticker              VARCHAR(20)      NOT NULL,
                date                DATE             NOT NULL,
                sentiment_1d        DOUBLE PRECISION,
                sentiment_3d        DOUBLE PRECISION,
                sentiment_7d        DOUBLE PRECISION,
                sentiment_momentum  DOUBLE PRECISION,
                article_count       INTEGER,
                PRIMARY KEY (ticker, date)
            )
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_sentiment_ticker_date
            ON sentiment (ticker, date DESC)
        """))
    print("Database initialised.")
    print(f"  Host: {os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}")
    print(f"  DB  : {os.getenv('DB_NAME')}")


def save_prices(ticker: str, df: pd.DataFrame):
    if df.empty:
        print(f"  Warning: empty DataFrame for {ticker}, skipping.")
        return

    with get_connection() as conn:
        for date, row in df.iterrows():
            conn.execute(text("""
                INSERT INTO prices
                    (ticker, date, open, high, low, close, volume)
                VALUES
                    (:ticker, :date, :open, :high, :low, :close, :volume)
                ON CONFLICT (ticker, date) DO UPDATE SET
                    open   = EXCLUDED.open,
                    high   = EXCLUDED.high,
                    low    = EXCLUDED.low,
                    close  = EXCLUDED.close,
                    volume = EXCLUDED.volume
            """), {
                "ticker": ticker,
                "date"  : date.strftime("%Y-%m-%d"),
                "open"  : round(float(row["Open"]),  2),
                "high"  : round(float(row["High"]),  2),
                "low"   : round(float(row["Low"]),   2),
                "close" : round(float(row["Close"]), 2),
                "volume": int(row["Volume"])
            })

        conn.execute(text("""
            INSERT INTO fetch_log (ticker, last_fetched)
            VALUES (:ticker, NOW())
            ON CONFLICT (ticker) DO UPDATE SET last_fetched = NOW()
        """), {"ticker": ticker})

    print(f"  Saved {len(df)} price rows for {ticker}")


def save_indicators(ticker: str, df: pd.DataFrame):
    col_map = {
        "SMA_20": "sma_20", "SMA_50": "sma_50",
        "EMA_20": "ema_20", "RSI": "rsi",
        "MACD": "macd", "MACD_Signal": "macd_signal",
        "MACD_Hist": "macd_hist", "BB_Upper": "bb_upper",
        "BB_Lower": "bb_lower", "BB_Width": "bb_width",
        "BB_Pct": "bb_pct", "Volume_Ratio": "volume_ratio"
    }

    with get_connection() as conn:
        for date, row in df.iterrows():
            values = {
                "ticker": ticker,
                "date"  : date.strftime("%Y-%m-%d")
            }
            for df_col, db_col in col_map.items():
                values[db_col] = (
                    round(float(row[df_col]), 6)
                    if df_col in row.index and pd.notna(row[df_col])
                    else None
                )

            conn.execute(text("""
                INSERT INTO indicators
                    (ticker, date, sma_20, sma_50, ema_20, rsi,
                     macd, macd_signal, macd_hist,
                     bb_upper, bb_lower, bb_width, bb_pct, volume_ratio)
                VALUES
                    (:ticker, :date, :sma_20, :sma_50, :ema_20, :rsi,
                     :macd, :macd_signal, :macd_hist,
                     :bb_upper, :bb_lower, :bb_width, :bb_pct, :volume_ratio)
                ON CONFLICT (ticker, date) DO UPDATE SET
                    sma_20      = EXCLUDED.sma_20,
                    sma_50      = EXCLUDED.sma_50,
                    ema_20      = EXCLUDED.ema_20,
                    rsi         = EXCLUDED.rsi,
                    macd        = EXCLUDED.macd,
                    macd_signal = EXCLUDED.macd_signal,
                    macd_hist   = EXCLUDED.macd_hist,
                    bb_upper    = EXCLUDED.bb_upper,
                    bb_lower    = EXCLUDED.bb_lower,
                    bb_width    = EXCLUDED.bb_width,
                    bb_pct      = EXCLUDED.bb_pct,
                    volume_ratio= EXCLUDED.volume_ratio
            """), values)

    print(f"  Saved indicators for {ticker}")


def load_prices(
    ticker: str,
    start: str = None,
    end: str = None
) -> pd.DataFrame:
    query  = "SELECT * FROM prices WHERE ticker = :ticker"
    params = {"ticker": ticker}

    if start:
        query += " AND date >= :start"
        params["start"] = start
    if end:
        query += " AND date <= :end"
        params["end"] = end

    query += " ORDER BY date ASC"

    with get_connection() as conn:
        df = pd.read_sql_query(text(query), conn, params=params)

    if df.empty:
        raise ValueError(
            f"No data for {ticker} in database. "
            f"Run the pipeline first."
        )

    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").drop(columns=["ticker"])
    df.columns = [c.title() for c in df.columns]
    return df


def load_features(
    ticker: str,
    start: str = None
) -> pd.DataFrame:
    """
    Load prices + indicators joined — ML-ready.
    This is the ONLY function Week 4 and Week 5 call.
    Everything else is hidden.
    """
    query = """
        SELECT
            p.date,
            p.close,
            p.volume,
            i.sma_20, i.sma_50, i.ema_20,
            i.rsi,
            i.macd, i.macd_signal, i.macd_hist,
            i.bb_upper, i.bb_lower, i.bb_width, i.bb_pct,
            i.volume_ratio
        FROM prices p
        JOIN indicators i
            ON p.ticker = i.ticker
            AND p.date  = i.date
        WHERE p.ticker = :ticker
    """
    params = {"ticker": ticker}

    if start:
        query += " AND p.date >= :start"
        params["start"] = start

    query += " ORDER BY p.date ASC"

    with get_connection() as conn:
        df = pd.read_sql_query(text(query), conn, params=params)

    if df.empty:
        raise ValueError(
            f"No features for {ticker}. Run the pipeline first."
        )

    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    return df


def get_latest_signals(tickers: list) -> pd.DataFrame:
    """
    Week 3 Exercise 2 — market overview table.
    Returns the most recent row for each ticker.
    """
    rows = []
    for ticker in tickers:
        try:
            with get_connection() as conn:
                result = conn.execute(text("""
                    SELECT
                        p.ticker,
                        p.date,
                        p.close,
                        i.rsi,
                        i.macd_hist,
                        i.sma_50,
                        CASE
                            WHEN p.close > i.sma_50 THEN 'Above SMA50'
                            ELSE 'Below SMA50'
                        END AS trend
                    FROM prices p
                    JOIN indicators i
                        ON p.ticker = i.ticker
                        AND p.date  = i.date
                    WHERE p.ticker = :ticker
                    ORDER BY p.date DESC
                    LIMIT 1
                """), {"ticker": ticker})
                row = result.fetchone()
                if row:
                    rows.append(dict(row._mapping))
        except Exception as e:
            print(f"  Warning: could not fetch signals for {ticker}: {e}")

    return pd.DataFrame(rows)

def save_sentiment(ticker: str, features_df: pd.DataFrame):
    """Save daily sentiment features to the sentiment table."""
    import math

    def safe_float(val):
        """Convert to float, return None if NaN — PostgreSQL stores NULL."""
        try:
            f = float(val)
            return None if math.isnan(f) else f
        except (TypeError, ValueError):
            return None

    with get_connection() as conn:
        for date, row in features_df.iterrows():
            conn.execute(text("""
                INSERT INTO sentiment
                    (ticker, date, sentiment_1d, sentiment_3d,
                     sentiment_7d, sentiment_momentum)
                VALUES
                    (:ticker, :date, :s1d, :s3d, :s7d, :smom)
                ON CONFLICT (ticker, date) DO UPDATE SET
                    sentiment_1d       = EXCLUDED.sentiment_1d,
                    sentiment_3d       = EXCLUDED.sentiment_3d,
                    sentiment_7d       = EXCLUDED.sentiment_7d,
                    sentiment_momentum = EXCLUDED.sentiment_momentum
            """), {
                "ticker": ticker,
                "date"  : date.strftime("%Y-%m-%d"),
                "s1d"   : safe_float(row.get("sentiment_1d")),
                "s3d"   : safe_float(row.get("sentiment_3d")),
                "s7d"   : safe_float(row.get("sentiment_7d")),
                "smom"  : safe_float(row.get("sentiment_momentum")),
            })
    print(f"  Saved sentiment for {ticker}")

    
def load_features_with_sentiment(
    ticker: str,
    start : str = None
) -> pd.DataFrame:
    """
    Load prices + indicators + sentiment — full feature set.
    Uses LEFT JOIN so rows without sentiment get 0 (not dropped).
    COALESCE fills NULL with 0 when no news existed for that day.
    This replaces load_features() for the enhanced model.
    """
    query = """
        SELECT
            p.date, p.close,
            i.sma_20, i.sma_50, i.ema_20,
            i.rsi, i.macd, i.macd_signal, i.macd_hist,
            i.bb_upper, i.bb_lower, i.bb_width, i.bb_pct,
            i.volume_ratio,
            COALESCE(s.sentiment_1d,       0) AS sentiment_1d,
            COALESCE(s.sentiment_3d,       0) AS sentiment_3d,
            COALESCE(s.sentiment_7d,       0) AS sentiment_7d,
            COALESCE(s.sentiment_momentum, 0) AS sentiment_momentum
        FROM prices p
        JOIN indicators i
            ON p.ticker = i.ticker AND p.date = i.date
        LEFT JOIN sentiment s
            ON p.ticker = s.ticker AND p.date = s.date
        WHERE p.ticker = :ticker
    """
    params = {"ticker": ticker}
    if start:
        query += " AND p.date >= :start"
        params["start"] = start
    query += " ORDER BY p.date ASC"

    with get_connection() as conn:
        df = pd.read_sql_query(text(query), conn, params=params)

    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")
    