'use client';

import { useEffect, useMemo, useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000';

type Company = { ticker: string; name?: string | null; sector?: string | null; };
type SeriesItem = { date: string; close: number };
type Indicators = {
  dates: string[];
  ma?: Record<string, (number|null)[]>;
  macd?: { dif: (number|null)[]; signal: (number|null)[]; hist: (number|null)[] };
  rsi?: (number|null)[];
  bb?: { mid: (number|null)[]; upper: (number|null)[]; lower: (number|null)[] };
};

export default function TAPlayground() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [ticker, setTicker] = useState('2330');
  const [from, setFrom] = useState<string>(new Date(Date.now() - 90*864e5).toISOString().slice(0,10));
  const [to, setTo] = useState<string>(new Date().toISOString().slice(0,10));

  // 指標參數
  const [ma, setMa] = useState('5,20,60');
  const [macd, setMacd] = useState('12,26,9');
  const [rsi, setRsi] = useState(14);
  const [bb, setBb] = useState('20,2');

  const [series, setSeries] = useState<SeriesItem[] | null>(null);
  const [indi, setIndi] = useState<Indicators | null>(null);
  const [loading, setLoading] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${API_BASE}/api/admin/companies?limit=5000`);
        if (!r.ok) throw new Error(`companies ${r.status}`);
        setCompanies(await r.json());
      } catch (e:any) {
        console.warn('load companies failed', e);
      }
    })();
  }, []);

  async function runSeries() {
    setLoading('series'); setErr(null);
    try {
      const url = `${API_BASE}/api/stocks/${encodeURIComponent(ticker)}/series?from=${from}&to=${to}`;
      const r = await fetch(url);
      if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
      setSeries(await r.json());
    } catch (e:any) { setErr(e.message); } finally { setLoading(null); }
  }

  async function runIndicators() {
    setLoading('indicators'); setErr(null);
    try {
      const q = new URLSearchParams({ from, to });
      if (ma) q.set('ma', ma);
      if (macd) q.set('macd', macd);
      if (rsi) q.set('rsiperiod', String(rsi));
      if (bb) q.set('bb', bb);
      const url = `${API_BASE}/api/stocks/${encodeURIComponent(ticker)}/indicators?${q}`;
      const r = await fetch(url);
      if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
      setIndi(await r.json());
    } catch (e:any) { setErr(e.message); } finally { setLoading(null); }
  }

  // --- 小型 SVG 畫圖元件（不加套件） ---
  function Poly({ data, w=720, h=160 }: { data: (number|null)[], w?:number, h?:number }) {
    const clean = data.filter((x): x is number => x !== null && Number.isFinite(x));
    if (!clean.length) return <div className="text-sm text-gray-500">No data</div>;
    const min = Math.min(...clean), max = Math.max(...clean);
    const values = data.map(v => (v==null ? null : v));
    const step = w / Math.max(1, values.length - 1);
    const norm = (v:number) => max===min ? h/2 : h - ((v - min) / (max - min)) * h;
    const pts = values.map((v,i) => v==null ? null : `${i*step},${norm(v)}`).filter(Boolean).join(' ');
    return (
      <svg width={w} height={h} className="mt-2">
        <polyline points={pts} fill="none" stroke="currentColor" strokeWidth="2" />
      </svg>
    );
  }

  const closeArr = useMemo(() => series?.map(s => s.close) ?? [], [series]);

  return (
    <main className="p-6 space-y-6">
      <h1 className="text-2xl font-semibold">技術分析（可選股票 / 時間區間 / 指標）</h1>

      <div className="grid gap-4 sm:grid-cols-3">
        <label className="flex flex-col gap-1">
          <span>Ticker</span>
          <input list="tickers" className="border rounded p-2" value={ticker} onChange={e=>setTicker(e.target.value.trim())}/>
          <datalist id="tickers">
            {companies.map(c => (
              <option key={c.ticker} value={c.ticker}>{c.ticker} {c.name ? `- ${c.name}` : ''}</option>
            ))}
          </datalist>
        </label>
        <label className="flex flex-col gap-1">
          <span>From</span>
          <input type="date" className="border rounded p-2" value={from} onChange={e=>setFrom(e.target.value)}/>
        </label>
        <label className="flex flex-col gap-1">
          <span>To</span>
          <input type="date" className="border rounded p-2" value={to} onChange={e=>setTo(e.target.value)}/>
        </label>
      </div>

      <div className="grid gap-4 sm:grid-cols-4">
        <label className="flex flex-col gap-1">
          <span>MA windows（逗號分隔）</span>
          <input className="border rounded p-2" value={ma} onChange={e=>setMa(e.target.value)}/>
        </label>
        <label className="flex flex-col gap-1">
          <span>MACD (fast,slow,signal)</span>
          <input className="border rounded p-2" value={macd} onChange={e=>setMacd(e.target.value)}/>
        </label>
        <label className="flex flex-col gap-1">
          <span>RSI period</span>
          <input type="number" className="border rounded p-2" value={rsi} onChange={e=>setRsi(Number(e.target.value)||0)}/>
        </label>
        <label className="flex flex-col gap-1">
          <span>Bollinger (window,k)</span>
          <input className="border rounded p-2" value={bb} onChange={e=>setBb(e.target.value)}/>
        </label>
      </div>

      <div className="flex gap-3">
        <button onClick={runSeries} className="rounded px-4 py-2 bg-black text-white disabled:opacity-50" disabled={!!loading}>載入 /series</button>
        <button onClick={runIndicators} className="rounded px-4 py-2 bg-black text-white disabled:opacity-50" disabled={!!loading}>載入 /indicators</button>
        {loading && <span>Loading {loading}...</span>}
        {err && <span className="text-red-600">Error: {err}</span>}
      </div>

      {/* 價格線 */}
      <section className="border rounded p-4">
        <h2 className="font-semibold">Close（/series）</h2>
        {series ? <Poly data={closeArr} /> : <div className="text-sm text-gray-500">請先點「載入 /series」</div>}
      </section>

      {/* 指標區 */}
      <section className="border rounded p-4 space-y-4">
        <h2 className="font-semibold">Indicators（/indicators）</h2>
        {!indi && <div className="text-sm text-gray-500">請先點「載入 /indicators」</div>}

        {indi?.ma && (
          <div>
            <div className="font-medium mb-1">MA</div>
            <div className="grid sm:grid-cols-3 gap-4">
              {Object.entries(indi.ma).map(([k, arr]) => (
                <div key={k} className="border rounded p-2">
                  <div className="text-sm text-gray-600">MA {k}</div>
                  <Poly data={arr} />
                </div>
              ))}
            </div>
          </div>
        )}

        {indi?.macd && (
          <div className="grid sm:grid-cols-3 gap-4">
            <div className="border rounded p-2">
              <div className="text-sm text-gray-600">MACD DIF</div>
              <Poly data={indi.macd.dif} />
            </div>
            <div className="border rounded p-2">
              <div className="text-sm text-gray-600">MACD Signal</div>
              <Poly data={indi.macd.signal} />
            </div>
            <div className="border rounded p-2">
              <div className="text-sm text-gray-600">MACD Hist</div>
              <Poly data={indi.macd.hist} />
            </div>
          </div>
        )}

        {indi?.rsi && (
          <div className="border rounded p-2">
            <div className="text-sm text-gray-600">RSI</div>
            <Poly data={indi.rsi} />
          </div>
        )}

        {indi?.bb && (
          <div className="grid sm:grid-cols-3 gap-4">
            <div className="border rounded p-2"><div className="text-sm text-gray-600">BB Mid</div><Poly data={indi.bb.mid} /></div>
            <div className="border rounded p-2"><div className="text-sm text-gray-600">BB Upper</div><Poly data={indi.bb.upper} /></div>
            <div className="border rounded p-2"><div className="text-sm text-gray-600">BB Lower</div><Poly data={indi.bb.lower} /></div>
          </div>
        )}
      </section>
    </main>
  );
}
