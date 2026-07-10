# Curated investing knowledge base for InvestIQ RAG system
# Each document is a self-contained explanation of one concept
# Written for beginner investors — no jargon without explanation

DOCUMENTS = [
    {
        "id"      : "rsi_basics",
        "topic"   : "RSI",
        "title"   : "What is RSI (Relative Strength Index)?",
        "content" : """
RSI stands for Relative Strength Index. It is a number between 0
and 100 that measures how fast and how much a stock's price has
been moving recently.

When RSI is above 70, the stock has been rising very quickly and
may be overbought — meaning it has risen too far too fast and
could pull back. When RSI is below 30, the stock may be oversold
— it has fallen too far too fast and could bounce back up.

RSI between 30 and 70 is considered neutral. The stock is moving
at a normal pace.

In InvestIQ, RSI is one of the key features our model uses to
predict future price direction. A low RSI (below 35) combined
with positive MACD momentum is historically one of the strongest
bullish setups we see in NIFTY50 stocks.

Important: RSI alone is not enough to make decisions. A stock
can stay overbought for weeks during a strong bull run, or stay
oversold during a prolonged bear market. Always look at multiple
signals together.
        """.strip()
    },
    {
        "id"      : "macd_basics",
        "topic"   : "MACD",
        "title"   : "What is MACD?",
        "content" : """
MACD stands for Moving Average Convergence Divergence. It sounds
complicated but the idea is simple: it measures whether a stock's
short-term momentum is stronger or weaker than its longer-term
momentum.

MACD is calculated by subtracting the 26-day average price from
the 12-day average price. When the short-term average is higher
than the long-term average, MACD is positive — the stock has
recent upward momentum. When MACD is negative, recent momentum
is downward.

The MACD histogram is the most important part for InvestIQ. It
shows whether momentum is accelerating or decelerating. A growing
histogram means momentum is building. A shrinking histogram is
an early warning that momentum is fading — often before the price
itself starts to turn.

A MACD crossover happens when the MACD line crosses above its
signal line. This is a bullish signal. When it crosses below,
it is bearish. In InvestIQ's model, the MACD histogram is the
second most important feature after the 50-day moving average.
        """.strip()
    },
    {
        "id"      : "bollinger_basics",
        "topic"   : "Bollinger Bands",
        "title"   : "What are Bollinger Bands?",
        "content" : """
Bollinger Bands are three lines drawn around a stock's price
chart. The middle band is the 20-day average price. The upper
band is the average plus two standard deviations. The lower band
is the average minus two standard deviations.

Standard deviation measures how spread out prices have been. When
the stock has been volatile, the bands widen. When the market is
calm, the bands narrow.

The Bollinger Band Squeeze happens when the bands get very narrow.
This means volatility is unusually low. Historically, squeezes
are followed by large price moves — but the direction is unknown
until the move starts. InvestIQ tracks band width to detect
squeeze conditions.

BB%B (Bollinger Percent B) tells you where the current price sits
within the bands. A value of 1.0 means the price is at the upper
band. A value of 0 means it is at the lower band. Values outside
0 to 1 mean the price has broken out of the bands.

In InvestIQ, a low BB%B (near or below 0.2) combined with
improving RSI suggests the stock is near a potential support
level.
        """.strip()
    },
    {
        "id"      : "moving_averages_basics",
        "topic"   : "Moving Averages",
        "title"   : "What are Moving Averages?",
        "content" : """
A moving average smooths out a stock's price history to reveal
the underlying trend. Instead of looking at today's price alone,
you look at the average of the last N days.

The 20-day moving average (SMA20) captures the short-term trend.
The 50-day moving average (SMA50) captures the medium-term trend.

When the current price is above the SMA50, the stock is in an
uptrend. When below, it is in a downtrend. This is one of the
most reliable and widely-used signals in technical analysis.

The Golden Cross happens when the 20-day average crosses above
the 50-day average. This is a strong bullish signal — it means
the short-term trend is now stronger than the medium-term trend.
The Death Cross is the opposite — the 20-day falls below the
50-day — a bearish signal.

In InvestIQ's XGBoost model, the 50-day moving average is the
single most important feature. Whether price is above or below
SMA50 is the strongest predictor of 10-day direction in our
NIFTY50 analysis.
        """.strip()
    },
    {
        "id"      : "atr_basics",
        "topic"   : "ATR",
        "title"   : "What is ATR (Average True Range)?",
        "content" : """
ATR stands for Average True Range. It measures how much a stock
typically moves in a single day, expressed in rupees (or the
stock's currency).

If a stock has an ATR of ₹25, it typically moves about ₹25 per
day — either up or down. A high ATR means the stock is volatile
and moves a lot. A low ATR means it is calm and predictable.

ATR as a percentage (ATR%) is more useful for comparing stocks
at different price levels. A stock at ₹1000 with ATR ₹20 has
ATR% of 2% — it moves 2% per day on average. A stock at ₹200
with ATR ₹4 also has ATR% of 2%.

InvestIQ uses ATR% to tell you the expected daily move for each
stock. When model confidence is LOW, a high ATR% means there is
more uncertainty — the stock could move significantly in either
direction. When ATR% is low, even uncertain predictions are less
risky because the stock doesn't move much.

ATR does not predict direction — only magnitude. It is a risk
measurement tool, not a trading signal.
        """.strip()
    },
    {
        "id"      : "volume_basics",
        "topic"   : "Volume",
        "title"   : "What does trading volume mean?",
        "content" : """
Volume is the number of shares that were bought and sold on a
given day. High volume means many investors were active. Low
volume means the market was quiet.

Volume confirms price moves. If a stock rises 3% on high volume,
it means many investors participated in the move — it is more
likely to continue. If it rises 3% on low volume, fewer investors
drove the move — it may not be as reliable.

InvestIQ tracks volume ratio — today's volume compared to the
20-day average. A volume ratio of 2.0 means twice the normal
volume traded today. This often signals that institutions (large
funds and banks) are actively buying or selling.

Unusually high volume (ratio above 2.5) combined with a price
move in one direction is one of the strongest short-term signals.
It suggests conviction behind the move.

Low volume during a price rise can be a warning sign — the move
may not have broad support.
        """.strip()
    },
    {
        "id"      : "probability_explained",
        "topic"   : "Probability",
        "title"   : "What does the InvestIQ probability score mean?",
        "content" : """
InvestIQ gives you a probability score for each stock — for
example, "68% chance of rising in 10 days."

This number comes from an XGBoost machine learning model trained
on two years of historical data for NIFTY50 stocks. The model
looks at 17 signals including technical indicators and news
sentiment, then outputs the probability that the stock will be
higher 10 trading days from now.

The probability has been calibrated using Platt scaling, which
means when the model says 68%, the stock has historically risen
approximately 68% of the time in similar conditions.

Confidence levels:
- HIGH confidence: probability is far from 50% (above 70% or below 30%)
- MEDIUM confidence: probability is moderately away from 50%
- LOW confidence: probability is close to 50% — the model is uncertain

A LOW confidence signal does not mean the model is broken. It
means the signals are mixed or contradictory. In these cases, it
is wise to wait for clearer signals before acting.

Important: even HIGH confidence predictions are wrong sometimes.
No model can predict markets with certainty. Use InvestIQ as one
input in your research, not as the only basis for decisions.
        """.strip()
    },
    {
        "id"      : "shap_explained",
        "topic"   : "SHAP",
        "title"   : "How does InvestIQ explain its predictions?",
        "content" : """
InvestIQ uses SHAP values to explain why the model made each
prediction. SHAP stands for SHapley Additive exPlanations — a
method from game theory that fairly distributes credit among the
features that drove a prediction.

For every prediction, InvestIQ shows you:
- Which signals pushed the probability UP (bullish factors)
- Which signals pushed the probability DOWN (bearish factors)
- How much each signal contributed

For example, if RSI is very low (oversold), SHAP might show it
contributed +0.14 to the probability — pushing it higher because
oversold stocks tend to bounce. If price is below SMA50, SHAP
might show -0.09 — pushing probability lower because the stock
is in a downtrend.

The sum of all SHAP values plus the base rate (the average
historical UP rate, about 49%) equals the final probability.

This transparency is what makes InvestIQ different from a black
box. You never just get a number — you always see the reasoning
behind it.
        """.strip()
    },
    {
        "id"      : "sentiment_explained",
        "topic"   : "News Sentiment",
        "title"   : "How does InvestIQ use news sentiment?",
        "content" : """
InvestIQ analyses recent news headlines about each stock using
FinBERT — a version of the BERT language model fine-tuned
specifically on financial news.

Each headline is scored from -1 (very negative) to +1 (very
positive). These scores are aggregated into:
- 1-day sentiment: today's news tone
- 3-day sentiment: average tone over 3 days
- 7-day sentiment: average tone over 7 days
- Sentiment momentum: is news getting better or worse?

News sentiment is one of InvestIQ's 17 model features. It adds
information that price indicators cannot capture — for example,
a positive earnings surprise or a regulatory concern.

Sentiment alone is not reliable. A single negative headline
might be misleading. That is why InvestIQ uses 3-day and 7-day
averages to capture sustained trends rather than reacting to
individual articles.

When sentiment is strongly positive AND technical indicators are
bullish, the combination gives a higher-confidence signal than
either alone.
        """.strip()
    },
    {
        "id"      : "nifty50_explained",
        "topic"   : "NIFTY50",
        "title"   : "What is NIFTY50?",
        "content" : """
NIFTY50 is India's most important stock market index. It tracks
the 50 largest companies listed on the National Stock Exchange
(NSE) of India.

These 50 companies represent about 65% of the total value of all
stocks on the NSE. When people say "the market went up today,"
they often mean the NIFTY50 index went up.

InvestIQ currently analyses 5 NIFTY50 stocks:
- Reliance Industries: India's largest company, energy and retail
- TCS (Tata Consultancy Services): India's largest IT company
- Infosys: Major IT services company
- HDFC Bank: One of India's largest private sector banks
- Wipro: IT services and consulting company

These 5 stocks were chosen because they are among the most
liquid (heavily traded) stocks in India, which means their
price signals are more reliable and less susceptible to
manipulation than smaller stocks.
        """.strip()
    },
]

# Create a lookup dictionary for fast access by ID
DOCUMENT_MAP = {doc["id"]: doc for doc in DOCUMENTS}

# Group documents by topic
TOPICS = {}
for doc in DOCUMENTS:
    topic = doc["topic"]
    if topic not in TOPICS:
        TOPICS[topic] = []
    TOPICS[topic].append(doc["id"])