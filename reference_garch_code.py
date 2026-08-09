# Forecasts with actual dates instead of Day 1...Day 6
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.structural import UnobservedComponents
from arch import arch_model
from scipy.stats import t, norm
import warnings
warnings.filterwarnings("ignore")

# ------------------ User-specified params ------------------
CSV_PATH = '/content/nifty_daily_data.csv'

# SSM (Kalman+GJR) params
SSM_WINDOW = 150
SSM_p, SSM_q = 1, 1
SSM_USE_GJR = True
SSM_CI = 0.65

# Pure GARCH params
GARCH_WINDOW = 100
GARCH_HORIZON = 6
GARCH_p, GARCH_q = 2, 1
GARCH_CI = 0.65
GARCH_USE_GJR = False
# -----------------------------------------------------------

def load_df(path):
    df = pd.read_csv(path, parse_dates=True, index_col=0)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.sort_index().copy()
    if 'Close' not in df.columns:
        raise ValueError("CSV must contain 'Close' column")
    df['Log_Return'] = np.log(df['Close'] / df['Close'].shift(1))
    df.dropna(subset=['Log_Return'], inplace=True)
    return df

def fit_kalman_local_level(returns):
    model = UnobservedComponents(returns, level='local level')
    res = model.fit(disp=False)
    try:
        ss = res.smoothed_state
        mu_smoothed = pd.Series(ss[0, :], index=returns.index)
    except Exception:
        mu_smoothed = pd.Series(res.predict(), index=returns.index)
    return {'res': res, 'mu_smoothed': mu_smoothed}

def estimate_phi_intercept(mu_smoothed):
    y = mu_smoothed.values[1:]
    x = mu_smoothed.values[:-1]
    if len(x) < 5:
        return 0.95, 0.0
    X = np.column_stack([x, np.ones(len(x))])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    return float(b[0]), float(b[1])

def fit_garch(residuals_dec, p=1, q=1, use_gjr=False, dist='t'):
    residuals_pct = residuals_dec * 100.0
    if use_gjr:
        am = arch_model(residuals_pct, vol='Garch', p=p, o=1, q=q, dist=dist, mean='Zero')
    else:
        am = arch_model(residuals_pct, vol='Garch', p=p, q=q, dist=dist, mean='Zero')
    return am.fit(disp='off')

def multi_day_cum_vol_from_fit(fit, horizon):
    f = fit.forecast(horizon=horizon, reindex=False)
    daily_vars = np.asarray(f.variance.values[0]).astype(float)
    cum_vars = np.cumsum(daily_vars)
    return np.sqrt(cum_vars) / 100.0

# ---------------- Forecast SSM ----------------
def forecast_ssm(df, window, horizon, p, q, use_gjr, ci):
    train = df.iloc[-window:]
    last_date = train.index[-1]
    last_price = float(train['Close'].iloc[-1])

    kal = fit_kalman_local_level(train['Log_Return'])
    mu_sm = kal['mu_smoothed']
    try:
        mu_last = float(kal['res'].filtered_state[0, -1])
    except Exception:
        mu_last = float(mu_sm.iloc[-1])
    phi, intercept = estimate_phi_intercept(mu_sm)

    residuals_dec = (train['Log_Return'] - mu_sm).dropna()
    gfit = fit_garch(residuals_dec, p=p, q=q, use_gjr=use_gjr)
    cum_vols = multi_day_cum_vol_from_fit(gfit, horizon)

    # build cumulative means
    mus = []
    mu = mu_last
    cum_means = []
    cum = 0.0
    for s in range(horizon):
        mu = intercept + phi * mu
        cum += mu
        cum_means.append(cum)

    # z quantile
    nu = gfit.params.get('nu', None)
    if nu is None or np.isnan(nu):
        z = norm.ppf((1 + ci) / 2.0)
    else:
        z = t.ppf((1 + ci) / 2.0, df=float(nu))

    # forecast dates
    forecast_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=horizon, freq="B")

    rows = []
    for s, d in enumerate(forecast_dates):
        lo = last_price * np.exp(cum_means[s] - z * cum_vols[s])
        hi = last_price * np.exp(cum_means[s] + z * cum_vols[s])
        med = last_price * np.exp(cum_means[s])
        rows.append({
                'Date': d,
                'Lower': int(round(lo)),
                'Median': int(round(med)),
                'Upper': int(round(hi))
            })
    table = pd.DataFrame(rows)
    return table, last_date, last_price

