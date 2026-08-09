"""analysis/screener.py — Quant Screener"""
from __future__ import annotations
import numpy as np
import pandas as pd
from datetime import datetime

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))
from config import SECTOR_KEYS, SCREENER_MIN_SIGNAL_STRENGTH

SECTOR_LIST = list(SECTOR_KEYS.keys())

TOP_CONTRIBUTORS = {
    "NIFTY Bank": ["HDFCBANK", "ICICIBANK", "SBIN"],
    "NIFTY IT": ["TCS", "INFY", "WIPRO"],
    "NIFTY Auto": ["TATAMOTORS", "MARUTI", "M&M"],
    "NIFTY Pharma": ["SUNPHARMA", "DRREDDY", "CIPLA"],
    "NIFTY FMCG": ["HINDUNILVR", "NESTLEIND", "ITC"],
    "NIFTY Metal": ["TATASTEEL", "HINDALCO", "JSWSTEEL"],
    "NIFTY Oil & Gas": ["RELIANCE", "ONGC", "BPCL"],
    "NIFTY Energy": ["RELIANCE", "NTPC", "POWERGRID"],
    "NIFTY Healthcare": ["SUNPHARMA", "APOLLOHOSP", "MAXHEALTH"],
    "NIFTY Realty": ["DLF", "GODREJPROP", "OBEROIRLTY"],
}


def run_screener(stock_data: pd.DataFrame, sector_data: pd.DataFrame = None) -> dict:
    print("\n🔍 Running Quant Screener...")
    stocks = _score_stocks(stock_data)
    sectors = _score_sectors(sector_data) if sector_data is not None else _score_sectors(stock_data)
    print(f"  ✓ Scored {len(stocks)} stocks, {len(sectors)} sectors")
    return {"generatedAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+05:30"), "stocks": stocks, "sectors": sectors}


def _score_stocks(df):
    if df is None or df.empty: return []
    results = []
    for _, row in df.iterrows():
        symbol = str(row.get("symbol", "")); name = str(row.get("name", symbol))
        ltp = float(row.get("ltp", row.get("close", 0)))
        change_pct = float(row.get("change_pct", row.get("changePct", 0)))
        mom = float(row.get("momentum_score", row.get("momentumScore", 50)))
        vol = float(row.get("volatility_score", row.get("volatilityScore", 50)))
        ml = float(row.get("ml_probability", row.get("mlProbability", 0.5)))
        score = mom * 0.4 + (100 - vol) * 0.2 + ml * 0.4 * 100
        signal = "bullish" if score >= 65 else "bearish" if score <= 35 else "neutral"
        ss = int(round(score))
        if ss < SCREENER_MIN_SIGNAL_STRENGTH and len(results) > 20: continue
        tags = []
        if mom > 70: tags.append("High Momentum")
        if mom < 30: tags.append("Weak Momentum")
        if vol > 60: tags.append("High Volatility")
        if abs(change_pct) > 2: tags.append("Volume Spike" if change_pct > 0 else "Profit Booking")
        if signal == "bullish" and mom > 60: tags.append("Breakout")
        if signal == "neutral": tags.append("Range Bound")
        if ml > 0.75: tags.append("ML Confidence")
        if not tags: tags.append("Mixed")
        results.append({"symbol": symbol, "name": name, "sector": str(row.get("sector", "NIFTY Other")), "ltp": round(ltp, 2), "changePct": round(change_pct, 2), "signal": signal, "signalStrength": ss, "metrics": {"momentumScore": int(round(mom)), "volatilityScore": int(round(vol)), "mlProbability": round(ml, 2)}, "tags": tags[:4]})
    results.sort(key=lambda x: x["signalStrength"], reverse=True)
    return results


def _score_sectors(df):
    if df is None or df.empty: return []
    results = []
    for _, row in df.iterrows():
        idx = str(row.get("index", row.get("symbol", "")))
        ltp = float(row.get("ltp", row.get("close", 0))); chg = float(row.get("change_pct", row.get("changePct", 0)))
        mom = float(row.get("momentum_score", row.get("momentumScore", 50)))
        vol = float(row.get("volatility_score", row.get("volatilityScore", 50)))
        ml = float(row.get("ml_probability", row.get("mlProbability", 0.5)))
        score = mom * 0.5 + (100 - vol) * 0.2 + ml * 0.3 * 100
        signal = "bullish" if score >= 65 else "bearish" if score <= 35 else "neutral"
        tags = []; tags.append("Momentum" if signal == "bullish" else "Weak" if signal == "bearish" else "Mixed")
        if abs(chg) > 1.5: tags.append("Breakout" if chg > 0 else "Pressure")
        results.append({"index": idx, "ltp": round(ltp, 2), "changePct": round(chg, 2), "signal": signal, "signalStrength": int(round(score)), "topContributors": TOP_CONTRIBUTORS.get(idx, ["—", "—", "—"]), "tags": tags[:3]})
    results.sort(key=lambda x: x["signalStrength"], reverse=True)
    return results
