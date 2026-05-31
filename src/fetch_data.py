"""
fetch_data.py
Downloads historical OHLCV data for every ticker in WATCHLIST and saves
each as a CSV in DATA_DIR.  Safe to re-run: existing files are overwritten.
"""

import os
import sys
import time

# Allow `python src/fetch_data.py` from the project root by making sure
# Python can find sibling modules (config.py) inside the src/ directory.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yfinance as yf

from config import DATA_DIR, INTERVAL, PERIOD, WATCHLIST


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fetch_one(ticker: str, period: str, interval: str):
    """Return a DataFrame of OHLCV history, or None on any error."""
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval)
        if df.empty:
            raise ValueError("empty response")
        return df
    except Exception as exc:
        print(f"    ERROR fetching {ticker}: {exc}")
        return None


def save_to_csv(df, ticker: str, data_dir: str) -> str:
    """Save *df* to <data_dir>/<TICKER_with_dots_as_underscores>.csv."""
    os.makedirs(data_dir, exist_ok=True)
    filename = ticker.replace(".", "_") + ".csv"
    path = os.path.join(data_dir, filename)
    df.to_csv(path)
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    total = len(WATCHLIST)
    ok, fail = 0, 0

    for i, ticker in enumerate(WATCHLIST, start=1):
        prefix = f"[{i}/{total}] {ticker:<18}"

        df = fetch_one(ticker, PERIOD, INTERVAL)

        if df is None:
            print(f"{prefix} ❌  skipped")
            fail += 1
        else:
            path = save_to_csv(df, ticker, DATA_DIR)
            latest_close = df["Close"].iloc[-1]
            print(f"{prefix} ✅  {len(df)} rows | latest ₹{latest_close:.2f} → {path}")
            ok += 1

        time.sleep(0.5)

    print()
    print(f"Done — {ok} succeeded, {fail} failed out of {total} tickers.")


if __name__ == "__main__":
    main()
