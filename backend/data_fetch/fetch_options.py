"""
data_fetch/fetch_options.py — Fetch Nifty options OI chain from Upstox.
Uses current SDK: OptionsApi, ExpiredInstrumentApi, MarketQuoteApi.
"""
from __future__ import annotations
import pandas as pd
from typing import Optional

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))

from config import (
    UPSTOX_ACCESS_TOKEN, INSTRUMENT_KEYS,
    OI_NUM_EXPIRIES, OI_STRIKE_RANGE_POINTS, UPSTOX_RATE_LIMIT,
)
from helpers import RateLimiter, get_upstox_client, ist_now, safe_float, safe_int

rate_limit = RateLimiter(UPSTOX_RATE_LIMIT)
API_VERSION = "2.0"


@rate_limit
def _fetch_option_contracts(client, instrument_key: str, expiry_date: str) -> Optional[list]:
    """Fetch option contracts via OptionsApi.get_option_contracts()."""
    from upstox_client import OptionsApi
    from upstox_client.rest import ApiException
    api = OptionsApi(client)
    try:
        resp = api.get_option_contracts(
            instrument_key=instrument_key,
            expiry_date=expiry_date,
            
        )
        return resp.data if resp else None
    except ApiException as e:
        print(f"  ⚠ Option chain fetch failed for {expiry_date}: {e}")
        return None


@rate_limit
def _fetch_ltp_batch(client, symbols: list) -> dict:
    """Batch LTP fetch via MarketQuoteApi.ltp() — supports up to 1000 symbols."""
    from upstox_client import MarketQuoteApi
    from upstox_client.rest import ApiException
    api = MarketQuoteApi(client)
    results = {}
    # Upstox supports up to 1000 symbols comma-separated in one call
    for i in range(0, len(symbols), 1000):
        batch = symbols[i:i + 1000]
        try:
            resp = api.ltp(symbol=",".join(batch), api_version=API_VERSION)
            if resp.data:
                for k, v in resp.data.items():
                    results[k] = v if isinstance(v, dict) else v.to_dict()
        except ApiException as e:
            print(f"  ⚠ Batch LTP failed: {e}")
    return results


def _get_expiries(client, instrument_key: str) -> list:
    """Fetch upcoming expiries via ExpiredInstrumentApi.get_expiries()."""
    from upstox_client import ExpiredInstrumentApi
    from upstox_client.rest import ApiException
    api = ExpiredInstrumentApi(client)
    try:
        resp = api.get_expiries(instrument_key=instrument_key)
        return sorted(resp.data) if resp.data else []
    except ApiException as e:
        print(f"  ❌ Failed to fetch expiries: {e}")
        return []


