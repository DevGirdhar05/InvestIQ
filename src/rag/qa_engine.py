import os
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from .retriever import get_context_for_query, retrieve

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

MODEL_NAME = "gemini-3.1-flash-lite"


def _get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


def answer_question(
    question    : str,
    ticker      : str = None,
    use_rag     : bool = True
) -> dict:
    """
    Answer an investing question using RAG.

    Flow:
    1. Retrieve relevant chunks from knowledge base
    2. Build prompt with retrieved context
    3. Call Gemini to generate grounded answer
    4. Return answer + sources

    Args:
        question : user's question in natural language
        ticker   : optional — adds stock-specific context
        use_rag  : if False, answers from LLM memory only
                   (for comparison/testing purposes)

    Returns dict with:
        answer   : plain-English answer string
        sources  : list of source document titles used
        chunks   : raw retrieved chunks (for debugging)
        used_rag : whether RAG was used
    """
    chunks  = []
    context = ""

    if use_rag:
        chunks  = retrieve(question, n_results=3)
        context = get_context_for_query(question, n_results=3)

    # Build the prompt
    ticker_context = (
        f"\nThe user is asking in the context of {ticker}."
        if ticker else ""
    )

    if use_rag and context:
        prompt = f"""
You are InvestIQ's Q&A assistant helping beginner investors
understand stock market concepts.

Answer the following question using ONLY the context provided
below. If the answer is not in the context, say so honestly —
do not make up information.{ticker_context}

CONTEXT FROM INVESTIQ KNOWLEDGE BASE:
{context}

USER QUESTION: {question}

Instructions:
- Answer in plain English, under 120 words
- Reference the source concepts naturally
- Do not recommend buying or selling
- If context doesn't fully answer the question, say what you
  know from context and acknowledge the gap
""".strip()
    else:
        # No RAG — answer from model memory
        prompt = f"""
You are InvestIQ's Q&A assistant helping beginner investors.
Answer this question in plain English, under 120 words.
Do not recommend buying or selling.{ticker_context}

Question: {question}
""".strip()

    client = _get_client()

    if client is None:
        return {
            "answer"  : "API not configured. Please add GEMINI_API_KEY to .env",
            "sources" : [],
            "chunks"  : [],
            "used_rag": use_rag
        }

    # Call Gemini with retry
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model   = MODEL_NAME,
                contents= prompt,
                config  = types.GenerateContentConfig(
                    max_output_tokens = 400,
                    temperature       = 0.2
                    # Low temperature for factual Q&A
                    # We want consistent, accurate answers
                    # not creative variation
                )
            )
            answer = response.text.strip()
            break

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                wait = 60 * (attempt + 1)
                print(f"  Rate limit — waiting {wait}s...")
                time.sleep(wait)
                continue
            else:
                answer = (
                    f"Could not generate answer: {e}. "
                    f"Please try again."
                )
                break
    else:
        answer = "Rate limit exceeded. Please try again in a minute."

    sources = list(set([c["title"] for c in chunks]))

    return {
        "answer"  : answer,
        "sources" : sources,
        "chunks"  : chunks,
        "used_rag": use_rag
    }


def answer_batch(questions: list, ticker: str = None) -> list:
    """
    Answer multiple questions — used for FAQ generation.
    Adds delay between calls to respect rate limits.
    """
    results = []
    for i, question in enumerate(questions):
        if i > 0:
            time.sleep(4)
        result = answer_question(question, ticker=ticker)
        result["question"] = question
        results.append(result)
        print(f"  ✓ Q{i+1}: {question[:50]}...")
    return results