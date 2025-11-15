import { NextResponse } from 'next/server';

const MOCK: Record<string, any> = {
  '2330': { ticker: '2330', name: 'TSMC', sector: 'Semiconductor', pe: 25, pb: 5 },
};

export async function GET(
  _req: Request,
  ctx: { params: Promise<{ ticker: string }> }
) {
  const { ticker } = await ctx.params; // <-- 這行是重點
  const data =
    MOCK[ticker] ?? { ticker, name: 'Unknown', sector: 'N/A', pe: null, pb: null };
  return NextResponse.json(data, { status: 200 });
}