# ---------------- Forecast pure GARCH ----------------
def forecast_garch(df, window, horizon, p, q, ci, use_gjr):
    train = df.iloc[-window:]
    last_date = train.index[-1]
    last_price = float(train['Close'].iloc[-1])

    train_pct = (train['Log_Return'] * 100.0).dropna()
    if use_gjr:
        am = arch_model(train_pct, vol='Garch', p=p, o=1, q=q, dist='t', mean='Constant')
    else:
        am = arch_model(train_pct, vol='Garch', p=p, q=q, dist='t', mean='Constant')
    fit = am.fit(disp='off')
    f = fit.forecast(horizon=horizon, reindex=False)
    daily_vars = np.asarray(f.variance.values[0]).astype(float)
    cum_vars = np.cumsum(daily_vars)
    cum_vols = np.sqrt(cum_vars) / 100.0
    mu_const = float(fit.params.get('mu', 0.0))/100.0 if 'mu' in fit.params else 0.0
    cum_means = np.array([mu_const * (s+1) for s in range(horizon)])

    nu = fit.params.get('nu', None)
    if nu is None or np.isnan(nu):
        z = norm.ppf((1 + ci) / 2.0)
    else:
        z = t.ppf((1 + ci) / 2.0, df=float(nu))

    forecast_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=horizon, freq="B")

    rows = []
    for s, d in enumerate(forecast_dates):
        lo = last_price * np.exp(cum_means[s] - z * cum_vols[s])
        hi = last_price * np.exp(cum_means[s] + z * cum_vols[s])
        med = last_price * np.exp(cum_means[s])
        rows.append({'Date': d, 'Lower': lo, 'Median': med, 'Upper': hi})
    table = pd.DataFrame(rows)
    return table, last_date, last_price

# ---------------- Run both ----------------
df = load_df(CSV_PATH)

ssm_tab, ssm_last_date, ssm_last_price = forecast_ssm(df, window=SSM_WINDOW, horizon=6, p=SSM_p, q=SSM_q, use_gjr=SSM_USE_GJR, ci=SSM_CI)
garch_tab, garch_last_date, garch_last_price = forecast_garch(df, window=GARCH_WINDOW, horizon=GARCH_HORIZON, p=GARCH_p, q=GARCH_q, ci=GARCH_CI, use_gjr=GARCH_USE_GJR)

print(f"SSM model last training date: {ssm_last_date.date()} | Last price: {ssm_last_price:.2f}")
display(ssm_tab)

print(f"\nPure GARCH model last training date: {garch_last_date.date()} | Last price: {garch_last_price:.2f}")
display(garch_tab)

# ---------------- Plot ----------------
plt.figure(figsize=(10,6))
plt.fill_between(ssm_tab['Date'], ssm_tab['Lower'], ssm_tab['Upper'], color='orange', alpha=0.3, label='SSM 65% band')
plt.plot(ssm_tab['Date'], ssm_tab['Median'], 'o-', color='darkorange', label='SSM median')

plt.fill_between(garch_tab['Date'], garch_tab['Lower'], garch_tab['Upper'], color='skyblue', alpha=0.3, label='GARCH 60% band')
plt.plot(garch_tab['Date'], garch_tab['Median'], 'o-', color='blue', label='GARCH median')

plt.xlabel('Date')
plt.ylabel('Predicted price')
plt.title('6-day forecasts with calendar dates')
plt.legend()
plt.grid(alpha=0.25)
plt.show()
