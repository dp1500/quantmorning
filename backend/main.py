#!/usr/bin/env python3
"""
main.py — QuantMorning backend pipeline orchestrator.

Run daily at ~6:00 AM IST to:
  1. Fetch Nifty historical candles from Upstox (2 years daily)
  2. Fetch market snapshot (Nifty, Sensex, VIX) + YFinance commodities
  3. Compute SSM Kalman + GARCH(2,1) dual forecast
  4. Fetch OI levels from Upstox option chain
  5. Compute momentum & volatility indicators
  6. Run quant screener on stocks & 17 sector indices
  7. Output all JSON → final_data/ (frontend-readable)
  8. Mirror to src/data/ (for Astro SSG)

Usage:
  python main.py                     # Full pipeline
  python main.py --skip-screener     # Skip screener (faster)
  python main.py --skip-upstox       # Skip Upstox (use YFinance only)
"""
from __future__ import annotations
import sys, io
# Fix Windows console encoding for emoji
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    FINAL_DATA_DIR, FRONTEND_DATA_DIR, UPSTOX_ACCESS_TOKEN, UPSTOX_API_KEY,
)
from helpers import write_json_dual, ist_now

# Data fetchers
from data_fetch.fetch_spot import (
    fetch_nifty_historical, build_nifty_snapshot,
    fetch_sensex_historical, build_sensex_snapshot,
    fetch_vix_historical, build_vix_snapshot,
)
from data_fetch.fetch_commodities import fetch_all_commodities, fetch_gift_nifty, fetch_asian_markets
from data_fetch.fetch_oi_historical import fetch_oi_historical

# Analysis
from analysis.forecast import compute_forecast
from analysis.momentum import compute_momentum
from analysis.volatility import compute_volatility
from analysis.screener import run_screener


