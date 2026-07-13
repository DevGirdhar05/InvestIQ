import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.api.routes import analyze, explain, sentiment, ask
from src.api.models import HealthResponse, MarketOverviewResponse
from src.api.dependencies import (
    get_xgb_model, get_shap_explainer, get_chroma_collection
)
from src.data.database import get_connection
from sqlalchemy import text
import pandas as pd
from datetime import date


# ── Startup and shutdown ──────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Code here runs ONCE at startup before any requests are handled.
    Use it to pre-load expensive resources so the first request
    isn't slow.

    Without this, the first /analyze request would load the model,
    build the SHAP explainer, and load ChromaDB — taking 5-10s.
    With lifespan, all of this happens at startup — requests are
    fast immediately.
    """
    print("InvestIQ API starting up...")

    print("  Loading XGBoost model...")
    get_xgb_model()

    print("  Building SHAP explainer...")
    get_shap_explainer()

    print("  Loading ChromaDB knowledge base...")
    get_chroma_collection()

    print("  All resources loaded. API ready.")

    yield   # API runs here

    # Shutdown code (if needed) goes after yield
    print("InvestIQ API shutting down.")


# ── App initialisation ────────────────────────────────────────────
app = FastAPI(
    title       = "InvestIQ API",
    description = """
AI-powered stock analysis platform for beginner NSE investors.

## Endpoints

- **/analyze/{ticker}** — ML prediction with SHAP explanations
- **/explain/{ticker}** — Plain-English explanation via Gemini
- **/sentiment/{ticker}** — FinBERT news sentiment scores
- **/ask** — RAG-powered investing Q&A
- **/overview** — Market overview for all watchlist stocks
- **/health** — API health check

## Supported tickers
RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS, WIPRO.NS
    """,
    version     = "1.0.0",
    lifespan    = lifespan
)

# ── CORS middleware ───────────────────────────────────────────────
# CORS allows the React frontend (different port/domain) to call
# this API. Without CORS, browsers block cross-origin requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],   # restrict to your domain in production
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Register routes ───────────────────────────────────────────────
app.include_router(analyze.router)
app.include_router(explain.router)
app.include_router(sentiment.router)
app.include_router(ask.router)


# ── Root and health endpoints ─────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {
        "name"       : "InvestIQ API",
        "version"    : "1.0.0",
        "docs"       : "/docs",
        "health"     : "/health",
        "endpoints"  : [
            "/analyze/{ticker}",
            "/explain/{ticker}",
            "/sentiment/{ticker}",
            "/ask",
            "/overview"
        ]
    }


@app.get("/health", response_model=HealthResponse, tags=["Root"])
async def health_check():
    from src.api.cache import get_cache_stats

    db_status    = "ok"
    model_status = "ok"

    try:
        with get_connection() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {e}"

    try:
        get_xgb_model()
    except Exception as e:
        model_status = f"error: {e}"

    cache_stats = get_cache_stats()
    overall     = (
        "ok" if db_status == "ok"
        and model_status == "ok"
        else "degraded"
    )

    return HealthResponse(
        status   = overall,
        database = db_status,
        model    = model_status
    )


@app.get("/overview", response_model=MarketOverviewResponse,
         tags=["Root"])
async def market_overview():
    """
    Latest signals for all watchlist stocks in one call.
    Used by the frontend's market overview table.
    """
    from src.data.database import get_latest_signals

    WATCHLIST = [
        "RELIANCE.NS", "TCS.NS", "INFY.NS",
        "HDFCBANK.NS", "WIPRO.NS"
    ]

    try:
        signals_df = get_latest_signals(WATCHLIST)
        stocks     = signals_df.to_dict(orient="records")

        # Convert date objects to strings for JSON serialisation
        for stock in stocks:
            if "date" in stock and hasattr(stock["date"], "isoformat"):
                stock["date"] = stock["date"].isoformat()

        return MarketOverviewResponse(
            date  = date.today().isoformat(),
            stocks= stocks
        )
    except Exception as e:
        return MarketOverviewResponse(
            date  = date.today().isoformat(),
            stocks= []
        )