export const revalidate = 0;

// 統一處理要打哪個後端
async function getFundamental(ticker: string) {
  // 1) 優先用後端的環境變數（SSR 用）
  const serverBase = process.env.API_BASE;
  // 2) 再看前端公開的（你 .env.local 會放這個）
  const clientBase = process.env.NEXT_PUBLIC_API_BASE;

  let url: string;

  if (serverBase || clientBase) {
    const base = serverBase ?? clientBase!;
    url = `${base}/api/stocks/${ticker}/fundamental`;
  } else {
    // 最後一招才用 mock，而且要給完整 origin，避免 Node 版 fetch 說 URL 解析不到
    const origin = process.env.NEXT_PUBLIC_SITE_ORIGIN ?? 'http://localhost:3000';
    url = `${origin}/api/mock/fundamental/${ticker}`;
  }

  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`fundamental fetch failed: ${res.status}`);
  }
  return res.json();
}

// ⭐ Next 16 的重點：params 是 Promise，要先 await
export default async function Page({
  params,
}: {
  params: Promise<{ ticker: string }>;
}) {
  const { ticker } = await params; // <-- 這行是你錯誤訊息在說的
  const fundamental = await getFundamental(ticker);
  const RealtimePriceCard = (await import('@/components/RealtimePriceCard')).default;

  return (
    <main style={{ padding: 24 }}>
      <h1>
        {fundamental.name}（{ticker}）
      </h1>
      <p>
        產業：{fundamental.sector}．P/E：{String(fundamental.pe)}．P/B：
        {String(fundamental.pb)}
      </p>
      <RealtimePriceCard ticker={ticker} />
    </main>
  );
}
