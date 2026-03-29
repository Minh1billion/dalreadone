import { useState } from 'react'
import type { FilePreview } from '../../api/files'
import DTypeBadge from '../ui/DTypeBadge'
import MissingBar from '../ui/MissingBar'

type Tab = 'overview' | 'missing' | 'sample'

function fmt(v: number | null): string {
  if (v == null) return '—'
  return Math.abs(v) >= 1000
    ? v.toLocaleString(undefined, { maximumFractionDigits: 1 })
    : v.toLocaleString(undefined, { maximumFractionDigits: 3 })
}

export default function FilePreviewPanel({
  preview,
  loading,
}: {
  preview: FilePreview | null
  loading: boolean
}) {
  const [tab, setTab] = useState<Tab>('overview')

  if (loading && !preview) {
    return (
      <div className="rounded-lg border border-gray-100 p-3 space-y-2">
        {[80, 60, 70].map((w, i) => (
          <div key={i} className="h-3 bg-gray-100 rounded animate-pulse" style={{ width: `${w}%` }} />
        ))}
      </div>
    )
  }

  if (!preview) return null

  const { shape, columns, dtypes, missing, describe, sample } = preview
  const totalNulls    = missing.reduce((s, c) => s + c.null_count, 0)
  const colsWithNulls = missing.filter(c => c.null_count > 0).length

  return (
    <div className="rounded-lg border border-gray-100 overflow-hidden">

      {/* ── Header ── */}
      <div className="px-3 py-2 bg-gray-50 border-b border-gray-100 flex items-center gap-2 flex-wrap">
        <span className="text-xs font-medium text-gray-700 truncate max-w-[120px]" title={preview.filename}>
          {preview.filename}
        </span>
        <div className="ml-auto flex items-center gap-1.5 flex-wrap justify-end">
          {preview.strategy === 'nlp' ? (
            <span
              className="px-1.5 py-0.5 bg-violet-50 text-violet-700 border border-violet-200 rounded text-xs font-medium"
              title={`Text-heavy columns: ${preview.text_cols.join(', ')}`}
            >
              NLP
            </span>
          ) : (
            <span
              className="px-1.5 py-0.5 bg-teal-50 text-teal-700 border border-teal-200 rounded text-xs font-medium"
              title="Standard structured/tabular data"
            >
              Structured
            </span>
          )}
          <span className="px-1.5 py-0.5 bg-primary-50 text-primary-700 border border-primary-100 rounded text-xs font-mono">
            {shape.rows.toLocaleString()} × {shape.cols}
          </span>
          {totalNulls > 0 && (
            <span className="px-1.5 py-0.5 bg-amber-50 text-amber-700 border border-amber-100 rounded text-xs">
              {colsWithNulls} col{colsWithNulls > 1 ? 's' : ''} w/ nulls
            </span>
          )}
        </div>
      </div>

      {/* ── Tabs ── */}
      <div className="flex border-b border-gray-100 bg-gray-50">
        {(['overview', 'missing', 'sample'] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 py-1.5 text-xs font-medium capitalize transition-colors
              ${tab === t
                ? 'text-primary-700 border-b-2 border-primary-600 bg-white'
                : 'text-gray-400 hover:text-gray-600'
              }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* ── Overview ── */}
      {tab === 'overview' && (
        <div className="max-h-60 overflow-y-auto">
          <div className="px-3 py-2 border-b border-gray-50">
            <div className="grid grid-cols-2 gap-x-4">
              {columns.map(col => (
                <div key={col} className="flex items-center justify-between gap-2 py-1 border-b border-gray-50">
                  <span
                    className={`text-xs truncate min-w-0 flex-1 ${
                      preview.text_cols.includes(col) ? 'text-violet-700 font-medium' : 'text-gray-700'
                    }`}
                    title={col}
                  >
                    {col}
                  </span>
                  <DTypeBadge dtype={dtypes[col]} />
                </div>
              ))}
            </div>
          </div>

          {describe.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-gray-400 bg-gray-50">
                    <th className="text-left px-3 py-1.5 font-medium sticky left-0 bg-gray-50 min-w-[72px]">column</th>
                    {(['mean', 'std', 'min', 'median', 'max'] as const).map(h => (
                      <th key={h} className="text-right px-2 py-1.5 font-medium whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {describe.map(row => (
                    <tr key={row.column} className="hover:bg-gray-50 transition-colors">
                      <td className="px-3 py-1.5 font-medium text-gray-700 sticky left-0 bg-white max-w-[72px] truncate" title={row.column}>
                        {row.column}
                      </td>
                      {(['mean', 'std', 'min', 'median', 'max'] as const).map(k => (
                        <td key={k} className="px-2 py-1.5 text-right text-gray-600 font-mono tabular-nums">
                          {fmt(row[k])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="px-3 py-3 text-xs text-gray-400">No numeric columns.</p>
          )}
        </div>
      )}

      {/* ── Missing ── */}
      {tab === 'missing' && (
        <div className="max-h-60 overflow-y-auto divide-y divide-gray-50">
          {missing.map(col => (
            <div key={col.column} className="px-3 py-2">
              <div className="flex items-center gap-1.5 mb-1.5">
                <span className="text-xs font-medium text-gray-700 truncate flex-1 min-w-0" title={col.column}>
                  {col.column}
                </span>
                <DTypeBadge dtype={col.dtype} />
                {col.null_count > 0 && (
                  <span className="text-xs text-amber-600 tabular-nums shrink-0">
                    {col.null_count.toLocaleString()}
                  </span>
                )}
              </div>
              <MissingBar pct={col.null_pct} />
            </div>
          ))}
        </div>
      )}

      {/* ── Sample ── */}
      {tab === 'sample' && (
        <div className="overflow-auto max-h-60">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-gray-50 text-gray-400">
                {columns.map(col => (
                  <th key={col} className="text-left px-3 py-1.5 font-medium whitespace-nowrap sticky top-0 bg-gray-50">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {sample.map((row, i) => (
                <tr key={i} className="hover:bg-gray-50 transition-colors">
                  {columns.map(col => (
                    <td key={col} className="px-3 py-1.5 font-mono text-gray-600 max-w-[100px] truncate" title={String(row[col] ?? '')}>
                      {row[col] == null
                        ? <span className="text-gray-300 italic">null</span>
                        : String(row[col])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {loading && preview && (
        <div className="px-3 py-1.5 bg-primary-50 text-primary-600 text-xs animate-pulse">
          Refreshing…
        </div>
      )}
    </div>
  )
}