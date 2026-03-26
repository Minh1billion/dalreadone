import { useEffect, useRef } from 'react'
import { Chart as ChartJS, registerables } from 'chart.js'
import type { Chart as ChartType } from '../../api/query'

ChartJS.register(...registerables)

interface Props {
  chart: ChartType
}

export default function ChartCard({ chart }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const instanceRef = useRef<ChartJS | null>(null)

  useEffect(() => {
    if (!canvasRef.current) return
    instanceRef.current?.destroy()

    const ctx = canvasRef.current.getContext('2d')!
    const { type, labels, data, series_labels } = chart

    // ── Build dataset(s) ──────────────────────────────────────────────
    const PALETTE = [
      '#d97706', '#f59e0b', '#fbbf24',
      '#a78bfa', '#60a5fa', '#34d399',
      '#f87171', '#fb923c', '#a3e635',
    ]

    let datasets: any[]

    if (type === 'grouped_bar') {
      datasets = (data as number[][]).map((series, i) => ({
        label: series_labels?.[i] ?? `Series ${i + 1}`,
        data: series,
        backgroundColor: PALETTE[i % PALETTE.length] + 'cc',
        borderColor: PALETTE[i % PALETTE.length],
        borderWidth: 1,
        borderRadius: 4,
      }))
    } else if (type === 'scatter') {
      const points = (data as [number, number][]).map(([x, y]) => ({ x, y }))
      datasets = [{
        label: chart.title,
        data: points,
        backgroundColor: '#d97706aa',
        borderColor: '#d97706',
        pointRadius: 5,
        pointHoverRadius: 7,
      }]
    } else if (type === 'pie') {
      datasets = [{
        data: data as number[],
        backgroundColor: PALETTE.slice(0, labels.length).map(c => c + 'cc'),
        borderColor: PALETTE.slice(0, labels.length),
        borderWidth: 1,
      }]
    } else {
      // bar | line | histogram
      datasets = [{
        label: chart.title,
        data: data as number[],
        backgroundColor: type === 'line' ? '#d97706' : '#d97706cc',
        borderColor: '#d97706',
        borderWidth: type === 'line' ? 2 : 1,
        borderRadius: type === 'bar' || type === 'histogram' ? 4 : 0,
        fill: type === 'line',
        tension: type === 'line' ? 0.4 : 0,
        pointRadius: type === 'line' ? 3 : 0,
      }]
    }

    const chartType = type === 'histogram' ? 'bar'
      : type === 'grouped_bar' ? 'bar'
      : type

    instanceRef.current = new ChartJS(ctx, {
      type: chartType as any,
      data: {
        labels: type === 'scatter' ? undefined : labels,
        datasets,
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            display: type === 'grouped_bar' || type === 'pie',
            position: 'bottom',
            labels: {
              color: '#6b7280',
              font: { size: 11 },
              boxWidth: 10,
              padding: 12,
            },
          },
          title: { display: false },
          tooltip: {
            backgroundColor: '#1f2937',
            titleColor: '#f9fafb',
            bodyColor: '#d1d5db',
            borderColor: '#374151',
            borderWidth: 1,
            padding: 10,
            cornerRadius: 6,
          },
        },
        scales: type === 'pie' ? {} : {
          x: {
            ticks: {
              color: '#9ca3af',
              font: { size: 10 },
              maxRotation: 40,
              maxTicksLimit: 12,
            },
            grid: { color: '#f3f4f6' },
          },
          y: {
            ticks: { color: '#9ca3af', font: { size: 10 } },
            grid: { color: '#f3f4f6' },
          },
        },
      },
    })

    return () => { instanceRef.current?.destroy() }
  }, [chart])

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <p className="text-xs font-medium text-gray-500 mb-3 uppercase tracking-wide">
        {chart.title}
      </p>
      <canvas ref={canvasRef} />
    </div>
  )
}