"""
config.py
Central configuration for the algo-trader-india project.
Keeps the watchlist and shared settings in one place.
"""

# --- Starting universe ---
# 2 ETFs (broad market anchors) + 6 affordable stocks
# All NSE-listed, under ~₹600 so we can size positions on ₹5000 capital

WATCHLIST = [
    # ETFs
    "NIFTYBEES.NS",   # Nifty 50 ETF — broad market
    "GOLDBEES.NS",    # Gold ETF — diversifier, uncorrelated to stocks

    # Stocks
    "ITC.NS",         # FMCG / tobacco
    "SBIN.NS",        # State Bank of India — banking
    "ONGC.NS",        # Oil & Natural Gas Corp — energy/PSU
    "COALINDIA.NS",   # Coal India — mining/PSU
    "WIPRO.NS",       # Wipro — IT
    "TATAPOWER.NS",   # Tata Power — power utility
]

# --- Data settings ---
PERIOD = "1y"        # 1 year of history (enough for 200-day MA filter)
INTERVAL = "1d"       # daily candles
DATA_DIR = "data"     # where CSVs are saved
