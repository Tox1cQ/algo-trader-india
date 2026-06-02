"""
filter_universe.py

Scans every CSV in data/ and selects stocks suitable for RSI(2) mean reversion:
- At least 1000 trading days of history (~4 years) for stable signals
- Latest close between Rs 50 and Rs 1000 (affordable, not penny)
- Daily return volatility under 4% (excludes extreme choppy stocks)

Prints a filtered list to copy into config.py.
"""

import os
import pandas as pd

DATA_DIR = "data"
MIN_HISTORY_DAYS = 1000
MIN_PRICE = 50.0
MAX_PRICE = 1000.0
MAX_DAILY_VOL = 0.04  # 4% std dev of daily returns


def evaluate(filename: str):
    """Return dict with stats, or None if file unreadable."""
    path = os.path.join(DATA_DIR, filename)
    try:
        df = pd.read_csv(path, parse_dates=["Date"])
    except Exception as exc:
        return {"filename": filename, "error": str(exc)}

    if df.empty or "Close" not in df.columns:
        return {"filename": filename, "error": "no Close column"}

    df = df.sort_values("Date").reset_index(drop=True)
    rows = len(df)
    latest_close = df["Close"].iloc[-1]
    daily_returns = df["Close"].pct_change().dropna()
    daily_vol = daily_returns.std() if len(daily_returns) > 1 else 0.0

    passes = (
        rows >= MIN_HISTORY_DAYS
        and MIN_PRICE <= latest_close <= MAX_PRICE
        and daily_vol <= MAX_DAILY_VOL
    )

    ticker = filename.replace("_NS.csv", "").replace(".csv", "") + ".NS"

    return {
        "ticker": ticker,
        "rows": rows,
        "close": latest_close,
        "vol": daily_vol,
        "passes": passes,
    }


def main():
    files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith(".csv"))
    print(f"Scanning {len(files)} CSV files in {DATA_DIR}/\n")

    passed = []
    failed = []
    for f in files:
        result = evaluate(f)
        if result is None or "error" in result:
            continue
        if result["passes"]:
            passed.append(result)
        else:
            failed.append(result)

    print(f"PASSED: {len(passed)} stocks\n")
    print(f"{'Ticker':<18} {'Rows':>6} {'Close':>10} {'DailyVol':>10}")
    print("-" * 50)
    for r in sorted(passed, key=lambda x: x["ticker"]):
        print(f"{r['ticker']:<18} {r['rows']:>6} {r['close']:>10.2f} {r['vol']*100:>9.2f}%")

    print(f"\nFAILED: {len(failed)} stocks (showing reasons)")
    print("-" * 70)
    for r in sorted(failed, key=lambda x: x["ticker"])[:15]:
        reasons = []
        if r["rows"] < MIN_HISTORY_DAYS:
            reasons.append(f"only {r['rows']} rows")
        if r["close"] < MIN_PRICE:
            reasons.append(f"price Rs {r['close']:.2f} < {MIN_PRICE}")
        if r["close"] > MAX_PRICE:
            reasons.append(f"price Rs {r['close']:.2f} > {MAX_PRICE}")
        if r["vol"] > MAX_DAILY_VOL:
            reasons.append(f"vol {r['vol']*100:.2f}% > {MAX_DAILY_VOL*100:.0f}%")
        print(f"  {r['ticker']:<18} : {', '.join(reasons)}")
    if len(failed) > 15:
        print(f"  ... and {len(failed) - 15} more failed")

    print("\n" + "=" * 60)
    print("Copy this WATCHLIST into src/config.py:")
    print("=" * 60)
    print("WATCHLIST = [")
    for r in sorted(passed, key=lambda x: x["ticker"]):
        print(f'    "{r["ticker"]}",')
    print("]")


if __name__ == "__main__":
    main()
