import joblib
import shap
import xgboost as xgb
from pathlib import Path
from functools import lru_cache
from src.rag.retriever import get_or_create_collection

MODELS_DIR = Path(__file__).parent.parent.parent / "models"


@lru_cache(maxsize=1)
def get_xgb_model() -> xgb.XGBClassifier:
    """
    Load XGBoost model once and cache it.
    lru_cache(maxsize=1) means it loads on first call
    and returns the cached version on all subsequent calls.
    Loading from disk takes ~100ms — we don't want that per request.
    """
    model_path = MODELS_DIR / "xgboost_model.pkl"
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found at {model_path}. "
            f"Run notebooks/05_xgboost.ipynb first."
        )
    return joblib.load(model_path)


@lru_cache(maxsize=1)
def get_shap_explainer() -> shap.TreeExplainer:
    """
    Build SHAP explainer once and cache it.
    TreeExplainer needs the trained model — load model first.
    """
    model = get_xgb_model()
    return shap.TreeExplainer(model)


@lru_cache(maxsize=1)
def get_chroma_collection():
    """Load ChromaDB collection once at startup."""
    return get_or_create_collection()


def get_model_and_explainer():
    """
    Convenience function returning both model and explainer.
    Used in route handlers that need both.
    """
    return get_xgb_model(), get_shap_explainer()