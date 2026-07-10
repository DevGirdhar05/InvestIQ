import os
import json
import time
import hashlib
from google import genai
from google.genai import types
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# ── Configure Gemini ──────────────────────────────────────────────
api_key = os.getenv("GEMINI_API_KEY")

client = None
if api_key:
    client = genai.Client(api_key=api_key)


# ── Feature name mapping ──────────────────────────────────────────
FEATURE_LABELS = {
    "sma_20"            : "20-day moving average",
    "sma_50"            : "50-day moving average",
    "ema_20"            : "20-day exponential moving average",
    "rsi"               : "RSI momentum indicator",
    "rsi_normalized"    : "RSI momentum indicator",
    "macd"              : "MACD trend indicator",
    "macd_signal"       : "MACD signal line",
    "macd_hist"         : "MACD momentum histogram",
    "bb_pct"            : "Bollinger Band position",
    "bb_width"          : "Bollinger Band width (volatility)",
    "bb_upper"          : "Bollinger upper band",
    "bb_lower"          : "Bollinger lower band",
    "volume_ratio"      : "trading volume vs average",
    "price_vs_sma20"    : "price position vs 20-day average",
    "price_vs_sma50"    : "price position vs 50-day average",
    "sentiment_1d"      : "1-day news sentiment",
    "sentiment_3d"      : "3-day news sentiment trend",
    "sentiment_7d"      : "7-day news sentiment trend",
    "sentiment_momentum": "news sentiment momentum",
}

FEATURE_DESCRIPTIONS = {
    "sma_50"            : "whether the stock's medium-term trend is up or down",
    "sma_20"            : "whether the stock's short-term trend is up or down",
    "macd_hist"         : "whether momentum is accelerating or decelerating",
    "macd_signal"       : "the smoothed momentum trend direction",
    "macd"              : "the overall momentum trend",
    "price_vs_sma50"    : "how far the price is from its long-term average",
    "price_vs_sma20"    : "how far the price is from its short-term average",
    "rsi"               : "whether the stock is overbought or oversold",
    "rsi_normalized"    : "whether the stock is overbought or oversold",
    "bb_pct"            : "where the price sits within its normal trading range",
    "bb_width"          : "how volatile the stock has been recently",
    "volume_ratio"      : "whether trading activity is unusually high or low",
    "sentiment_3d"      : "the tone of recent news about this company",
    "sentiment_1d"      : "today's news sentiment about this company",
    "sentiment_momentum": "whether news sentiment is improving or worsening",
}

SYSTEM_PROMPT = """
You are InvestIQ's explanation engine. You translate machine
learning model outputs into plain English for beginner investors.

Your tone is friendly, clear, and honest. You never recommend
buying or selling — you only explain what the signals suggest
and how confident the model is.

You always remind users that stock market predictions are
probabilistic — even a high-confidence signal can be wrong.

You explain technical terms in brackets when you must use them.
You keep explanations concise — under 150 words.
""".strip()


