// app/stocks/page.tsx  — Server Component
import LineChart from '@/components/LineChart';

type SP = { [k: string]: string | string[] | undefined };
type PriceRow = {
  trade_date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
};

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<SP>;
}) {
  const sp = await searchParams;
  const ticker = (sp.ticker as string) ?? '2330';
  const from = (sp.from as string) ?? '2025-01-01';
  const to = (sp.to as string) ?? '2025-12-31';

  const base =
    process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, '') || 'http://localhost:8000';

  // 抓公司清單 + 區間序列（都在伺服端取，避免 hydration 差異）
  const [companies, series]: [any[], PriceRow[]] = await Promise.all([
    fetch(`${base}/api/admin/companies?limit=20000`, { cache: 'no-store' }).then((r) =>
      r.json(),
    ),
    fetch(
      `${base}/api/stocks/${encodeURIComponent(
        ticker,
      )}/series?from=${from}&to=${to}`,
      { cache: 'no-store' },
    ).then((r) => r.json()),
  ]);

  // 做一些展示用的衍生資料
  const valid = (series || []).filter((d) => Number.isFinite(d.close as any));
  const latest = valid.at(-1);
  const first = valid.at(0);
  const retPct =
    latest && first ? (((latest.close! - first.close!) / first.close!) * 100) : null;

  const chartData =
    valid.map((d) => ({ date: d.trade_date, value: Number(d.close) })) ?? [];

  return (
    <main style={{ padding: 24 }}>
      {/* 查詢表單 */}
      <form method="get" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <input list="tickers" name="ticker" defaultValue={ticker} placeholder="Ticker" />
        <datalist id="tickers">
          {Array.isArray(companies) &&
            companies.map((c: any) => (
              <option key={c.ticker} value={c.ticker}>
                {c.name || c.ticker}
              </option>
            ))}
        </datalist>

        <input type="date" name="from" defaultValue={from} />
        <input type="date" name="to" defaultValue={to} />
        <button type="submit">Go</button>
      </form>

      {/* 小統計卡片 */}
      <section style={{ display: 'flex', gap: 16, marginTop: 16 }}>
        <div style={{ padding: 12, border: '1px solid #eee', borderRadius: 8 }}>
          <div style={{ fontSize: 12, color: '#666' }}>Latest Close</div>
          <div style={{ fontSize: 20, fontWeight: 600 }}>
            {latest?.close ?? '—'}
          </div>
          <div style={{ fontSize: 12, color: '#666' }}>{latest?.trade_date ?? ''}</div>
        </div>
        <div style={{ padding: 12, border: '1px solid #eee', borderRadius: 8 }}>
          <div style={{ fontSize: 12, color: '#666' }}>Period Return</div>
          <div style={{ fontSize: 20, fontWeight: 600 }}>
            {retPct === null ? '—' : `${retPct.toFixed(2)}%`}
          </div>
          <div style={{ fontSize: 12, color: '#666' }}>
            {from} → {to}
          </div>
        </div>
        <div style={{ padding: 12, border: '1px solid #eee', borderRadius: 8 }}>
          <div style={{ fontSize: 12, color: '#666' }}>Points</div>
          <div style={{ fontSize: 20, fontWeight: 600 }}>{valid.length}</div>
        </div>
      </section>

      {/* 收盤價折線圖（SVG，無外掛） */}
      <section style={{ marginTop: 16 }}>
        <LineChart
          data={chartData.map((d) => ({ date: d.date, value: d.value }))}
          width={900}
          height={300}
        />
      </section>

      {/* 最近 10 筆表格 */}
      <section style={{ marginTop: 16 }}>
        <table
          style={{
            borderCollapse: 'collapse',
            width: '100%',
            fontSize: 12,
            border: '1px solid #eee',
          }}
        >
          <thead>
            <tr>
              {['date', 'open', 'high', 'low', 'close', 'volume'].map((h) => (
                <th
                  key={h}
                  style={{ textAlign: 'right', padding: '6px 8px', borderBottom: '1px solid #eee' }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {(valid.slice(-10).reverse() as PriceRow[]).map((r) => (
              <tr key={r.trade_date}>
                <td style={{ textAlign: 'right', padding: '6px 8px' }}>{r.trade_date}</td>
                <td style={{ textAlign: 'right', padding: '6px 8px' }}>{r.open ?? ''}</td>
                <td style={{ textAlign: 'right', padding: '6px 8px' }}>{r.high ?? ''}</td>
                <td style={{ textAlign: 'right', padding: '6px 8px' }}>{r.low ?? ''}</td>
                <td style={{ textAlign: 'right', padding: '6px 8px' }}>{r.close ?? ''}</td>
                <td style={{ textAlign: 'right', padding: '6px 8px' }}>{r.volume ?? ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}
