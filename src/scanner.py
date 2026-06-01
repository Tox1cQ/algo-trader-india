import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd

from config import DATA_DIR, WATCHLIST
from strategy import generate_signals

_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", DATA_DIR)


def scan_watchlist():
    results = []

    for ticker in WATCHLIST:
        filename = ticker.replace(".", "_") + ".csv"
        path = os.path.join(_DATA_PATH, filename)

        if not os.path.exists(path):
            print(f"WARNING: {filename} not found, skipping {ticker}")
            continue

        df = pd.read_csv(path, parse_dates=["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
        df = generate_signals(df)

        last = df.iloc[-1]
        close = last["Close"]
        rsi_val = last["RSI"]
        ma200 = last["MA200"]
        signal = last["Signal"]

        if pd.isna(ma200):
            trend = "N/A"
        elif close > ma200:
            trend = "Uptrend"
        else:
            trend = "Downtrend"

        results.append({
            "ticker": ticker,
            "close": close,
            "rsi": rsi_val,
            "trend": trend,
            "signal": signal,
        })

    if not results:
        print("No data available. Run fetch_data.py first.")
        return

    # --- Build display rows ---
    headers = ["Ticker", "Close", "RSI(2)", "Trend", "Signal"]
    rows = []
    for r in results:
        rsi_str = f"{r['rsi']:.2f}" if pd.notna(r["rsi"]) else "N/A"
        rows.append([
            r["ticker"],
            f"₹{r['close']:.2f}",
            rsi_str,
            r["trend"],
            r["signal"],
        ])

    # --- Dynamic column widths ---
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    fmt = "|" + "|".join(f" {{:<{w}}} " for w in widths) + "|"

    print()
    print(sep)
    print(fmt.format(*headers))
    print(sep)
    for row in rows:
        print(fmt.format(*row))
    print(sep)

    # --- Summary ---
    buys  = [r["ticker"] for r in results if r["signal"] == "BUY"]
    sells = [r["ticker"] for r in results if r["signal"] == "SELL"]

    print()
    print(f"Today's BUY signals:  {', '.join(buys)  if buys  else 'None'}")
    print(f"Today's SELL signals: {', '.join(sells) if sells else 'None'}")


if __name__ == "__main__":
    scan_watchlist()
