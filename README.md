# InvestIQ 📈

> An AI-powered stock analysis platform that combines technical indicators, machine learning, and natural language explanations to make stock market signals accessible to beginner investors.

---

## What this project does

InvestIQ analyses NSE-listed stocks to help beginner investors understand what is happening in a stock before making a decision:

- Computes 15+ technical indicators from scratch — RSI, MACD, Bollinger Bands, ATR, Moving Averages
- Generates plain-English signal summaries showing overbought/oversold conditions, trend direction, and volatility regime
- Predicts probability of price rise using XGBoost trained on historical indicator data
- Explains every prediction in plain English using an LLM, grounded in a curated investing knowledge base via RAG
- Serves everything through a FastAPI backend with a React dashboard

---

## Demo

> Live deployment coming soon.

**Sample signal output — RELIANCE.NS:**

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
│  yfinance (OHLCV)          NewsAPI (headlines)       │
└────────────────┬────────────────┬───────────────────┘
                 │                │
                 ▼                ▼
┌─────────────────────────────────────────────────────┐
│  Storage                                             │
│  PostgreSQL (prices, indicators, sentiment)          │
│  Redis (15-min response cache)                       │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│  ML Layer                                            │
│  Feature engineering (17 indicators)                 │
│  XGBoost classifier → calibrated P(up/down)          │
│  FinBERT sentiment scoring                           │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│  AI Layer                                            │
│  LLM API — plain-English explanations                │
│  RAG (Pinecone) — grounded investing Q&A             │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│  API Layer                                           │
│  FastAPI — /analyze  /explain  /sentiment  /ask      │
│  Celery workers — daily data fetch + model retrain   │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│  Frontend                                            │
│  React + Recharts — price chart + indicator overlays │
│  Probability gauge — P(up) with confidence level     │
│  LLM explanation panel — streamed plain-English text  │
│  News sentiment feed                                 │
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
│   ├── models/                 # XGBoost, SHAP, calibration
│   ├── sentiment/              # FinBERT news sentiment
│   └── api/                    # FastAPI routes
│
├── notebooks/                  # Exploration and analysis
├── data/
│   ├── raw/                    # Downloaded CSV files
│   └── charts/                 # Saved charts
├── models/                     # Saved model files (.pkl)
├── .env                        # DB credentials (not committed)
├── requirements.txt
└── README.md
```

---

## Tech stack

| Layer | Technology | Why |
|---|---|---|
| Data | yfinance | Free NSE/BSE/US OHLCV data |
| Database | PostgreSQL + SQLAlchemy | Concurrent writes, proper types, connection pooling |
| Indicators | NumPy + pandas | All built from scratch — no black-box libraries |
| ML model | XGBoost + scikit-learn | Best-in-class for tabular data, fast retraining |
| Explainability | SHAP | Feature contribution per prediction, not just global importance |
| Sentiment | FinBERT (HuggingFace) | Financial domain vocabulary — understands "crashed through resistance" |
| LLM | Anthropic Claude API | Plain-English explanations grounded in retrieved context |
| RAG | LangChain + Pinecone | Prevents hallucination, cites sources |
| Backend | FastAPI + Celery + Redis | Async, background jobs, response caching |
| Frontend | React + Recharts | Interactive charts, probability gauge |
| Deployment | Docker + Railway + Vercel | One-command local setup, cloud hosting |

---

## Indicators

All indicators are implemented from scratch. No TA-Lib dependency.

| Indicator | Formula | What it signals |
|---|---|---|
| SMA 20 / 50 | `rolling(N).mean()` | Short and medium-term trend |
| EMA 20 | `ewm(span=N, adjust=False).mean()` | Trend with recency bias |
| Golden / Death Cross | SMA20 vs SMA50 crossover | Trend reversal |
| RSI (14) | `100 - 100 / (1 + avg_gain/avg_loss)` | Overbought > 70, oversold < 30 |
| MACD | `EMA(12) - EMA(26)` | Momentum direction |
| MACD Histogram | `MACD - Signal(9)` | Momentum acceleration |
| Bollinger Bands | `SMA ± 2 × StdDev(20)` | Volatility and price extremes |
| BB %B | `(price - lower) / (upper - lower)` | Position within the band |
| BB Width | `(upper - lower) / middle` | Squeeze detection |
| Volume Ratio | `volume / rolling_mean(volume, 20)` | Institutional activity |
| ATR (14) | `EMA(TrueRange, 14)` | Expected daily move in ₹ |
| ATR % | `ATR / close × 100` | Normalised daily volatility |

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
-- Run inside psql
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
# Download data and populate the database
python src/data/pipeline.py

# Generate today's signal card for any ticker
cd notebooks && python 02_indicators.py
```

---

## Design decisions

**Direction prediction, not price prediction**
Predicting exact price is a regression problem with enormous irreducible noise — even the best models have poor MSE. Direction prediction (will price be higher in 5 days?) is a classification problem where 55% accuracy is genuinely useful. Calibrated probabilities — "68% chance of rising" — are more honest and actionable than a specific price target.

**XGBoost over LSTM**
Technical indicators reduce price sequences to a flat feature vector — a tabular row, not a sequence. XGBoost is best-in-class for tabular data and trains in under a second for daily retraining. SHAP values give full per-prediction explainability, which is essential for a platform whose core value is explaining signals to beginners. An LSTM would be a black box with slower training and higher overfitting risk on this dataset size.

**Indicators from scratch**
Every indicator is implemented with documented math — no TA-Lib dependency. This means the codebase is fully auditable, bugs are catchable, and any formula can be modified (e.g. changing the RSI period or True Range definition). It also means the math can be explained cold in any technical interview.

**PostgreSQL from day one**
SQLite fails under concurrent writes — FastAPI's multiple worker processes cause "database is locked" errors. PostgreSQL handles true concurrent writes with row-level locking. The abstraction layer (`load_features()`, `save_prices()`) means the ML and API code never imported a database driver directly — the entire storage layer swapped from SQLite to PostgreSQL by changing one file.

**Separate prices and indicators tables**
Raw data (prices) and derived data (indicators) are stored separately. Adding a new indicator means recomputing the indicators table without re-downloading two years of price data. This separation also makes it easy to backfill indicators for new tickers without touching the price pipeline.

---

## Roadmap

- [x] Data ingestion — yfinance + PostgreSQL pipeline
- [x] Technical indicator engine — 12 indicators from scratch  
- [x] Signal summary card with plain-English interpretation
- [ ] ML model — XGBoost with walk-forward backtesting
- [ ] SHAP explainability — per-prediction feature contributions
- [ ] News sentiment — FinBERT scoring + rolling aggregation
- [ ] LLM explanation layer — Claude API with structured prompts
- [ ] RAG knowledge base — grounded investing Q&A
- [ ] FastAPI backend — REST API with Redis caching
- [ ] Celery jobs — daily data fetch + nightly model retrain
- [ ] React dashboard — interactive chart + probability gauge
- [ ] Docker containerisation — one-command local setup
- [ ] Cloud deployment — Railway (backend) + Vercel (frontend)

---

## Author

**Dev** — B.Tech Computer Science, Delhi Technological University

Built as the centrepiece of my internship portfolio.

---

## Licence

MIT
