# InvestIQ 📈

> An AI-powered stock analysis platform that combines technical indicators, machine learning, and natural language explanations to make stock market signals accessible to beginner investors.

---

## What this project does

InvestIQ analyses NSE-listed stocks to help beginner investors understand what is happening in a stock before making a decision:

- Computes 13 technical indicators from scratch — RSI, MACD, Bollinger Bands, ATR, Moving Averages
- Predicts probability of price rise using XGBoost trained on historical indicator data (AUC: 0.69)
- Explains every prediction using SHAP values — shows which indicators drove the signal and why
- Calibrates raw model scores to true probabilities using Platt scaling
- Generates plain-English signal summaries for beginner investors
- *(Coming soon)* LLM explanation layer — converts SHAP output to plain English via Claude API
- *(Coming soon)* News sentiment — FinBERT scoring of financial headlines as an ML feature
- *(Coming soon)* FastAPI backend + React dashboard with probability gauge

---

## Demo

> Live deployment coming soon.

**Sample prediction output — RELIANCE.NS:**

```
Date             : 2026-07-03
Prediction       : P(UP in 10 days) = 62.4%  |  Confidence: MEDIUM

Top contributing signals:
  sma_50           ▲ bullish    +0.18   (price approaching SMA50)
  macd_hist        ▲ bullish    +0.14   (histogram turning positive)
  price_vs_sma50   ▼ bearish    -0.09   (still below 50-day average)
  bb_pct           ▲ bullish    +0.07   (price near lower band)
  rsi_normalized   ▲ bullish    +0.05   (RSI below 50, oversold bias)
```

**Signal card — all indicators at a glance:**

```
Close Price  : ₹1,304.00
RSI (14)     : 46.3    — Neutral zone
MACD         : Bullish crossover — momentum accelerating
Trend        : Downtrend (price -2.6% below SMA50)
Bollinger %B : 0.52    — Near middle of bands
ATR          : ₹18.80  — 1.44% expected daily move
Overall Bias : BULLISH (3 bullish / 1 bearish signals)
```

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Data Sources                                        │
│  yfinance (OHLCV daily)     NewsAPI (headlines)      │
└────────────────┬────────────────┬───────────────────┘
                 │                │
                 ▼                ▼
┌─────────────────────────────────────────────────────┐
│  Storage                                             │
│  PostgreSQL — prices, indicators, sentiment          │
│  Redis — 15-min API response cache                   │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│  ML Layer                                            │
│  13 technical indicator features                     │
│  XGBoost classifier → calibrated P(up/down)          │
│  SHAP values → per-prediction feature attribution    │
│  FinBERT sentiment scoring (coming soon)             │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│  AI Layer (coming soon)                              │
│  Claude API — plain-English SHAP explanations        │
│  RAG (Pinecone) — grounded investing Q&A             │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│  API + Frontend (coming soon)                        │
│  FastAPI — /analyze /explain /sentiment /ask         │
│  React + Recharts — chart, probability gauge, news   │
└─────────────────────────────────────────────────────┘
```

---

## Project structure

```
investiq/
├── src/
│   ├── data/
│   │   ├── fetch.py            # yfinance wrapper with caching
│   │   ├── database.py         # PostgreSQL via SQLAlchemy
│   │   └── pipeline.py         # fetch → indicators → store
│   │
│   ├── indicators/
│   │   ├── moving_averages.py  # SMA, EMA, crossover signals
│   │   ├── rsi.py              # RSI from scratch
│   │   ├── macd.py             # MACD, signal line, histogram
│   │   ├── bollinger.py        # Bollinger Bands, BB%B, width
│   │   ├── atr.py              # Average True Range
│   │   └── pipeline.py         # compute_all_indicators()
│   │
│   ├── models/
│   │   ├── features.py         # build_dataset(), time_series_split()
│   │   ├── logistic_model.py   # baseline classifier
│   │   └── xgboost_model.py    # production model + SHAP + calibration
│   │
│   ├── sentiment/              # FinBERT news sentiment (coming soon)
│   └── api/                    # FastAPI routes (coming soon)
│
├── notebooks/
│   ├── 01_explore.ipynb        # yfinance, normalisation
│   ├── 02_indicators.ipynb     # indicator analysis, signal card
│   ├── 03_pipeline_test.ipynb  # DB verification, market overview
│   ├── 04_first_model.ipynb    # logistic regression baseline
│   └── 05_xgboost.ipynb        # XGBoost, SHAP, calibration
│
├── data/
│   ├── raw/                    # Downloaded CSV files (not committed)
│   └── charts/                 # Saved charts (not committed)
├── models/                     # Saved .pkl files (not committed)
├── .env                        # DB credentials (not committed)
└── requirements.txt
```

---

## Tech stack

| Layer | Technology | Why |
|---|---|---|
| Data | yfinance | Free NSE/BSE/US OHLCV data |
| Database | PostgreSQL + SQLAlchemy | Concurrent writes, connection pooling, proper types |
| Indicators | NumPy + pandas | All built from scratch — no TA-Lib black box |
| ML model | XGBoost | Best-in-class for tabular data, fast retraining |
| Explainability | SHAP | Per-prediction feature attribution with direction |
| Calibration | Platt scaling | Converts raw scores to true probabilities |
| Sentiment | FinBERT (coming soon) | Financial domain vocabulary awareness |
| LLM | Claude API (coming soon) | Plain-English SHAP explanations |
| RAG | LangChain + Pinecone (coming soon) | Grounded investing Q&A |
| Backend | FastAPI + Redis + Celery (coming soon) | Async API, caching, background jobs |
| Frontend | React + Recharts (coming soon) | Interactive chart, probability gauge |
| Deployment | Docker + Railway + Vercel (coming soon) | One-command setup, cloud hosting |

---

## Model performance

| Model | Horizon | Test AUC | Test Accuracy | Notes |
|---|---|---|---|---|
| Always-UP baseline | 10d | 0.500 | 34.1% | Test period was bearish |
| Logistic Regression | 10d | 0.693 | 55.1% | Strong linear baseline |
| **XGBoost** | **10d** | **0.691** | **58.0%** | **Production model** |

Horizon=10 days was selected empirically from a sweep of 1, 3, 5, and 10 day windows. AUC of 0.69 is near the upper bound achievable from technical indicators alone on daily OHLCV data.

**Top SHAP features (mean absolute contribution):**

| Feature | Importance | Interpretation |
|---|---|---|
| sma_50 | 1.435 | Medium-term trend direction is the dominant signal |
| macd_hist | 1.075 | Momentum acceleration second most important |
| macd_signal | 0.685 | Trend confirmation layer |
| price_vs_sma50 | 0.509 | Distance from average — mean reversion signal |
| bb_pct | 0.300 | Volatility-adjusted price position |

---

## Indicators

All indicators implemented from scratch. No TA-Lib dependency.

| Indicator | Formula | Signal |
|---|---|---|
| SMA 20 / 50 | `rolling(N).mean()` | Golden Cross / Death Cross |
| EMA 20 | `ewm(span=N, adjust=False).mean()` | Trend with recency bias |
| RSI (14) | `100 - 100/(1 + avg_gain/avg_loss)` | Overbought > 70, oversold < 30 |
| MACD | `EMA(12) - EMA(26)` | Momentum direction |
| MACD Histogram | `MACD - Signal(9)` | Momentum acceleration |
| Bollinger Bands | `SMA ± 2 × StdDev(20)` | Volatility and price extremes |
| BB %B | `(price - lower) / (upper - lower)` | Position within the band |
| ATR (14) | `EMA(True Range, 14)` | Expected daily move in ₹ |
| Volume Ratio | `volume / rolling_mean(20)` | Unusual institutional activity |

---

## Quick start

### Requirements

- Python 3.11+
- PostgreSQL 15

### Setup

```bash
git clone https://github.com/yourusername/investiq.git
cd investiq

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### PostgreSQL

