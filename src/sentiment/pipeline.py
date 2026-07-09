import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.sentiment.news_fetcher import fetch_news, TICKER_TO_QUERY
from src.sentiment.finbert      import FinBERTScorer
from src.sentiment.aggregator   import (
    aggregate_daily_sentiment,
    build_sentiment_features
)
from src.data.database import save_sentiment, load_prices

# Load FinBERT once — reuse across all tickers
_scorer = None

def get_scorer() -> FinBERTScorer:
    """Lazy loader — only initialise FinBERT when first needed."""
    global _scorer
    if _scorer is None:
        _scorer = FinBERTScorer()
    return _scorer


def run_sentiment_pipeline(
    tickers : list,
    days_back: int = 30
) -> dict:
    """
    Full pipeline:
    1. Fetch headlines via NewsAPI
    2. Score each with FinBERT
    3. Aggregate to daily scores
    4. Build rolling features (1d, 3d, 7d, momentum)
    5. Save to PostgreSQL sentiment table
    """
    scorer  = get_scorer()
    results = {"success": [], "failed": []}

    for ticker in tickers:
        print(f"\n{'─'*45}")
        print(f"Sentiment pipeline: {ticker}")

        try:
            # Step 1: Fetch news
            news_df = fetch_news(ticker, days_back=days_back)
            if news_df.empty:
                print(f"  No news — skipping {ticker}")
                results["failed"].append(ticker)
                continue

            # Step 2: Score with FinBERT
            scored_df = scorer.score_dataframe(news_df)
            print(f"  Score range: "
                  f"{scored_df['sentiment_score'].min():.3f} to "
                  f"{scored_df['sentiment_score'].max():.3f}")

            # Step 3: Aggregate to daily
            daily = aggregate_daily_sentiment(scored_df,
                                              method="mean")

            # Step 4: Build features aligned to price dates
            prices    = load_prices(ticker)
            features  = build_sentiment_features(
                daily, prices.index, windows=[1, 3, 7]
            )

            # Step 5: Save to DB
            save_sentiment(ticker, features)

            results["success"].append(ticker)
            print(f"  3d sentiment today: "
                  f"{features['sentiment_3d'].iloc[-1]:.3f}")
            print(f"  Momentum today    : "
                  f"{features['sentiment_momentum'].iloc[-1]:.3f}")
            print(f"  ✓ {ticker} complete")

        except Exception as e:
            results["failed"].append(ticker)
            print(f"  ✗ {ticker} failed: {e}")

    print(f"\n{'═'*45}")
    print(f"Sentiment pipeline complete.")
    print(f"  Success: {results['success']}")
    if results["failed"]:
        print(f"  Failed : {results['failed']}")

    return results