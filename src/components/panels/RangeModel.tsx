import React, { useMemo } from 'react';
import {
  ComposedChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, ReferenceArea, ReferenceDot,
} from 'recharts';
import { CHART_COLORS } from '../charts/ChartTheme';

interface RangeModelData {
  forecastDate: string;
  forecastPrice: number;
  d5Date: string;
  d5Upper: number;
  d5Lower: number;
  d5Median: number;
  actualDays: { date: string; open: number; high: number; low: number; close: number }[];
  signal: string;
}

const RangeModel: React.FC<{ data?: RangeModelData }> = ({ data }) => {
  if (!data) return null;

  const chartData = useMemo(() => {
    return data.actualDays.map((d: any) => {
      const overbought = d.high > data.d5Upper;
      const oversold = d.low < data.d5Lower;
      return {
        date: d.date?.slice(5),
        fullDate: d.date,
        close: d.close,
        high: d.high,
        low: d.low,
        overbought,
        oversold,
        upper: data.d5Upper,
        lower: data.d5Lower,
      };
    });
  }, [data]);

  const hasOverbought = chartData.some((d: any) => d.overbought);
  const hasOversold = chartData.some((d: any) => d.oversold);
  const overallSignal = hasOverbought && hasOversold ? 'volatile'
    : hasOverbought ? 'overbought' : hasOversold ? 'oversold' : 'neutral';

  const signalLabel = overallSignal === 'overbought' ? '▲ Overbought'
    : overallSignal === 'oversold' ? '▼ Oversold'
    : overallSignal === 'volatile' ? '⇅ Volatile' : '— Range Bound';
  const signalClass = overallSignal === 'overbought' ? 'text-red-400 bg-red-400/10 border-red-400/20'
    : overallSignal === 'oversold' ? 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20'
    : overallSignal === 'volatile' ? 'text-purple-400 bg-purple-400/10 border-purple-400/20'
    : 'text-text-tertiary bg-bg-tertiary border-border-primary';

  const formatPrice = (v: number) => v >= 1000 ? (v / 1000).toFixed(0) + 'K' : v.toString();
  const yMin = Math.min(data.d5Lower, ...data.actualDays.map((d: any) => d.low)) - 80;
  const yMax = Math.max(data.d5Upper, ...data.actualDays.map((d: any) => d.high)) + 80;

  const overboughtDots = chartData.filter((d: any) => d.overbought);
  const oversoldDots = chartData.filter((d: any) => d.oversold);

  return (
    <div className="bg-bg-card border border-border-primary rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-semibold text-text-primary tracking-tight">Range Model</h2>
          <span className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full border ${signalClass}`}>{signalLabel}</span>
        </div>
        <div className="flex items-center gap-4 text-[10px] text-text-tertiary font-mono">
          <span>Forecast {data.forecastDate?.slice(5)}</span>
          <span>Range {data.d5Lower?.toLocaleString()}–{data.d5Upper?.toLocaleString()}</span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="rangeFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={overallSignal === 'overbought' ? '#ef4444' : overallSignal === 'oversold' ? '#22c55e' : '#a855f7'} stopOpacity={0.08} />
              <stop offset="100%" stopColor={overallSignal === 'overbought' ? '#ef4444' : overallSignal === 'oversold' ? '#22c55e' : '#a855f7'} stopOpacity={0.01} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.border} strokeOpacity={0.3} />
          <XAxis dataKey="date" tick={{ fontSize: 10, fill: CHART_COLORS.textTertiary }} tickLine={false} axisLine={false} />
          <YAxis type="number" domain={[yMin, yMax]} tickFormatter={formatPrice}
            tick={{ fontSize: 10, fill: CHART_COLORS.textTertiary }} tickLine={false} axisLine={false} width={45} />
          <Tooltip content={({ active, payload, label }: any) => {
            if (!active || !payload?.length) return null;
            const d = payload[0]?.payload;
            return (
              <div className="bg-bg-card border border-border-primary rounded-lg px-3 py-2 shadow-xl text-xs">
                <p className="text-text-tertiary mb-1">{d?.fullDate || label}</p>
                <p className="text-text-primary font-medium">Close: {d?.close?.toLocaleString('en-IN')}</p>
                <p className="text-text-tertiary">H: {d?.high?.toLocaleString()} L: {d?.low?.toLocaleString()}</p>
                {d?.overbought && <p className="text-red-400 font-semibold mt-0.5">▲ Crossed above D5 High</p>}
                {d?.oversold && <p className="text-emerald-400 font-semibold mt-0.5">▼ Crossed below D5 Low</p>}
              </div>
            );
          }} />

          <ReferenceArea y1={data.d5Lower} y2={data.d5Upper} fill="url(#rangeFill)" stroke="none" />
          <ReferenceLine y={data.d5Upper} stroke={overallSignal === 'overbought' ? '#ef4444' : '#a855f7'}
            strokeDasharray="4 4" strokeOpacity={0.5}
            label={{ value: `D5 High`, position: 'right', fill: overallSignal === 'overbought' ? '#ef4444' : '#a855f7', fontSize: 9 }} />
          <ReferenceLine y={data.d5Lower} stroke={overallSignal === 'oversold' ? '#22c55e' : '#a855f7'}
            strokeDasharray="4 4" strokeOpacity={0.5}
            label={{ value: `D5 Low`, position: 'right', fill: overallSignal === 'oversold' ? '#22c55e' : '#a855f7', fontSize: 9 }} />

          <Line type="monotone" dataKey="close" stroke={CHART_COLORS.textPrimary}
            strokeWidth={2.5} dot={{ r: 4, fill: CHART_COLORS.bgCard, stroke: CHART_COLORS.textPrimary, strokeWidth: 2 }}
            name="Nifty" connectNulls />

          {/* Per-day overbought markers */}
          {overboughtDots.map((d: any, i: number) => (
            <ReferenceDot key={`ob-${i}`} x={d.date} y={d.high} r={5} fill="#ef4444" stroke="#ef4444" strokeWidth={1}
              label={{ value: '▲', position: 'top', fill: '#ef4444', fontSize: 12, fontWeight: 'bold' }} />
          ))}
          {/* Per-day oversold markers */}
          {oversoldDots.map((d: any, i: number) => (
            <ReferenceDot key={`os-${i}`} x={d.date} y={d.low} r={5} fill="#22c55e" stroke="#22c55e" strokeWidth={1}
              label={{ value: '▼', position: 'bottom', fill: '#22c55e', fontSize: 12, fontWeight: 'bold' }} />
          ))}
        </ComposedChart>
      </ResponsiveContainer>

      <div className="flex items-center gap-4 text-[10px] text-text-tertiary font-mono mt-2 border-t border-border-primary pt-2">
        <span>Forecast <span className="text-text-secondary">{data.forecastDate}</span></span>
        <span>→ D5 <span className="text-text-secondary">{data.d5Date}</span></span>
        {overboughtDots.length > 0 && (
          <span className="text-red-400">▲ {overboughtDots.length}d above</span>
        )}
        {oversoldDots.length > 0 && (
          <span className="text-emerald-400">▼ {oversoldDots.length}d below</span>
        )}
      </div>
    </div>
  );
};

export default RangeModel;