def fetch_oi_analysis(spot_price: float) -> dict:
    """Fetch OI analysis for the latest 2 Nifty expiries."""
    print("\n📋 Fetching Options OI data...")
    client = get_upstox_client(UPSTOX_ACCESS_TOKEN)

    all_expiries = _get_expiries(client, INSTRUMENT_KEYS["nifty50"])
    if not all_expiries:
        print("  ❌ No upcoming expiries")
        return {"latestExpiry": None, "secondLatestExpiry": None}

    today = ist_now().strftime("%Y-%m-%d")
    future_expiries = [e for e in all_expiries if e >= today][:OI_NUM_EXPIRIES]
    if not future_expiries:
        print("  ❌ No upcoming expiries")
        return {"latestExpiry": None, "secondLatestExpiry": None}

    results = {}
    strike_min = int((spot_price - OI_STRIKE_RANGE_POINTS) // 50 * 50)
    strike_max = int((spot_price + OI_STRIKE_RANGE_POINTS) // 50 * 50)

    for expiry_date in future_expiries:
        contracts = _fetch_option_contracts(client, INSTRUMENT_KEYS["nifty50"], expiry_date)
        if not contracts:
            continue
        filtered = [c for c in contracts if strike_min <= safe_float(getattr(c, 'strike_price', 0)) <= strike_max]
        instrument_keys = [c.instrument_key for c in filtered]
        ltp_data = _fetch_ltp_batch(client, instrument_keys)

        strike_map = {}
        for contract in filtered:
            strike = safe_int(getattr(contract, 'strike_price', 0))
            key = contract.instrument_key
            oi = safe_int((ltp_data.get(key) or {}).get("oi", 0))
            is_call = "CE" in (getattr(contract, 'trading_symbol', '') or '')
            change_oi = safe_int((ltp_data.get(key) or {}).get("change_oi", 0))
            if strike not in strike_map:
                strike_map[strike] = {"callOI": 0, "putOI": 0, "callChange": 0, "putChange": 0}
            if is_call:
                strike_map[strike]["callOI"] = oi
                strike_map[strike]["callChange"] = change_oi
            else:
                strike_map[strike]["putOI"] = oi
                strike_map[strike]["putChange"] = change_oi

        levels = [{"strike": s, **v} for s, v in sorted(strike_map.items())]
        total_call = sum(l["callOI"] for l in levels)
        total_put = sum(l["putOI"] for l in levels)
        pcr = total_put / total_call if total_call > 0 else 0
        max_pain = max(levels, key=lambda l: l["callOI"] + l["putOI"])["strike"] if levels else 0
        days_left = max((pd.Timestamp(expiry_date) - pd.Timestamp.now(tz="Asia/Kolkata")).days, 0)

        expiry_data = {
            "date": expiry_date, "daysToExpiry": days_left,
            "totalCallOI": total_call, "totalPutOI": total_put,
            "putCallRatio": round(pcr, 2), "maxPain": max_pain, "levels": levels,
            "oiChange24h": {"callChange": 0, "putChange": 0, "pcrChange": 0},
            "oiChange1hrPrevDay": {"callChange": 0, "putChange": 0, "pcrChange": 0},
        }
        key = "latestExpiry" if len(results) == 0 else "secondLatestExpiry"
        results[key] = expiry_data
        print(f"  ✓ {expiry_date}: {len(levels)} strikes, PCR={pcr:.2f}, Max Pain={max_pain}")

    if "latestExpiry" not in results:
        results["latestExpiry"] = None
    if "secondLatestExpiry" not in results:
        results["secondLatestExpiry"] = None
    return results


def fetch_oi_compact(spot_price: float) -> Optional[dict]:
    """Fetch compact OI data for combined NiftyRangeIntel view."""
    client = get_upstox_client(UPSTOX_ACCESS_TOKEN)

    all_expiries = _get_expiries(client, INSTRUMENT_KEYS["nifty50"])
    if not all_expiries:
        return None

    today = ist_now().strftime("%Y-%m-%d")
    future = [e for e in all_expiries if e >= today]
    if not future:
        return None
    expiry_date = future[0]

    contracts = _fetch_option_contracts(client, INSTRUMENT_KEYS["nifty50"], expiry_date)
    if not contracts:
        return None

    strike_min = int((spot_price - OI_STRIKE_RANGE_POINTS) // 50 * 50)
    strike_max = int((spot_price + OI_STRIKE_RANGE_POINTS) // 50 * 50)
    filtered = [c for c in contracts if strike_min <= safe_float(getattr(c, 'strike_price', 0)) <= strike_max]
    instrument_keys = [c.instrument_key for c in filtered]
    ltp_data = _fetch_ltp_batch(client, instrument_keys)

    strike_oi = {}
    for contract in filtered:
        strike = safe_int(getattr(contract, 'strike_price', 0))
        oi = safe_int((ltp_data.get(contract.instrument_key) or {}).get("oi", 0))
        is_call = "CE" in (getattr(contract, 'trading_symbol', '') or '')
        if strike not in strike_oi:
            strike_oi[strike] = {"callOI": 0, "putOI": 0}
        if is_call:
            strike_oi[strike]["callOI"] = oi
        else:
            strike_oi[strike]["putOI"] = oi

    strikes = sorted([{"strike": s, **d} for s, d in strike_oi.items()], key=lambda x: x["strike"])
    total_call = sum(s["callOI"] for s in strikes)
    total_put = sum(s["putOI"] for s in strikes)
    pcr = total_put / total_call if total_call > 0 else 0
    max_pain = max(strikes, key=lambda s: s["callOI"] + s["putOI"])["strike"] if strikes else 0
    days_left = max((pd.Timestamp(expiry_date) - pd.Timestamp.now(tz="Asia/Kolkata")).days, 0)

    return {
        "expiryDate": expiry_date, "daysLeft": days_left,
        "maxPain": max_pain, "pcr": round(pcr, 2), "strikes": strikes,
    }