def build_explanation_prompt(
    ticker      : str,
    company_name: str,
    date        : str,
    prob_up     : float,
    confidence  : str,
    top_features: list,
    horizon     : int = 10
) -> str:
    """
    Build the prompt for Gemini.
    Converts SHAP output into structured natural language context.
    """
    prob_pct  = round(prob_up * 100, 1)
    prob_down = round((1 - prob_up) * 100, 1)

    feature_lines = []
    for f in top_features[:5]:
        label       = FEATURE_LABELS.get(f["feature"], f["feature"])
        description = FEATURE_DESCRIPTIONS.get(
            f["feature"], f["feature"]
        )
        direction = f["direction"]
        magnitude = f["magnitude"]

        if magnitude > 0.3:
            strength = "strongly"
        elif magnitude > 0.15:
            strength = "moderately"
        else:
            strength = "mildly"

        feature_lines.append(
            f"- {label}: {strength} {direction} "
            f"(measures {description})"
        )

    features_text = "\n".join(feature_lines)

    # For Gemini we combine system + user into one prompt
    # since the free API doesn't support separate system messages
    # in the same way
    prompt = f"""
{SYSTEM_PROMPT}

---

You are analysing {company_name} ({ticker}) as of {date}.

PREDICTION:
- Probability of price rising in {horizon} trading days: {prob_pct}%
- Probability of price falling: {prob_down}%
- Model confidence: {confidence.upper()}

TOP SIGNALS DRIVING THIS PREDICTION (most to least influential):
{features_text}

Please write a clear, friendly explanation of this prediction for
a beginner investor who has never heard of RSI or MACD.

Your explanation should:
1. Start with the overall picture in one sentence
2. Explain the 2-3 most important signals in plain English
3. Mention any conflicting signals honestly
4. End with a confidence statement and a reminder that this
   is a probability, not a guarantee

Keep the explanation under 150 words. Do not use technical
jargon without explanation. Do not recommend buying or selling.
""".strip()

    return prompt

def build_batch_prompt(predictions: list) -> str:
    """
    Build ONE prompt for the entire portfolio.
    Gemini returns a JSON array.
    """

    portfolio_text = []

    for pred in predictions:

        prob_pct = round(pred["prob_up"] * 100, 1)
        prob_down = round((1 - pred["prob_up"]) * 100, 1)

        feature_lines = []

        for f in pred["top_features"][:5]:

            label = FEATURE_LABELS.get(
                f["feature"],
                f["feature"]
            )

            description = FEATURE_DESCRIPTIONS.get(
                f["feature"],
                f["feature"]
            )

            direction = f["direction"]

            feature_lines.append(
                f"- {label}: {direction} "
                f"(measures {description})"
            )

        portfolio_text.append(
    f"""
    Ticker: {pred["ticker"]}
    Company: {pred.get("company_name", pred["ticker"])}

    Probability Up: {prob_pct}%
    Probability Down: {prob_down}%

    Confidence:
    {pred["confidence"]}

    Top Signals:
    {chr(10).join(feature_lines)}
    """
            )

    return f"""
    {SYSTEM_PROMPT}

    You are explaining predictions for MULTIPLE stocks.

    Return ONLY valid JSON.

    Format:

    [
    {{
    "ticker":"RELIANCE.NS",
    "explanation":"..."
    }},
    {{
    "ticker":"TCS.NS",
    "explanation":"..."
    }}
    ]

    Explanation Rules:

    - Under 120 words
    - Friendly
    - Beginner audience
    - Mention strongest signals
    - Mention confidence
    - Mention uncertainty
    - Never recommend buy/sell

    Stocks:

    {chr(10).join(portfolio_text)}
    """

def parse_batch_response(text: str):

    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    try:
        data = json.loads(text)

        return {
            item["ticker"]: item["explanation"]
            for item in data
        }

    except Exception:

        return {}

def generate_explanation(
    ticker      : str,
    company_name: str,
    date        : str,
    prob_up     : float,
    confidence  : str,
    top_features: list,
    horizon     : int = 10
) -> str:

    if client is None:
        return _template_explanation(
            company_name, prob_up, confidence, top_features
        )

    prompt = build_explanation_prompt(
        ticker, company_name, date,
        prob_up, confidence, top_features, horizon
    )

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model   = "gemini-3.1-flash-lite",
                contents= prompt,
                config  = types.GenerateContentConfig(
                    max_output_tokens = 800,
                    temperature       = 0.3
                )
            )
            return response.text.strip()

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                wait = 60 * (attempt + 1)
                print(f"  Rate limit — waiting {wait}s...")
                time.sleep(wait)
                continue
            elif "503" in error_str or "UNAVAILABLE" in error_str:
                wait = 15 * (attempt + 1)
                print(f"  Server busy — waiting {wait}s...")
                time.sleep(wait)
                continue
            elif "404" in error_str or "NOT_FOUND" in error_str:
                print(f"  Model not found — trying gemini-3.1-flash...")
                try:
                    response = client.models.generate_content(
                        model   = "gemini-3.1-flash",
                        contents= prompt,
                        config  = types.GenerateContentConfig(
                            max_output_tokens=800,
                            temperature=0.3
                        )
                    )
                    return response.text.strip()
                except Exception:
                    break
            else:
                print(f"  Gemini error: {e}")
                break

    return _template_explanation(
        company_name, prob_up, confidence, top_features
    )
