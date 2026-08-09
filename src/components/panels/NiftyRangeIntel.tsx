import React, { useMemo, useState } from 'react';
import {
  AreaChart, Area, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, Legend, ComposedChart,
} from 'recharts';
import type { GarchForecast } from '../../lib/types';
import { CHART_COLORS, ChartGradients } from '../charts/ChartTheme';

// ═══════════════════════════════════════════════════════════════
const FORECAST_HEIGHT = 450;
const OI_HEIGHT = 450;  // matches forecast height for alignment
// ═══════════════════════════════════════════════════════════════

const ForecastTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  const get = (key: string) => payload.find((p: any) => p.dataKey === key)?.value;
  const actual = get('actual');
  const m1Med = get('m1Median'); const m1Lo = get('m1Upper'); const m1Hi = get('m1Lower');
  const m2Med = get('m2Median'); const m2Lo = get('m2Upper'); const m2Hi = get('m2Lower');
  return (
    <div className="bg-bg-card border border-border-primary rounded-lg px-3 py-2 shadow-xl text-xs">
      <p className="text-text-tertiary mb-1">{label}</p>
      {actual != null && <p className="text-emerald-400 font-medium">Actual: {actual.toLocaleString('en-IN')}</p>}
      {m1Med != null && (
        <p className="text-amber-400">
          Model 1: <span className="font-medium">{Math.round(m1Med).toLocaleString('en-IN')}</span>
          <span className="text-text-tertiary ml-1">({Math.round(m1Hi)?.toLocaleString()} – {Math.round(m1Lo)?.toLocaleString()})</span>
        </p>
      )}
      {m2Med != null && (
        <p className="text-blue-400">
          Model 2: <span className="font-medium">{Math.round(m2Med).toLocaleString('en-IN')}</span>
          <span className="text-text-tertiary ml-1">({Math.round(m2Hi)?.toLocaleString()} – {Math.round(m2Lo)?.toLocaleString()})</span>
        </p>
      )}
    </div>
  );
};

