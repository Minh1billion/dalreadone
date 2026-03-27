import { useState } from 'react'
import type { QueryResponse } from '../../api/query'

interface Props {
  data:     QueryResponse
  filename: string
  question: string | null
}


export default function ExportPdfButton({ data, filename, question }: Props) {
  const [exporting, setExporting] = useState(false)

  async function handleExport() {
    setExporting(true)
    try {
      await exportPdf(data, filename, question)
    } finally {
      setExporting(false)
    }
  }

  return (
    <button
      onClick={handleExport}
      disabled={exporting}
      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50"
    >
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="12" y1="18" x2="12" y2="12"/>
        <line x1="9" y1="15" x2="15" y2="15"/>
      </svg>
      {exporting ? 'Preparing…' : 'Export PDF'}
    </button>
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
    .filter((l) => !l.match(/^\s*\|?[-:]+[-| :]*\|?\s*$/))  // skip separator rows
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

  // Make first row a header
  const [head, ...body] = rows
  const headerRow = head.replace(/<td>/g, '<th>').replace(/<\/td>/g, '</th>')

  return `<table><thead>${headerRow}</thead><tbody>${body.join('')}</tbody></table>`
}

async function captureChartImages(
  _chartTitles: string[]
): Promise<Record<string, string>> {
  // Grab chart canvases from the live DOM by matching title text nearby
  const images: Record<string, string> = {}
  const cards = document.querySelectorAll<HTMLElement>('[data-chart-title]')
  cards.forEach((card) => {
    const title = card.getAttribute('data-chart-title') ?? ''
    const canvas = card.querySelector('canvas')
    if (canvas) {
      images[title] = canvas.toDataURL('image/png')
    }
  })
  return images
}

async function exportPdf(
  data: QueryResponse,
  filename: string,
  question: string | null
) {
  const allCharts = [...(data.charts ?? []), ...(data.interesting_charts ?? [])]
  const chartImages = await captureChartImages(allCharts.map((c) => c.title))

  const dateStr = new Date().toLocaleDateString('en-GB', {
    year: 'numeric', month: 'short', day: 'numeric',
  })

  const chartsHtml = allCharts.map((chart) => {
    const img = chartImages[chart.title]
    return `
      <div class="chart-block">
        <p class="chart-title">${escHtml(chart.title)}</p>
        ${img ? `<img src="${img}" class="chart-img" />` : '<p class="muted">Chart not available</p>'}
      </div>`
  }).join('')

  // Split result string into named sections
  const resultSections = data.result
    ? data.result.split(/\n\n(?=\[)/).map((section) => {
        const match = section.match(/^\[(.+?)\]\n([\s\S]*)/)
        if (match) return { label: match[1], content: match[2] }
        return { label: '', content: section }
      })
    : []

  const dataHtml = resultSections.map(({ label, content }) => `
    ${label ? `<h3>${escHtml(label)}</h3>` : ''}
    ${markdownTableToHtml(content)}
  `).join('')

  const interestingHtml = data.interesting_result ? `
    <h2>Interesting findings <span class="badge purple">Pass 2</span></h2>
    ${data.interesting_reason ? `<p class="reason">${escHtml(data.interesting_reason)}</p>` : ''}
    ${markdownTableToHtml(data.interesting_result)}
  ` : ''

  const codeHtml = data.code ? `
    <h2>Generated code <span class="badge gray">Python</span></h2>
    <pre class="code">${escHtml(data.code)}</pre>
  ` : ''

  const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>DALreaDone — ${escHtml(filename)}</title>
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

<h2>Insight <span class="badge amber">AI summary</span></h2>
<div class="insight-box">${escHtml(data.insight ?? '')}</div>

${allCharts.length > 0 ? `<h2>Charts <span class="badge gray">${allCharts.length}</span></h2>${chartsHtml}` : ''}

<h2>Data <span class="badge gray">Pass 1</span></h2>
${data.explore_reason ? `<p class="reason">${escHtml(data.explore_reason)}</p>` : ''}
${dataHtml}

${interestingHtml}
${codeHtml}

</body>
</html>`

  const win = window.open('', '_blank')
  if (!win) { alert('Please allow popups to export PDF.'); return }
  win.document.write(html)
  win.document.close()
  win.onload = () => {
    setTimeout(() => { win.print() }, 400)
  }
}