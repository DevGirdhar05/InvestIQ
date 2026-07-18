import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


def wait_for_db(max_retries=30, delay=2):
    """Wait for PostgreSQL to be ready before connecting."""
    from sqlalchemy.exc import OperationalError
    from src.data.database import engine

    print("Waiting for database...")
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("SELECT 1"))
            print("  Database ready.")
            return True
        except Exception:
            print(f"  Attempt {attempt+1}/{max_retries} — retrying in {delay}s...")
            time.sleep(delay)

    print("  Database not available after max retries.")
    return False


def main():
    if not wait_for_db():
        sys.exit(1)

    from src.data.database import initialise_database
    print("Initialising database schema...")
    initialise_database()

    from src.data.database import get_connection
    from sqlalchemy import text

    with get_connection() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM prices"))
        count  = result.fetchone()[0]

    if count == 0:
        print("No data found — running initial pipeline...")
        from src.data.pipeline import run_pipeline
        run_pipeline(period="2y")
        print("Initial data load complete.")
    else:
        print(f"Database has {count} price rows — skipping pipeline.")

    # ── Always run sentiment pipeline on startup ──────────────
    # Sentiment table may be empty even if prices exist
    # (fresh Docker volume, or first deploy)
    with get_connection() as conn:
        result = conn.execute(
            text("SELECT COUNT(*) FROM sentiment")
        )
        sent_count = result.fetchone()[0]

    if sent_count == 0:
        print("No sentiment data — running sentiment pipeline...")
        try:
            from src.sentiment.pipeline import run_sentiment_pipeline
            run_sentiment_pipeline(
                ["RELIANCE.NS","TCS.NS","INFY.NS",
                 "HDFCBANK.NS","WIPRO.NS"],
                days_back=30
            )
            print("Sentiment pipeline complete.")
        except Exception as e:
            print(f"Sentiment pipeline failed (non-fatal): {e}")
            print("Sentiment will show neutral until pipeline runs.")
    else:
        print(f"Sentiment has {sent_count} rows — skipping.")

    print("Initialisation complete.")

    
if __name__ == "__main__":
    main()