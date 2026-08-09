import React, { useMemo } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import type { NiftyChartData, NiftyCandle } from '../../lib/types';
import { CHART_COLORS, ChartGradients, ChartTooltip } from '../charts/ChartTheme';

const NiftyChart: React.FC<{ data?: NiftyChartData }> = ({ data: propData }) => {
  const chartData = propData;

  const candles: NiftyCandle[] = useMemo(() => {
    if (chartData?.threeYearData?.length) return chartData.threeYearData;
    // Fallback mock — 2 years of business days
    const mock: NiftyCandle[] = [];
    const start = new Date('2024-08-01');
    let price = 24000;
    for (let i = 0; i < 500; i++) {
      const d = new Date(start);
      d.setDate(d.getDate() + i);
      if (d.getDay() === 0 || d.getDay() === 6) continue;
      const change = (Math.random() - 0.48) * 180;
      price = Math.max(20000, price + change);
      mock.push({
        date: d.toISOString().slice(0, 10),
        open: price - change * 0.3,
        high: price + Math.abs(change) * 0.5,
        low: price - Math.abs(change) * 0.5,
        close: price,
        volume: Math.floor(Math.random() * 100000),
      });
    }
    return mock;
  }, [chartData]);

  const formatY = (v: number) => v >= 1000 ? (v / 1000).toFixed(0) + 'K' : v.toString();
  const formatDate = (d: string) => {
    const date = new Date(d);
    return date.toLocaleDateString('en-IN', { month: 'short', year: '2-digit' });
  };

  // Compute tick interval — show ~12 labels for readability
  const tickInterval = Math.max(1, Math.floor(candles.length / 10));

  return (
    <div className="bg-bg-card border border-border-primary rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-semibold text-text-primary tracking-tight">Nifty 50 — 2 Year Chart</h2>
        </div>
        <div className="flex items-center gap-4 text-[10px] text-text-tertiary font-mono">
          <span>ATH {chartData?.ath?.toLocaleString() || '—'}</span>
          <span>6M H/L {chartData?.sixMonthHigh?.toLocaleString() || '—'}/{chartData?.sixMonthLow?.toLocaleString() || '—'}</span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={320}>
        <AreaChart data={candles} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <ChartGradients />
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.border} strokeOpacity={0.5} />
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            tick={{ fontSize: 10, fill: CHART_COLORS.textTertiary }}
            tickLine={false}
            axisLine={false}
            interval={tickInterval}
          />
          <YAxis
            tickFormatter={formatY}
            tick={{ fontSize: 10, fill: CHART_COLORS.textTertiary }}
            tickLine={false}
            axisLine={false}
            domain={['auto', 'auto']}
            width={50}
          />
          <Tooltip content={<ChartTooltip formatter={(v: number) => v.toLocaleString('en-IN')} />} />
          <Area
            type="monotone"
            dataKey="close"
            stroke={CHART_COLORS.primary}
            strokeWidth={1.5}
            fill="url(#greenGrad)"
            dot={false}
            name="Nifty 50"
          />
          {/* ATH */}
          {chartData?.ath > 0 && (
            <ReferenceLine y={chartData.ath} stroke={CHART_COLORS.amber} strokeDasharray="4 4" strokeOpacity={0.6}
              label={{ value: 'ATH', position: 'right', fill: CHART_COLORS.amber, fontSize: 9, fontWeight: 600 }}
            />
          )}
          {/* 6 Month High */}
          {chartData?.sixMonthHigh > 0 && (
            <ReferenceLine y={chartData.sixMonthHigh} stroke={CHART_COLORS.blue} strokeDasharray="2 2" strokeOpacity={0.4}
              label={{ value: '6M H', position: 'right', fill: CHART_COLORS.blue, fontSize: 8 }}
            />
          )}
          {/* 6 Month Low */}
          {chartData?.sixMonthLow > 0 && (
            <ReferenceLine y={chartData.sixMonthLow} stroke={CHART_COLORS.red} strokeDasharray="2 2" strokeOpacity={0.4}
              label={{ value: '6M L', position: 'right', fill: CHART_COLORS.red, fontSize: 8 }}
            />
          )}
          {/* 1 Month High */}
          {chartData?.oneMonthHigh > 0 && (
            <ReferenceLine y={chartData.oneMonthHigh} stroke="#a855f7" strokeDasharray="1 2" strokeOpacity={0.35}
              label={{ value: '1M H', position: 'right', fill: '#a855f7', fontSize: 8 }}
            />
          )}
          {/* 1 Month Low */}
          {chartData?.oneMonthLow > 0 && (
            <ReferenceLine y={chartData.oneMonthLow} stroke="#f97316" strokeDasharray="1 2" strokeOpacity={0.35}
              label={{ value: '1M L', position: 'right', fill: '#f97316', fontSize: 8 }}
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
      <div className="flex items-center gap-5 text-[10px] text-text-tertiary mt-1 justify-center">
        <span className="flex items-center gap-1"><span className="w-2 h-0.5 bg-amber-400 inline-block rounded"></span> ATH</span>
        <span className="flex items-center gap-1"><span className="w-2 h-0.5 bg-blue-400 inline-block rounded"></span> 6M H</span>
        <span className="flex items-center gap-1"><span className="w-2 h-0.5 bg-red-400 inline-block rounded"></span> 6M L</span>
        <span className="flex items-center gap-1"><span className="w-2 h-0.5 bg-purple-400 inline-block rounded"></span> 1M H</span>
        <span className="flex items-center gap-1"><span className="w-2 h-0.5 bg-orange-400 inline-block rounded"></span> 1M L</span>
      </div>
    </div>
  );
};

export default NiftyChart;
