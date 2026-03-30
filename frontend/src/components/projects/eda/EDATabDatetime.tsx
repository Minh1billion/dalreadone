import type { EDAReport } from './EDATypes'
import { InfoCard } from './EDAHelpers'

export function EDATabDatetime({ report }: { report: EDAReport }) {
  const entries = Object.entries(report.datetime)

  if (entries.length === 0)
    return <p className="text-sm text-gray-400 text-center py-8">No datetime columns detected.</p>

  return (
    <div className="space-y-4">
      {entries.map(([col, d]) => (
        <div key={col} className="rounded-xl border border-gray-100 p-4">
          <p className="text-sm font-semibold text-gray-700 font-mono mb-4">{col}</p>
          <div className="grid grid-cols-3 gap-3">
            <InfoCard label="Min date"  value={d.min_date} />
            <InfoCard label="Max date"  value={d.max_date} />
            <InfoCard label="Range"     value={`${d.date_range_days} days`} />
            <InfoCard label="Frequency" value={d.inferred_freq ?? 'unknown'} />
            <InfoCard label="Gaps"      value={d.gaps_count != null ? String(d.gaps_count) : '—'} />
            <InfoCard label="Timezone"  value={d.timezone} />
          </div>
          {d.seasonality_hint && d.seasonality_hint !== 'unknown' && (
            <p className="mt-3 text-xs text-violet-600 bg-violet-50 rounded-lg px-3 py-2">
              Seasonality hint: {d.seasonality_hint}
            </p>
          )}
        </div>
      ))}
    </div>
  )
}