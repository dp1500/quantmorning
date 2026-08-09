import React, { useState, useMemo } from 'react';
import { ChevronDown, ChevronRight, Search, SlidersHorizontal } from 'lucide-react';
import type { ScreenerData, StockSignal, SignalType } from '../../lib/types';
import { signalColor, formatPrice, formatPct, pnlColor } from '../../lib/formatters';
import { SECTORS } from '../../lib/constants';

const sampleData: ScreenerData = {
  generatedAt: new Date().toISOString(),
  stocks: [
    { symbol: 'HDFCBANK', name: 'HDFC Bank', sector: 'NIFTY Bank', ltp: 1680.5, changePct: 1.24, signal: 'bullish', signalStrength: 82, metrics: { momentumScore: 78, volatilityScore: 25, mlProbability: 0.85 }, tags: ['High Momentum', 'Breakout', 'ML Confidence'] },
    { symbol: 'RELIANCE', name: 'Reliance Industries', sector: 'NIFTY Oil & Gas', ltp: 2945.3, changePct: -0.45, signal: 'neutral', signalStrength: 52, metrics: { momentumScore: 48, volatilityScore: 35, mlProbability: 0.55 }, tags: ['Range Bound'] },
    { symbol: 'TCS', name: 'Tata Consultancy', sector: 'NIFTY IT', ltp: 4230.0, changePct: 2.15, signal: 'bullish', signalStrength: 88, metrics: { momentumScore: 85, volatilityScore: 20, mlProbability: 0.92 }, tags: ['High Momentum', 'Breakout', 'ML Confidence'] },
    { symbol: 'TATAMOTORS', name: 'Tata Motors', sector: 'NIFTY Auto', ltp: 980.25, changePct: -2.8, signal: 'bearish', signalStrength: 22, metrics: { momentumScore: 20, volatilityScore: 72, mlProbability: 0.18 }, tags: ['Weak Momentum', 'High Volatility', 'Profit Booking'] },
    { symbol: 'SUNPHARMA', name: 'Sun Pharma', sector: 'NIFTY Pharma', ltp: 1520.8, changePct: 0.88, signal: 'neutral', signalStrength: 55, metrics: { momentumScore: 52, volatilityScore: 30, mlProbability: 0.58 }, tags: ['Mixed'] },
    { symbol: 'INFY', name: 'Infosys', sector: 'NIFTY IT', ltp: 1780.6, changePct: 1.45, signal: 'bullish', signalStrength: 75, metrics: { momentumScore: 70, volatilityScore: 28, mlProbability: 0.78 }, tags: ['High Momentum'] },
    { symbol: 'HINDUNILVR', name: 'Hindustan Unilever', sector: 'NIFTY FMCG', ltp: 2590.0, changePct: -0.22, signal: 'neutral', signalStrength: 48, metrics: { momentumScore: 42, volatilityScore: 22, mlProbability: 0.48 }, tags: ['Range Bound'] },
  ],
  sectors: [
    { index: 'NIFTY IT', ltp: 38200, changePct: 1.65, signal: 'bullish', signalStrength: 78, topContributors: ['TCS', 'INFY', 'WIPRO'], tags: ['Momentum'] },
    { index: 'NIFTY Bank', ltp: 49800, changePct: 0.95, signal: 'bullish', signalStrength: 72, topContributors: ['HDFCBANK', 'ICICIBANK', 'SBIN'], tags: ['Momentum'] },
    { index: 'NIFTY Auto', ltp: 22800, changePct: -1.2, signal: 'bearish', signalStrength: 30, topContributors: ['TATAMOTORS', 'MARUTI', 'M&M'], tags: ['Weak'] },
    { index: 'NIFTY Oil & Gas', ltp: 11900, changePct: 0.15, signal: 'neutral', signalStrength: 52, topContributors: ['RELIANCE', 'ONGC', 'BPCL'], tags: ['Mixed'] },
  ],
};

type Tab = 'stocks' | 'sectors';
type SortKey = 'signalStrength' | 'changePct' | 'momentum' | 'volatility';

