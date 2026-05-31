# algo-trader-india

A fully automated stock trading pipeline for the Indian stock market, built as a learning project.

## Overview

This project is being built in two phases:

- **Phase 1** — Free tier using `yfinance` for market data and paper trading (no real money)
- **Phase 2** — Live trading via the Groww API with real capital

## Tech Stack

- **Language:** Python 3
- **Market Data:** yfinance (Phase 1), Groww API (Phase 2)
- **Broker:** Groww
- **Libraries:** pandas, numpy, matplotlib

## Project Structure

```
algo-trader-india/
├── data/          # Downloaded market data (gitignored)
├── src/           # Source code
├── notebooks/     # Jupyter notebooks for experiments
├── tests/         # Test scripts
└── requirements.txt
```

## Setup

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/algo-trader-india.git
cd algo-trader-india

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Status

🚧 Phase 1 — In development
