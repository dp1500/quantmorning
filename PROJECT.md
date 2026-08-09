# QuantMorning — Project Overview & Architecture
> Pre-market quantitative analysis dashboard for the Indian stock market.
> flow: Python used for fetching data from upstocks API  + doing analysis to creating final json data everyday  → FINAL JSON Uplaoded to github pages or server → friontend by Astro SSG . All pre-market. No live LTP.

---

## Final Aim

A single-page, dark-themed, premium fintech dashboard deployed on GitHub Pages that renders at 6:30 AM IST every weekday. It shows yesterday's Nifty/Sensex/VIX metrics, dual-model GARCH-Kalman 5-day forecasts with OI level overlays, momentum & volatility metrics, a Nifty 500 quant screener, and live commodity/forex/Asian market data — all assembled from a daily Python pipeline that fetches, computes, and outputs JSON files consumed by an Astro static site.

---

## Directory Map

```
quantmorning/
│
├── backend/                          # PYTHON — the brain (runs once daily)
│   ├── main.py                       # Orchestrator: fetch → analyze → output JSON
│   ├── config.py                     # API keys, instrument keys, model params
│   ├── helpers.py                    # RateLimiter, JSON writer, date utils, safe_float
│   ├── requirements.txt              # pandas, numpy, statsmodels, arch, scipy, yfinance, upstox-python
│   │
│   ├── data_fetch/                   # Fetchers — one domain each, pure I/O
│   │   ├── fetch_spot.py             # Nifty / Sensex / VIX daily candles from Upstox HistoryApi
│   │   ├── fetch_commodities.py      # Brent, Gold, USDINR, DXY, GIFT Nifty, Asian markets via YFinance
│   │   ├── fetch_options.py          # OI chain (live LTP-based — legacy, being replaced)
│   │   └── fetch_oi_historical.py    # OI data: 15-min candles, last 2 days, next 2 Thursday expiries
│   │
│   ├── analysis/                     # Quant models — pure math, no I/O
│   │   ├── forecast.py               # SSM Kalman (150d) + GARCH(2,1) dual forecast → 5-day ahead
│   │   ├── momentum.py               # RSI(14), MACD(12/26/9), Stochastic(14/3), ROC(12)
│   │   ├── volatility.py             # HV(20d/50d), ATR(14), Bollinger Bands(20,2), IV estimate
│   │   └── screener.py               # Composite scoring: momentum + vol + ML prob → signals
│   │
│   └── data/                         # Intermediate raw storage (optional)
│
├── final_data/                       # JSON output → ready for frontend consumption
│   ├── market_snapshot.json          # Nifty, Sensex, VIX, Brent, Gold, USD/INR, DXY, GIFT Nifty, Asian
│   ├── nifty_chart_data.json         # 2-year OHLC candles + ATH/6M/1M markers
│   ├── garch_forecast.json           # 5-day SSM + GARCH forecast + OI strike levels
│   ├── quant_metrics.json            # Momentum + volatility indicators
│   ├── oi_analysis.json              # Detailed OI: expiries, PCR, strike-level call/put OI
│   └── screener_data.json            # Stock + sector signals with strength scores
│
├── src/                              # ASTRO frontend — reads JSON at build time
│   ├── data/                         # Mirrored JSON (pipeline writes here too for Astro imports)
│   ├── pages/index.astro             # Single page: 5-panel layout
│   ├── layouts/BaseLayout.astro      # HTML shell, Inter + JetBrains Mono fonts
│   ├── styles/global.css             # Tailwind v4 dark theme (bg-primary #0a0a0b)
│   ├── lib/
│   │   ├── types.ts                  # All TypeScript interfaces matching JSON schemas
│   │   ├── formatters.ts             # Indian number formatting, VIX regime, signal colors
│   │   └── constants.ts              # Site config, 17 sectors, market hours
│   ├── components/
│   │   ├── layout/NavBar.astro       # Sticky glass-nav header
│   │   ├── ui/                       # Reusable: MetricCard, Sparkline, Badge, SectionHeader, QuickCard
│   │   ├── charts/ChartTheme.tsx     # Recharts theme, gradient defs, tooltip
│   │   └── panels/
│   │       ├── MarketSnapshot.astro  # Pre-market index cards + commodities + Asian (Astro SSG)
│   │       ├── NiftyChart.tsx        # 2-year area chart with ATH/6M/1M reference lines (React)
│   │       ├── NiftyRangeIntel.tsx   # Combined SSM+GARCH forecast + OI bars on same chart (React)
│   │       ├── QuantMetrics.astro    # Momentum/volatility gauge cards (Astro SSG)
│   │       └── Screener.tsx          # Searchable stock/sector table with expandable rows (React)
│
├── .github/workflows/
│   ├── daily-data.yml                # 6:00 AM IST cron: run pipeline → commit JSON → push
│   └── deploy.yml                    # On push to main: Astro build → GitHub Pages deploy
│
├── package.json                      # Astro, React, Tailwind v4, Recharts, lucide-react
├── astro.config.mjs                  # Astro + React + Tailwind v4 Vite plugin
└── tsconfig.json
```

