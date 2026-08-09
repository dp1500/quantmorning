"""
data_fetch/fetch_commodities.py — YFinance commodities, forex, GIFT Nifty, Asian markets.

Commodities (Gold, Brent, USDINR, DXY): latest close vs previous close (~24h change)
Asian markets (Nikkei, KOSPI, Hang Seng): latest open vs previous close
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta

import sys
import math
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))

from config import YFINANCE_SYMBOLS, ASIAN_MARKETS
from helpers import ist_now, safe_float

IST = timezone(timedelta(hours=5, minutes=30))


def _commodity_quote(symbol: str, name: str, precision: int = 2) -> dict:
    """
    Commodities/forex: latest Close vs previous Close (~24h change).
    Uses 3 daily candles to get the last complete bar.
    """
    import yfinance as yf
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="3d", interval="1d")
        if hist.empty or len(hist) < 2:
            return _empty(name, symbol)

        rows = [(idx, row) for idx, row in hist.iterrows()]
        rows.sort(key=lambda x: x[0])

        latest_close = safe_float(rows[-1][1]["Close"])
        prev_close   = safe_float(rows[-2][1]["Close"])
        latest_high  = safe_float(rows[-1][1]["High"])
        latest_low   = safe_float(rows[-1][1]["Low"])

        change = latest_close - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0

        sparkline = [safe_float(r[1]["Close"]) for r in rows[-8:]] if len(rows) >= 2 else []

        return {
            "symbol": symbol, "name": name,
            "ltp": round(latest_close, precision), "prevClose": round(prev_close, precision),
            "change": round(change, precision), "changePct": round(change_pct, 2),
            "dayHigh": round(latest_high, precision), "dayLow": round(latest_low, precision),
            "sparkline": [round(s, precision) for s in sparkline],
        }
    except Exception as e:
        print(f"  ⚠ YFinance failed for {name}: {e}")
        return _empty(name, symbol)


def _asian_quote(symbol: str, name: str, precision: int = 0) -> dict:
    """
    Asian markets: latest Open (today's session) vs previous Close.
    By 7 AM IST, Nikkei/KOSPI/Hang Seng have opened for the day.
    """
    import yfinance as yf
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="3d", interval="1d")
        if hist.empty or len(hist) < 2:
            return _empty(name, symbol)

        rows = [(idx, row) for idx, row in hist.iterrows()]
        rows.sort(key=lambda x: x[0])
        today_ist = datetime.now(IST).date()

        latest_date, latest_row = rows[-1]
        prev_date, prev_row = rows[-2]

        # If latest candle is today: use Open as display (session has started)
        # If latest candle is yesterday: use Close (market hasn't opened yet)
        if latest_date == today_ist:
            display_val = safe_float(latest_row["Open"])
        else:
            display_val = safe_float(latest_row["Close"])

        prev_close = safe_float(prev_row["Close"])
        change = round(display_val - prev_close, precision) if not (math.isnan(display_val) or math.isnan(prev_close)) else 0.0
        change_pct = (change / prev_close * 100) if prev_close else 0
        high = safe_float(latest_row["High"])
        low = safe_float(latest_row["Low"])

        sparkline = [safe_float(r[1]["Close"]) for r in rows[-8:]] if len(rows) >= 2 else []

        return {
            "symbol": symbol, "name": name,
            "ltp": round(display_val, precision), "prevClose": round(prev_close, precision),
            "change": round(change, precision), "changePct": round(change_pct, 2),
            "dayHigh": round(high, precision), "dayLow": round(low, precision),
            "sparkline": [round(s, precision) for s in sparkline],
        }
    except Exception as e:
        print(f"  ⚠ YFinance failed for {name}: {e}")
        return _empty(name, symbol)


def _empty(name: str, symbol: str) -> dict:
    return {"symbol": symbol, "name": name, "ltp": 0, "prevClose": 0,
            "change": 0, "changePct": 0, "dayHigh": 0, "dayLow": 0, "sparkline": []}


# ────────────────────────── Public API ──────────────────────────

def fetch_all_commodities() -> dict:
    """Brent, Gold, USD/INR, DXY: latest close vs previous close."""
    print("\n🛢️ Fetching commodities & forex (YFinance)...")
    name_map = {"brent_oil": "Brent Crude", "gold": "Gold (COMEX)", "usd_inr": "USD/INR", "dxy": "DXY"}
    results = {}
    for key, symbol in YFINANCE_SYMBOLS.items():
        prec = 0 if key == "gold" else 2
        results[key] = _commodity_quote(symbol, name_map[key], precision=prec)
        r = results[key]
        print(f"  ✓ {r['name']}: {r['ltp']} (24h: {r['changePct']:+.2f}%)")
    return results


def fetch_gift_nifty() -> dict:
    """GIFT Nifty via ^NSEI proxy."""
    print("\n🇮🇳 Fetching GIFT Nifty...")
    import yfinance as yf
    try:
        ticker = yf.Ticker("^NSEI")
        hist = ticker.history(period="3d", interval="1d")
        if not hist.empty and len(hist) >= 2:
            rows = sorted([(idx, row) for idx, row in hist.iterrows()])
            prev_close = safe_float(rows[-2][1]["Close"])
            current = safe_float(rows[-1][1]["Close"])
            change = current - prev_close
            change_pct = (change / prev_close * 100) if prev_close else 0
            r = {"symbol": "^NSEI", "name": "GIFT Nifty", "ltp": round(current, 0),
                 "prevClose": round(prev_close, 0), "change": round(change, 0),
                 "changePct": round(change_pct, 2)}
            print(f"  ✓ GIFT Nifty: {current:.0f} ({change_pct:+.2f}%)")
            return r
    except Exception:
        pass
    print("  ⚠ GIFT Nifty unavailable")
    return {"symbol": "NSE", "name": "GIFT Nifty", "ltp": 0, "prevClose": 0, "change": 0, "changePct": 0}


def fetch_asian_markets() -> list:
    """Nikkei, KOSPI, Hang Seng: latest Open vs previous Close."""
    print("\n🏯 Fetching Asian markets (Open vs prev Close)...")
    results = []
    for key, cfg in ASIAN_MARKETS.items():
        q = _asian_quote(cfg["symbol"], cfg["name"], precision=0)
        print(f"  ✓ {q['name']}: {q['ltp']:.0f} ({q['changePct']:+.2f}%)")
        results.append(q)
    return results
