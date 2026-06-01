import pandas as pd
import numpy as np


def rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Compute the Relative Strength Index (RSI) using Wilder's smoothing method.

    RSI measures the speed and magnitude of recent price changes to evaluate
    whether an asset is overbought or oversold on a 0-100 scale.

    Interpretation:
        - RSI > 70  -> typically considered overbought (potential reversal down)
        - RSI < 30  -> typically considered oversold  (potential reversal up)
        - RSI = 50  -> neutral momentum

    Wilder's smoothing uses an exponential moving average with alpha = 1/period
    (expressed in pandas EWM as com = period - 1, so that alpha = 1/(1+com) = 1/period).

    Args:
        prices: A pandas Series of closing prices, sorted oldest -> newest.
        period: Lookback window for the smoothing average. Default is 14.

    Returns:
        A pandas Series of RSI values aligned to the input index.
        The first `period` values are NaN (insufficient history).
    """
    if period < 1:
        raise ValueError(f"period must be >= 1, got {period}")

    # Day-over-day price change
    delta = prices.diff()

    # Separate gains (positive moves) and losses (negative moves, made positive)
    gains = delta.clip(lower=0)      # negative deltas become 0
    losses = (-delta).clip(lower=0)  # positive deltas become 0, negatives flipped

    # Wilder's smoothing: EMA with alpha = 1/period (com = period - 1).
    # adjust=False enforces the recursive formula: avg_n = avg_{n-1}*(1-a) + x_n*a
    avg_gain = gains.ewm(com=period - 1, min_periods=period, adjust=False).mean()
    avg_loss = losses.ewm(com=period - 1, min_periods=period, adjust=False).mean()

    # Relative Strength; replace 0 avg_loss with NaN to avoid ZeroDivisionError
    rs = avg_gain / avg_loss.replace(0, np.nan)

    # Standard RSI formula
    rsi_values = 100 - (100 / (1 + rs))

    # Pure upward streak (avg_loss == 0) means RSI = 100 by definition
    rsi_values = rsi_values.where(avg_loss != 0, other=100.0)

    return rsi_values


def donchian_high(prices: pd.Series, period: int = 20) -> pd.Series:
    return prices.shift(1).rolling(period).max()


def donchian_low(prices: pd.Series, period: int = 10) -> pd.Series:
    return prices.shift(1).rolling(period).min()


def moving_average(prices: pd.Series, period: int) -> pd.Series:
    return prices.rolling(period).mean()


if __name__ == "__main__":
    df = pd.read_csv("data/ITC_NS.csv", parse_dates=["Date"])
    df = df.sort_values("Date").reset_index(drop=True)

    df["RSI_2"] = rsi(df["Close"], period=2)

    print(f"\nITC_NS - RSI(2) - last 10 trading days\n{'-' * 45}")
    print(df[["Date", "Close", "RSI_2"]].tail(10).to_string(index=False))