def main():
    parser = argparse.ArgumentParser(description="QuantMorning Data Pipeline")
    parser.add_argument("--skip-screener", action="store_true", help="Skip quant screener")
    parser.add_argument("--skip-upstox", action="store_true", help="Skip Upstox API calls (test mode)")
    args = parser.parse_args()

    print("=" * 60)
    print(f"📊 QUANTMORNING PIPELINE — {ist_now().strftime('%Y-%m-%d %H:%M IST')}")
    print("=" * 60)

    if args.skip_upstox:
        print("\n⚠️  --skip-upstox mode: using sample data only")

    FINAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    FRONTEND_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # =============================================
    # 1. FETCH NIFTY HISTORICAL DATA
    # =============================================
    if not args.skip_upstox and UPSTOX_ACCESS_TOKEN:
        nifty_df = fetch_nifty_historical()
    else:
        import pandas as pd
        nifty_df = _mock_nifty_data()

    # =============================================
    # 2. MARKET SNAPSHOT (all pre-market: yesterday vs day-before from candles)
    # =============================================
    if not args.skip_upstox and UPSTOX_ACCESS_TOKEN:
        nifty_snapshot = build_nifty_snapshot(nifty_df)
        sensex_df = fetch_sensex_historical()
        ss = build_sensex_snapshot(sensex_df)
        vix_df = fetch_vix_historical()
        vs = build_vix_snapshot(vix_df)
        upstox_assets = {}
        if nifty_snapshot:
            upstox_assets["nifty50"] = nifty_snapshot
        if ss:
            upstox_assets["sensex"] = ss
        if vs:
            upstox_assets["india_vix"] = vs
    else:
        upstox_assets = _mock_spot()

    commodity_assets = fetch_all_commodities()
    gift_nifty = fetch_gift_nifty()
    asian_markets = fetch_asian_markets()

    # Map commodity keys from snake_case → camelCase for frontend
    commodity_mapped = {
        "brentOil": commodity_assets.get("brent_oil", {}),
        "gold": commodity_assets.get("gold", {}),
        "usdInr": commodity_assets.get("usd_inr", {}),
        "dxy": commodity_assets.get("dxy", {}),
    }

    # VIX regime classification
    vix_val = upstox_assets.get("india_vix", {}).get("ltp", 15)
    vix_regime = "low" if vix_val < 13 else "normal" if vix_val < 17 else "elevated" if vix_val < 22 else "high"

    market_snapshot = {
        "timestamp": ist_now().isoformat(),
        "assets": {**upstox_assets, **commodity_mapped},
        "giftNifty": gift_nifty,
        "asianMarkets": asian_markets,
        "vixRegime": vix_regime,
    }
    write_json_dual(market_snapshot, FINAL_DATA_DIR, FRONTEND_DATA_DIR, "market_snapshot.json")

    # =============================================
    # 3. NIFTY CHART DATA (2-year OHLC + markers)
    # =============================================
    spot_price = upstox_assets.get("nifty50", {}).get("ltp", 25300)
    chart_json = _build_nifty_chart_json(nifty_df, spot_price)
    write_json_dual(chart_json, FINAL_DATA_DIR, FRONTEND_DATA_DIR, "nifty_chart_data.json")

    # =============================================
    # 4. OI HISTORICAL (15-min, last 2 days, next 2 Tuesdays)
    # =============================================
    if not args.skip_upstox and UPSTOX_ACCESS_TOKEN:
        oi_data = fetch_oi_historical(spot_price)
    else:
        oi_data = {"expiries": [], "oiLevels": [], "spotPrice": spot_price}

    # Extract compact OI levels for the forecast chart (first expiry's strikes)
    oi_compact = None
    if oi_data.get("expiries") and len(oi_data["expiries"]) > 0:
        first = oi_data["expiries"][0]
        oi_compact = {
            "expiryDate": first.get("expiryDate"),
            "daysLeft": first.get("daysToExpiry", 0),
            "maxPain": _calc_max_pain(first.get("strikes", [])),
            "pcr": first.get("pcr", 0),
            "strikes": first.get("strikes", []),
        }

    # =============================================
    # 5. FORECAST (SSM Kalman + GARCH)
    # =============================================

    forecast_json = compute_forecast(nifty_df, oi_levels=oi_compact)
    write_json_dual(forecast_json, FINAL_DATA_DIR, FRONTEND_DATA_DIR, "garch_forecast.json")

    # =============================================
    # 6. MOMENTUM & VOLATILITY
    # =============================================
    momentum = compute_momentum(nifty_df)
    volatility = compute_volatility(nifty_df)
    quant_metrics_json = {"nifty": {"momentum": momentum, "volatility": volatility}}
    write_json_dual(quant_metrics_json, FINAL_DATA_DIR, FRONTEND_DATA_DIR, "quant_metrics.json")

    # =============================================
    # 7. OI ANALYSIS (detailed — from historical fetcher)
    # =============================================
    write_json_dual(oi_data, FINAL_DATA_DIR, FRONTEND_DATA_DIR, "oi_analysis.json")

    # =============================================
    # 8. QUANT SCREENER
    # =============================================
    if not args.skip_screener:
        import numpy as np
        stock_df = _build_mock_screener(spot_price)
        screener_json = run_screener(stock_df)
        write_json_dual(screener_json, FINAL_DATA_DIR, FRONTEND_DATA_DIR, "screener_data.json")

    print("\n" + "=" * 60)
    print("✅ PIPELINE COMPLETE")
    print(f"   final_data/: {', '.join(f.name for f in FINAL_DATA_DIR.glob('*.json'))}")
    print("=" * 60)


# ---- Helpers ----

def _build_nifty_chart_json(df, spot_price: float) -> dict:
    import pandas as pd
    if df.empty:
        return {"ath": 0, "athDate": "", "thisYearHigh": 0, "thisYearHighDate": "",
                "sixMonthHigh": 0, "sixMonthLow": 0, "threeMonthHigh": 0, "threeMonthLow": 0,
                "oneMonthHigh": 0, "oneMonthLow": 0, "threeYearData": []}

    close = df["close"].astype(float)
    ath = float(close.max())
    ath_idx = close.idxmax()
    try:
        ath_date = df["date"].iloc[ath_idx].strftime("%Y-%m-%d")
    except Exception:
        ath_date = ""

    recent = df.tail(250)
    yr_high = float(recent["close"].max())
    yr_high_idx = recent["close"].idxmax()
    try:
        yr_high_date = recent["date"].iloc[yr_high_idx].strftime("%Y-%m-%d")
    except Exception:
        yr_high_date = ""

    six = df.tail(125); three = df.tail(63); one = df.tail(21)

    chart_data = df[["date", "open", "high", "low", "close", "volume"]].copy()
    chart_data["date"] = pd.to_datetime(chart_data["date"]).dt.strftime("%Y-%m-%d")

    return {
        "ath": round(ath, 2), "athDate": ath_date,
        "thisYearHigh": round(yr_high, 2), "thisYearHighDate": yr_high_date,
        "sixMonthHigh": round(float(six["high"].max()), 2),
        "sixMonthLow": round(float(six["low"].min()), 2),
        "threeMonthHigh": round(float(three["high"].max()), 2),
        "threeMonthLow": round(float(three["low"].min()), 2),
        "oneMonthHigh": round(float(one["high"].max()), 2),
        "oneMonthLow": round(float(one["low"].min()), 2),
        "threeYearData": chart_data.to_dict(orient="records"),
    }


