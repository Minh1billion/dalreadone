import { useEffect, useRef } from 'react'
import { Chart as ChartJS, registerables } from 'chart.js'
import type {
  Chart,
  StandardChart,
  WordCloudChart,
  SentimentDistributionChart,
  TopPhrasesChart,
} from '../../api/query'

ChartJS.register(...registerables)

// ── Seaborn-inspired palettes ─────────────────────────────────────────────────

const PALETTES = {
  deep: [
    '#4c72b0', '#dd8452', '#55a868', '#c44e52', '#8172b3',
    '#937860', '#da8bc3', '#8c8c8c', '#ccb974', '#64b5cd',
  ],
  muted: [
    '#4878d0', '#ee854a', '#6acc64', '#d65f5f', '#956cb4',
    '#8c613c', '#dc7ec0', '#797979', '#d5bb67', '#82c6e2',
  ],
  colorblind: [
    '#0173b2', '#de8f05', '#029e73', '#d55e00', '#cc78bc',
    '#ca9161', '#fbafe4', '#949494', '#ece133', '#56b4e9',
  ],
  pastel: [
    '#a1c9f4', '#ffb482', '#8de5a1', '#ff9f9b', '#d0bbff',
    '#debb9b', '#fab0e4', '#cfcfcf', '#fffea3', '#b9f2f0',
  ],
  dark: [
    '#001c7f', '#b1400d', '#12711c', '#8c0800', '#591e71',
    '#592f0d', '#a23582', '#3c3c3c', '#b8850a', '#006374',
  ],
}

function getPalette(title: string): string[] {
  const hash = title.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0)
  const keys = Object.keys(PALETTES) as (keyof typeof PALETTES)[]
  return PALETTES[keys[hash % keys.length]]
}

