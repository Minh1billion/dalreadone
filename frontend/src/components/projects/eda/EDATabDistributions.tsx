import type { EDAReport } from './EDATypes'
import { Sparkline } from './EDAHelpers'

const DIST_COLOR: Record<string, string> = {
  'right-skewed':         '#f59e0b',
  'left-skewed':          '#3b82f6',
  'approximately-normal': '#8b5cf6',
  'uniform':              '#10b981',
}

export function EDATabDistributions({ report }: { report: EDAReport }) {
  const { distributions } = report

  return (
    <div className="grid grid-cols-2 gap-4">
      {Object.entries(distributions).map(([col, d]) => {
        const color = DIST_COLOR[d.dist_type_hint] ?? '#6b7280'
        const maxCount = Math.max(...d.histogram_bins.map(x => x.count), 1)
        const { outlier_summary: o } = d

        return (
          <div key={col} className="rounded-xl border border-gray-100 p-4">
            <div className="flex items-start justify-between mb-3">
              <p className="text-sm font-semibold text-gray-700 font-mono">{col}</p>
              <span
                className="text-[10px] px-2 py-0.5 rounded-full font-medium border"
                style={{ color, borderColor: color, backgroundColor: color + '15' }}
              >
                {d.dist_type_hint}
              </span>
            </div>

            <div className="mb-3">
              <Sparkline bins={d.histogram_bins} color={color} />
            </div>

            <div className="space-y-1 max-h-40 overflow-y-auto">
              {d.histogram_bins.filter(b => b.count > 0).map((b, i) => (
                <div key={i} className="flex items-center gap-2 text-[10px]">
                  <span className="text-gray-400 font-mono w-36 truncate">{b.range}</span>
                  <div className="flex-1 h-1 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${(b.count / maxCount) * 100}%`, backgroundColor: color }}
                    />
                  </div>
                  <span className="text-gray-500 w-4 text-right tabular-nums">{b.count}</span>
                </div>
              ))}
            </div>

            <div className="mt-3 pt-3 border-t border-gray-50 flex items-center justify-between text-[11px]">
              <span className="text-gray-400">Normality ({d.normality_test.method})</span>
              <div className="flex items-center gap-2">
                <span className="text-gray-500 tabular-nums">p={d.normality_test.p_value.toFixed(4)}</span>
                <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${d.normality_test.is_normal ? 'bg-green-50 text-green-600' : 'bg-gray-100 text-gray-500'}`}>
                  {d.normality_test.is_normal ? '✓ normal' : '✗ non-normal'}
                </span>
              </div>
            </div>

            {o.count > 0 && (
              <div className="mt-2 text-[10px] text-red-500 space-y-0.5">
                <p>
                  Outliers: {o.count.toLocaleString()} rows ({o.pct}%)
                  &nbsp;·&nbsp; fence [{o.lower_fence}, {o.upper_fence}]
                </p>
                {o.preview_idx.length > 0 && (
                  <p className="text-red-400">
                    Sample idx: {o.preview_idx.join(', ')}{o.count > o.preview_idx.length ? ', …' : ''}
                  </p>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}