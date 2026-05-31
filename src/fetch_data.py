"""
fetch_data.py
Downloads historical stock data from Yahoo Finance using yfinance.
Phase 1 of the algo-trader-india project.
"""

import yfinance as yf
import os

# --- Configuration ---
TICKER = "RELIANCE.NS"   # Reliance Industries on NSE (India)
PERIOD = "1mo"           # last 1 month of data
INTERVAL = "1d"          # daily candles

# --- Main script ---
def fetch_stock_data(ticker: str, period: str, interval: str):
    """Download stock data and return it as a pandas DataFrame."""
    print(f"Fetching {ticker} data — period={period}, interval={interval}...")
    
    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval=interval)
    
    return df


def main():
    df = fetch_stock_data(TICKER, PERIOD, INTERVAL)

    if df.empty:
        print("⚠️  No data returned. Check ticker symbol or internet connection.")
        return

    # Show a quick preview
    print("\n--- Last 5 days ---")
    print(df.tail())

    print(f"\nLatest closing price: ₹{df['Close'].iloc[-1]:.2f}")
    print(f"Total rows fetched:   {len(df)}")

    # Save to CSV
    os.makedirs("data", exist_ok=True)
    output_path = f"data/{TICKER.replace('.', '_')}.csv"
    df.to_csv(output_path)
    print(f"\n✅ Saved to {output_path}")


if __name__ == "__main__":
    main()
