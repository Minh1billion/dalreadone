export const fmtNum = (n: number, digits = 2) =>
  typeof n === 'number' ? n.toLocaleString(undefined, { maximumFractionDigits: digits }) : '—'

export const qualityColor = (score: number) =>
  score >= 0.9 ? 'text-emerald-600' : score >= 0.7 ? 'text-amber-500' : 'text-red-500'

export const qualityBg = (score: number) =>
  score >= 0.9 ? 'bg-emerald-50 border-emerald-100' : score >= 0.7 ? 'bg-amber-50 border-amber-100' : 'bg-red-50 border-red-100'

export function InfoCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-xl border border-gray-100 bg-gray-50 p-4">
      <p className="text-[11px] text-gray-400 mb-1">{label}</p>
      <p className="text-lg font-semibold text-gray-800 tabular-nums">{value}</p>
      {sub && <p className="text-[10px] text-gray-400 mt-0.5">{sub}</p>}
    </div>
  )
}

export function MiniBar({ value, max, color = 'bg-violet-400' }: { value: number; max: number; color?: string }) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[10px] text-gray-400 w-6 text-right">{Math.round(pct)}%</span>
    </div>
  )
}

export function Sparkline({ bins, color = '#8b5cf6' }: { bins: Array<{ range: string; count: number }>; color?: string }) {
  if (!bins?.length) return null
  const max = Math.max(...bins.map(b => b.count), 1)
  const w = 120, h = 32, bw = w / bins.length
  return (
    <svg width={w} height={h} className="overflow-visible">
      {bins.map((b, i) => {
        const barH = (b.count / max) * h
        return (
          <rect key={i} x={i * bw + 0.5} y={h - barH} width={bw - 1} height={barH}
            fill={color} fillOpacity={0.7} rx={1} />
        )
      })}
    </svg>
  )
}