const Screener: React.FC<{ data?: ScreenerData }> = ({ data: propData }) => {
  const screenerData = propData || sampleData;
  const [tab, setTab] = useState<Tab>('stocks');
  const [search, setSearch] = useState('');
  const [sectorFilter, setSectorFilter] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('signalStrength');
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const stocks = screenerData.stocks || [];
  const sectors = screenerData.sectors || [];

  const filteredStocks = useMemo(() => {
    let list = [...stocks];
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(s => s.symbol.toLowerCase().includes(q) || s.name.toLowerCase().includes(q));
    }
    if (sectorFilter) list = list.filter(s => s.sector === sectorFilter);
    if (sortKey === 'signalStrength') list.sort((a, b) => b.signalStrength - a.signalStrength);
    if (sortKey === 'changePct') list.sort((a, b) => b.changePct - a.changePct);
    if (sortKey === 'momentum') list.sort((a, b) => b.metrics.momentumScore - a.metrics.momentumScore);
    if (sortKey === 'volatility') list.sort((a, b) => a.metrics.volatilityScore - b.metrics.volatilityScore);
    return list;
  }, [stocks, search, sectorFilter, sortKey]);

  const toggleExpand = (symbol: string) => {
    const next = new Set(expanded);
    if (next.has(symbol)) next.delete(symbol); else next.add(symbol);
    setExpanded(next);
  };

  const signalEmoji = (s: SignalType) => s === 'bullish' ? '▲' : s === 'bearish' ? '▼' : '—';

  return (
    <div className="bg-bg-card border border-border-primary rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-semibold text-text-primary tracking-tight">Quant Screener</h2>
          <span className="text-[10px] font-medium text-text-tertiary bg-bg-tertiary px-2 py-0.5 rounded-full border border-border-primary">
            Nifty 500 + 17 Sectors
          </span>
        </div>
        <span className="text-[10px] text-text-tertiary font-mono">
          {screenerData.generatedAt ? new Date(screenerData.generatedAt).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : ''}
        </span>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 mb-4">
        {(['stocks', 'sectors'] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-1.5 text-xs font-medium rounded-full transition-colors ${tab === t ? 'bg-accent/15 text-accent' : 'text-text-tertiary hover:text-text-secondary'}`}
          >
            {t.charAt(0).toUpperCase() + t.slice(1)}
            <span className="ml-1 text-text-disabled text-[10px]">
              {t === 'stocks' ? stocks.length : sectors.length}
            </span>
          </button>
        ))}
      </div>

      {/* Search & Filters */}
      {tab === 'stocks' && (
        <div className="flex items-center gap-2 mb-3">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-disabled" />
            <input
              type="text"
              placeholder="Search symbols..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full bg-bg-input border border-border-primary rounded-lg pl-8 pr-3 py-1.5 text-xs text-text-primary placeholder-text-disabled focus:outline-none focus:border-accent/30"
            />
          </div>
          <select
            value={sectorFilter}
            onChange={e => setSectorFilter(e.target.value)}
            className="bg-bg-input border border-border-primary rounded-lg px-2.5 py-1.5 text-xs text-text-secondary focus:outline-none focus:border-accent/30"
          >
            <option value="">All Sectors</option>
            {SECTORS.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <div className="flex items-center gap-0.5 ml-auto">
            <SlidersHorizontal className="w-3 h-3 text-text-disabled mr-1" />
            {(['signalStrength', 'changePct', 'momentum', 'volatility'] as SortKey[]).map(k => (
              <button
                key={k}
                onClick={() => setSortKey(k)}
                className={`px-2 py-1 text-[10px] rounded ${sortKey === k ? 'bg-accent/15 text-accent' : 'text-text-tertiary hover:text-text-secondary'}`}
              >
                {k === 'signalStrength' ? 'Signal' : k === 'changePct' ? '%Chg' : k === 'momentum' ? 'Mom' : 'Vol'}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-text-tertiary font-mono uppercase tracking-wider text-[10px]">
              <th className="text-left py-2 pr-2">Symbol</th>
              <th className="text-right py-2 px-2">LTP</th>
              <th className="text-right py-2 px-2">Chg%</th>
              <th className="text-center py-2 px-2">Signal</th>
              <th className="text-right py-2 px-2">Strength</th>
              <th className="text-center py-2 pl-2"></th>
            </tr>
          </thead>
          <tbody>
            {tab === 'stocks' && filteredStocks.map(stock => (
              <React.Fragment key={stock.symbol}>
                <tr
                  onClick={() => toggleExpand(stock.symbol)}
                  className="border-t border-border-primary hover:bg-bg-card-hover cursor-pointer transition-colors"
                >
                  <td className="py-2.5 pr-2">
                    <div className="flex items-center gap-2">
                      {expanded.has(stock.symbol) ? <ChevronDown className="w-3 h-3 text-text-disabled" /> : <ChevronRight className="w-3 h-3 text-text-disabled" />}
                      <div>
                        <span className="font-medium text-text-primary">{stock.symbol}</span>
                        <span className="text-text-tertiary ml-1.5">{stock.name}</span>
                      </div>
                    </div>
                  </td>
                  <td className="py-2.5 px-2 text-right font-mono text-text-primary">{formatPrice(stock.ltp)}</td>
                  <td className={`py-2.5 px-2 text-right font-mono font-medium ${pnlColor(stock.changePct)}`}>{formatPct(stock.changePct)}</td>
                  <td className="py-2.5 px-2 text-center">
                    <span className="text-sm">{signalEmoji(stock.signal)}</span>
                  </td>
                  <td className="py-2.5 px-2 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-16 h-1 bg-bg-tertiary rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${stock.signalStrength >= 65 ? 'bg-emerald-400' : stock.signalStrength <= 35 ? 'bg-red-400' : 'bg-amber-400'}`}
                          style={{ width: `${stock.signalStrength}%` }}
                        />
                      </div>
                      <span className="font-mono text-text-secondary w-5">{stock.signalStrength}</span>
                    </div>
                  </td>
                  <td className="py-2.5 pl-2">
                    <span className={`text-[9px] font-semibold uppercase px-1.5 py-0.5 rounded border ${signalColor(stock.signal)}`}>
                      {stock.signal}
                    </span>
                  </td>
                </tr>
                {expanded.has(stock.symbol) && (
                  <tr className="border-t border-border-subtle bg-bg-secondary/50">
                    <td colSpan={6} className="p-4">
                      <div className="grid grid-cols-3 gap-4 text-[10px]">
                        <div>
                          <span className="text-text-tertiary block mb-1">Momentum Score</span>
                          <span className="font-semibold text-text-primary">{stock.metrics.momentumScore}</span>
                        </div>
                        <div>
                          <span className="text-text-tertiary block mb-1">Volatility Score</span>
                          <span className="font-semibold text-text-primary">{stock.metrics.volatilityScore}</span>
                        </div>
                        <div>
                          <span className="text-text-tertiary block mb-1">ML Probability</span>
                          <span className="font-semibold text-text-primary">{stock.metrics.mlProbability}</span>
                        </div>
                      </div>
                      {stock.tags.length > 0 && (
                        <div className="flex items-center gap-1.5 mt-2">
                          {stock.tags.map(tag => (
                            <span key={tag} className="text-[9px] text-text-tertiary bg-bg-tertiary px-1.5 py-0.5 rounded border border-border-primary">{tag}</span>
                          ))}
                        </div>
                      )}
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}

            {tab === 'sectors' && sectors.map(sector => (
              <tr
                key={sector.index}
                onClick={() => toggleExpand(sector.index)}
                className="border-t border-border-primary hover:bg-bg-card-hover cursor-pointer transition-colors"
              >
                <td className="py-2.5 pr-2">
                  <div className="flex items-center gap-2">
                    {expanded.has(sector.index) ? <ChevronDown className="w-3 h-3 text-text-disabled" /> : <ChevronRight className="w-3 h-3 text-text-disabled" />}
                    <span className="font-medium text-text-primary">{sector.index}</span>
                  </div>
                </td>
                <td className="py-2.5 px-2 text-right font-mono text-text-primary">{formatPrice(sector.ltp)}</td>
                <td className={`py-2.5 px-2 text-right font-mono font-medium ${pnlColor(sector.changePct)}`}>{formatPct(sector.changePct)}</td>
                <td className="py-2.5 px-2 text-center"><span className="text-sm">{signalEmoji(sector.signal)}</span></td>
                <td className="py-2.5 px-2 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <div className="w-16 h-1 bg-bg-tertiary rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${sector.signalStrength >= 65 ? 'bg-emerald-400' : sector.signalStrength <= 35 ? 'bg-red-400' : 'bg-amber-400'}`}
                        style={{ width: `${sector.signalStrength}%` }}
                      />
                    </div>
                    <span className="font-mono text-text-secondary w-5">{sector.signalStrength}</span>
                  </div>
                </td>
                <td className="py-2.5 pl-2">
                  <span className={`text-[9px] font-semibold uppercase px-1.5 py-0.5 rounded border ${signalColor(sector.signal)}`}>
                    {sector.signal}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {tab === 'stocks' && filteredStocks.length === 0 && (
        <div className="text-center py-8 text-text-tertiary text-xs">No stocks found matching your filters.</div>
      )}
    </div>
  );
};

export default Screener;