---

## Data Flow (6:00 AM IST daily)

```
GitHub Actions triggers main.py
│
├── 1. fetch_nifty_historical()          Upstox HistoryApi                    → nifty_df (496 candles)
├── 2. fetch_sensex_historical()         Upstox HistoryApi                    → sensex_df (496 candles)
├── 3. fetch_vix_historical()            Upstox HistoryApi                    → vix_df (496 candles)
├── 4. build_nifty_snapshot(nifty_df)     iloc[-1] close vs iloc[-2] close    → {ltp, prevClose, change, changePct, prevHigh, prevLow, prevRangePct}
├── 5. build_sensex_snapshot(sensex_df)  same pattern                         → Sensex card
├── 6. build_vix_snapshot(vix_df)        same pattern                         → VIX card
├── 7. fetch_all_commodities()           YFinance BZ=F, GC=F, USDINR=X, DXY   → Brent, Gold, USD/INR, DXY
├── 8. fetch_gift_nifty()                YFinance ^NSEI                       → GIFT Nifty proxy
├── 9. fetch_asian_markets()             YFinance ^N225, ^KS11, ^HSI          → Nikkei, KOSPI, Hang Seng
│
├── 10. _build_nifty_chart_json(nifty_df)  ATH, 6M/1M H/L from DF            → nifty_chart_data.json
├── 11. fetch_oi_historical(spot)         Upstox 15-min candles, 2 expiries   → oi_analysis.json
├── 12. compute_forecast(nifty_df, oi)    SSM Kalman + GARCH(2,1)             → garch_forecast.json
├── 13. compute_momentum(nifty_df)        RSI, MACD, Stoch, ROC               → quant_metrics.json
├── 14. compute_volatility(nifty_df)      HV, ATR, BB, IV                     → quant_metrics.json
├── 15. run_screener(stock_df)            Composite scoring                   → screener_data.json
│
├── write_json_dual() copies each to final_data/ AND src/data/
├── git add + commit + push
│
└── push triggers deploy.yml → Astro build → GitHub Pages
```

---

## Design Philosophy

### Pre-Market Only
- **No live LTP for any Indian index.** Every Nifty/Sensex/VIX value comes from historical daily candles: `iloc[-1]` (yesterday) compared against `iloc[-2]` (day before).
- Commodities & forex use latest available candle: Open if today's partial candle exists, Close if yesterday's.
- The pipeline runs at 6 AM IST before markets open. No intraday data.

### Separation of Concerns
```
Fetchers (data_fetch/)     →   I/O only: HTTP calls, DataFrame returns
Models (analysis/)          →   Pure functions: DataFrame in → dict out
Main (main.py)              →   Orchestration only: calls fetchers, passes to models, writes JSON
Frontend (src/)             →   Reads JSON at Astro build time, renders SSG
```

### Extensibility
Adding a new analysis is 3 steps:
1. `backend/analysis/new_model.py` — pure function, df → dict
2. `backend/main.py` — one import + one `write_json_dual()` call
3. `src/components/panels/NewPanel.tsx` — reads the JSON, renders chart

The JSON schema is the contract. Change it in the model, update types.ts, and the frontend auto-adapts.

---

## Key Technical Details

### Upstox SDK (v2)
| Class | Method | Used For |
|-------|--------|----------|
| `HistoryApi` | `get_historical_candle_data1(api_version="2.0")` | All daily + 15-min candles |
| `ExpiredInstrumentApi` | `get_expiries()` | Expiry date list |
| `OptionsApi` | `get_option_contracts(expiry_date=)` | Option contract list per expiry |
| `MarketQuoteApi` | `ltp(symbol=, api_version="2.0")` | **NOT USED** for indices anymore |

### Forecast Model
```
SSM Kalman (150d window)
  → Local-level Kalman filter on log returns
  → AR(1) drift on smoothed state  (phi + intercept via least squares)
  → GJR-GARCH(1,1) on residuals    (Student-t, 65% CI)
  → Cumulative mean + cumulative vol → D+1 to D+5 price levels

GARCH(2,1) comparison (100d window)
  → Pure GARCH on Student-t, Constant mean
  → Same cumulative expansion → comparison line
```

