"""analysis/volatility.py"""
from __future__ import annotations
import numpy as np
import pandas as pd

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))
from config import HV_WINDOW_20, HV_WINDOW_50, ATR_PERIOD, BB_PERIOD, BB_STD


def compute_volatility(df: pd.DataFrame) -> dict:
    print("\n📉 Computing volatility metrics...")
    if df.empty or 'close' not in df.columns:
        return {"historicalVol20d": 0, "historicalVol50d": 0, "atr14": 0, "bollingerUpper": 0, "bollingerLower": 0, "bollingerMiddle": 0, "impliedVolatility": 0}
    c = df['close'].astype(float).values
    h = df['high'].astype(float).values if 'high' in df.columns else c
    l = df['low'].astype(float).values if 'low' in df.columns else c
    hv20 = _hv(c, HV_WINDOW_20); hv50 = _hv(c, HV_WINDOW_50); atr = _atr(c, h, l, ATR_PERIOD)
    bu, bm, bl = _bb(c, BB_PERIOD, BB_STD); iv = hv20 * 1.15
    result = {"historicalVol20d": round(hv20, 1), "historicalVol50d": round(hv50, 1), "atr14": round(atr, 1), "bollingerUpper": round(bu, 1), "bollingerLower": round(bl, 1), "bollingerMiddle": round(bm, 1), "impliedVolatility": round(iv, 1)}
    print(f"  ✓ HV(20d)={hv20:.1f}% ATR={atr:.1f} BB=[{bl:.0f}–{bu:.0f}]")
    return result


def _hv(close, w): return 0.0 if len(close) < w + 1 else float(np.std(np.log(close[-w-1:][1:] / close[-w-1:][:-1]) * 100) * np.sqrt(252))
def _atr(close, high, low, period):
    if len(close) < period + 1: return 0.0
    pc = np.roll(close, 1); pc[0] = close[0]
    return float(np.mean(np.maximum(high - low, np.maximum(np.abs(high - pc), np.abs(low - pc)))[-period:]))
def _bb(close, period, nstd):
    if len(close) < period: return (float(close[-1]), float(close[-1]), float(close[-1]))
    s = pd.Series(close[-period:]); m = float(s.mean()); std = float(s.std()); return (m + nstd * std, m, m - nstd * std)
