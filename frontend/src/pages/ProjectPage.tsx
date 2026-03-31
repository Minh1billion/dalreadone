import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useFilePanel } from '../hooks/useFilePanel'
import { useEDA } from '../hooks/useEDA'
import { FilePanelSidebar } from '../components/projects/FilePanelSidebar'
import { EDAResultDashboard } from '../components/projects/eda/EDAResultDashboard'

const EDA_STEPS = [
  { key: 'schema',                 label: 'Schema profile' },
  { key: 'missing_and_duplicates', label: 'Missing & duplicates' },
  { key: 'univariate',             label: 'Univariate stats' },
  { key: 'datetime',               label: 'Datetime analysis' },
  { key: 'correlations',           label: 'Correlations' },
  { key: 'distributions',          label: 'Distributions' },
  { key: 'data_quality_score',     label: 'Quality score' },
]

function stepIndex(key: string | null) {
  if (!key) return -1
  return EDA_STEPS.findIndex((s) => s.key === key)
}

export default function ProjectPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const pid = Number(projectId)

  const [activeFileId, setActiveFileId] = useState<number | null>(null)

  const panel = useFilePanel({
    projectId: pid,
    activeFileId,
    onSelectFile: (id) => { setActiveFileId(id || null); eda.reset() },
  })

  const eda = useEDA(activeFileId)
  const currentStepIdx = stepIndex(eda.step)

  const activeFile = panel.files.find((f: any) => f.id === activeFileId)

  return (
    <div className="flex h-[calc(100vh-56px)] bg-gray-50">

      <FilePanelSidebar
        files={panel.files}
        activeFileId={activeFileId}
        isLoading={panel.isLoading}
        isUploading={panel.isUploading}
        uploadProgress={panel.uploadProgress ?? 0}
        uploadError={panel.uploadError}
        inputRef={panel.inputRef}
        onSelectFile={(id) => {
          const newId = id === activeFileId ? null : id
          setActiveFileId(newId)
          eda.reset()
        }}
        onDelete={panel.handleDelete}
        onTriggerFilePicker={panel.triggerFilePicker}
        onFileChange={panel.handleFileChange}
      />

      {/* ── Main ── */}
      <main className="flex-1 overflow-y-auto p-6">
        {!activeFileId ? (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm">
            Select a file to get started
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-6">

            {/* Preview */}
            <section className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-gray-700">Preview</h2>
                {panel.preview && (
                  <span className="text-xs text-gray-400">
                    {panel.preview.n_rows.toLocaleString()} rows × {panel.preview.n_cols} cols
                  </span>
                )}
              </div>
              {panel.previewLoading ? (
                <div className="p-5 text-xs text-gray-400 animate-pulse">Loading preview…</div>
              ) : panel.previewError ? (
                <div className="p-5 text-xs text-red-500">{panel.previewError}</div>
              ) : panel.preview ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="bg-gray-50">
                        {panel.preview.columns.map((col: string) => (
                          <th key={col} className="px-3 py-2 text-left font-medium text-gray-500 whitespace-nowrap border-b border-gray-100">{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {panel.preview.rows.slice(0, 10).map((row: any, i: number) => (
                        <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}>
                          {panel.preview!.columns.map((col: string) => (
                            <td key={col} className="px-3 py-2 text-gray-600 whitespace-nowrap max-w-40 truncate border-b border-gray-50">
                              {row[col] == null ? <span className="text-gray-300">—</span> : String(row[col])}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : null}
            </section>

            {/* EDA */}
            <section className="bg-white rounded-xl border border-gray-100 shadow-sm">
              <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-gray-700">EDA Analysis</h2>
                {!eda.isRunning && (
                  <button onClick={eda.start} disabled={eda.starting}
                    className="text-xs px-3 py-1.5 rounded-md bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 transition-colors">
                    {eda.starting ? 'Starting…' : eda.isDone ? 'Re-run' : 'Run EDA'}
                  </button>
                )}
              </div>

              <div className="p-5">
                {!eda.taskId && !eda.starting && !eda.startError && (
                  <p className="text-sm text-gray-400 text-center py-6">Click "Run EDA" to analyze this file.</p>
                )}
                {eda.startError && (
                  <p className="text-sm text-red-500 py-2">{eda.startError}</p>
                )}

                {(eda.isRunning || eda.starting) && (
                  <div className="space-y-5">
                    <div>
                      <div className="flex justify-between text-xs text-gray-500 mb-1.5">
                        <span>{eda.step ? EDA_STEPS.find(s => s.key === eda.step)?.label ?? eda.step : 'Starting…'}</span>
                        <span>{eda.progress}%</span>
                      </div>
                      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div className="h-full bg-primary-500 rounded-full transition-all duration-500"
                          style={{ width: `${eda.progress}%` }} />
                      </div>
                    </div>
                    <ol className="space-y-1.5">
                      {EDA_STEPS.map((s, i) => {
                        const done = i < currentStepIdx, active = i === currentStepIdx
                        return (
                          <li key={s.key} className="flex items-center gap-3 text-xs">
                            <span className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 text-[10px] font-medium transition-colors ${
                              done ? 'bg-primary-500 text-white' : active ? 'bg-primary-100 text-primary-700 ring-2 ring-primary-400' : 'bg-gray-100 text-gray-400'
                            }`}>{done ? '✓' : i + 1}</span>
                            <span className={done ? 'text-gray-500 line-through' : active ? 'text-primary-700 font-medium' : 'text-gray-400'}>
                              {s.label}
                            </span>
                            {active && <span className="ml-auto text-[10px] text-primary-500 animate-pulse">running</span>}
                          </li>
                        )
                      })}
                    </ol>
                  </div>
                )}

                {eda.isError && (
                  <div className="rounded-lg bg-red-50 border border-red-100 p-4 text-sm text-red-600">
                    <p className="font-medium mb-1">Analysis failed</p>
                    <p className="text-xs text-red-500">{eda.edaError}</p>
                    <button onClick={eda.start} className="mt-3 text-xs underline text-red-600 hover:text-red-700">Retry</button>
                  </div>
                )}

                {eda.isDone && eda.result && (
                  <EDAResultDashboard
                    result={eda.result}
                    filename={activeFile?.filename}
                  />
                )}
              </div>
            </section>

          </div>
        )}
      </main>
    </div>
  )
}