import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import math

import pandas as pd

from config import DATA_DIR, WATCHLIST
from strategy import generate_signals

_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", DATA_DIR)

POSITION_SIZE = 1000    # Rs per trade
MAX_POSITIONS = 5
MAX_HOLD_DAYS = 5
STOP_LOSS_PCT = 0.05    # 5%
COST_PCT      = 0.0015  # 0.15% per side
SLIPPAGE_PCT  = 0.0005  # 0.05% per side


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_all_data() -> dict:
    data = {}
    for ticker in WATCHLIST:
        filename = ticker.replace(".", "_") + ".csv"
        path = os.path.join(_DATA_PATH, filename)
        if not os.path.exists(path):
            print(f"WARNING: {filename} not found, skipping {ticker}")
            continue
        df = pd.read_csv(path, parse_dates=["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
        # Strip tz without UTC conversion: 2025-05-29 00:00:00+05:30 -> 2025-05-29 00:00:00
        if df["Date"].dt.tz is not None:
            df["Date"] = df["Date"].apply(lambda ts: ts.replace(tzinfo=None))
        df = generate_signals(df)
        data[ticker] = df
    return data


# ---------------------------------------------------------------------------
# Backtest engine
# ---------------------------------------------------------------------------

def run_backtest(data: dict) -> list:
    """
    Simulate the RSI(2) + 200-MA strategy over historical daily data.

    Note: 200-day MA warmup means signals only start around row 200 of each
    ticker. With 1 year of data, expect 5-20 total trades -- statistically thin
    but enough to verify correctness.
    """
    if not data:
        return []

    all_dates = sorted({d for df in data.values() for d in df["Date"]})

    # Pre-build O(1) lookups: {date: integer_row_index} per ticker
    ticker_info = {}
    for ticker, df in data.items():
        dates = list(df["Date"])
        ticker_info[ticker] = {
            "df":          df,
            "date_to_pos": {d: i for i, d in enumerate(dates)},
        }

    open_positions = []
    closed_trades  = []

    for date in all_dates:

        # --------------------------------------------------------------------
        # Step a: process exits for all open positions
        # --------------------------------------------------------------------
        surviving = []
        for pos in open_positions:
            ticker = pos["ticker"]
            d2p    = ticker_info[ticker]["date_to_pos"]
            df     = ticker_info[ticker]["df"]

            if date not in d2p:
                surviving.append(pos)
                continue

            today_idx = d2p[date]
            row       = df.iloc[today_idx]
            pos["days_held"] += 1

            open_px = row["Open"]
            low_px  = row["Low"]
            stop_px = pos["entry_price"] * (1 - STOP_LOSS_PCT)

            exit_price  = None
            exit_reason = None

            if low_px <= stop_px:
                # Gap protection: if we open below the stop, we fill at open
                exit_price  = min(open_px, stop_px)
                exit_reason = "stop_loss"
            else:
                yest_signal = df.iloc[today_idx - 1]["Signal"] if today_idx > 0 else "HOLD"
                if yest_signal == "SELL":
                    exit_price  = open_px * (1 - SLIPPAGE_PCT)
                    exit_reason = "SELL_signal"
                elif pos["days_held"] >= MAX_HOLD_DAYS:
                    exit_price  = open_px * (1 - SLIPPAGE_PCT)
                    exit_reason = "max_hold"

            if exit_price is not None:
                units       = pos["units"]
                gross_pnl   = (exit_price - pos["entry_price"]) * units
                entry_cost  = pos["entry_price"] * units * COST_PCT
                exit_cost   = exit_price * units * COST_PCT
                costs       = entry_cost + exit_cost
                net_pnl     = gross_pnl - costs
                entry_value = pos["entry_price"] * units
                return_pct  = net_pnl / entry_value * 100 if entry_value else 0.0
                closed_trades.append({
                    "ticker":       ticker,
                    "entry_date":   pos["entry_date"],
                    "entry_price":  pos["entry_price"],
                    "exit_date":    date,
                    "exit_price":   exit_price,
                    "units":        units,
                    "holding_days": pos["days_held"],
                    "gross_pnl":    gross_pnl,
                    "costs":        costs,
                    "net_pnl":      net_pnl,
                    "return_pct":   return_pct,
                    "exit_reason":  exit_reason,
                })
            else:
                surviving.append(pos)

        open_positions = surviving

        # --------------------------------------------------------------------
        # Step b: check entries
        # --------------------------------------------------------------------
        held_tickers = {p["ticker"] for p in open_positions}

        for ticker in WATCHLIST:
            if len(open_positions) >= MAX_POSITIONS:
                break
            if ticker not in ticker_info or ticker in held_tickers:
                continue

            d2p = ticker_info[ticker]["date_to_pos"]
            df  = ticker_info[ticker]["df"]

            if date not in d2p:
                continue

            today_idx = d2p[date]
            if today_idx == 0:
                continue

            yest_signal = df.iloc[today_idx - 1]["Signal"]
            if yest_signal != "BUY":
                continue

            row         = df.iloc[today_idx]
            entry_price = row["Open"] * (1 + SLIPPAGE_PCT)
            units       = int(math.floor(POSITION_SIZE / entry_price))
            if units == 0:
                continue

            open_positions.append({
                "ticker":      ticker,
                "entry_date":  date,
                "entry_price": entry_price,
                "units":       units,
                "days_held":   0,
            })
            held_tickers.add(ticker)

    # ------------------------------------------------------------------------
    # Close any remaining open positions at final close price
    # ------------------------------------------------------------------------
    for pos in open_positions:
        ticker     = pos["ticker"]
        df         = ticker_info[ticker]["df"]
        last_row   = df.iloc[-1]
        exit_price = last_row["Close"]
        exit_date  = last_row["Date"]

        units       = pos["units"]
        gross_pnl   = (exit_price - pos["entry_price"]) * units
        entry_cost  = pos["entry_price"] * units * COST_PCT
        exit_cost   = exit_price * units * COST_PCT
        costs       = entry_cost + exit_cost
        net_pnl     = gross_pnl - costs
        entry_value = pos["entry_price"] * units
        return_pct  = net_pnl / entry_value * 100 if entry_value else 0.0

        closed_trades.append({
            "ticker":       ticker,
            "entry_date":   pos["entry_date"],
            "entry_price":  pos["entry_price"],
            "exit_date":    exit_date,
            "exit_price":   exit_price,
            "units":        units,
            "holding_days": pos["days_held"],
            "gross_pnl":    gross_pnl,
            "costs":        costs,
            "net_pnl":      net_pnl,
            "return_pct":   return_pct,
            "exit_reason":  "end_of_backtest",
        })

    return closed_trades


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _fmt_date(d) -> str:
    return d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)[:10]


def _print_table(headers: list, rows: list) -> None:
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    def fmt_row(cells):
        return "|" + "|".join(f" {str(c):<{w}} " for c, w in zip(cells, widths)) + "|"

    print(sep)
    print(fmt_row(headers))
    print(sep)
    for row in rows:
        print(fmt_row(row))
    print(sep)


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

def print_results(trades: list) -> None:
    if not trades:
        print("\nNo trades were generated.")
        return

    # --- Last 20 trades table ---
    recent    = trades[-20:]
    start_idx = len(trades) - len(recent) + 1
    print(f"\nRecent trades ({len(recent)} of {len(trades)} total):")

    headers = ["#", "Ticker", "Entry Date", "Exit Date", "Reason",
               "Units", "Entry Px", "Exit Px", "Hold", "Net P&L", "Ret%"]
    rows = []
    for i, t in enumerate(recent, start_idx):
        rows.append([
            i,
            t["ticker"],
            _fmt_date(t["entry_date"]),
            _fmt_date(t["exit_date"]),
            t["exit_reason"],
            t["units"],
            f"₹{t['entry_price']:.2f}",
            f"₹{t['exit_price']:.2f}",
            t["holding_days"],
            f"₹{t['net_pnl']:+.2f}",
            f"{t['return_pct']:+.2f}%",
        ])
    _print_table(headers, rows)

    # --- Summary stats ---
    total   = len(trades)
    winners = [t for t in trades if t["net_pnl"] > 0]
    losers  = [t for t in trades if t["net_pnl"] <= 0]
    win_rate = len(winners) / total * 100

    total_net    = sum(t["net_pnl"]   for t in trades)
    avg_win      = sum(t["net_pnl"]   for t in winners) / len(winners) if winners else 0.0
    avg_loss     = sum(t["net_pnl"]   for t in losers)  / len(losers)  if losers  else 0.0
    gross_wins   = sum(t["gross_pnl"] for t in winners) if winners else 0.0
    gross_losses = abs(sum(t["gross_pnl"] for t in losers)) if losers else 0.0
    pf           = gross_wins / gross_losses if gross_losses > 0 else float("inf")
    avg_hold     = sum(t["holding_days"] for t in trades) / total
    total_costs  = sum(t["costs"] for t in trades)

    max_streak = streak = 0
    for t in trades:
        if t["net_pnl"] <= 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0

    pf_str = f"{pf:.2f}" if pf != float("inf") else "inf (no losses)"
    W   = 36
    SEP = "=" * (W + 22)

    print()
    print(SEP)
    print("  SUMMARY")
    print(SEP)
    print(f"  {'Total trades':<{W}} {total}")
    print(f"  {'Winning trades':<{W}} {len(winners)}  ({win_rate:.2f}%)")
    print(f"  {'Losing trades':<{W}} {len(losers)}")
    print(f"  {'Total net P&L':<{W}} ₹{total_net:+.2f}")
    print(f"  {'Average win':<{W}} ₹{avg_win:.2f}")
    print(f"  {'Average loss':<{W}} ₹{avg_loss:.2f}")
    print(f"  {'Profit factor (gross W / gross L)':<{W}} {pf_str}")
    print(f"  {'Max consecutive losses':<{W}} {max_streak}")
    print(f"  {'Average holding days':<{W}} {avg_hold:.1f}")
    print(f"  {'Total costs paid':<{W}} ₹{total_costs:.2f}")
    print(SEP)

    # --- Per-stock summary ---
    by_ticker: dict = {}
    for t in trades:
        tk = t["ticker"]
        if tk not in by_ticker:
            by_ticker[tk] = {"trades": 0, "wins": 0, "net_pnl": 0.0}
        by_ticker[tk]["trades"]  += 1
        by_ticker[tk]["wins"]    += int(t["net_pnl"] > 0)
        by_ticker[tk]["net_pnl"] += t["net_pnl"]

    print("\nPer-stock summary:")
    tk_headers = ["Ticker", "Trades", "Wins", "Win Rate", "Net P&L"]
    tk_rows = []
    for tk in sorted(by_ticker):
        s  = by_ticker[tk]
        wr = s["wins"] / s["trades"] * 100 if s["trades"] else 0.0
        tk_rows.append([tk, s["trades"], s["wins"], f"{wr:.2f}%", f"₹{s['net_pnl']:+.2f}"])
    _print_table(tk_headers, tk_rows)


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    data   = load_all_data()
    trades = run_backtest(data)
    print_results(trades)
