// components/LineChart.tsx
'use client';

import * as React from 'react';

type SeriesPoint = { date: string; value: number };

export default function LineChart({
  data,
  width = 800,
  height = 260,
  padding = 24,
}: {
  data: SeriesPoint[];
  width?: number;
  height?: number;
  padding?: number;
}) {
  if (!data?.length) {
    return <div style={{ padding: 8, color: '#888' }}>No data</div>;
  }

  const xs = data.map((_, i) => i);
  const ys = data.map((d) => d.value).filter((v) => Number.isFinite(v));

  const minX = 0;
  const maxX = xs.length - 1;
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);

  const W = width;
  const H = height;
  const P = padding;

  const sx = (x: number) =>
    P + ((x - minX) / Math.max(1, maxX - minX)) * (W - 2 * P);
  const sy = (y: number) =>
    H - P - ((y - minY) / Math.max(1e-9, maxY - minY)) * (H - 2 * P);

  const path = data
    .map((d, i) => `${i === 0 ? 'M' : 'L'} ${sx(i).toFixed(2)} ${sy(d.value).toFixed(2)}`)
    .join(' ');

  // 產生 4 條水平輔助線
  const grid: number[] = [];
  for (let i = 0; i <= 4; i++) grid.push(minY + ((maxY - minY) * i) / 4);

  return (
    <svg width={W} height={H} role="img" aria-label="line chart">
      {/* grid */}
      {grid.map((gy, i) => (
        <g key={i}>
          <line
            x1={P}
            x2={W - P}
            y1={sy(gy)}
            y2={sy(gy)}
            stroke="#eee"
            strokeDasharray="4 4"
          />
          <text x={P - 6} y={sy(gy)} fontSize="10" textAnchor="end" dy="0.33em" fill="#999">
            {Number(gy).toFixed(2)}
          </text>
        </g>
      ))}

      {/* series path */}
      <path d={path} fill="none" stroke="#1f77b4" strokeWidth="2" />

      {/* axes */}
      <rect x={P} y={P} width={W - 2 * P} height={H - 2 * P} fill="none" stroke="#ddd" />
    </svg>
  );
}
