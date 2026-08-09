"""
data_fetch/fetch_spot.py — Pre-market: build cards from historical daily candles.
Uses Upstox HistoryV3Api (not V2) for full 2+ year daily data.
"""
from __future__ import annotations
import pandas as pd
from datetime import timedelta

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))

from config import (
    UPSTOX_ACCESS_TOKEN, INSTRUMENT_KEYS,
    HISTORICAL_YEARS, UPSTOX_RATE_LIMIT,
)
from helpers import RateLimiter, get_upstox_client, ist_now, safe_float

rate_limit = RateLimiter(UPSTOX_RATE_LIMIT)


@rate_limit
def _fetch_historical_v3(client, instrument_key: str, from_date: str, to_date: str,
                         unit: str = "days", interval: int = 1) -> pd.DataFrame:
    """
    Fetch historical candles via V3 API.
    V3 supports full multi-year ranges (no 1-year cap like V2).
    unit="days", interval=1 = daily OHLC
    unit="minutes", interval=10 = 10-min intraday OHLC+OI
    """
    from upstox_client import HistoryV3Api
    api = HistoryV3Api(client)
    try:
        resp = api.get_historical_candle_data1(
            instrument_key=instrument_key,
            unit=unit,
            interval=interval,
            to_date=to_date,
            from_date=from_date,
        )
        if resp.data and resp.data.candles:
            df = pd.DataFrame(resp.data.candles,
                columns=["timestamp", "open", "high", "low", "close", "volume", "oi"])
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df.sort_values("timestamp")
    except Exception as e:
        print(f"  ⚠ V3 fetch failed {instrument_key}: {e}")
    return pd.DataFrame()


def _fetch_index_historical(instrument_key: str, label: str) -> pd.DataFrame:
    """Fetch 2+ years of daily candles via V3 API."""
    print(f"\n📈 Fetching {label} historical (2 years, V3)...")
    client = get_upstox_client(UPSTOX_ACCESS_TOKEN)
    to_date = ist_now().strftime("%Y-%m-%d")
    from_date = (ist_now() - timedelta(days=HISTORICAL_YEARS * 365)).strftime("%Y-%m-%d")
    df = _fetch_historical_v3(client, instrument_key, from_date, to_date, unit="days", interval=1)
    if df.empty:
        print(f"  ❌ No {label} historical data.")
        return df
    df = df.rename(columns={"timestamp": "date"})
    print(f"  ✓ {len(df)} candles: {df['date'].iloc[0].strftime('%Y-%m-%d')} → {df['date'].iloc[-1].strftime('%Y-%m-%d')}")
    return df


def fetch_nifty_historical() -> pd.DataFrame:
    return _fetch_index_historical(INSTRUMENT_KEYS["nifty50"], "Nifty 50")

def fetch_sensex_historical() -> pd.DataFrame:
    return _fetch_index_historical(INSTRUMENT_KEYS["sensex"], "SENSEX")

def fetch_vix_historical() -> pd.DataFrame:
    return _fetch_index_historical(INSTRUMENT_KEYS["india_vix"], "India VIX")


# ────────────────────────── Snapshot builders (pure, no I/O) ──────────────────────────

def build_nifty_snapshot(nifty_df: pd.DataFrame) -> dict | None:
    if nifty_df is None or len(nifty_df) < 2:
        return None
    return _build_index_card(nifty_df, "NIFTY 50")

def build_sensex_snapshot(sensex_df: pd.DataFrame) -> dict | None:
    if sensex_df is None or len(sensex_df) < 2:
        return None
    return _build_index_card(sensex_df, "SENSEX")

def build_vix_snapshot(vix_df: pd.DataFrame) -> dict | None:
    if vix_df is None or len(vix_df) < 2:
        return None
    return _build_index_card(vix_df, "India VIX")


def _build_index_card(df: pd.DataFrame, label: str) -> dict:
    latest = df.iloc[-1]    # yesterday
    previous = df.iloc[-2]  # day before
    close_val = safe_float(latest["close"])
    prev_close = safe_float(previous["close"])
    high_val = safe_float(latest["high"])
    low_val = safe_float(latest["low"])
    change = close_val - prev_close
    change_pct = (change / prev_close) * 100 if prev_close else 0
    range_pct = ((high_val - low_val) / prev_close) * 100 if prev_close else 0
    date_str = str(latest["date"])[:10]

    print(f"  ✓ {label} (yesterday={date_str}): close={close_val:.0f} chg={change:+.0f} ({change_pct:+.2f}%) "
          f"range={low_val:.0f}–{high_val:.0f} ({range_pct:.1f}%)")

    return {
        "symbol": label, "name": label,
        "ltp": round(close_val, 2), "prevClose": round(prev_close, 2),
        "change": round(change, 2), "changePct": round(change_pct, 2),
        "dayHigh": round(high_val, 2), "dayLow": round(low_val, 2),
        "prevHigh": round(high_val, 2), "prevLow": round(low_val, 2),
        "prevRangePct": round(range_pct, 2), "ydayDate": date_str,
    }