def _template_explanation(
    company_name: str,
    prob_up     : float,
    confidence  : str,
    top_features: list
) -> str:
    """
    Fallback template-based explanation when API is unavailable.
    Used when Gemini API key is missing or rate limit hit.
    Ensures the app always shows something useful.
    """
    prob_pct    = round(prob_up * 100, 1)
    direction   = "rise" if prob_up > 0.5 else "fall"
    top_feature = top_features[0] if top_features else None
    top_label   = FEATURE_LABELS.get(
        top_feature["feature"], top_feature["feature"]
    ) if top_feature else "technical indicators"
    top_dir     = top_feature["direction"] if top_feature else "neutral"

    return (
        f"{company_name} shows a {prob_pct}% probability of "
        f"a price {direction} over the next 10 trading days. "
        f"The strongest signal comes from the {top_label}, "
        f"which is currently {top_dir}. "
        f"Model confidence is {confidence}. "
        f"Remember: this is a probability estimate, not a guarantee."
    )


def generate_indicator_explanation(
    indicator_name: str,
    indicator_value: float,
    ticker: str = ""
) -> str:
    if client is None:
        return f"{indicator_name} is currently {indicator_value:.2f}."

    prompt = f"""
Explain what a {indicator_name} value of {indicator_value:.2f}
means for {'stock ' + ticker if ticker else 'a stock'}.
Keep it under 60 words. Plain English only.
No buy/sell recommendations. Beginner audience.
""".strip()

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=200,
                temperature=0.2,
            ),
        )
        return response.text.strip()
    except Exception:
        return f"{indicator_name}: {indicator_value:.2f}"

def batch_explain_portfolio(predictions: list):

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:

        return [

            {
                **pred,
                "explanation":
                _template_explanation(
                    pred.get("company_name", pred["ticker"]),
                    pred["prob_up"],
                    pred["confidence"],
                    pred["top_features"]
                )
            }

            for pred in predictions
        ]


    prompt = build_batch_prompt(predictions)

    try:

        response = client.models.generate_content(

            model="gemini-3.1-flash-lite",

            contents=prompt,

            config=types.GenerateContentConfig(

                temperature=0.3,

                max_output_tokens=1500,

                response_mime_type="application/json"

            )

        )

        explanations = parse_batch_response(
            response.text
        )

    except Exception as e:

        print("Gemini batch failed:", e)

        explanations = {}

    results = []

    for pred in predictions:

        explanation = explanations.get(

            pred["ticker"],

            _template_explanation(

                pred.get(
                    "company_name",
                    pred["ticker"]
                ),

                pred["prob_up"],

                pred["confidence"],

                pred["top_features"]

            )

        )

        results.append({

            **pred,

            "explanation": explanation

        })

    return results

def make_cache_key(
    ticker      : str,
    date        : str,
    prob_up     : float,
    top_features: list
) -> str:
    """
    Generate a deterministic cache key for an explanation request.
    Same inputs → same key → Redis cache hit → no API call.
    Used in Week 11 when Redis caching is implemented.
    """
    content = json.dumps({
        "ticker"  : ticker,
        "date"    : date,
        "prob_up" : round(prob_up, 3),
        "features": [f["feature"] for f in top_features[:3]]
    }, sort_keys=True)
    return f"explain:{hashlib.md5(content.encode()).hexdigest()}"