# InvestIQ

InvestIQ is an AI-powered stock market analysis and prediction platform.

The goal of this project is to combine financial data, technical indicators, and machine learning models to help users analyze stocks and make better investment decisions.

## Features

### Implemented

* Historical stock data collection using Yahoo Finance
* CSV caching to avoid repeated API calls
* Batch downloading for multiple stocks
* Daily return calculations
* Market direction analysis (green vs red days)
* Best and worst trading day identification
* Normalized multi-stock comparison charts
* Visualization of stock performance over time

### Planned

* Technical indicators:

  * Simple Moving Average (SMA)
  * Exponential Moving Average (EMA)
  * Relative Strength Index (RSI)
  * MACD
* Machine learning models for stock prediction
* FastAPI backend for serving predictions
* React frontend dashboard for visualization

## Tech Stack

* Python
* Pandas
* yfinance
* Matplotlib
* Scikit-learn
* FastAPI
* React

## Project Structure

```text
InvestIQ/
├── data/
│   ├── raw/                    # Cached stock CSV files
│   └── charts/                 # Generated visualisations
│
├── src/
│   ├── data/
│   │   └── fetch.py            # Stock data ingestion utilities
│   │
│   ├── indicators/            # Technical indicators
│   ├── models/                # Machine learning models
│   ├── api/                   # FastAPI backend
│   └── ui/                    # Frontend application
│
├── notebooks/
│   ├── 01_explore.py
│   └── 02_compare_stocks.py
│
├── tests/
├── requirements.txt
└── README.md
```

## Installation

```bash
git clone <repository-url>
cd InvestIQ

python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

## Usage

Fetch historical stock data:

```bash
python notebooks/01_explore.py
```

Generate multi-stock comparison charts:

```bash
python notebooks/02_compare_stocks.py
```

## Example Analysis

Current analysis includes:

* Daily return calculations
* Green vs red day statistics
* Best and worst trading day identification
* Relative performance comparison across multiple NIFTY50 companies

## Current Status

### Completed

* Project setup and structure
* Historical stock data ingestion pipeline
* CSV caching system
* Multi-stock batch downloading
* Exploratory stock analysis
* Normalized performance comparison visualizations

### Upcoming Milestones

* Technical indicators
* Feature engineering
* Machine learning models
* Prediction API
* Interactive frontend dashboard

