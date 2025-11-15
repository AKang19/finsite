// app/stocks/page.tsx
export const revalidate = 0;

async function fetchCompanies() {
  const base = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
  const r = await fetch(`${base}/api/admin/companies?limit=5000`, { cache: 'no-store' });
  return r.json();
}

async function fetchSeries(ticker: string, from: string, to: string) {
  const base = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
  const r = await fetch(`${base}/api/stocks/${ticker}/series?from=${from}&to=${to}`, { cache: 'no-store' });
  return r.json();
}

export default async function Page({ searchParams }: { searchParams: Promise<Record<string, string>> }) {
  const sp = await searchParams;
  const companies = await fetchCompanies();
  const ticker = sp.ticker || '2330';
  const from = sp.from || '2025-01-01';
  const to = sp.to || '2025-12-31';
  const series = await fetchSeries(ticker, from, to);

  return (
    <main style={{ padding: 24 }}>
      <form method="get" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <select name="ticker" defaultValue={ticker}>
          {companies.map((c: any) => (
            <option key={c.ticker} value={c.ticker}>{c.ticker} {c.name}</option>
          ))}
        </select>
        <input type="date" name="from" defaultValue={from} />
        <input type="date" name="to" defaultValue={to} />
        <button type="submit">Load</button>
      </form>

      <div style={{ marginTop: 16 }}>
        <h3>{ticker} Close ( {from} → {to} )</h3>
        <ul style={{ maxHeight: 320, overflow: 'auto', fontFamily: 'monospace' }}>
          {series.map((row: any) => (
            <li key={row.date}>{row.date}  {row.close}</li>
          ))}
        </ul>
      </div>
    </main>
  );
}
