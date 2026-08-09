"""
data_fetch/fetch_oi_historical.py — OI data: V3 HistoryV3Api, 10-min candles,
last 2 trading days, next 2 TUESDAY expiries (NSE moved weekly to Tuesday, Sept 2025).
"""
from __future__ import annotations
import pandas as pd
from datetime import datetime, timedelta

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))

from config import UPSTOX_ACCESS_TOKEN, INSTRUMENT_KEYS, UPSTOX_RATE_LIMIT
from helpers import RateLimiter, get_upstox_client, ist_now, safe_float, safe_int

rate_limit = RateLimiter(UPSTOX_RATE_LIMIT)


def _next_tuesday_expiries(num: int = 2) -> list[str]:
    """
    Compute next 'num' Tuesdays as Nifty weekly expiry dates.
    NSE moved Nifty weekly expiry to Tuesday (Sept 2025).
    Does NOT use ExpiredInstrumentApi (that only returns past dates).
    """
    from datetime import date
    today = date.today()
    # Find next Tuesday
    days_until_tuesday = (1 - today.weekday()) % 7
    if days_until_tuesday == 0:
        days_until_tuesday = 7  # if today is Tuesday, go to next
    next_tue = today + timedelta(days=days_until_tuesday)
    return [(next_tue + timedelta(weeks=i)).strftime("%Y-%m-%d") for i in range(num)]


@rate_limit
def _get_option_contracts(client, instrument_key: str, expiry_date: str) -> list:
    from upstox_client import OptionsApi
    api = OptionsApi(client)
    try:
        resp = api.get_option_contracts(instrument_key=instrument_key, expiry_date=expiry_date)
        return resp.data if resp.data else []
    except Exception as e:
        print(f"  ⚠ Contract fetch failed: {e}")
        return []


@rate_limit
def _fetch_oi_v3(client, instrument_key: str, from_date: str, to_date: str) -> pd.DataFrame:
    """Fetch 10-min OI candles via V3 API (V2 didn't support 10/15min)."""
    from upstox_client import HistoryV3Api
    api = HistoryV3Api(client)
    try:
        resp = api.get_historical_candle_data1(
            instrument_key=instrument_key,
            unit="minutes",
            interval=10,
            to_date=to_date,
            from_date=from_date,
        )
        if resp.data and resp.data.candles:
            df = pd.DataFrame(resp.data.candles,
                columns=["timestamp", "open", "high", "low", "close", "volume", "oi"])
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df.sort_values("timestamp")
    except Exception as e:
        pass  # silent on individual contract failures
    return pd.DataFrame()


def fetch_oi_historical(spot_price: float) -> dict:
    """
    Fetch 10-min OI data for last 2 trading days, next 2 Tuesday expiries.
    """
    print("\n📋 Fetching OI historical (10-min V3, next 2 Tuesdays)...")
    client = get_upstox_client(UPSTOX_ACCESS_TOKEN)

    expiries = _next_tuesday_expiries(2)
    if not expiries:
        print("  ❌ No Tuesday expiries found")
        return {"expiries": [], "oiLevels": [], "spotPrice": spot_price}

    print(f"  🎯 Tuesday expiries: {expiries}")

    to_date = ist_now().strftime("%Y-%m-%d")
    from_date = (ist_now() - timedelta(days=5)).strftime("%Y-%m-%d")

    strike_window = 600  # ±12 strikes of 50 pts each
    strike_min = int((spot_price - strike_window) // 50 * 50)
    strike_max = int((spot_price + strike_window) // 50 * 50)

    all_oi_levels = []

    for expiry_date in expiries:
        print(f"\n  📅 Expiry {expiry_date}")
        contracts = _get_option_contracts(client, INSTRUMENT_KEYS["nifty50"], expiry_date)
        if not contracts:
            continue

        filtered = [c for c in contracts if strike_min <= safe_float(c.strike_price, 0) <= strike_max]
        print(f"     {len(filtered)} contracts in range {strike_min}–{strike_max}")

        expiry_oi = {"expiryDate": expiry_date, "strikes": []}
        count = 0

        for contract in filtered:
            strike = safe_int(contract.strike_price)
            is_call = "CE" in (contract.trading_symbol or "")

            df = _fetch_oi_v3(client, contract.instrument_key, from_date, to_date)
            if df.empty:
                continue

            count += 1
            last_oi = safe_int(df["oi"].iloc[-1])
            prev_oi = safe_int(df["oi"].iloc[-2]) if len(df) >= 2 else last_oi

            existing = next((s for s in expiry_oi["strikes"] if s["strike"] == strike), None)
            if existing:
                if is_call:
                    existing["callOI"] = last_oi
                    existing["callChange"] = last_oi - prev_oi
                else:
                    existing["putOI"] = last_oi
                    existing["putChange"] = last_oi - prev_oi
            else:
                expiry_oi["strikes"].append({
                    "strike": strike,
                    "callOI": last_oi if is_call else 0,
                    "putOI": last_oi if not is_call else 0,
                    "callChange": (last_oi - prev_oi) if is_call else 0,
                    "putChange": (last_oi - prev_oi) if not is_call else 0,
                })
            print(f"     {count}/{len(filtered)} {contract.trading_symbol} OI={last_oi}", end="\r")

        expiry_oi["strikes"].sort(key=lambda x: x["strike"])
        total_call = sum(s["callOI"] for s in expiry_oi["strikes"])
        total_put = sum(s["putOI"] for s in expiry_oi["strikes"])
        expiry_oi["totalCallOI"] = total_call
        expiry_oi["totalPutOI"] = total_put
        expiry_oi["pcr"] = round(total_put / total_call, 2) if total_call > 0 else 0
        dt = datetime.strptime(expiry_date, "%Y-%m-%d")
        expiry_oi["daysToExpiry"] = max((dt - datetime.now()).days, 0)

        print(f"\n     ✓ {len(expiry_oi['strikes'])} strikes, PCR={expiry_oi['pcr']}")
        all_oi_levels.append(expiry_oi)

    print(f"  ✅ Fetched OI for {len(all_oi_levels)} expiries")
    return {"expiries": all_oi_levels, "spotPrice": spot_price, "updatedAt": ist_now().isoformat()}
