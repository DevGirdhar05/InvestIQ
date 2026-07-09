import os
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# NewsAPI searches text — it doesn't understand ticker symbols
# Map tickers to company names that appear in news headlines
TICKER_TO_QUERY = {
    "RELIANCE.NS" : "Reliance Industries",
    "TCS.NS"      : "Tata Consultancy Services TCS",
    "INFY.NS"     : "Infosys",
    "HDFCBANK.NS" : "HDFC Bank",
    "WIPRO.NS"    : "Wipro",
}


def fetch_news(
    ticker      : str,
    days_back   : int = 7,
    max_articles: int = 50
) -> pd.DataFrame:
    """
    Fetch recent news headlines for a stock via NewsAPI.

    Args:
        ticker       : e.g. "RELIANCE.NS"
        days_back    : how many calendar days of news to fetch
        max_articles : maximum articles to return (NewsAPI cap=100)

    Returns:
        DataFrame with columns: date, headline, description, source
        Empty DataFrame if no articles found or API unavailable.
    """
    from newsapi import NewsApiClient

    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "NEWS_API_KEY not found in .env. "
            "Get a free key at newsapi.org"
        )

    query     = TICKER_TO_QUERY.get(ticker, ticker)
    newsapi   = NewsApiClient(api_key=api_key)
    date_from = (datetime.now() - timedelta(days=days_back)
                 ).strftime("%Y-%m-%d")
    date_to   = datetime.now().strftime("%Y-%m-%d")

    try:
        response = newsapi.get_everything(
            q          = query,
            from_param = date_from,
            to         = date_to,
            language   = "en",
            sort_by    = "publishedAt",
            page_size  = min(max_articles, 100)
        )
    except Exception as e:
        print(f"  NewsAPI error for {ticker}: {e}")
        return pd.DataFrame()

    if response["status"] != "ok" or not response["articles"]:
        print(f"  No articles found for {ticker} "
              f"({date_from} to {date_to})")
        return pd.DataFrame()

    articles = []
    for article in response["articles"]:
        articles.append({
            "date"       : article["publishedAt"][:10],
            "headline"   : article["title"]       or "",
            "description": article["description"] or "",
            "source"     : article["source"]["name"] or ""
        })

    df           = pd.DataFrame(articles)
    df["date"]   = pd.to_datetime(df["date"])
    df           = df.sort_values("date", ascending=False
                                   ).reset_index(drop=True)

    print(f"  Fetched {len(df)} articles for {ticker} "
          f"({date_from} → {date_to})")
    return df