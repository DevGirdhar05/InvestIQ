import yfinance as yf 
import pandas as pd 
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"
DATA_DIR.mkdir(parents=True,exist_ok=True)

def fetch_stock_data(
    ticker : str,
    period : str = "1y",
    save : bool = True
) -> pd.DataFrame : 
    print(f"Fetching {ticker}  ({period})...")
    stock=yf.Ticker(ticker)
    df=stock.history(period = period)

    if df.empty:
        raise ValueError(
            f"No data returned for '{ticker}'. "
            f"Check the symbol- NSE stocks need .NS suffix"
        )

    df.index=df.index.tz_localize(None)

    df=df[["Open","High","Low","Close","Volume"]]

    df = df.dropna(subset=["Close"])

    df.round(2)

    print(f"Downloaded {len(df)} trading days")
    print(f"Range : {df.index[0].date()} -> {df.index[-1].date()}")
    print(f"Latest Close : ₹{df['Close'].iloc[-1]:,.2f}")

    if save:
        filename=DATA_DIR/f"{ticker.replace('.','_')}_{period}.csv"
        df.to_csv(filename)
        print(f"Saved to {filename}")
    
    return df

def fetch_multiple(
    tickers: list[str],
    period: str="1y",
) -> dict[str,pd.DataFrame] : 
    results={}
    
    for ticker in tickers:
        try:
            results[ticker]=fetch_stock_data(ticker,period)
        except ValueError as e:
            print(f"Warning : {e}")
    
    print(f"\n Successfully downloaded {len(results)}/{len(tickers)} stocks")
    return results

def load_from_csv(ticker : str,period : str="1y")->pd.DataFrame : 
    filename=DATA_DIR/f"{ticker.replace('.','_')}_{period}.csv"

    if not filename.exists():
        raise FileNotFoundError(
            f"No cached data for {ticker}. Run fetch_stock_data() first."
        )
    df=pd.read_csv(filename,index_col=0,parse_dates=True)
    return df
