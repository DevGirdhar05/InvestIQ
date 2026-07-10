from fastapi import APIRouter, HTTPException
from src.api.models import ExplanationResponse
from src.api.routes.analyze import (
    analyze_ticker, get_company_name
)
from src.models.explainer import generate_explanation

router = APIRouter(prefix="/explain", tags=["Explanation"])

HORIZON = 10


@router.get("/{ticker}", response_model=ExplanationResponse)
async def explain_ticker(ticker: str):
    """
    Get plain-English explanation for a ticker's prediction.

    Calls /analyze internally, then passes the result to
    Gemini to generate a beginner-friendly explanation.
    """
    ticker = ticker.upper()

    try:
        # Get the analysis first
        analysis = await analyze_ticker(ticker)

        company_name = get_company_name(ticker)

        # Generate explanation
        explanation = generate_explanation(
            ticker       = ticker,
            company_name = company_name,
            date         = analysis.date,
            prob_up      = analysis.probability_up,
            confidence   = analysis.confidence,
            top_features = [f.dict() for f in analysis.top_features],
            horizon      = HORIZON
        )

        return ExplanationResponse(
            ticker        = ticker,
            date          = analysis.date,
            probability_up= analysis.probability_up,
            confidence    = analysis.confidence,
            explanation   = explanation,
            word_count    = len(explanation.split()),
            error         = None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Explanation failed for {ticker}: {str(e)}"
        )