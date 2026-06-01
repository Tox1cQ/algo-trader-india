import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd

from indicators import moving_average


def generate_signals_ma_cross(df, fast_period=10, slow_period=30):
    if "Close" not in df.columns:
        raise ValueError("Input DataFrame must contain a 'Close' column.")

    result = df.copy()
    result["MA_fast"] = moving_average(result["Close"], fast_period)
    result["MA_slow"] = moving_average(result["Close"], slow_period)

    fast      = result["MA_fast"]
    slow      = result["MA_slow"]
    fast_prev = fast.shift(1)
    slow_prev = slow.shift(1)

    crosses_up   = (fast > slow) & (fast_prev <= slow_prev)
    crosses_down = (fast < slow) & (fast_prev >= slow_prev)

    result["Signal"] = np.select(
        [crosses_up, crosses_down], ["BUY", "SELL"], default="HOLD"
    )
    return result


if __name__ == "__main__":
    csv_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "data", "COALINDIA_NS.csv"
    )
    df = pd.read_csv(csv_path, parse_dates=["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    if df["Date"].dt.tz is not None:
        df["Date"] = df["Date"].apply(lambda ts: ts.replace(tzinfo=None))

    result = generate_signals_ma_cross(df)

    display = result[["Date", "Close", "MA_fast", "MA_slow", "Signal"]].copy()
    display["MA_fast"] = display["MA_fast"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "NaN")
    display["MA_slow"] = display["MA_slow"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "NaN")

    print("\nCOALINDIA_NS - MA Cross (10/30) - Last 30 Trading Days")
    print("-" * 60)
    print(display.tail(30).to_string(index=False))

    counts = result["Signal"].value_counts()
    print("\nSignal counts across full history:")
    print("-" * 30)
    for signal in ["BUY", "SELL", "HOLD"]:
        print(f"  {signal}: {counts.get(signal, 0)}")
