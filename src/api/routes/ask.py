from fastapi import APIRouter, HTTPException
from src.api.models import AskRequest, AskResponse
from src.rag.qa_engine import answer_question

router = APIRouter(prefix="/ask", tags=["Q&A"])


@router.post("/", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Answer an investing question using RAG.

    Retrieves relevant context from InvestIQ's knowledge base
    and generates a grounded plain-English answer.

    Example:
        POST /ask
        {"question": "What does RSI below 30 mean?",
         "ticker": "RELIANCE.NS"}
    """
    try:
        result = answer_question(
            question = request.question,
            ticker   = request.ticker,
            use_rag  = True
        )

        return AskResponse(
            question = request.question,
            answer   = result["answer"],
            sources  = result["sources"],
            used_rag = result["used_rag"],
            error    = None
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Q&A failed: {str(e)}"
        )