"""
analysis/forecast.py — SSM Kalman filter + GARCH(2,1) dual forecast.

Given Nifty daily OHLC data, produces 5-day ahead forecasts using:
  1. SSM local-level Kalman filter (150d window) with AR(1) drift
     and GJR-GARCH(1,1) on residuals → 65% CI
  2. Pure GARCH(2,1) on Student-t → 65% CI (comparison)

Does NOT require upstox_client — operates only on pandas DataFrames.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from datetime import timedelta
from scipy.stats import t as t_dist, norm
from typing import Optional
import warnings
warnings.filterwarnings("ignore")

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))

from config import (
    SSM_WINDOW, SSM_P, SSM_Q, SSM_CI,
    GARCH_WINDOW, GARCH_HORIZON, GARCH_P, GARCH_Q, GARCH_CI,
)
from helpers import ist_now


def compute_forecast(df: pd.DataFrame, oi_levels: Optional[dict] = None) -> dict:
    """
    Main entry point. Computes dual forecast and returns GarchForecast dict.

    Args:
        df: DataFrame with 'date' and 'close' columns (daily, ascending).
        oi_levels: Optional compact OI dict from fetch_oi_compact().

    Returns:
        Dict matching the frontend GarchForecast TypeScript type.
    """
    print("\n🔮 Running SSM Kalman + GARCH(2,1) dual forecast...")

    if df.empty or 'close' not in df.columns:
        return _empty_forecast()

    df = df.sort_values("date").dropna(subset=["close"]).copy()
    if 'date' not in df.columns and isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index()
    df["date"] = pd.to_datetime(df["date"])

    # Ensure business-day frequency
    df = df.set_index("date")
    df = df.asfreq("B")
    df["close"] = df["close"].ffill()
    df = df.dropna(subset=["close"]).reset_index()

    # Log returns
    df["log_return"] = np.log(df["close"] / df["close"].shift(1))
    df = df.dropna(subset=["log_return"])

    if len(df) < max(SSM_WINDOW, GARCH_WINDOW):
        print(f"  ❌ Not enough data ({len(df)} rows, need {max(SSM_WINDOW, GARCH_WINDOW)})")
        return _empty_forecast()

    # ---- SSM Kalman forecast ----
    ssm_forecast, _, _ = _forecast_ssm(df)
    # ---- GARCH forecast ----
    garch_forecast, _, _ = _forecast_garch(df)

    # Last 5 actual days
    last_n = df.iloc[-5:]
    last_5 = [
        {"date": row["date"].strftime("%Y-%m-%d"), "actual": round(float(row["close"]), 2),
         "forecast": None, "lowerCI": None, "upperCI": None}
        for _, row in last_n.iterrows()
    ]

    # 5-day forecast
    forecast_5 = []
    for i in range(GARCH_HORIZON):
        ssm_r = ssm_forecast.iloc[i] if i < len(ssm_forecast) else None
        garch_r = garch_forecast.iloc[i] if i < len(garch_forecast) else None
        fdate = (df["date"].iloc[-1] + timedelta(days=1) + pd.offsets.BDay(i))
        if ssm_r is not None and isinstance(ssm_r.get("Date"), pd.Timestamp):
            fdate = ssm_r["Date"]
        forecast_5.append({
            "date": fdate.strftime("%Y-%m-%d") if isinstance(fdate, pd.Timestamp) else str(fdate)[:10],
            "actual": None,
            "ssmMedian": round(float(ssm_r["Median"]), 0) if ssm_r is not None else None,
            "ssmLower": round(float(ssm_r["Lower"]), 0) if ssm_r is not None else None,
            "ssmUpper": round(float(ssm_r["Upper"]), 0) if ssm_r is not None else None,
            "garchMedian": round(float(garch_r["Median"]), 1) if garch_r is not None else None,
            "garchLower": round(float(garch_r["Lower"]), 1) if garch_r is not None else None,
            "garchUpper": round(float(garch_r["Upper"]), 1) if garch_r is not None else None,
        })

    ssm_vol = _estimate_annual_vol(df) * 0.95
    garch_vol = _estimate_annual_vol(df)

    result = {
        "lastUpdated": ist_now().strftime("%Y-%m-%dT%H:%M:%S+05:30"),
        "model": "SSM Kalman + GARCH(2,1)",
        "modelDesc": "Local-level Kalman filter (150d) with AR(1) drift + GJR-GARCH residuals; GARCH(2,1) on Student-t for comparison",
        "last5Days": last_5,
        "forecast5Days": forecast_5,
        "ssmAnnualVol": round(ssm_vol, 1),
        "garchAnnualVol": round(garch_vol, 1),
    }

    if oi_levels:
        result["oiLevels"] = oi_levels

    print(f"  ✓ SSM D+1: {forecast_5[0]['ssmMedian']} (range {forecast_5[0]['ssmLower']}–{forecast_5[0]['ssmUpper']})")
    print(f"  ✓ GARCH D+1: {forecast_5[0]['garchMedian']} (range {forecast_5[0]['garchLower']}–{forecast_5[0]['garchUpper']})")

    return result


def _estimate_annual_vol(df: pd.DataFrame) -> float:
    returns = df["log_return"].tail(GARCH_WINDOW).dropna()
    if len(returns) < 5:
        return 0.0
    return float(returns.std() * np.sqrt(252))


def _forecast_ssm(df: pd.DataFrame) -> tuple:
    """SSM Kalman local-level + GJR-GARCH on residuals."""
    from statsmodels.tsa.statespace.structural import UnobservedComponents
    from arch import arch_model

    train = df.iloc[-SSM_WINDOW:].copy()
    last_date = train["date"].iloc[-1]
    last_price = float(train["close"].iloc[-1])
    returns = train["log_return"].values

    # Kalman local-level
    try:
        model = UnobservedComponents(returns, level='local level')
        res = model.fit(disp=False)
        mu_vals = res.smoothed_state[0, :]
        mu_last = float(res.filtered_state[0, -1])
    except Exception:
        mu_vals = pd.Series(returns).ewm(span=20).mean().values
        mu_last = float(mu_vals[-1])

    # AR(1) drift on smoothed state
    if len(mu_vals) > 5:
        y = mu_vals[1:]
        x = mu_vals[:-1]
        X = np.column_stack([x, np.ones(len(x))])
        b, *_ = np.linalg.lstsq(X, y, rcond=None)
        phi, intercept = float(b[0]), float(b[1])
    else:
        phi, intercept = 0.95, 0.0

    # GJR-GARCH on residuals
    # Align: returns[1:] has len-1; mu_vals may be same len as returns
    ret_diff = returns[1:]
    mu_aligned = mu_vals[1:] if len(mu_vals) == len(returns) else mu_vals[:len(ret_diff)]
    rlen = min(len(ret_diff), len(mu_aligned))
    residuals_dec = ret_diff[:rlen] - mu_aligned[:rlen]
    residuals_dec = residuals_dec[~np.isnan(residuals_dec)]
    residuals_pct = residuals_dec * 100.0

    try:
        am = arch_model(residuals_pct, vol='Garch', p=SSM_P, o=1, q=SSM_Q, dist='t', mean='Zero')
        gfit = am.fit(disp='off')
        f = gfit.forecast(horizon=GARCH_HORIZON, reindex=False)
        daily_vars = np.asarray(f.variance.values[0]).astype(float)
    except Exception:
        daily_vars = np.full(GARCH_HORIZON, float(np.var(residuals_pct)))

    cum_vars = np.cumsum(daily_vars)
    cum_vols = np.sqrt(cum_vars) / 100.0

    # Cumulative mean
    mu = mu_last
    cum_means = []
    cum = 0.0
    for _ in range(GARCH_HORIZON):
        mu = intercept + phi * mu
        cum += mu
        cum_means.append(cum)

    # Quantile
    try:
        nu = gfit.params.get('nu', None)
    except Exception:
        nu = None
    z = norm.ppf((1 + SSM_CI) / 2.0) if (nu is None or np.isnan(nu)) else t_dist.ppf((1 + SSM_CI) / 2.0, df=float(nu))

    forecast_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=GARCH_HORIZON, freq="B")
    rows = []
    for s, d in enumerate(forecast_dates):
        lo = last_price * np.exp(cum_means[s] - z * cum_vols[s])
        hi = last_price * np.exp(cum_means[s] + z * cum_vols[s])
        med = last_price * np.exp(cum_means[s])
        rows.append({"Date": d, "Lower": round(lo), "Median": round(med), "Upper": round(hi)})

    return pd.DataFrame(rows), last_date, last_price


def _forecast_garch(df: pd.DataFrame) -> tuple:
    """Pure GARCH(2,1) on Student-t."""
    from arch import arch_model

    train = df.iloc[-GARCH_WINDOW:].copy()
    last_date = train["date"].iloc[-1]
    last_price = float(train["close"].iloc[-1])
    train_pct = (train["log_return"] * 100.0).dropna().values

    try:
        am = arch_model(train_pct, vol='Garch', p=GARCH_P, q=GARCH_Q, dist='t', mean='Constant')
        fit = am.fit(disp='off')
        f = fit.forecast(horizon=GARCH_HORIZON, reindex=False)
        daily_vars = np.asarray(f.variance.values[0]).astype(float)
        mu_const = float(fit.params.get('mu', 0.0)) if 'mu' in fit.params else 0.0
    except Exception:
        daily_vars = np.full(GARCH_HORIZON, float(np.var(train_pct)))
        mu_const = float(np.mean(train_pct))

    cum_vars = np.cumsum(daily_vars)
    cum_vols = np.sqrt(cum_vars) / 100.0

    if np.any(np.isnan(cum_vols)) or np.any(cum_vols <= 0):
        std_val = float(np.std(train_pct))
        cum_vols = np.array([std_val * np.sqrt(i + 1) / 100.0 for i in range(GARCH_HORIZON)])

    cum_means = np.array([mu_const * (s + 1) / 100.0 for s in range(GARCH_HORIZON)])

    try:
        nu = fit.params.get('nu', None)
    except Exception:
        nu = None
    z = norm.ppf((1 + GARCH_CI) / 2.0) if (nu is None or np.isnan(nu)) else t_dist.ppf((1 + GARCH_CI) / 2.0, df=float(nu))

    forecast_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=GARCH_HORIZON, freq="B")
    rows = []
    for s, d in enumerate(forecast_dates):
        lo = last_price * np.exp(min(cum_means[s] - z * cum_vols[s], 0.5))
        hi = last_price * np.exp(max(cum_means[s] + z * cum_vols[s], -0.3))
        med = last_price * np.exp(cum_means[s])
        rows.append({"Date": d, "Lower": round(lo, 1), "Median": round(med, 1), "Upper": round(hi, 1)})

    return pd.DataFrame(rows), last_date, last_price


def _empty_forecast() -> dict:
    return {
        "lastUpdated": ist_now().strftime("%Y-%m-%dT%H:%M:%S+05:30"),
        "model": "SSM Kalman + GARCH(2,1)",
        "modelDesc": "Forecast unavailable — insufficient data",
        "last5Days": [], "forecast5Days": [],
        "ssmAnnualVol": 0, "garchAnnualVol": 0,
    }
