import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd

from indicators import donchian_high, donchian_low


def generate_signals_donchian(df, entry_period=20, exit_period=10):
    if "Close" not in df.columns:
        raise ValueError("Input DataFrame must contain a 'Close' column.")

    result = df.copy()
    result["DonchianHigh"] = donchian_high(result["Close"], period=entry_period)
    result["DonchianLow"]  = donchian_low(result["Close"],  period=exit_period)

    conditions = [
        result["Close"] > result["DonchianHigh"],
        result["Close"] < result["DonchianLow"],
    ]
    choices = ["BUY", "SELL"]
    result["Signal"] = np.select(conditions, choices, default="HOLD")

    return result


if __name__ == "__main__":
    csv_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "data", "COALINDIA_NS.csv"
    )
    df = pd.read_csv(csv_path, parse_dates=["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    if df["Date"].dt.tz is not None:
        df["Date"] = df["Date"].apply(lambda ts: ts.replace(tzinfo=None))

    result = generate_signals_donchian(df)

    display = result[["Date", "Close", "DonchianHigh", "DonchianLow", "Signal"]].copy()
    display["DonchianHigh"] = display["DonchianHigh"].map(
        lambda x: f"{x:.2f}" if pd.notna(x) else "NaN"
    )
    display["DonchianLow"] = display["DonchianLow"].map(
        lambda x: f"{x:.2f}" if pd.notna(x) else "NaN"
    )

    print("\nCOALINDIA_NS - Donchian Channel - Last 15 Trading Days")
    print("-" * 60)
    print(display.tail(15).to_string(index=False))

    counts = result["Signal"].value_counts()
    print("\nSignal counts across full history:")
    print("-" * 30)
    for signal in ["BUY", "SELL", "HOLD"]:
        print(f"  {signal}: {counts.get(signal, 0)}")