### Moment indicators
RSI(14), MACD(12/26/9), Stochastic(14/3), ROC(12)

### Volatility indicators
Historical Vol (20d, 50d annualized), ATR(14), Bollinger Bands (20,2), IV ≈ HV20d × 1.15

### Commodities via YFinance
BZ=F (Brent), GC=F (Gold), USDINR=X, DX-Y.NYB (DXY), ^N225 (Nikkei), ^KS11 (KOSPI), ^HSI (Hang Seng), ^NSEI (GIFT Nifty proxy)

### Formatting
Indian number system: lakh/crore. VIX regime: <13=Low, <17=Normal, <22=Elevated, ≥22=High. Signal colors: emerald=long, red=short, amber=neutral.

---

## JSON Output Schemas

### market_snapshot.json
```json
{
  "timestamp": "ISO",
  "assets": {
    "nifty50":  { "ltp": closes[-1], "prevClose": closes[-2], "change", "changePct",
                  "dayHigh": highs[-1], "dayLow": lows[-1],
                  "prevHigh", "prevLow", "prevRangePct" },
    "sensex":   { /* same */ },
    "india_vix":{" /* same */ },
    "brentOil": { "ltp", "prevClose", "change", "changePct", "sparkline" },
    "gold":     { /* same */ },
    "usdInr":   { /* same */ },
    "dxy":      { /* same */ }
  },
  "giftNifty":  { "ltp", "prevClose", "change", "changePct" },
  "asianMarkets": [ { "name", "ltp", "prevClose", "change", "changePct", "sparkline" }, ... ],
  "vixRegime": "low|normal|elevated|high"
}
```

### garch_forecast.json
```json
{
  "lastUpdated": "ISO",
  "last5Days": [ { "date", "actual", "forecast": null, "lowerCI": null, "upperCI": null } ],
  "forecast5Days": [ {
    "date", "actual": null,
    "ssmMedian", "ssmLower", "ssmUpper",
    "garchMedian", "garchLower", "garchUpper"
  } ],
  "ssmAnnualVol", "garchAnnualVol",
  "oiLevels": { "expiryDate", "daysLeft", "maxPain", "pcr",
                "strikes": [ { "strike", "callOI", "putOI" } ] }
}
```

### nifty_chart_data.json
```json
{
  "ath", "athDate",
  "sixMonthHigh", "sixMonthLow", "oneMonthHigh", "oneMonthLow",
  "threeYearData": [ { "date", "open", "high", "low", "close", "volume" } ]
}
```

### quant_metrics.json
```json
{
  "nifty": {
    "momentum": { "rsi", "macd", "macdSignal", "macdHistogram", "stochastic", "roc" },
    "volatility": { "historicalVol20d", "historicalVol50d", "atr14",
                    "bollingerUpper", "bollingerLower", "bollingerMiddle",
                    "impliedVolatility" }
  }
}
```

### screener_data.json
```json
{
  "stocks": [ { "symbol", "name", "sector", "ltp", "changePct",
                "signal": "bullish|bearish|neutral", "signalStrength",
                "metrics": { "momentumScore", "volatilityScore", "mlProbability" },
                "tags": [] } ],
  "sectors": [ { "index", "ltp", "changePct", "signal", "signalStrength",
                 "topContributors": [], "tags": [] } ]
}
```

### oi_analysis.json
```json
{
  "expiries": [ {
    "expiryDate", "daysToExpiry", "totalCallOI", "totalPutOI", "pcr",
    "strikes": [ { "strike", "callOI", "putOI", "callChange", "putChange" } ]
  } ],
  "spotPrice"
}
```

---

## Current State & Known Issues

### ✅ Working
- Nifty 2Y historical + chart with ATH/6M/1M ref lines
- Nifty/Sensex/VIX pre-market cards (all from historical candles)
- SSM Kalman + GARCH(2,1) dual forecast
- Momentum & volatility indicators
- Quant screener (rule-based; ready for ML plugin)
- Commodities: Brent, Gold, USD/INR, DXY
- GIFT Nifty proxy via YFinance
- Asian markets: Nikkei, KOSPI, Hang Seng
- GitHub Actions workflows (daily-data + deploy)
- Astro build: clean, ~10s

### ⚠️ Needs Attention
- OI data fetcher (`fetch_oi_historical.py`) built but untested (needs Upstox with auto-login for large contract batches)
- Brent Crude sometimes returns 0 from YFinance (data provider issue)
- Token expires every ~24h (standard Upstox; needs auto-refresh)
- Fake screener data in mock mode (20 hardcoded stocks — needs real Nifty 500 symbols)
- No live auto-refresh (by design: SSG, rebuild on pipeline push)
