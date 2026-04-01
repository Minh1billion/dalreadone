import { useState, useRef, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { useFilePanel } from '../hooks/useFilePanel'
import { useEDA } from '../hooks/useEDA'
import { usePreprocess } from '../hooks/usePreprocess'
import { FilePanelSidebar } from '../components/projects/FilePanelSidebar'
import { EDASection } from '../components/projects/eda/EDASection'
import { PreprocessSection } from '../components/projects/preprocess/PreprocessSection'

const SIDEBAR_MIN     = 180
const SIDEBAR_MAX     = 480
const SIDEBAR_DEFAULT = 256

export default function ProjectPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const pid = Number(projectId)

  const [activeFileId, setActiveFileId] = useState<number | null>(null)
  const [sidebarWidth, setSidebarWidth] = useState(SIDEBAR_DEFAULT)
  const dragging = useRef(false)
  const startX   = useRef(0)
  const startW   = useRef(0)

  const panel = useFilePanel({
    projectId: pid,
    activeFileId,
    onSelectFile: (id) => { setActiveFileId(id || null); eda.reset(); preprocess.reset() },
  })

  const eda        = useEDA(activeFileId)
  const preprocess = usePreprocess(activeFileId)
  const activeFile = panel.files.find((f: any) => f.id === activeFileId)

  const onDragStart = useCallback((e: React.MouseEvent) => {
    dragging.current = true
    startX.current   = e.clientX
    startW.current   = sidebarWidth

    const onMove = (e: MouseEvent) => {
      if (!dragging.current) return
      setSidebarWidth(Math.min(SIDEBAR_MAX, Math.max(SIDEBAR_MIN, startW.current + e.clientX - startX.current)))
    }
    const onUp = () => {
      dragging.current = false
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup',   onUp)
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup',   onUp)
  }, [sidebarWidth])

  return (
    <div className='flex h-[calc(100vh-56px)] bg-gray-50 overflow-hidden select-none'>

      <div style={{ width: sidebarWidth }} className='shrink-0 h-full'>
        <FilePanelSidebar
          files={panel.files}
          activeFileId={activeFileId}
          isLoading={panel.isLoading}
          isUploading={panel.isUploading}
          uploadProgress={panel.uploadProgress ?? 0}
          uploadError={panel.uploadError}
          inputRef={panel.inputRef}
          onSelectFile={(id) => { setActiveFileId(id === activeFileId ? null : id); eda.reset(); preprocess.reset() }}
          onDelete={panel.handleDelete}
          onTriggerFilePicker={panel.triggerFilePicker}
          onFileChange={panel.handleFileChange}
        />
      </div>

      <div
        onMouseDown={onDragStart}
        className='w-1 shrink-0 h-full cursor-col-resize bg-transparent hover:bg-primary-200 active:bg-primary-300 transition-colors'
      />

      <main className='flex-1 overflow-y-auto p-6 min-w-0'>
        {!activeFileId ? (
          <div className='flex items-center justify-center h-full text-gray-400 text-sm'>
            Select a file to get started
          </div>
        ) : (
          <div className='max-w-4xl mx-auto space-y-4'>

            <section className='bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden'>
              <div className='px-5 py-3 border-b border-gray-100 flex items-center justify-between'>
                <h2 className='text-sm font-semibold text-gray-700'>Preview</h2>
                {panel.preview && (
                  <span className='text-xs text-gray-400'>
                    {panel.preview.n_rows.toLocaleString()} rows × {panel.preview.n_cols} cols
                  </span>
                )}
              </div>
              {panel.previewLoading ? (
                <div className='p-5 text-xs text-gray-400 animate-pulse'>Loading preview…</div>
              ) : panel.previewError ? (
                <div className='p-5 text-xs text-red-500'>{panel.previewError}</div>
              ) : panel.preview ? (
                <div className='overflow-x-auto'>
                  <table className='w-full text-xs'>
                    <thead>
                      <tr className='bg-gray-50'>
                        {panel.preview.columns.map((col: string) => (
                          <th key={col} className='px-3 py-2 text-left font-medium text-gray-500 whitespace-nowrap border-b border-gray-100'>
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {panel.preview.rows.slice(0, 10).map((row: any, i: number) => (
                        <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}>
                          {panel.preview!.columns.map((col: string) => (
                            <td key={col} className='px-3 py-2 text-gray-600 whitespace-nowrap max-w-40 truncate border-b border-gray-50'>
                              {row[col] == null ? <span className='text-gray-300'>—</span> : String(row[col])}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : null}
            </section>

            <EDASection eda={eda} activeFile={activeFile} />

            <PreprocessSection
              preprocess={preprocess}
              preview={panel.preview}
              onConfirmSuccess={panel.triggerRefresh}
            />

          </div>
        )}
      </main>
    </div>
  )
}