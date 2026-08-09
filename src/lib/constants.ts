// constants.ts — Site-wide constants
import type { SignalType } from './types';

export const SITE = {
  name: 'QuantMorning',
  tagline: 'Pre-market quantitative analysis for the Indian market',
  description: 'Nifty 50 quantitative analysis — SSM Kalman + GARCH forecasts, options OI, momentum & volatility metrics, and a quant stock screener.',
  url: 'https://quantmorning.com',
} as const;

export const SECTORS = [
  'NIFTY Bank',
  'NIFTY Financial Services',
  'NIFTY IT',
  'NIFTY Auto',
  'NIFTY Pharma',
  'NIFTY FMCG',
  'NIFTY Realty',
  'NIFTY Metal',
  'NIFTY PSU Bank',
  'NIFTY Energy',
  'NIFTY Healthcare',
  'NIFTY Consumer Durables',
  'NIFTY Oil & Gas',
  'NIFTY Media',
  'NIFTY Infrastructure',
  'NIFTY Commodities',
  'NIFTY MNC',
] as const;

export const MARKET_HOURS = {
  open: '09:15',
  close: '15:30',
  preOpen: '09:00',
} as const;

export const SIGNAL_COLORS: Record<SignalType, { bg: string; text: string; border: string }> = {
  bullish: { bg: 'bg-emerald-400/10', text: 'text-emerald-400', border: 'border-emerald-400/20' },
  bearish: { bg: 'bg-red-400/10', text: 'text-red-400', border: 'border-red-400/20' },
  neutral: { bg: 'bg-amber-400/10', text: 'text-amber-400', border: 'border-amber-400/20' },
};

export const MODEL_DESC =
  'SSM local-level Kalman filter (150d) with AR(1) drift + GJR-GARCH residuals; GARCH(2,1) on Student-t for comparison';