const NiftyRangeIntel: React.FC<{ data?: GarchForecast; oiAnalysis?: any }> = ({
  data: propData,
  oiAnalysis,
}) => {
  const forecastData = propData;
  const [oiExpiryIdx, setOiExpiryIdx] = useState(0);

  const expiries = useMemo(() => {
    if (!oiAnalysis?.expiries?.length) return [];
    return oiAnalysis.expiries;
  }, [oiAnalysis]);

  const activeExpiry = expiries[oiExpiryIdx] || null;

  // ── Shared Y-axis domain (aligns forecast chart and OI chart) ──
  const sharedYDomain = useMemo(() => {
    if (!forecastData) return [24000, 25000];
    const vals: number[] = [];
    (forecastData.last5Days || []).forEach((d: any) => { if (d.actual) vals.push(d.actual); });
    (forecastData.forecast5Days || []).forEach((d: any) => {
      if (d.ssmLower) vals.push(d.ssmLower);
      if (d.ssmUpper) vals.push(d.ssmUpper);
    });
    if (vals.length < 2) return [24000, 25000];
    const min = Math.min(...vals);
    const max = Math.max(...vals);
    const pad = (max - min) * 0.15;
    return [Math.floor(min - pad), Math.ceil(max + pad)];
  }, [forecastData]);

  // ── GARCH chart data ──
  const forecastChartData = useMemo(() => {
    if (!forecastData) return [];
    const rows: any[] = [];
    (forecastData.last5Days || []).slice(-3).forEach((d: any) => {
      rows.push({ date: d.date?.slice(5), actual: d.actual,
        m1Median: null, m1Lower: null, m1Upper: null,
        m2Median: null, m2Lower: null, m2Upper: null, isForecast: false });
    });
    (forecastData.forecast5Days || []).forEach((d: any) => {
      rows.push({ date: d.date?.slice(5), actual: null,
        m1Median: d.ssmMedian, m1Lower: d.ssmLower, m1Upper: d.ssmUpper,
        m2Median: d.garchMedian, m2Lower: d.garchLower, m2Upper: d.garchUpper, isForecast: true });
    });
    return rows;
  }, [forecastData]);

  // ── OI bar data (with numeric strike for Y-axis alignment) ──
  const oiBarData = useMemo(() => {
    if (!activeExpiry?.strikes?.length) return [];
    return activeExpiry.strikes.map((s: any) => ({
      strike: s.strike,
      callOI: s.callOI || 0,
      putOI: s.putOI || 0,
      label: (s.strike / 1000).toFixed(1) + 'K',
    }));
  }, [activeExpiry]);

  const spotPrice = forecastData?.last5Days?.length
    ? forecastData.last5Days[forecastData.last5Days.length - 1].actual : 0;

  const formatOI = (v: number) => {
    const abs = Math.abs(v);
    if (abs >= 10000000) return (v / 10000000).toFixed(1) + 'Cr';
    if (abs >= 100000) return (v / 100000).toFixed(1) + 'L';
    return (v / 1000).toFixed(0) + 'K';
  };

  const formatPrice = (v: number) => v >= 1000 ? (v / 1000).toFixed(0) + 'K' : v.toString();

  return (
    <div className="bg-bg-card border border-border-primary rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-text-primary tracking-tight">Nifty Range Analysis & Forecast</h2>
        <div className="flex items-center gap-4 text-[10px] text-text-tertiary font-mono">
          <span>Spot {spotPrice ? spotPrice.toLocaleString('en-IN') : '—'}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* ── LEFT: Forecast (65%) ── */}
        <div className="lg:col-span-2">
          <ResponsiveContainer width="100%" height={FORECAST_HEIGHT}>
            <ComposedChart data={forecastChartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <ChartGradients />
                <linearGradient id="m1Band" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.20} /><stop offset="100%" stopColor="#f59e0b" stopOpacity={0.02} />
                </linearGradient>
                <linearGradient id="m2Band" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.14} /><stop offset="100%" stopColor="#3b82f6" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.border} strokeOpacity={0.3} />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: CHART_COLORS.textTertiary }} tickLine={false} axisLine={false} />
              <YAxis type="number" domain={sharedYDomain as [number, number]}
                tickFormatter={formatPrice} tick={{ fontSize: 10, fill: CHART_COLORS.textTertiary }}
                tickLine={false} axisLine={false} width={45}
              />
              <Tooltip content={<ForecastTooltip />} />
              <Legend wrapperStyle={{ fontSize: 10 }} iconType="line" iconSize={10} />

              <Line type="monotone" dataKey="actual" stroke={CHART_COLORS.primary} strokeWidth={2.5}
                dot={{ r: 4, fill: CHART_COLORS.primary, strokeWidth: 0 }} name="Actual" connectNulls />
              <Area type="monotone" dataKey="m1Upper" stroke="none" fill="url(#m1Band)" name="Model 1 range" />
              <Area type="monotone" dataKey="m1Lower" stroke="none" fill="#1a1a1d" name="" />
              <Line type="monotone" dataKey="m1Median" stroke="#f59e0b" strokeWidth={2}
                dot={{ r: 3, fill: '#f59e0b', strokeWidth: 0 }} name="Model 1" connectNulls />
              <Area type="monotone" dataKey="m2Upper" stroke="none" fill="url(#m2Band)" name="Model 2 range" />
              <Area type="monotone" dataKey="m2Lower" stroke="none" fill="#1a1a1d" name="" />
              <Line type="monotone" dataKey="m2Median" stroke="#3b82f6" strokeWidth={2} strokeDasharray="4 3"
                dot={{ r: 3, fill: '#3b82f6', strokeWidth: 0 }} name="Model 2" connectNulls />
              {forecastChartData.length > 3 && (
                <ReferenceLine x={forecastChartData[2]?.date} stroke={CHART_COLORS.textTertiary} strokeDasharray="1 2" strokeOpacity={0.3} />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* ── RIGHT: OI Levels (35%) — Y-axis aligned with forecast ── */}
        <div className="lg:col-span-1 flex flex-col">
          {expiries.length > 1 && (
            <div className="flex items-center gap-1 mb-2">
              {expiries.map((exp: any, i: number) => (
                <button key={i} onClick={() => setOiExpiryIdx(i)}
                  className={`px-2.5 py-1 text-[10px] font-medium rounded-full transition-colors ${
                    i === oiExpiryIdx ? 'bg-accent/15 text-accent border border-accent/20' : 'text-text-tertiary hover:text-text-secondary border border-transparent'
                  }`}>{exp.expiryDate?.slice(5)}</button>
              ))}
            </div>
          )}
          {oiBarData.length > 0 ? (
            <div className="flex-1">
              <ResponsiveContainer width="100%" height={OI_HEIGHT}>
                <BarChart data={oiBarData} layout="vertical" margin={{ top: 5, right: 10, left: 0, bottom: 5 }} barGap={2} barCategoryGap={4}>
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.border} strokeOpacity={0.15} horizontal={false} />
                  <XAxis type="number" tickFormatter={formatOI} tick={{ fontSize: 9, fill: CHART_COLORS.textTertiary }} tickLine={false} axisLine={false} />
                  <YAxis type="number" dataKey="strike" domain={sharedYDomain as [number, number]}
                    tickFormatter={(v: number) => (v / 1000).toFixed(1) + 'K'}
                    tick={{ fontSize: 10, fill: CHART_COLORS.textSecondary, fontWeight: 500 }}
                    tickLine={false} axisLine={false} orientation="right" width={45}
                  />
                  <Tooltip formatter={(v: number, name: string) => [v.toLocaleString('en-IN'), name]}
                    contentStyle={{ backgroundColor: '#1a1a1d', border: '1px solid #252529', borderRadius: 8, fontSize: 11, color: '#fafafa' }} />
                  <Bar dataKey="putOI" fill="#ef4444" fillOpacity={0.5} barSize={5} radius={[0, 2, 2, 0]} name="Put OI" />
                  <Bar dataKey="callOI" fill="#22c55e" fillOpacity={0.5} barSize={5} radius={[2, 0, 0, 2]} name="Call OI" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="flex items-center justify-center flex-1 min-h-[200px] text-xs text-text-tertiary">No OI data</div>
          )}
          {activeExpiry && (
            <div className="flex items-center gap-3 text-[10px] text-text-tertiary font-mono border-t border-border-primary pt-2 mt-1">
              <span>PCR <span className="text-text-secondary">{activeExpiry.pcr}</span></span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NiftyRangeIntel;
