'use client';

import { useEffect, useState } from 'react';

type PriceData = {
  price: number;
  ts: string;
};

export default function RealtimePriceCard({ ticker }: { ticker: string }) {
  const [data, setData] = useState<PriceData | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    // 1) 優先吃你 .env.local 的
    // 2) 沒有的話就直接打後端的預設
    const base =
      process.env.NEXT_PUBLIC_API_BASE ||
      'http://localhost:8000';

    async function load() {
      try {
        const r = await fetch(`${base}/api/stocks/${ticker}/price`, {
          cache: 'no-store',
        }); // <-- 這次一定會是 http://localhost:8000/... 不是 /api/...
        if (!r.ok) throw new Error(`price fetch failed: ${r.status}`);
        const j = await r.json();
        if (mounted) {
          setData({ price: j.price, ts: j.ts });
          setErr(null);
        }
      } catch (e: any) {
        console.error(e);
        if (mounted) {
          setErr(e?.message ?? 'fetch error');
        }
      }
    }

    load();
    const id = setInterval(load, 5000);
    return () => {
      mounted = false;
      clearInterval(id);
    };
  }, [ticker]);

  return (
    <div style={{ marginTop: 16, padding: 12, border: '1px solid #444' }}>
      <h2>Realtime price</h2>
      {err && <p style={{ color: 'tomato' }}>{err}</p>}
      {data ? (
        <p>
          {data.price} @ {data.ts}
        </p>
      ) : (
        <p>Loading…</p>
      )}
    </div>
  );
}
