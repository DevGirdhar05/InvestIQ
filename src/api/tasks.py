import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from celery import Celery
from celery.schedules import crontab
import os
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Celery uses Redis as both broker (message queue) and backend
# (result storage). Same Redis instance, different DB numbers.
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "investiq",
    broker  = REDIS_URL,
    backend = REDIS_URL
)

celery_app.conf.update(
    task_serializer  = "json",
    result_serializer= "json",
    accept_content   = ["json"],
    timezone         = "Asia/Kolkata",   # IST for NSE market hours
    enable_utc       = False,
)

# ── Scheduled tasks ───────────────────────────────────────────────
celery_app.conf.beat_schedule = {
    "daily-data-update": {
        "task"    : "src.api.tasks.run_daily_pipeline",
        "schedule": crontab(
            hour   = 16,
            minute = 15,
            day_of_week = "1-5"   # Monday to Friday only
        ),
        # NSE closes at 3:30 PM IST
        # We run at 4:15 PM to ensure all data is settled
    },
}


@celery_app.task(bind=True, max_retries=3)
def run_daily_pipeline(self):
    """
    Fetch latest market data and update the database.
    Runs automatically at 4:15 PM IST on weekdays.

    bind=True gives access to self for retry logic.
    max_retries=3 means it retries 3 times if it fails.
    """
    try:
        print("Celery: starting daily pipeline...")
        from src.data.pipeline import run_daily_update
        results = run_daily_update()

        # Invalidate cache after data update
        # so next request gets fresh data
        from src.api.cache import cache_flush_pattern
        cache_flush_pattern("analyze:*")
        cache_flush_pattern("explain:*")
        cache_flush_pattern("sentiment:*")

        print(f"Celery: pipeline complete. {results}")
        return results

    except Exception as exc:
        # Retry after 5 minutes on failure
        raise self.retry(exc=exc, countdown=300)


@celery_app.task
def run_pipeline_for_ticker(ticker: str):
    """
    Fetch and update data for a single ticker on demand.
    Called when a user requests a ticker not yet in the DB.
    """
    from src.data.pipeline import run_pipeline
    result = run_pipeline(tickers=[ticker], period="2y")

    # Clear cache for this ticker
    from src.api.cache import cache_delete
    cache_delete(f"analyze:{ticker}")
    cache_delete(f"explain:{ticker}")

    return result


@celery_app.task
def invalidate_cache(pattern: str = "*"):
    """Manually invalidate cache entries matching a pattern."""
    from src.api.cache import cache_flush_pattern
    cache_flush_pattern(pattern)
    return f"Cache cleared for pattern: {pattern}"