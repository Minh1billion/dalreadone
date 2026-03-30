import type { EDAReport } from './EDATypes'

const corrColor = (v: number) => {
  const abs = Math.abs(v)
  if (abs > 0.7) return 'bg-violet-600 text-white'
  if (abs > 0.4) return 'bg-violet-200 text-violet-800'
  if (abs > 0.2) return 'bg-violet-50 text-violet-500'
  return 'bg-gray-50 text-gray-500'
}

export function EDATabCorrelations({ report }: { report: EDAReport }) {
  const { correlations } = report

  return (
    <div className="space-y-5">
      <div className="rounded-xl border border-gray-100 overflow-hidden">
        <div className="px-4 py-2.5 bg-gray-50 border-b border-gray-100">
          <p className="text-xs font-semibold text-gray-600">Pearson correlations (numeric)</p>
        </div>
        <div className="divide-y divide-gray-50">
          {Object.entries(correlations.pearson).map(([pair, val]) => {
            const [a, b] = pair.split('__')
            return (
              <div key={pair} className="px-4 py-2.5 flex items-center gap-3">
                <span className="text-xs font-mono text-gray-500 flex-1">{a} ↔ {b}</span>
                <div className="w-32 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full rounded-full bg-violet-400" style={{ width: `${Math.abs(val) * 100}%` }} />
                </div>
                <span className={`text-[11px] px-2 py-0.5 rounded font-mono font-medium ${corrColor(val)}`}>
                  {val.toFixed(3)}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      <div className="rounded-xl border border-gray-100 overflow-hidden">
        <div className="px-4 py-2.5 bg-gray-50 border-b border-gray-100">
          <p className="text-xs font-semibold text-gray-600">Top Cramér's V pairs (categorical)</p>
        </div>
        <div className="divide-y divide-gray-50">
          {correlations.top_corr_pairs.map((p, i) => (
            <div key={i} className="px-4 py-2.5 flex items-center gap-3">
              <span className="text-xs font-mono text-gray-500 flex-1">{p.col_a} ↔ {p.col_b}</span>
              <span className="text-[10px] text-gray-400">{p.method}</span>
              <span className={`text-[11px] px-2 py-0.5 rounded font-mono font-medium ${corrColor(Math.min(p.value, 1))}`}>
                {p.value.toFixed(3)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}