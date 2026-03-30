import { useState } from 'react'
import type { EDAReport } from './EDATypes'
import { fmtNum, MiniBar } from './EDAHelpers'

export function EDATabUnivariate({ report }: { report: EDAReport }) {
  const { univariate } = report
  const [sub, setSub] = useState<'numeric' | 'categorical'>('numeric')

  return (
    <div className="space-y-4">
      <div className="flex gap-1 p-0.5 bg-gray-100 rounded-lg w-fit">
        {(['numeric', 'categorical'] as const).map(t => (
          <button key={t} onClick={() => setSub(t)}
            className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
              sub === t ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {t === 'numeric'
              ? `Numeric (${Object.keys(univariate.numeric).length})`
              : `Categorical (${Object.keys(univariate.categorical).length})`}
          </button>
        ))}
      </div>

      {sub === 'numeric' ? (
        <div className="space-y-3">
          {Object.entries(univariate.numeric).map(([col, s]) => (
            <div key={col} className="rounded-xl border border-gray-100 p-4">
              <div className="flex items-start justify-between mb-3">
                <p className="text-sm font-semibold text-gray-700 font-mono">{col}</p>
                {s.outlier_count > 0 && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-red-50 text-red-500 border border-red-100">
                    {s.outlier_count} outlier{s.outlier_count > 1 ? 's' : ''}
                  </span>
                )}
              </div>
              <div className="grid grid-cols-4 gap-3 mb-3">
                {[
                  { label: 'Mean',   value: fmtNum(s.mean) },
                  { label: 'Median', value: fmtNum(s.median) },
                  { label: 'Std',    value: fmtNum(s.std) },
                  { label: 'Min',    value: fmtNum(s.min) },
                  { label: 'Max',    value: fmtNum(s.max) },
                  { label: 'P25',    value: fmtNum(s.p25) },
                  { label: 'P75',    value: fmtNum(s.p75) },
                  { label: 'Skew',   value: fmtNum(s.skewness) },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-gray-50 rounded-lg p-2.5 text-center">
                    <p className="text-[10px] text-gray-400 mb-0.5">{label}</p>
                    <p className="text-xs font-semibold text-gray-700 tabular-nums">{value}</p>
                  </div>
                ))}
              </div>
              {s.zeros_pct > 0 && <p className="text-[10px] text-gray-400">Zeros: {s.zeros_pct}%</p>}
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {Object.entries(univariate.categorical).map(([col, s]) => (
            <div key={col} className="rounded-xl border border-gray-100 p-4">
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm font-semibold text-gray-700 font-mono">{col}</p>
                <div className="flex gap-3 text-[11px] text-gray-400">
                  <span>cardinality: <strong className="text-gray-600">{s.cardinality}</strong></span>
                  <span>entropy: <strong className="text-gray-600">{fmtNum(s.entropy)}</strong></span>
                  <span>mode: <strong className="text-violet-600">{s.mode}</strong></span>
                </div>
              </div>
              <div className="space-y-1.5">
                {s.top_values.map((v) => (
                  <div key={v.value} className="flex items-center gap-3">
                    <span className="text-xs text-gray-600 w-36 truncate">{v.value}</span>
                    <div className="flex-1"><MiniBar value={v.pct} max={100} /></div>
                    <span className="text-[11px] text-gray-400 tabular-nums w-16 text-right">
                      {v.count} ({v.pct}%)
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}