function withAlpha(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r},${g},${b},${alpha})`
}

// ── Shared card wrapper ───────────────────────────────────────────────────────

function ChartWrapper({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4" data-chart-title={title}>
      <p className="text-xs font-medium text-gray-500 mb-3 uppercase tracking-wide">{title}</p>
      {children}
    </div>
  )
}

// ── Standard Chart.js renderer ────────────────────────────────────────────────

function StandardChartCard({ chart }: { chart: StandardChart }) {
  const canvasRef   = useRef<HTMLCanvasElement>(null)
  const instanceRef = useRef<ChartJS | null>(null)

  useEffect(() => {
    if (!canvasRef.current) return
    instanceRef.current?.destroy()

    const ctx     = canvasRef.current.getContext('2d')!
    const { type, labels, data, series_labels, title } = chart
    const PALETTE = getPalette(title)

    let datasets: any[]

    if (type === 'grouped_bar') {
      datasets = (data as number[][]).map((series, i) => ({
        label:           series_labels?.[i] ?? `Series ${i + 1}`,
        data:            series,
        backgroundColor: withAlpha(PALETTE[i % PALETTE.length], 0.8),
        borderColor:     PALETTE[i % PALETTE.length],
        borderWidth:     1,
        borderRadius:    3,
      }))
    } else if (type === 'scatter') {
      const points = (data as [number, number][]).map(([x, y]) => ({ x, y }))
      datasets = [{
        label:           title,
        data:            points,
        backgroundColor: withAlpha(PALETTE[0], 0.65),
        borderColor:     PALETTE[0],
        pointRadius:     5,
        pointHoverRadius: 7,
      }]
    } else if (type === 'pie') {
      datasets = [{
        data:            data as number[],
        backgroundColor: PALETTE.slice(0, labels.length).map(c => withAlpha(c, 0.82)),
        borderColor:     PALETTE.slice(0, labels.length),
        borderWidth:     1,
      }]
    } else if (type === 'histogram') {
      datasets = [{
        label:           title,
        data:            data as number[],
        backgroundColor: PALETTE.slice(0, (data as number[]).length).map(c => withAlpha(c, 0.75)),
        borderColor:     PALETTE.slice(0, (data as number[]).length),
        borderWidth:     1,
        borderRadius:    2,
      }]
    } else if (type === 'line') {
      datasets = [{
        label:            title,
        data:             data as number[],
        backgroundColor:  withAlpha(PALETTE[0], 0.12),
        borderColor:      PALETTE[0],
        borderWidth:      2,
        fill:             true,
        tension:          0.4,
        pointRadius:      3,
        pointBackgroundColor: PALETTE[0],
        pointBorderColor: '#fff',
        pointBorderWidth: 1.5,
      }]
    } else {
      // bar — each bar gets its own palette colour
      datasets = [{
        label:           title,
        data:            data as number[],
        backgroundColor: (data as number[]).map((_, i) => withAlpha(PALETTE[i % PALETTE.length], 0.8)),
        borderColor:     (data as number[]).map((_, i) => PALETTE[i % PALETTE.length]),
        borderWidth:     1,
        borderRadius:    4,
      }]
    }

    const chartType = type === 'histogram' || type === 'grouped_bar' ? 'bar' : type

    instanceRef.current = new ChartJS(ctx, {
      type: chartType as any,
      data: { labels: type === 'scatter' ? undefined : labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            display:  type === 'grouped_bar' || type === 'pie',
            position: 'bottom',
            labels:   { color: '#6b7280', font: { size: 11 }, boxWidth: 10, padding: 12 },
          },
          title:   { display: false },
          tooltip: {
            backgroundColor: '#1f2937',
            titleColor:      '#f9fafb',
            bodyColor:       '#d1d5db',
            borderColor:     '#374151',
            borderWidth:     1,
            padding:         10,
            cornerRadius:    6,
          },
        },
        scales: type === 'pie' ? {} : {
          x: {
            ticks: { color: '#9ca3af', font: { size: 10 }, maxRotation: 40, maxTicksLimit: 12 },
            grid:  { color: '#f3f4f6' },
          },
          y: {
            ticks: { color: '#9ca3af', font: { size: 10 } },
            grid:  { color: '#f3f4f6' },
          },
        },
      },
    })

    return () => { instanceRef.current?.destroy() }
  }, [chart])

  return (
    <ChartWrapper title={chart.title}>
      <canvas ref={canvasRef} />
    </ChartWrapper>
  )
}

// ── WordCloud renderer ────────────────────────────────────────────────────────

function WordCloudCard({ chart }: { chart: WordCloudChart }) {
  const max    = Math.max(...chart.items.map(i => i.weight), 1)
  const COLORS = ['#4c72b0', '#dd8452', '#55a868', '#c44e52', '#8172b3', '#937860']

  return (
    <ChartWrapper title={chart.title}>
      <div className="flex flex-wrap gap-2 justify-center py-2">
        {chart.items.map((item, i) => {
          // Scale font size between 11px and 28px based on relative weight
          const size    = 11 + Math.round((item.weight / max) * 17)
          const color   = COLORS[i % COLORS.length]
          const opacity = 0.55 + (item.weight / max) * 0.45

          return (
            <span
              key={item.word}
              style={{ fontSize: size, color, opacity }}
              className="font-medium leading-tight cursor-default select-none"
              title={`weight: ${item.weight.toFixed(3)}`}
            >
              {item.word}
            </span>
          )
        })}
      </div>
    </ChartWrapper>
  )
}

// ── SentimentDistribution renderer ───────────────────────────────────────────

function SentimentDistributionCard({ chart }: { chart: SentimentDistributionChart }) {
  const segments = [
    { label: 'Positive', value: chart.positive, color: '#55a868', bg: 'bg-green-50',  text: 'text-green-700' },
    { label: 'Negative', value: chart.negative, color: '#c44e52', bg: 'bg-red-50',    text: 'text-red-700'   },
    { label: 'Neutral',  value: chart.neutral,  color: '#8c8c8c', bg: 'bg-gray-50',   text: 'text-gray-600'  },
  ]

  return (
    <ChartWrapper title={chart.title}>
      {/* Stacked bar */}
      <div className="flex h-6 rounded-full overflow-hidden mb-4">
        {segments.map(s =>
          s.value > 0 ? (
            <div
              key={s.label}
              style={{ width: `${s.value}%`, backgroundColor: s.color }}
              title={`${s.label}: ${s.value.toFixed(1)}%`}
            />
          ) : null
        )}
      </div>

      {/* Legend */}
      <div className="flex justify-around">
        {segments.map(s => (
          <div key={s.label} className={`flex flex-col items-center px-3 py-2 rounded-lg ${s.bg}`}>
            <span className={`text-lg font-bold ${s.text}`}>{s.value.toFixed(1)}%</span>
            <span className="text-xs text-gray-500 mt-0.5">{s.label}</span>
          </div>
        ))}
      </div>
    </ChartWrapper>
  )
}

// ── TopPhrases renderer (horizontal bar) ─────────────────────────────────────

function TopPhrasesCard({ chart }: { chart: TopPhrasesChart }) {
  const max = Math.max(...chart.data, 1)

  return (
    <ChartWrapper title={chart.title}>
      <div className="space-y-1.5">
        {chart.labels.map((label, i) => (
          <div key={label} className="flex items-center gap-2">
            <span className="text-xs text-gray-500 w-32 truncate flex-none text-right" title={label}>
              {label}
            </span>
            <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width:           `${(chart.data[i] / max) * 100}%`,
                  backgroundColor: '#4c72b0',
                  opacity:         0.7 + (chart.data[i] / max) * 0.3,
                }}
              />
            </div>
            <span className="text-xs text-gray-400 w-10 text-right flex-none">
              {typeof chart.data[i] === 'number' && chart.data[i] < 1
                ? chart.data[i].toFixed(3)
                : Math.round(chart.data[i])}
            </span>
          </div>
        ))}
      </div>
    </ChartWrapper>
  )
}

// ── Main dispatcher ───────────────────────────────────────────────────────────

interface Props {
  chart: Chart
}

export default function ChartCard({ chart }: Props) {
  switch (chart.type) {
    case 'wordcloud_data':
      return <WordCloudCard chart={chart} />
    case 'sentiment_distribution':
      return <SentimentDistributionCard chart={chart} />
    case 'top_phrases':
      return <TopPhrasesCard chart={chart} />
    default:
      return <StandardChartCard chart={chart as StandardChart} />
  }
}