```bash
# macOS
brew install postgresql@15 && brew services start postgresql@15

# Ubuntu / WSL
sudo apt install postgresql -y && sudo service postgresql start
```

```sql
CREATE DATABASE investiq;
CREATE USER investiq_user WITH PASSWORD 'investiq123';
GRANT ALL PRIVILEGES ON DATABASE investiq TO investiq_user;
GRANT ALL ON SCHEMA public TO investiq_user;
```

### Environment

Create `.env` in the project root:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=investiq
DB_USER=investiq_user
DB_PASSWORD=investiq123
```

### Run

```bash
# Populate the database (first time)
python src/data/pipeline.py

# Train the model
jupyter notebook notebooks/05_xgboost.ipynb

# Verify signal output for any ticker
jupyter notebook notebooks/02_indicators.ipynb
```

---

## Design decisions

**Why predict direction and not price?**
Price prediction is regression with enormous irreducible noise. Direction prediction (will price be higher in 10 days?) is classification where 58% accuracy is genuinely useful. Calibrated probabilities — shown as "62% chance of rising" — are more honest and actionable than a specific price target.

**Why XGBoost over LSTM?**
Technical indicators reduce price sequences to a flat 13-feature vector per day — a tabular row, not a sequence. XGBoost is best-in-class for tabular data. SHAP values give full per-prediction explainability, which is essential for a platform whose core value is explaining signals to beginners. An LSTM would be a black box with slower training and higher overfitting risk on 350 training samples.

**Why indicators from scratch?**
Every formula is documented with the math. No TA-Lib black box. Bugs are catchable. Any formula can be modified. The implementation can be explained line by line in any technical interview.

**Why separate prices and indicators tables?**
Adding a new indicator only requires recomputing the indicators table — no re-downloading of price history. Different update frequencies: prices update daily, indicator formulas change when we improve the model.

**Why Platt scaling instead of sklearn CalibratedClassifierCV?**
sklearn 1.4+ removed `cv='prefit'` as a valid string parameter. We implement Platt scaling manually: fit a logistic regression on raw XGBoost scores using a held-out calibration set. This is identical to what sklearn did internally and works across all sklearn versions.

---

## Roadmap

- [x] Data ingestion — yfinance + PostgreSQL pipeline
- [x] Technical indicator engine — 13 indicators from scratch
- [x] Signal summary card with plain-English interpretation
- [x] Logistic regression baseline (AUC: 0.693)
- [x] XGBoost production model (AUC: 0.691, Accuracy: 58%)
- [x] SHAP explainability — per-prediction feature contributions
- [x] Platt scaling probability calibration
- [ ] Walk-forward backtesting — Sharpe ratio, max drawdown
- [ ] News sentiment — FinBERT scoring + rolling aggregation
- [ ] LLM explanation layer — Claude API with structured prompts
- [ ] RAG knowledge base — grounded investing Q&A
- [ ] FastAPI backend — REST API with Redis caching
- [ ] Celery workers — daily data fetch + nightly model retrain
- [ ] React dashboard — interactive chart + probability gauge
- [ ] Docker containerisation
- [ ] Cloud deployment — Railway + Vercel

---

## Author

**Dev** — B.Tech Computer Science, Delhi Technological University (3rd year)
.

---

## Licence

MIT
