import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd

from indicators import rsi, moving_average


def generate_signals_rsi_v2(
    df: pd.DataFrame,
    rsi_period: int = 2,
    fast_ma_period: int = 50,
    slow_ma_period: int = 100,
    oversold: float = 5,
    overbought: float = 60,
) -> pd.DataFrame:
    """
    RSI(2) mean-reversion with dual-MA trend filter.

    BUY  : RSI < oversold  AND MA_fast > MA_slow  (oversold during medium-term uptrend)
    SELL : RSI > overbought
    HOLD : everything else (including NaN warmup rows)

    Args:
        df:              DataFrame with at least a "Close" column, sorted oldest -> newest.
        rsi_period:      Lookback for RSI. Default 2.
        fast_ma_period:  Short MA period for trend filter. Default 50.
        slow_ma_period:  Long MA period for trend filter. Default 100.
        oversold:        RSI threshold for BUY entry. Default 5.
        overbought:      RSI threshold for SELL exit. Default 60.

    Returns:
        A copy of df with new columns: "RSI", "MA_fast", "MA_slow", "Signal".
    """
    if "Close" not in df.columns:
        raise ValueError("Input DataFrame must contain a 'Close' column.")

    result = df.copy()
    result["RSI"]     = rsi(result["Close"], period=rsi_period)
    result["MA_fast"] = moving_average(result["Close"], fast_ma_period)
    result["MA_slow"] = moving_average(result["Close"], slow_ma_period)

    conditions = [
        (result["RSI"] < oversold) & (result["MA_fast"] > result["MA_slow"]),
        result["RSI"] > overbought,
    ]
    choices = ["BUY", "SELL"]
    result["Signal"] = np.select(conditions, choices, default="HOLD")

    return result


if __name__ == "__main__":
    csv_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "data", "ITC_NS.csv"
    )
    df = pd.read_csv(csv_path, parse_dates=["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    if df["Date"].dt.tz is not None:
        df["Date"] = df["Date"].apply(lambda ts: ts.replace(tzinfo=None))

    result = generate_signals_rsi_v2(df)

    display = result[["Date", "Close", "RSI", "MA_fast", "MA_slow", "Signal"]].copy()
    display["Date"]    = display["Date"].dt.strftime("%Y-%m-%d")
    display["Close"]   = display["Close"].map(lambda x: f"{x:.2f}")
    display["RSI"]     = display["RSI"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "NaN")
    display["MA_fast"] = display["MA_fast"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "NaN")
    display["MA_slow"] = display["MA_slow"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "NaN")

    print("\nITC_NS - RSI(2) Mean Reversion v2 (MA50/MA100) - Last 20 Trading Days")
    print("-" * 70)
    print(display.tail(20).to_string(index=False))

    counts = result["Signal"].value_counts()
    print("\nSignal counts across full history:")
    print("-" * 30)
    for signal in ["BUY", "SELL", "HOLD"]:
        print(f"  {signal}: {counts.get(signal, 0)}")
