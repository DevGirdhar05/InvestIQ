from fastapi import APIRouter, HTTPException
from src.api.models import ExplanationResponse
from src.api.routes.analyze import (
    analyze_ticker, get_company_name
)
from src.models.explainer import generate_explanation
from src.api.cache import cache_get, cache_set, TTL_EXPLANATION
from datetime import date as date_module


router = APIRouter(prefix="/explain", tags=["Explanation"])

HORIZON = 10


@router.get("/{ticker}", response_model=ExplanationResponse)
async def explain_ticker(ticker: str):
    ticker    = ticker.upper()
    cache_key = f"explain:{ticker}"
    cached    = cache_get(cache_key)

    if cached:
        return ExplanationResponse(**cached)

    try:
        analysis     = await analyze_ticker(ticker)
        company_name = get_company_name(ticker)
        explanation = generate_explanation(
            ticker       = ticker,
            company_name = company_name,
            date         = date_module.today().strftime("%B %d, %Y"),  # always today
            prob_up      = analysis.probability_up,
            confidence   = analysis.confidence,
            top_features = [f.dict() for f in analysis.top_features],
            horizon      = HORIZON
        )

        result = ExplanationResponse(
            ticker        = ticker,
            date          = analysis.date,
            probability_up= analysis.probability_up,
            confidence    = analysis.confidence,
            explanation   = explanation,
            word_count    = len(explanation.split()),
            error         = None
        )

        cache_set(cache_key, result.dict(), ttl=TTL_EXPLANATION)
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
            detail=f"Explanation failed: {str(e)}")