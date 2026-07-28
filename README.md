# InvestIQ 📈

> AI-powered stock analysis platform that combines machine learning,
> NLP, and large language models to make stock market signals 
> accessible to beginner investors.

[![Live Demo](https://img.shields.io/badge/Live-Demo-indigo?style=flat)](https://investiq-pi-nine.vercel.app/)
[![API Docs](https://img.shields.io/badge/API-Docs-cyan?style=flat)](https://mellow-miracle-production-862b.up.railway.app//docs)
[![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

---

## Live Demo

| Service | URL |
|---|---|
| Frontend | https://investiq-pi-nine.vercel.app/ |
| API | https://mellow-miracle-production-862b.up.railway.app/ |
| API Docs | https://mellow-miracle-production-862b.up.railway.app//docs |

---

## What it does

InvestIQ analyses NSE-listed stocks and explains what the signals mean:

- **Predicts** probability of price rise over 10 trading days using XGBoost
- **Explains** each prediction in plain English using SHAP + Gemini API  
- **Scores** news sentiment using FinBERT trained on financial text
- **Answers** investing questions using RAG over a curated knowledge base
- **Updates** data automatically every day at 4:15 PM after market close

---

## Architecture
yfinance (OHLCV) + NewsAPI (headlines)
↓
PostgreSQL + Redis (cache)
↓
XGBoost classifier (17 features)
FinBERT sentiment scoring
SHAP explainability
↓
Gemini API (plain-English explanations)
ChromaDB RAG (grounded Q&A)
↓
FastAPI + Celery (REST API + background jobs)
↓
React + Recharts (dashboard)
↓
Docker Compose → Railway + Vercel


---

## Model performance

| Metric | Value |
|---|---|
| Test AUC (single split) | 0.691 |
| Walk-forward mean AUC (11 windows) | 0.776 ± 0.159 |
| Test Accuracy | 58.0% |
| Annualised alpha vs buy-and-hold | +8.2% |
| Sharpe ratio | 0.286 |
| Max drawdown | -7.49% |
| Prediction horizon | 10 trading days |

Walk-forward test period: Jul 2025 – Jun 2026. Buy-and-hold returned -4.99% in the same period.

---

## Tech stack

| Layer | Technology | Why |
|---|---|---|
| Data | yfinance + NewsAPI | Free NSE OHLCV + headlines |
| Database | PostgreSQL 15 + SQLAlchemy | Concurrent writes, connection pooling |
| Cache | Redis 7 | 85x speedup on repeated requests |
| ML | XGBoost + scikit-learn | Best-in-class for tabular data |
| Explainability | SHAP TreeExplainer | Per-prediction feature attribution |
| Calibration | Platt scaling (manual) | sklearn 1.9 compatibility |
| Sentiment | FinBERT (HuggingFace) | Financial domain vocabulary |
| LLM | Google Gemini | Plain-English explanations, free tier |
| RAG | ChromaDB + sentence-transformers | Grounded Q&A, no hallucination |
| Backend | FastAPI + Celery | Async API, scheduled background jobs |
| Frontend | React + Recharts | Interactive charts, probability gauge |
| Deployment | Docker, Railway, Vercel | Containerized deployment for backend and frontend |

---

## Quick start

### Requirements
- Python 3.13+
- PostgreSQL 15
- Redis 7
- Node.js 18+
- Docker (optional)

### Option A — Docker (recommended)

```bash
git clone https://github.com/yourusername/investiq.git
cd investiq
cp .env.example .env   # fill in your API keys
docker-compose up
```

Open http://localhost:3000

### Option B — Local development

```bash
# Backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python src/data/pipeline.py    # fetch initial data
uvicorn src.api.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm install && npm start
```

### Environment variables

```bash
# .env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=investiq
DB_USER=investiq_user
DB_PASSWORD=investiq123
REDIS_URL=redis://localhost:6379/0
GEMINI_API_KEY=your_key_here     # free at aistudio.google.com
NEWS_API_KEY=your_key_here       # free at newsapi.org
```

---

## API endpoints
GET /health — DB + model + cache status
GET /overview — All watchlist stocks at a glance
GET /analyze/{ticker} — XGBoost prediction + SHAP features
GET /explain/{ticker} — Gemini plain-English explanation
GET /sentiment/{ticker} — FinBERT news sentiment scores
GET /prices/{ticker} — Historical OHLCV + indicators
POST /ask — RAG-powered investing Q&A
GET /docs — Swagger UI


Example:
```bash
curl https://mellow-miracle-production-862b.up.railway.app//analyze/RELIANCE.NS
```

---

## Key design decisions

**Why direction prediction, not price?**
Price prediction is regression with enormous irreducible noise. Direction prediction is classification where 58% accuracy is commercially meaningful (50% = random). Calibrated probabilities are more honest than specific price targets.

**Why XGBoost over LSTM?**
Technical indicators reduce price sequences to a flat feature vector — tabular classification, not sequence prediction. XGBoost is best-in-class for tabular data. SHAP gives full per-prediction explainability which is essential for a platform explaining signals to beginners.

**Why separate prices and indicators tables?**
Different update frequencies. Adding a new indicator recomputes the indicators table without re-downloading price history. Raw data and derived data evolve independently.

**Why Platt scaling instead of sklearn CalibratedClassifierCV?**
sklearn 1.9 removed cv='prefit'. We implement Platt scaling manually — logistic regression on raw XGBoost scores using a held-out calibration set. Identical mathematics, no version dependency.

**Why Redis TTL of 15 minutes?**
Stock data changes meaningfully once per day. 15 minutes is conservative enough to serve fresh data during market hours while delivering 85x speedup on repeated requests. Explanation TTL is 1 hour — Gemini responses don't change minute-to-minute.

---

## Project structure
investiq/
├── src/
│ ├── data/ # yfinance, PostgreSQL, pipeline
│ ├── indicators/ # RSI, MACD, Bollinger, ATR, EMA/SMA
│ ├── models/ # XGBoost, SHAP, calibration, explainer
│ ├── sentiment/ # FinBERT, NewsAPI, aggregation
│ ├── rag/ # ChromaDB, knowledge base, Q&A engine
│ └── api/ # FastAPI routes, cache, Celery tasks
├── frontend/ # React dashboard
├── scripts/ # DB init, seed data
├── notebooks/ # Experiments and model development
├── models/ # Saved .pkl files (gitignored)
├── data/ # Raw CSV files (gitignored)
├── Dockerfile
├── docker-compose.yml
└── 

---

## Author

**Dev** — B.Tech Computer Science, DTU (3rd year)

Passionate about Machine Learning, Backend Development, and Building AI-powered Applications.

---

## Licence

MIT
