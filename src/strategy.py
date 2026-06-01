import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd

from indicators import rsi


def generate_signals(
    df: pd.DataFrame,
    rsi_period: int = 2,
    ma_period: int = 200,
    oversold: float = 10,
    overbought: float = 70,
) -> pd.DataFrame:
    """
    Generate RSI(2) mean-reversion trading signals with a long-term MA trend filter.

    BUY  : RSI < oversold  AND Close > MA{ma_period}
    SELL : RSI > overbought
    HOLD : everything else (including rows with insufficient history)

    Args:
        df:          DataFrame with at least a "Close" column, sorted oldest -> newest.
        rsi_period:  Lookback for RSI calculation. Default 2.
        ma_period:   Lookback for the trend-filter moving average. Default 200.
        oversold:    RSI threshold below which a BUY signal is considered. Default 10.
        overbought:  RSI threshold above which a SELL signal is considered. Default 70.

    Returns:
        A copy of df with three new columns: "RSI", "MA200", "Signal".
    """
    if "Close" not in df.columns:
        raise ValueError("Input DataFrame must contain a 'Close' column.")

    result = df.copy()

    result["RSI"] = rsi(result["Close"], period=rsi_period)
    result["MA200"] = result["Close"].rolling(ma_period).mean()

    conditions = [
        (result["RSI"] < oversold) & (result["Close"] > result["MA200"]),
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

    result = generate_signals(df)

    display = result[["Date", "Close", "RSI", "MA200", "Signal"]].copy()
    display["RSI"] = display["RSI"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "NaN")
    display["MA200"] = display["MA200"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "NaN")

    print("\nITC_NS - RSI(2) Mean Reversion - Last 15 Trading Days")
    print("-" * 60)
    print(display.tail(15).to_string(index=False))

    counts = result["Signal"].value_counts()
    print("\nSignal counts across full history:")
    print("-" * 30)
    for signal in ["BUY", "SELL", "HOLD"]:
        print(f"  {signal}: {counts.get(signal, 0)}")