def _build_mock_screener(spot_price: float):
    import numpy as np
    import pandas as pd
    from config import SECTOR_KEYS
    symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR",
               "SBIN", "BHARTIARTL", "KOTAKBANK", "WIPRO", "AXISBANK", "LT",
               "SUNPHARMA", "BAJFINANCE", "MARUTI", "TITAN", "ASIANPAINT",
               "HCLTECH", "ULTRACEMCO", "NTPC"]
    sectors = list(SECTOR_KEYS.keys())
    np.random.seed(42)
    data = []
    for sym in symbols:
        ltp = spot_price * np.random.uniform(0.1, 5.0)
        data.append({
            "symbol": sym, "name": sym,
            "sector": np.random.choice(sectors),
            "ltp": round(ltp, 2),
            "change_pct": round(np.random.uniform(-3, 3), 2),
            "momentum_score": int(np.random.uniform(20, 90)),
            "volatility_score": int(np.random.uniform(10, 80)),
            "ml_probability": round(np.random.uniform(0.2, 0.9), 2),
        })
    return pd.DataFrame(data)


def _mock_nifty_data():
    import pandas as pd
    import numpy as np
    dates = pd.date_range("2023-08-01", periods=500, freq="B")
    price = 20000
    closes = []
    for _ in dates:
        price += (np.random.randn() * 120)
        closes.append(max(18000, price))
    df = pd.DataFrame({
        "date": dates, "open": [c * (1 + np.random.randn() * 0.005) for c in closes],
        "high": [c * (1 + abs(np.random.randn()) * 0.008) for c in closes],
        "low": [c * (1 - abs(np.random.randn()) * 0.008) for c in closes],
        "close": closes,
        "volume": np.random.randint(50000, 200000, len(dates)),
    })
    print("\n📈 Using mock Nifty data (500 days)")
    return df


def _calc_max_pain(strikes):
    if not strikes:
        return 0
    return max(strikes, key=lambda s: s.get('callOI',0) + s.get('putOI',0)).get('strike', 0)


def _mock_spot() -> dict:
    print("\n📊 Using mock spot data")
    return {
        "nifty50": {"symbol": "NIFTY 50", "name": "NIFTY 50", "ltp": 25300, "prevClose": 25120,
                    "change": 180, "changePct": 0.72, "dayHigh": 25350, "dayLow": 25080,
                    "prevHigh": 25350, "prevLow": 25080, "prevRangePct": 1.07, "ydayDate": "2026-08-06"},
        "sensex": {"symbol": "SENSEX", "name": "SENSEX", "ltp": 78499, "prevClose": 78350,
                    "change": 149, "changePct": 0.19, "dayHigh": 78600, "dayLow": 78300,
                    "prevHigh": 78600, "prevLow": 78300, "prevRangePct": 0.38, "ydayDate": "2026-08-06"},
        "india_vix": {"symbol": "India VIX", "name": "India VIX", "ltp": 12.16, "prevClose": 13.40,
                       "change": -1.24, "changePct": -9.25, "dayHigh": 13.80, "dayLow": 12.00,
                       "prevHigh": 13.80, "prevLow": 12.00, "prevRangePct": 13.43, "ydayDate": "2026-08-06"},
    }


if __name__ == "__main__":
    main()
