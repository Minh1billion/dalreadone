import type { EDAReport } from './EDATypes'
import { qualityColor, qualityBg, InfoCard, MiniBar } from './EDAHelpers'

export function EDATabOverview({ report }: { report: EDAReport }) {
  const { schema, data_quality_score: q, missing_and_duplicates: m } = report

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Overall',      value: q.overall_score },
          { label: 'Completeness', value: q.completeness },
          { label: 'Uniqueness',   value: q.uniqueness },
          { label: 'Consistency',  value: q.consistency },
        ].map(({ label, value }) => (
          <div key={label} className={`rounded-xl border p-4 text-center ${qualityBg(value)}`}>
            <p className={`text-2xl font-bold tabular-nums ${qualityColor(value)}`}>
              {Math.round(value * 100)}<span className="text-xs font-normal opacity-60">%</span>
            </p>
            <p className="text-[11px] text-gray-500 mt-1">{label}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-3">
        <InfoCard label="Rows"       value={schema.n_rows.toLocaleString()} sub={`${schema.memory_mb} MB`} />
        <InfoCard label="Columns"    value={String(schema.n_cols)}          sub="total fields" />
        <InfoCard label="Duplicates" value={String(m.duplicate_rows)}       sub={`${m.duplicate_pct}% of rows`} />
      </div>

      {Object.keys(m.columns).length > 0 && (
        <div className="rounded-xl border border-gray-100 overflow-hidden">
          <div className="px-4 py-2.5 border-b border-gray-100 bg-gray-50">
            <p className="text-xs font-semibold text-gray-600">Missing values by column</p>
          </div>
          <div className="divide-y divide-gray-50">
            {Object.entries(m.columns).map(([col, info]) => (
              <div key={col} className="px-4 py-2.5 flex items-center gap-3">
                <span className="text-xs text-gray-700 w-32 truncate font-mono">{col}</span>
                <div className="flex-1">
                  <MiniBar value={info.null_pct} max={100} color={info.null_pct > 10 ? 'bg-red-400' : 'bg-amber-400'} />
                </div>
                <span className="text-xs text-gray-500 tabular-nums w-20 text-right">
                  {info.null_count} ({info.null_pct}%)
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {q.flags?.length > 0 && (
        <div className="rounded-xl bg-amber-50 border border-amber-100 p-4">
          <p className="text-xs font-semibold text-amber-700 mb-2">⚠ Quality flags</p>
          <ul className="space-y-1">
            {q.flags.map((flag, i) => (
              <li key={i} className="text-xs text-amber-600 flex gap-2"><span className="shrink-0">•</span>{flag}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}