import React from 'react';

export const CHART_COLORS = {
  primary: '#22c55e',
  secondary: '#3b82f6',
  purple: '#a855f7',
  amber: '#f59e0b',
  red: '#ef4444',
  cyan: '#06b6d4',
  textPrimary: '#fafafa',
  textSecondary: '#a1a1aa',
  textTertiary: '#71717a',
  border: '#252529',
  bgCard: '#1a1a1d',
  bgSecondary: '#111113',
};

export const chartConfig = {
  background: 'transparent',
  textColor: CHART_COLORS.textSecondary,
  fontSize: 11,
  fontFamily: 'Inter, sans-serif',
  tickColor: CHART_COLORS.textTertiary,
  gridColor: CHART_COLORS.border,
  crosshairColor: 'rgba(255,255,255,0.04)',
};

/** Gradient defs for Recharts area fills */
export function ChartGradients() {
  return (
    <defs>
      <linearGradient id="greenGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor="#22c55e" stopOpacity={0.2} />
        <stop offset="100%" stopColor="#22c55e" stopOpacity={0} />
      </linearGradient>
      <linearGradient id="blueGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.15} />
        <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
      </linearGradient>
      <linearGradient id="purpleGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor="#a855f7" stopOpacity={0.15} />
        <stop offset="100%" stopColor="#a855f7" stopOpacity={0} />
      </linearGradient>
      <linearGradient id="redGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor="#ef4444" stopOpacity={0.12} />
        <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
      </linearGradient>
    </defs>
  );
}

/** Shared tooltip wrapper */
export function ChartTooltip({ active, payload, label, formatter }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-bg-card border border-border-primary rounded-lg px-3 py-2 shadow-xl">
      <p className="text-xs text-text-tertiary mb-1">{label}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} className="text-xs font-medium" style={{ color: entry.color }}>
          {entry.name}: {formatter ? formatter(entry.value) : entry.value?.toLocaleString?.() ?? entry.value}
        </p>
      ))}
    </div>
  );
}
