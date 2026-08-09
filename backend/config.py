"""
config.py — Central configuration for QuantMorning backend.
API keys, paths, model parameters, instrument keys.
"""
from __future__ import annotations
import os
from pathlib import Path

# ---- PATHS ----
ROOT = Path(__file__).resolve().parent.parent  # quantmorning/
BACKEND_DIR = ROOT / "backend"
DATA_DIR = BACKEND_DIR / "data"
FINAL_DATA_DIR = ROOT / "final_data"
FRONTEND_DATA_DIR = ROOT / "src" / "data"

# ---- UPSTOX CREDENTIALS ----
UPSTOX_API_KEY = "b9400d3c-b823-487f-8bf2-ecd4688a283d"
UPSTOX_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI0WEM2RVEiLCJqdGkiOiI2YTc2YzJlMjk1ZjJhODc1MTE3MjUxODMiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzg2MTY4MDM0LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3ODYyMjY0MDB9.q7ZwXTfU0D0fG0_w8UJSc1g_Q8pEJWpqoMFZbdAl4NM"
UPSTOX_BASE_URL = "https://api.upstox.com/v2"
UPSTOX_RATE_LIMIT = 99

# ---- INSTRUMENT KEYS ----
INSTRUMENT_KEYS = {
    "nifty50":      "NSE_INDEX|Nifty 50",
    "sensex":       "BSE_INDEX|SENSEX",
    "nifty_bank":   "NSE_INDEX|Nifty Bank",
    "india_vix":    "NSE_INDEX|India VIX",
}

SECTOR_KEYS = {
    "NIFTY Bank":               "NSE_INDEX|Nifty Bank",
    "NIFTY Financial Services":  "NSE_INDEX|Nifty Financial Services",
    "NIFTY IT":                  "NSE_INDEX|Nifty IT",
    "NIFTY Auto":                "NSE_INDEX|Nifty Auto",
    "NIFTY Pharma":             "NSE_INDEX|Nifty Pharma",
    "NIFTY FMCG":               "NSE_INDEX|Nifty FMCG",
    "NIFTY Realty":             "NSE_INDEX|Nifty Realty",
    "NIFTY Metal":              "NSE_INDEX|Nifty Metal",
    "NIFTY PSU Bank":           "NSE_INDEX|Nifty PSU Bank",
    "NIFTY Energy":             "NSE_INDEX|Nifty Energy",
    "NIFTY Healthcare":         "NSE_INDEX|Nifty Healthcare",
    "NIFTY Consumer Durables":  "NSE_INDEX|Nifty Consumer Durables",
    "NIFTY Oil & Gas":          "NSE_INDEX|Nifty Oil & Gas",
    "NIFTY Media":              "NSE_INDEX|Nifty Media",
    "NIFTY Infrastructure":     "NSE_INDEX|Nifty Infrastructure",
    "NIFTY Commodities":        "NSE_INDEX|Nifty Commodities",
    "NIFTY MNC":                "NSE_INDEX|Nifty MNC",
}

YFINANCE_SYMBOLS = {
    "brent_oil": "BZ=F",
    "gold":      "GC=F",
    "usd_inr":   "USDINR=X",
    "dxy":       "DX-Y.NYB",   # US Dollar Index
}

# GIFT Nifty (NSE IFSC) + Asian markets
GIFT_NIFTY_SYMBOL = "^NSEI"   # Nifty 50 from YFinance for GIFT Nifty proxy
ASIAN_MARKETS = {
    "nikkei":    {"symbol": "^N225", "name": "Nikkei 225"},
    "kospi":     {"symbol": "^KS11", "name": "KOSPI"},
    "hangseng":  {"symbol": "^HSI",  "name": "Hang Seng"},
}

# ---- HISTORICAL & FORECAST PARAMS ----
HISTORICAL_YEARS = 2
HISTORICAL_INTERVAL = "day"

SSM_WINDOW = 150
SSM_P, SSM_Q = 1, 1
SSM_CI = 0.65

GARCH_WINDOW = 100
GARCH_HORIZON = 5
GARCH_P, GARCH_Q = 2, 1
GARCH_CI = 0.65

# ---- MOMENTUM & VOLATILITY ----
RSI_PERIOD = 14
MACD_FAST, MACD_SLOW, MACD_SIGNAL = 12, 26, 9
STOCH_K, STOCH_D = 14, 3
ROC_PERIOD = 12
HV_WINDOW_20, HV_WINDOW_50 = 20, 50
ATR_PERIOD = 14
BB_PERIOD, BB_STD = 20, 2

# ---- OPTIONS OI ----
OI_NUM_EXPIRIES = 2
OI_STRIKE_RANGE_POINTS = 800

# ---- SCREENER ----
NIFTY500_SYMBOLS_FILE = BACKEND_DIR / "data" / "nifty500_symbols.csv"
SCREENER_MIN_SIGNAL_STRENGTH = 50
