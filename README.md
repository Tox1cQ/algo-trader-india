# algo-trader-india

A backtesting research framework for systematic swing trading on Indian equities, built from scratch in Python as a learning project.

## TL;DR

Built a complete event-driven backtesting pipeline (data ingestion → indicators → strategies → backtest → daily scanner) on Indian NSE stocks. Tested four trading strategies across multiple watchlists with realistic transaction costs and slippage. **Key finding: simple mechanical strategies on ₹5,000 retail capital do not consistently extract edge once realistic costs are modeled — consistent with academic literature on retail algo trading.**

This repo prioritizes honest research over impressive numbers.

## What's inside

```
algo-trader-india/
├── src/
│   ├── config.py
│   ├── fetch_data.py
│   ├── indicators.py            # RSI Wilder, Donchian, Moving Average
│   ├── strategy.py              # RSI(2) + 200-MA filter
│   ├── strategy_donchian.py
│   ├── strategy_ma_cross.py     # 10/30 golden cross
│   ├── strategy_rsi_v2.py       # stricter thresholds
│   ├── scanner.py
│   ├── filter_universe.py
│   └── backtest.py
├── data/                        # gitignored CSVs
├── notebooks/
├── tests/
└── requirements.txt
```

## Architecture

The pipeline is strategy-agnostic: any module producing a `Signal` column (`BUY` / `SELL` / `HOLD`) plugs into the backtest engine via the `--strategy` flag.

- Run `scanner.py` for today's actionable signals
- Run `backtest.py --strategy <name>` for historical analysis

## Backtest engine — realistic by design

- **Event-driven:** walks chronologically through every trading day
- **Per-stock isolation:** failures don't crash the whole run
- **Costs:** 0.15% per side (brokerage + STT + GST), charged at actual fill price
- **Slippage:** 0.05% for liquid largecaps, 0.3% for smallcaps
- **Gap-down protection:** stops use `min(open, stop_price)` for realistic fills
- **Exit priority:** stop loss → SELL signal → max hold
- **Position sizing:** ₹1,000 per trade, max 5 simultaneous = ₹5,000 max deployed

## Research log

| Strategy | Universe | Trades | Win Rate | Net P&L | Profit Factor | Verdict |
|---|---|---|---|---|---|---|
| RSI(2) mean reversion | 8 stocks, 5y | 302 | 51.66% | -₹737 | 1.02 | Breakeven gross, costs erased edge |
| Donchian Breakout (20/10) | 8 stocks, 5y | 413 | 41.89% | -₹1,721 | 0.92 | Indian markets too choppy for breakouts |
| MA Crossover (10/30) | 8 stocks, 5y | 162 | 36.42% | +₹1,430 | 1.54 | Only consistent winner |
| MA Crossover (10/30) | 90 smallcaps, 5y | 401 | 24.44% | -₹1,175 | 0.99 | Universe expansion + 0.3% slippage erased edge |
| RSI(2) v2 + MA50/100 filter | 56 filtered stocks | 1,031 | 48.69% | -₹5,779 | 0.84 | Parameter tuning made it worse |

## Key research findings

1. Trend-following beat mean reversion on Indian equities 2021–2026
2. Naive universe expansion does **not** improve results (more signals ≠ more edge)
3. Costs are the dominant variable on small capital (₹2,915 in costs alone for RSI(2) v2)
4. Parameter tuning is dangerous — v2 was worse than v1
5. The MA Crossover "win" deserves skepticism — likely lucky stock selection

## Known limitations

- **Survivorship bias:** today's watchlist used for the 5-year backtest
- No regime detection
- `yfinance` data has occasional delays and gaps
- NSE equity only
- No walk-forward validation

## What I'd build next

- Paper trading loop
- Equity curve visualization (matplotlib)
- Walk-forward optimization
- Volatility regime detection
- Phase 2 with Groww API

## Tech stack

Python 3.14, pandas, numpy, yfinance, matplotlib, argparse. Developed on WSL Ubuntu.

## Honest reflection

This project was scoped as learning + resume with a ₹5,000 capital constraint. Across multiple strategies and watchlist configurations, no variant produced returns justifying real capital deployment relative to just holding NIFTYBEES. The most valuable output is not a profitable bot — it's the verified, evidence-based understanding that simple mechanical algo trading on small retail capital faces a structural disadvantage from transaction costs. The research framework is reusable and scales to larger capital or different asset classes.

## Setup

```bash
git clone https://github.com/tushar/algo-trader-india
cd algo-trader-india
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Fetch historical data
python src/fetch_data.py

# Run a backtest
python src/backtest.py --strategy ma_cross
```
