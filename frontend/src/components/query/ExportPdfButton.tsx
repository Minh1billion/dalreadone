import { useState } from 'react'
import type { QueryResponse } from '../../api/query'

interface Props {
  data:     QueryResponse
  filename: string
  question: string | null
}

interface ExportOptions {
  insight:      boolean
  charts:       boolean
  data:         boolean
  interesting:  boolean
  code:         boolean
}

const DEFAULT_OPTIONS: ExportOptions = {
  insight:     true,
  charts:      true,
  data:        true,
  interesting: true,
  code:        false,
}

const SECTION_LABELS: { key: keyof ExportOptions; label: string; description: string }[] = [
  { key: 'insight',     label: 'Insight',              description: 'AI summary of findings' },
  { key: 'charts',     label: 'Charts',               description: 'All visualisations' },
  { key: 'data',       label: 'Data',                 description: 'Pass 1 raw results' },
  { key: 'interesting',label: 'Interesting findings', description: 'Pass 2 deeper analysis' },
  { key: 'code',       label: 'Generated code',       description: 'Python code used' },
]

export default function ExportPdfButton({ data, filename, question }: Props) {
  const [showDialog, setShowDialog] = useState(false)
  const [options, setOptions]       = useState<ExportOptions>(DEFAULT_OPTIONS)
  const [exporting, setExporting]   = useState(false)

  const hasInteresting = !!(data.interesting_reason && data.interesting_result)
  const hasCharts      = (data.charts?.length ?? 0) + (data.interesting_charts?.length ?? 0) > 0

  // Sections that are actually available
  const available: (keyof ExportOptions)[] = [
    'insight',
    ...(hasCharts      ? ['charts' as const]      : []),
    'data',
    ...(hasInteresting ? ['interesting' as const] : []),
    ...(data.code      ? ['code' as const]        : []),
  ]

  const selectedCount = available.filter(k => options[k]).length

  function toggle(key: keyof ExportOptions) {
    setOptions(prev => ({ ...prev, [key]: !prev[key] }))
  }

  function selectAll()  { setOptions(prev => ({ ...prev, ...Object.fromEntries(available.map(k => [k, true]))  })) }
  function selectNone() { setOptions(prev => ({ ...prev, ...Object.fromEntries(available.map(k => [k, false])) })) }

  async function handleExport() {
    setExporting(true)
    try {
      await exportPdf(data, filename, question, options)
      setShowDialog(false)
    } finally {
      setExporting(false)
    }
  }

  return (
    <>
      <button
        onClick={() => setShowDialog(true)}
        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="12" y1="18" x2="12" y2="12"/>
          <line x1="9" y1="15" x2="15" y2="15"/>
        </svg>
        Export PDF
      </button>

      {/* ── Dialog ──────────────────────────────────────────────────────────── */}
      {showDialog && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
          onClick={(e) => { if (e.target === e.currentTarget) setShowDialog(false) }}
        >
          <div className="bg-white rounded-2xl shadow-xl border border-gray-100 w-full max-w-sm mx-4 overflow-hidden">

            {/* Header */}
            <div className="px-5 pt-5 pb-4 border-b border-gray-100">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-semibold text-gray-900">Export PDF</h2>
                  <p className="text-xs text-gray-400 mt-0.5">Choose what to include</p>
                </div>
                <button
                  onClick={() => setShowDialog(false)}
                  className="w-7 h-7 flex items-center justify-center rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>
            </div>

            {/* Section toggles */}
            <div className="px-5 py-4 space-y-1">
              {SECTION_LABELS.filter(s => available.includes(s.key)).map(({ key, label, description }) => (
                <label
                  key={key}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-colors select-none
                    ${options[key] ? 'bg-primary-50 hover:bg-primary-50/80' : 'hover:bg-gray-50'}`}
                >
                  {/* Custom checkbox */}
                  <span className={`flex-none w-4 h-4 rounded border flex items-center justify-center transition-colors
                    ${options[key]
                      ? 'bg-primary-600 border-primary-600'
                      : 'border-gray-300 bg-white'}`}
                  >
                    {options[key] && (
                      <svg width="9" height="9" viewBox="0 0 12 12" fill="none">
                        <polyline points="2,6 5,9 10,3" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    )}
                  </span>
                  <input type="checkbox" className="sr-only" checked={options[key]} onChange={() => toggle(key)} />
                  <div className="flex-1 min-w-0">
                    <p className={`text-xs font-medium ${options[key] ? 'text-primary-700' : 'text-gray-700'}`}>{label}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{description}</p>
                  </div>
                </label>
              ))}
            </div>

            {/* Footer */}
            <div className="px-5 pb-5 flex items-center gap-2">
              <div className="flex gap-1.5 mr-auto">
                <button onClick={selectAll}  className="text-xs text-gray-400 hover:text-gray-600 transition-colors">All</button>
                <span className="text-gray-200">·</span>
                <button onClick={selectNone} className="text-xs text-gray-400 hover:text-gray-600 transition-colors">None</button>
              </div>

              <button
                onClick={() => setShowDialog(false)}
                className="px-3 py-1.5 text-xs font-medium text-gray-500 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>

              <button
                onClick={handleExport}
                disabled={exporting || selectedCount === 0}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-primary-600 hover:bg-primary-700 text-white rounded-md transition-colors disabled:opacity-50"
              >
                {exporting ? (
                  <>
                    <svg className="animate-spin" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
                    </svg>
                    Preparing…
                  </>
                ) : (
                  <>
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                      <polyline points="14 2 14 8 20 8"/>
                    </svg>
                    Export {selectedCount > 0 ? `(${selectedCount})` : ''}
                  </>
                )}
              </button>
            </div>

          </div>
        </div>
      )}
    </>
  )
}


// ── PDF generation logic ──────────────────────────────────────────────────────

function escHtml(s: string) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function markdownTableToHtml(md: string): string {
  const lines = md.trim().split('\n')
  if (lines.length < 2) return `<pre>${escHtml(md)}</pre>`

  const rows = lines
    .filter((l) => !l.match(/^\s*\|?[-:]+[-| :]*\|?\s*$/))
    .map((l) =>
      '<tr>' +
      l.split('|')
        .map((c) => c.trim())
        .filter((_, i, arr) => i > 0 && i < arr.length - 1)
        .map((c) => `<td>${escHtml(c)}</td>`)
        .join('') +
      '</tr>'
    )

  if (rows.length === 0) return `<pre>${escHtml(md)}</pre>`

  const [head, ...body] = rows
  const headerRow = head.replace(/<td>/g, '<th>').replace(/<\/td>/g, '</th>')
  return `<table><thead>${headerRow}</thead><tbody>${body.join('')}</tbody></table>`
}

async function captureChartImages(_chartTitles: string[]): Promise<Record<string, string>> {
  const images: Record<string, string> = {}
  const cards = document.querySelectorAll<HTMLElement>('[data-chart-title]')
  cards.forEach((card) => {
    const title = card.getAttribute('data-chart-title') ?? ''
    const canvas = card.querySelector('canvas')
    if (canvas) images[title] = canvas.toDataURL('image/png')
  })
  return images
}

async function exportPdf(
  data: QueryResponse,
  filename: string,
  question: string | null,
  options: ExportOptions,
) {
  const allCharts = [...(data.charts ?? []), ...(data.interesting_charts ?? [])]
  const chartImages = options.charts ? await captureChartImages(allCharts.map((c) => c.title)) : {}

  const dateStr = new Date().toLocaleDateString('en-GB', {
    year: 'numeric', month: 'short', day: 'numeric',
  })

  const chartsHtml = options.charts ? allCharts.map((chart) => {
    const img = chartImages[chart.title]
    return `
      <div class="chart-block">
        <p class="chart-title">${escHtml(chart.title)}</p>
        ${img ? `<img src="${img}" class="chart-img" />` : '<p class="muted">Chart not available</p>'}
      </div>`
  }).join('') : ''

  const resultSections = data.result
    ? data.result.split(/\n\n(?=\[)/).map((section) => {
        const match = section.match(/^\[(.+?)\]\n([\s\S]*)/)
        if (match) return { label: match[1], content: match[2] }
        return { label: '', content: section }
      })
    : []

  const dataHtml = options.data ? resultSections.map(({ label, content }) => `
    ${label ? `<h3>${escHtml(label)}</h3>` : ''}
    ${markdownTableToHtml(content)}
  `).join('') : ''

  const interestingHtml = options.interesting && data.interesting_result ? `
    <h2>Interesting findings <span class="badge purple">Pass 2</span></h2>
    ${data.interesting_reason ? `<p class="reason">${escHtml(data.interesting_reason)}</p>` : ''}
    ${markdownTableToHtml(data.interesting_result)}
  ` : ''

  const codeHtml = options.code && data.code ? `
    <h2>Generated code <span class="badge gray">Python</span></h2>
    <pre class="code">${escHtml(data.code)}</pre>
  ` : ''

  const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>Export — ${escHtml(filename)}</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 12px; color: #1a1a1a; padding: 40px; line-height: 1.6; }
  h1   { font-size: 18px; font-weight: 600; margin-bottom: 4px; }
  h2   { font-size: 14px; font-weight: 600; margin: 28px 0 10px; color: #111; }
  h3   { font-size: 12px; font-weight: 600; margin: 16px 0 6px; color: #444; }
  .meta  { font-size: 11px; color: #888; margin-bottom: 32px; }
  .badge { font-size: 10px; font-weight: 500; padding: 1px 7px; border-radius: 99px; }
  .badge.amber  { background: #fef3c7; color: #92400e; }
  .badge.gray   { background: #f3f4f6; color: #6b7280; }
  .badge.purple { background: #f5f3ff; color: #6d28d9; }
  .insight-box { background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 14px 16px; margin-bottom: 8px; font-size: 13px; line-height: 1.7; }
  .reason { font-size: 11px; color: #6b7280; font-style: italic; margin-bottom: 8px; }
  table { width: 100%; border-collapse: collapse; font-size: 11px; margin-bottom: 8px; }
  th    { background: #f9fafb; text-align: left; padding: 5px 8px; border: 1px solid #e5e7eb; font-weight: 600; color: #374151; }
  td    { padding: 4px 8px; border: 1px solid #e5e7eb; color: #374151; }
  tr:nth-child(even) td { background: #f9fafb; }
  pre   { background: #f8f8f8; border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; font-size: 10.5px; overflow-wrap: break-word; white-space: pre-wrap; }
  .chart-block { margin: 12px 0; page-break-inside: avoid; }
  .chart-title { font-size: 11px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }
  .chart-img   { max-width: 100%; border: 1px solid #e5e7eb; border-radius: 8px; }
  .muted { color: #9ca3af; font-size: 11px; }
  @media print { body { padding: 20px; } }
</style>
</head>
<body>

<h1>${escHtml(filename)}</h1>
<p class="meta">
  ${question ? `Query: <em>"${escHtml(question)}"</em> &nbsp;·&nbsp;` : 'Auto-explore &nbsp;·&nbsp; '}
  Exported ${dateStr}
</p>

${options.insight && data.insight ? `
<h2>Insight <span class="badge amber">AI summary</span></h2>
<div class="insight-box">${escHtml(data.insight)}</div>
` : ''}

${options.charts && allCharts.length > 0 ? `<h2>Charts <span class="badge gray">${allCharts.length}</span></h2>${chartsHtml}` : ''}

${options.data ? `
<h2>Data <span class="badge gray">Pass 1</span></h2>
${data.explore_reason ? `<p class="reason">${escHtml(data.explore_reason)}</p>` : ''}
${dataHtml}
` : ''}

${interestingHtml}
${codeHtml}

</body>
</html>`

  const win = window.open('', '_blank')
  if (!win) { alert('Please allow popups to export PDF.'); return }
  win.document.write(html)
  win.document.close()
  win.onload = () => { setTimeout(() => { win.print() }, 400) }
}