import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def wait_for_db(max_retries=30, delay=2):
    """Wait for PostgreSQL to be ready before connecting."""
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

    from src.data.database import initialise_database, get_connection
    from sqlalchemy import text

    print("Initialising database schema...")
    initialise_database()

    with get_connection() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM prices"))
        count = result.fetchone()[0]

    if count == 0:
        print("No data found — running initial pipeline...")
        from src.data.pipeline import run_pipeline
        run_pipeline(period="2y")
        print("Initial data load complete.")
    else:
        print(f"Database has {count} price rows — skipping pipeline.")

    # Skip FinBERT on startup
    print("Skipping sentiment pipeline on startup.")

    print("Initialisation complete.")


if __name__ == "__main__":
    main()