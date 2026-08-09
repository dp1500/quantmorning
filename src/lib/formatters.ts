// formatters.ts — Indian number system formatters
import type { SignalType } from './types';

const LAKH = 1_00_000;
const CRORE = 1_00_00_000;

/** Format a number in Indian system: 1,50,000 style */
export function formatIndian(num: number, decimals = 2): string {
  if (num == null || isNaN(num)) return '—';
  const abs = Math.abs(num);
  if (abs >= CRORE) {
    return (num / CRORE).toFixed(2) + ' Cr';
  }
  if (abs >= LAKH) {
    return (num / LAKH).toFixed(2) + ' L';
  }
  if (abs >= 1000) {
    const s = num.toFixed(0);
    const last3 = s.slice(-3);
    const rest = s.slice(0, -3);
    return rest.replace(/\B(?=(\d{2})+(?!\d))/g, ',') + ',' + last3;
  }
  return num.toFixed(decimals);
}

/** Format a price: no commas above 1000, just clean number */
export function formatPrice(n: number, decimals = 2): string {
  if (n == null || isNaN(n)) return '—';
  return n.toLocaleString('en-IN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

/** Format percentage change */
export function formatPct(n: number): string {
  if (n == null || isNaN(n)) return '—';
  const sign = n > 0 ? '+' : n < 0 ? '' : '';
  return sign + n.toFixed(2) + '%';
}

/** Format OI as shorthand: 1.2L, 3.5Cr */
export function formatOI(n: number): string {
  if (n == null || isNaN(n)) return '—';
  const abs = Math.abs(n);
  if (abs >= CRORE) return (n / CRORE).toFixed(1) + ' Cr';
  if (abs >= LAKH) return (n / LAKH).toFixed(1) + ' L';
  return n.toLocaleString('en-IN');
}

/** Signal badge color classes */
export function signalColor(signal: SignalType): string {
  switch (signal) {
    case 'bullish': return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20';
    case 'bearish': return 'text-red-400 bg-red-400/10 border-red-400/20';
    case 'neutral': return 'text-amber-400 bg-amber-400/10 border-amber-400/20';
  }
}

/** Tailwind text color for positive/negative */
export function pnlColor(n: number): string {
  if (n > 0) return 'text-emerald-400';
  if (n < 0) return 'text-red-400';
  return 'text-zinc-400';
}

/** VIX regime label + color */
export function vixRegimeInfo(regime: string): { label: string; color: string } {
  switch (regime) {
    case 'low': return { label: 'Low', color: 'text-emerald-400' };
    case 'normal': return { label: 'Normal', color: 'text-text-secondary' };
    case 'elevated': return { label: 'Elevated', color: 'text-amber-400' };
    case 'high': return { label: 'High', color: 'text-red-400' };
    default: return { label: regime, color: 'text-text-tertiary' };
  }
}
