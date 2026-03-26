import { useState } from 'react'
import type { QueryResponse } from '../../api/query'
import ChartCard from './ChartCard'

function IconChevron({ open }: { open: boolean }) {
  return (
    <svg
      width="14" height="14" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      className={`transition-transform ${open ? 'rotate-180' : ''}`}
    >
      <polyline points="6 9 12 15 18 9" />
    </svg>
  )
}

function Section({
  label,
  badge,
  badgeColor = 'gray',
  defaultOpen = true,
  children,
}: {
  label: string
  badge?: string
  badgeColor?: 'gray' | 'amber' | 'purple'
  defaultOpen?: boolean
  children: React.ReactNode
}) {
  const [open, setOpen] = useState(defaultOpen)
  const badgeClasses = {
    gray:   'bg-gray-100 text-gray-500',
    amber:  'bg-primary-50 text-primary-700',
    purple: 'bg-purple-50 text-purple-600',
  }[badgeColor]

  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 bg-white hover:bg-gray-50 transition-colors text-left"
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-900">{label}</span>
          {badge && (
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${badgeClasses}`}>
              {badge}
            </span>
          )}
        </div>
        <span className="text-gray-400"><IconChevron open={open} /></span>
      </button>

      {open && (
        <div className="border-t border-gray-100 px-4 py-4 bg-white">
          {children}
        </div>
      )}
    </div>
  )
}

function MarkdownResult({ text }: { text: string }) {
  return (
    <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono leading-relaxed overflow-x-auto bg-gray-50 rounded-lg p-3">
      {text}
    </pre>
  )
}

function CodeBlock({ code }: { code: string }) {
  const [copied, setCopied] = useState(false)

  function copy() {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="relative">
      <button
        onClick={copy}
        className="absolute top-2 right-2 text-xs px-2 py-1 bg-gray-200 hover:bg-gray-300 text-gray-600 rounded transition-colors"
      >
        {copied ? 'Copied!' : 'Copy'}
      </button>
      <pre className="text-xs text-gray-700 font-mono leading-relaxed overflow-x-auto bg-gray-50 rounded-lg p-3 pr-16 whitespace-pre">
        {code}
      </pre>
    </div>
  )
}

interface Props {
  data: QueryResponse
}

export default function ResultPanel({ data }: Props) {
  const hasInteresting = !!(data.interesting_reason && data.interesting_result)
  const allCharts = [...data.charts, ...data.interesting_charts]

  return (
    <div className="space-y-3">

      {/* Insight — always on top */}
      <Section label="Insight" badge="AI summary" badgeColor="amber">
        <p className="text-sm text-gray-700 leading-relaxed">{data.insight}</p>
      </Section>

      {/* Charts — merged pass1 + pass2 */}
      {allCharts.length > 0 && (
        <Section label="Charts" badge={`${allCharts.length}`} badgeColor="gray">
          <div className="grid grid-cols-1 gap-4">
            {allCharts.map((chart, i) => (
              <ChartCard key={i} chart={chart} />
            ))}
          </div>
        </Section>
      )}

      {/* Result — markdown table */}
      <Section label="Data" badge="Pass 1" badgeColor="gray">
        <div className="space-y-2">
          {data.explore_reason && (
            <p className="text-xs text-gray-500 italic mb-2">{data.explore_reason}</p>
          )}
          <MarkdownResult text={data.result} />
        </div>
      </Section>

      {/* Interesting findings */}
      {hasInteresting && (
        <Section label="Interesting findings" badge="Pass 2" badgeColor="purple" defaultOpen={false}>
          <div className="space-y-2">
            {data.interesting_reason && (
              <p className="text-xs text-gray-500 italic mb-2">{data.interesting_reason}</p>
            )}
            <MarkdownResult text={data.interesting_result!} />
          </div>
        </Section>
      )}

      {/* Code */}
      <Section label="Generated code" badge="Python" badgeColor="gray" defaultOpen={false}>
        <CodeBlock code={data.code} />
      </Section>

      {/* Cost report */}
      <Section label="Cost report" badgeColor="gray" defaultOpen={false}>
        <div className="space-y-3">
          {/* Summary row */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Total tokens', value: data.cost_report.total_tokens.toLocaleString() },
              { label: 'Cost (USD)', value: `$${data.cost_report.total_cost_usd.toFixed(5)}` },
              { label: 'Latency', value: `${data.cost_report.total_latency_ms}ms` },
            ].map(({ label, value }) => (
              <div key={label} className="bg-gray-50 rounded-lg p-3 text-center">
                <p className="text-xs text-gray-400">{label}</p>
                <p className="text-sm font-semibold text-gray-800 mt-0.5">{value}</p>
              </div>
            ))}
          </div>

          {/* Per-stage table */}
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-1.5 text-gray-400 font-medium">Stage</th>
                  <th className="text-right py-1.5 text-gray-400 font-medium">In</th>
                  <th className="text-right py-1.5 text-gray-400 font-medium">Out</th>
                  <th className="text-right py-1.5 text-gray-400 font-medium">Cost</th>
                  <th className="text-right py-1.5 text-gray-400 font-medium">ms</th>
                </tr>
              </thead>
              <tbody>
                {data.cost_report.calls.map((call, i) => (
                  <tr key={i} className="border-b border-gray-50">
                    <td className={`py-1.5 font-mono ${call.skipped ? 'text-gray-300' : 'text-gray-600'}`}>
                      {call.stage}
                    </td>
                    {call.skipped ? (
                      <td colSpan={4} className="py-1.5 text-gray-300 text-right italic">
                        skipped — {call.skip_reason}
                      </td>
                    ) : (
                      <>
                        <td className="py-1.5 text-right text-gray-500">{call.prompt_tokens}</td>
                        <td className="py-1.5 text-right text-gray-500">{call.completion_tokens}</td>
                        <td className="py-1.5 text-right text-gray-500">${call.cost_usd.toFixed(5)}</td>
                        <td className="py-1.5 text-right text-gray-500">{call.latency_ms}</td>
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </Section>

    </div>
  )
}