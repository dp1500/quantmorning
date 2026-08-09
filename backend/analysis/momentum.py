"""analysis/momentum.py"""
from __future__ import annotations
import numpy as np
import pandas as pd

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))
from config import RSI_PERIOD, MACD_FAST, MACD_SLOW, MACD_SIGNAL, STOCH_K, STOCH_D, ROC_PERIOD


def compute_momentum(df: pd.DataFrame) -> dict:
    print("\n📐 Computing momentum indicators...")
    if df.empty or 'close' not in df.columns:
        return {"rsi": 50.0, "macd": 0.0, "macdSignal": 0.0, "macdHistogram": 0.0, "stochastic": 50.0, "roc": 0.0}
    close = df['close'].astype(float).values
    high = df['high'].astype(float).values if 'high' in df.columns else close
    low = df['low'].astype(float).values if 'low' in df.columns else close
    rsi = _rsi(close, RSI_PERIOD)
    ml, sl, hl = _macd(close, MACD_FAST, MACD_SLOW, MACD_SIGNAL)
    stoch = _stoch(close, high, low, STOCH_K, STOCH_D)
    roc = _roc(close, ROC_PERIOD)
    result = {"rsi": round(rsi, 1), "macd": round(ml, 1), "macdSignal": round(sl, 1), "macdHistogram": round(hl, 1), "stochastic": round(stoch, 1), "roc": round(roc, 1)}
    print(f"  ✓ RSI={rsi:.1f} MACD={ml:.1f} Stoch={stoch:.1f} ROC={roc:.1f}")
    return result


def _rsi(close, period): return 50.0 if len(close) < period + 1 else float(100 - (100 / (1 + max(np.mean(np.maximum(np.diff(close[-period-1:]), 0)), 1e-10) / max(np.mean(np.abs(np.minimum(np.diff(close[-period-1:]), 0))), 1e-10))))
def _macd(close, fast, slow, sig):
    if len(close) < slow + sig: return (0.0, 0.0, 0.0)
    s = pd.Series(close); ef = s.ewm(span=fast, adjust=False).mean(); es = s.ewm(span=slow, adjust=False).mean(); ml = ef - es; sl = ml.ewm(span=sig, adjust=False).mean(); return (round(float(ml.iloc[-1]), 2), round(float(sl.iloc[-1]), 2), round(float((ml - sl).iloc[-1]), 2))
def _stoch(close, high, low, k, d): return 50.0 if len(close) < k + d or (s := np.max(high[-k:]) - np.min(low[-k:])) == 0 else float(((close[-1] - np.min(low[-k:])) / s) * 100)
def _roc(close, period): return 0.0 if len(close) < period + 1 else float(((close[-1] - close[-period-1]) / close[-period-1]) * 100)
