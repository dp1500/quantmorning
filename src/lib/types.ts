// types.ts — All TypeScript types for QuantMorning JSON data artifacts

export interface PrevDayOHLC {
  prevHigh: number;
  prevLow: number;
  prevRangePct: number;
}

export interface AssetQuote {
  symbol: string;
  name: string;
  ltp: number;
  prevClose: number;
  change: number;
  changePct: number;
  dayHigh: number;
  dayLow: number;
  sparkline?: number[];
  // prev day OHLC (only for Nifty/Sensex)
  prevHigh?: number;
  prevLow?: number;
  prevRangePct?: number;
}

export interface GiftNiftyQuote {
  symbol: string;
  name: string;
  ltp: number;
  prevClose: number;
  change: number;
  changePct: number;
}

export interface AsianMarketQuote {
  symbol: string;
  name: string;
  ltp: number;
  prevClose: number;
  change: number;
  changePct: number;
  sparkline?: number[];
}

export type VixRegime = 'low' | 'normal' | 'elevated' | 'high';

export interface MarketSnapshot {
  timestamp: string;
  assets: {
    nifty50?: AssetQuote;
    sensex?: AssetQuote;
    india_vix?: AssetQuote;
    brentOil?: AssetQuote;
    gold?: AssetQuote;
    usdInr?: AssetQuote;
    dxy?: AssetQuote;
  };
  giftNifty: GiftNiftyQuote;
  asianMarkets: AsianMarketQuote[];
  vixRegime: VixRegime;
}

export interface NiftyCandle {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface NiftyChartData {
  ath: number;
  athDate: string;
  thisYearHigh: number;
  thisYearHighDate: string;
  sixMonthHigh: number;
  sixMonthLow: number;
  threeMonthHigh: number;
  threeMonthLow: number;
  oneMonthHigh: number;
  oneMonthLow: number;
  threeYearData: NiftyCandle[];
}

export interface PastDay {
  date: string;
  actual: number | null;
  forecast: number | null;
  lowerCI: number | null;
  upperCI: number | null;
}

export interface ForecastDay {
  date: string;
  actual: null;
  ssmMedian: number;
  ssmLower: number;
  ssmUpper: number;
  garchMedian: number;
  garchLower: number;
  garchUpper: number;
}

export interface OIStrike {
  strike: number;
  callOI: number;
  putOI: number;
}

export interface OILevelsCompact {
  expiryDate: string;
  daysLeft: number;
  maxPain: number;
  pcr: number;
  strikes: OIStrike[];
}

export interface GarchForecast {
  lastUpdated: string;
  model: string;
  modelDesc: string;
  last5Days: PastDay[];
  forecast5Days: ForecastDay[];
  ssmAnnualVol: number;
  garchAnnualVol: number;
  oiLevels?: OILevelsCompact;
  rangeModel?: Record<string, any>;
}

export interface MomentumMetrics {
  rsi: number;
  macd: number;
  macdSignal: number;
  macdHistogram: number;
  stochastic: number;
  roc: number;
}

export interface VolatilityMetrics {
  historicalVol20d: number;
  historicalVol50d: number;
  atr14: number;
  bollingerUpper: number;
  bollingerLower: number;
  bollingerMiddle: number;
  impliedVolatility: number;
}

export interface QuantMetricsData {
  nifty: {
    momentum: MomentumMetrics;
    volatility: VolatilityMetrics;
  };
}

export interface OIAnalysisLevel {
  strike: number;
  callOI: number;
  putOI: number;
  callChange: number;
  putChange: number;
}

export interface OIExpiryData {
  date: string;
  daysToExpiry: number;
  totalCallOI: number;
  totalPutOI: number;
  putCallRatio: number;
  maxPain: number;
  levels: OIAnalysisLevel[];
  oiChange24h: {
    callChange: number;
    putChange: number;
    pcrChange: number;
  };
  oiChange1hrPrevDay: {
    callChange: number;
    putChange: number;
    pcrChange: number;
  };
}

export interface OIAnalysis {
  latestExpiry: OIExpiryData | null;
  secondLatestExpiry: OIExpiryData | null;
}

export type SignalType = 'bullish' | 'bearish' | 'neutral';

export interface StockSignal {
  symbol: string;
  name: string;
  sector: string;
  ltp: number;
  changePct: number;
  signal: SignalType;
  signalStrength: number;
  metrics: {
    momentumScore: number;
    volatilityScore: number;
    mlProbability: number;
  };
  tags: string[];
}

export interface SectorSignal {
  index: string;
  ltp: number;
  changePct: number;
  signal: SignalType;
  signalStrength: number;
  topContributors: string[];
  tags: string[];
}

export interface ScreenerData {
  generatedAt: string;
  stocks: StockSignal[];
  sectors: SectorSignal[];
}
