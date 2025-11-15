import { NextResponse } from 'next/server';

export async function GET(_: Request, { params }: { params: { ticker: string } }) {
  // 隨機價模擬
  const px = 800 + Math.round(Math.random() * 20) - 10;
  return NextResponse.json({ ticker: params.ticker, price: px, ts: Date.now() });
}
