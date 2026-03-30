import { useState } from 'react'
import type { EDAReport } from './EDATypes'
import { EDATabOverview }      from './EDATabOverview'
import { EDATabSchema }        from './EDATabSchema'
import { EDATabUnivariate }    from './EDATabUnivariate'
import { EDATabDistributions } from './EDATabDistributions'
import { EDATabCorrelations }  from './EDATabCorrelations'
import { EDATabDatetime }      from './EDATabDatetime'

const TABS = [
  { key: 'overview',      label: 'Overview' },
  { key: 'schema',        label: 'Schema' },
  { key: 'univariate',    label: 'Univariate' },
  { key: 'distributions', label: 'Distributions' },
  { key: 'correlations',  label: 'Correlations' },
  { key: 'datetime',      label: 'Datetime' },
]

interface Props {
  result: any
  filename?: string
}

export function EDAResultDashboard({ result, filename }: Props) {
  const report: EDAReport = result?.eda_report
  if (!report) return null

  const [activeTab, setActiveTab] = useState('overview')

  const tabContent: Record<string, React.ReactNode> = {
    overview:      <EDATabOverview      report={report} />,
    schema:        <EDATabSchema        report={report} />,
    univariate:    <EDATabUnivariate    report={report} />,
    distributions: <EDATabDistributions report={report} />,
    correlations:  <EDATabCorrelations  report={report} />,
    datetime:      <EDATabDatetime      report={report} />,
  }

  const downloadJSON = () => {
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href = url
    a.download = filename ? `eda_${filename}.json` : 'eda_report.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-4">
      {filename && (
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9 17v-2a4 4 0 014-4h4M7 7h.01M3 7a4 4 0 014-4h6l5 5v11a2 2 0 01-2 2H7a2 2 0 01-2-2V7z" />
          </svg>
          <span className="font-mono text-gray-500 font-medium">{filename}</span>
        </div>
      )}

      <div className="flex items-center gap-1 border-b border-gray-100 pb-0">
        {TABS.map(t => (
          <button key={t.key} onClick={() => setActiveTab(t.key)}
            className={`px-3 py-2 text-xs font-medium border-b-2 transition-colors -mb-px ${
              activeTab === t.key
                ? 'border-violet-500 text-violet-700'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
        <div className="ml-auto pb-1">
          <button onClick={downloadJSON}
            className="text-xs px-2.5 py-1.5 rounded-md border border-gray-200 text-gray-500 hover:bg-gray-50 transition-colors flex items-center gap-1.5"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            JSON
          </button>
        </div>
      </div>

      <div>{tabContent[activeTab]}</div>
    </div>
  )
}