from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class FeatureContribution(BaseModel):
    """Single SHAP feature contribution."""
    feature   : str
    value     : float
    shap_value: float
    direction : str   # "bullish" or "bearish"
    magnitude : float


class AnalysisResponse(BaseModel):
    """Response from /analyze/{ticker}"""
    ticker          : str
    company_name    : str
    date            : str
    probability_up  : float = Field(ge=0, le=1)
    probability_down: float = Field(ge=0, le=1)
    confidence      : str   # "high", "medium", "low"
    top_features    : list[FeatureContribution]
    horizon_days    : int
    training_samples: int
    error           : Optional[str] = None


class ExplanationResponse(BaseModel):
    """Response from /explain/{ticker}"""
    ticker         : str
    date           : str
    probability_up : float
    confidence     : str
    explanation    : str
    word_count     : int
    error          : Optional[str] = None


class SentimentResponse(BaseModel):
    """Response from /sentiment/{ticker}"""
    ticker              : str
    date                : str
    sentiment_1d        : float
    sentiment_3d        : float
    sentiment_7d        : float
    sentiment_momentum  : float
    sentiment_label     : str   # "STRONGLY POSITIVE" etc
    error               : Optional[str] = None


class AskRequest(BaseModel):
    """Request body for /ask"""
    question: str = Field(min_length=5, max_length=500)
    ticker  : Optional[str] = None


class AskResponse(BaseModel):
    """Response from /ask"""
    question : str
    answer   : str
    sources  : list[str]
    used_rag : bool
    error    : Optional[str] = None


class HealthResponse(BaseModel):
    """Response from /health"""
    status  : str
    database: str
    model   : str
    cache   : Optional[dict] = None
    version : str = "1.0.0"


class MarketOverviewResponse(BaseModel):
    """Response from /overview"""
    date   : str
    stocks : list[dict]