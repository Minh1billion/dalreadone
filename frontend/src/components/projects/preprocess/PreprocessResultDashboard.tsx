import { useState } from 'react'
import type { StepName } from '../../../api/preprocess'
import { STEP_META } from './PreprocessTypes'

interface Props {
  result:    Record<string, unknown>
  saving:    boolean
  saved:     boolean
  saveError: string | null
  onSave:    () => void
}

function Badge({ children, color = 'gray' }: { children: React.ReactNode; color?: 'gray' | 'green' | 'red' | 'yellow' }) {
  const cls = {
    gray:   'bg-gray-100 text-gray-600',
    green:  'bg-green-100 text-green-700',
    red:    'bg-red-100 text-red-600',
    yellow: 'bg-yellow-100 text-yellow-700',
  }[color]
  return <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${cls}`}>{children}</span>
}

function MissingResult({ data }: { data: any }) {
  const cols = Object.entries(data?.columns ?? {}) as [string, any][]
  return (
    <div className="space-y-2">
      <div className="flex gap-4 text-xs text-gray-500">
        <span>Dropped cols: <strong className="text-gray-700">{data?.dropped_cols?.length ?? 0}</strong></span>
        <span>Dropped rows: <strong className="text-gray-700">{data?.dropped_rows ?? 0}</strong></span>
        <span>Cols after: <strong className="text-gray-700">{data?.cols_after ?? '—'}</strong></span>
      </div>
      {cols.length > 0 && (
        <div className="rounded-lg border border-gray-100 overflow-hidden">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-100">
                <th className="text-left px-3 py-2 font-medium text-gray-500">Column</th>
                <th className="text-left px-3 py-2 font-medium text-gray-500">Null %</th>
                <th className="text-left px-3 py-2 font-medium text-gray-500">Action</th>
              </tr>
            </thead>
            <tbody>
              {cols.map(([col, info]) => (
                <tr key={col} className="border-b border-gray-50 last:border-0">
                  <td className="px-3 py-1.5 text-gray-700 font-mono text-[11px]">{col}</td>
                  <td className="px-3 py-1.5 text-gray-500">{info.null_pct_before ?? 0}%</td>
                  <td className="px-3 py-1.5">
                    <Badge color={info.action === 'drop_col' ? 'red' : info.action === 'skip' ? 'gray' : 'green'}>
                      {info.action}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function EncodingResult({ data }: { data: any }) {
  const cols = Object.entries(data?.columns ?? {}) as [string, any][]
  return (
    <div className="space-y-2">
      <p className="text-xs text-gray-500">Cols after: <strong className="text-gray-700">{data?.cols_after ?? '—'}</strong></p>
      {cols.length > 0 && (
        <div className="rounded-lg border border-gray-100 overflow-hidden">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-100">
                <th className="text-left px-3 py-2 font-medium text-gray-500">Column</th>
                <th className="text-left px-3 py-2 font-medium text-gray-500">Strategy</th>
                <th className="text-left px-3 py-2 font-medium text-gray-500">New cols</th>
              </tr>
            </thead>
            <tbody>
              {cols.map(([col, info]) => (
                <tr key={col} className="border-b border-gray-50 last:border-0">
                  <td className="px-3 py-1.5 text-gray-700 font-mono text-[11px]">{col}</td>
                  <td className="px-3 py-1.5"><Badge>{info.strategy}</Badge></td>
                  <td className="px-3 py-1.5 text-gray-400 text-[11px]">
                    {info.new_cols?.length ? info.new_cols.join(', ') : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function OutlierResult({ data }: { data: any }) {
  const cols = Object.entries(data?.columns ?? {}) as [string, any][]
  return (
    <div className="space-y-2">
      <div className="flex gap-4 text-xs text-gray-500">
        <span>Rows after: <strong className="text-gray-700">{data?.rows_after ?? '—'}</strong></span>
      </div>
      {cols.length > 0 && (
        <div className="rounded-lg border border-gray-100 overflow-hidden">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-100">
                <th className="text-left px-3 py-2 font-medium text-gray-500">Column</th>
                <th className="text-left px-3 py-2 font-medium text-gray-500">Strategy</th>
                <th className="text-left px-3 py-2 font-medium text-gray-500">Before</th>
                <th className="text-left px-3 py-2 font-medium text-gray-500">After</th>
              </tr>
            </thead>
            <tbody>
              {cols.map(([col, info]) => (
                <tr key={col} className="border-b border-gray-50 last:border-0">
                  <td className="px-3 py-1.5 text-gray-700 font-mono text-[11px]">{col}</td>
                  <td className="px-3 py-1.5"><Badge>{info.strategy}</Badge></td>
                  <td className="px-3 py-1.5 text-gray-500">{info.outlier_count_before ?? 0} ({info.outlier_pct_before ?? 0}%)</td>
                  <td className="px-3 py-1.5">
                    <Badge color={(info.outlier_count_after ?? 0) === 0 ? 'green' : 'yellow'}>
                      {info.outlier_count_after ?? 0}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function ScalingResult({ data }: { data: any }) {
  const cols = Object.entries(data?.columns ?? {}) as [string, any][]
  return (
    <div className="space-y-2">
      <p className="text-xs text-gray-500">Cols scaled: <strong className="text-gray-700">{data?.cols_scaled ?? '—'}</strong></p>
      {cols.length > 0 && (
        <div className="rounded-lg border border-gray-100 overflow-hidden">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-100">
                <th className="text-left px-3 py-2 font-medium text-gray-500">Column</th>
                <th className="text-left px-3 py-2 font-medium text-gray-500">Strategy</th>
                <th className="text-left px-3 py-2 font-medium text-gray-500">Fit params</th>
              </tr>
            </thead>
            <tbody>
              {cols.map(([col, info]) => (
                <tr key={col} className="border-b border-gray-50 last:border-0">
                  <td className="px-3 py-1.5 text-gray-700 font-mono text-[11px]">{col}</td>
                  <td className="px-3 py-1.5"><Badge>{info.strategy}</Badge></td>
                  <td className="px-3 py-1.5 text-gray-400 text-[11px] font-mono">
                    {info.fit_params
                      ? Object.entries(info.fit_params)
                          .map(([k, v]) => `${k}: ${typeof v === 'number' ? v.toFixed(3) : v}`)
                          .join(' · ')
                      : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

const RESULT_COMPONENTS: Record<StepName, React.ComponentType<{ data: any }>> = {
  missing:  MissingResult,
  encoding: EncodingResult,
  outlier:  OutlierResult,
  scaling:  ScalingResult,
}

export function PreprocessResultDashboard({ result, saving, saved, saveError, onSave }: Props) {
  const report   = (result?.preprocess_report ?? {}) as Record<string, any>
  const meta     = report.meta as any
  const executed: StepName[] = meta?.steps_executed ?? []
  const [active, setActive] = useState<StepName>(executed[0] ?? 'missing')

  return (
    <div className="space-y-4">
      {/* Summary + Save */}
      <div className="flex items-center gap-4 text-xs text-gray-500 bg-gray-50 rounded-lg px-4 py-2.5">
        <span>Rows out: <strong className="text-gray-700">{meta?.rows_out?.toLocaleString() ?? '—'}</strong></span>
        <span>Cols out: <strong className="text-gray-700">{meta?.cols_out ?? '—'}</strong></span>
        <span className="text-gray-400">{executed.length} step{executed.length !== 1 ? 's' : ''} executed</span>

        <div className="ml-auto flex items-center gap-2">
          {saveError && (
            <span className="text-red-500 text-[11px]">{saveError}</span>
          )}
          {saved ? (
            <span className="inline-flex items-center gap-1 text-green-600 text-[11px] font-medium">
              <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 00-1.414 0L8 12.586 4.707 9.293a1 1 0 00-1.414 1.414l4 4a1 1 0 001.414 0l8-8a1 1 0 000-1.414z" clipRule="evenodd" />
              </svg>
              Saved to project
            </span>
          ) : (
            <button
              onClick={onSave}
              disabled={saving}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 transition-colors text-[11px] font-medium"
            >
              {saving ? 'Saving…' : 'Save to project'}
            </button>
          )}
        </div>
      </div>

      {/* Step tabs */}
      <div className="flex gap-1 border-b border-gray-100">
        {executed.map((key) => {
          const m = STEP_META.find((s) => s.key === key)!
          return (
            <button
              key={key}
              onClick={() => setActive(key)}
              className={`px-3 py-2 text-xs font-medium border-b-2 -mb-px transition-colors ${
                active === key
                  ? 'border-primary-500 text-primary-700'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {m.label}
            </button>
          )
        })}
      </div>

      <div className="min-h-25">
        {(() => {
          const Component = RESULT_COMPONENTS[active]
          const data = report[active]
          return Component ? <Component data={data} /> : null
        })()}
      </div>
    </div>
  )
}