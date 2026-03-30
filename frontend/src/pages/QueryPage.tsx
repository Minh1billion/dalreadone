import { useState, useRef, useCallback, useEffect } from 'react'
import { useQueryPage } from '../hooks/useQueryPage'
import { useQueryHistory } from '../hooks/useQueryHistory'
import FilePanel from '../components/query/FilePanel'
import HistoryPanel from '../components/query/HistoryPanel'
import ResultPanel from '../components/query/ResultPanel'
import ExportPdfButton from '../components/query/ExportPdfButton'
import StopwordsEditor from '../components/query/StopwordsEditor'
import { IconBack, IconSend } from '../components/ui/icons'
import type { QueryResponse } from '../api/query'

const MIN_LEFT_PX = 220
const MAX_LEFT_PX = 520
const DEFAULT_LEFT_PX = 320

type LeftTab = 'files' | 'history'

export default function QueryPage() {
  const {
    pid,
    activeFileId,
    question,
    setQuestion,
    stopwords,
    setStopwords,
    handleSelectFile,
    handleSubmit: _handleSubmit,
    handleKeyDown,
    handleBack,
    data: liveData,
    loading,
    error,
  } = useQueryPage()

  const history = useQueryHistory()

  // ── History-view state ─────────────────────────────────────────────────────
  const [historicalResult, setHistoricalResult] = useState<QueryResponse | null>(null)
  const [historicalMeta, setHistoricalMeta] = useState<{
    id: number; question: string | null; filename: string
  } | null>(null)

  const [activeFilename, setActiveFilename] = useState('')

  const displayData     = historicalResult ?? liveData
  const displayQuestion = historicalMeta?.question ?? question
  const displayFilename = historicalMeta?.filename ?? activeFilename

  function handleSelectHistoryItem(
    result: QueryResponse,
    meta: { id: number; question: string | null; filename: string; file_id: number }
  ) {
    setHistoricalResult(result)
    setHistoricalMeta(meta)
    history.setViewingId(meta.id)
    setMobileLeftOpen(false)
  }

  function clearHistoricalResult() {
    setHistoricalResult(null)
    setHistoricalMeta(null)
    history.setViewingId(null)
  }

  function handleRerun({ file_id, question: q }: { file_id: number; question: string | null }) {
    clearHistoricalResult()
    handleSelectFile(file_id)
    setQuestion(q ?? '')
    setLeftTab('files')
    setMobileLeftOpen(false)
  }

  useEffect(() => {
    if (liveData) clearHistoricalResult()
  }, [liveData])

  // ── Left panel tab ──────────────────────────────────────────────────────────
  const [leftTab, setLeftTab] = useState<LeftTab>('files')

  // ── Drag-to-resize ──────────────────────────────────────────────────────────
  const [leftWidth, setLeftWidth] = useState(DEFAULT_LEFT_PX)
  const [dragging, setDragging] = useState(false)
  const dragStartX = useRef(0)
  const dragStartWidth = useRef(DEFAULT_LEFT_PX)

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    dragStartX.current = e.clientX
    dragStartWidth.current = leftWidth
    setDragging(true)
  }, [leftWidth])

  useEffect(() => {
    if (!dragging) return
    const onMove = (e: MouseEvent) => {
      const delta = e.clientX - dragStartX.current
      const next = Math.min(MAX_LEFT_PX, Math.max(MIN_LEFT_PX, dragStartWidth.current + delta))
      setLeftWidth(next)
    }
    const onUp = () => setDragging(false)
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
  }, [dragging])

  // ── Mobile overlay ──────────────────────────────────────────────────────────
  const [mobileLeftOpen, setMobileLeftOpen] = useState(false)

  // ── Submit ──────────────────────────────────────────────────────────────────
  function handleSubmit(e: React.FormEvent) {
    _handleSubmit(e)
    setMobileLeftOpen(false)
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">

      {/* Top bar */}
      <div className="flex-none border-b border-gray-200 bg-white px-5 py-3 flex items-center gap-3">
        <button
          onClick={() => setMobileLeftOpen(o => !o)}
          className="md:hidden flex items-center justify-center w-8 h-8 rounded-md text-gray-500 hover:bg-gray-100 transition-colors"
          aria-label="Toggle panel"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="3" width="7" height="18" rx="1"/><rect x="14" y="3" width="7" height="18" rx="1"/>
          </svg>
        </button>

        <button onClick={handleBack} className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-900 transition-colors">
          <IconBack />
          <span className="hidden sm:inline">Projects</span>
        </button>
        <span className="text-gray-300">/</span>
        <span className="text-sm font-medium text-gray-900">Query</span>

        {displayData && (
          <div className="ml-auto">
            <ExportPdfButton
              data={displayData}
              filename={displayFilename}
              question={displayQuestion}
            />
          </div>
        )}
      </div>

      {/* Main split */}
      <div
        className="flex-1 flex overflow-hidden relative"
        style={{ userSelect: dragging ? 'none' : undefined }}
      >

        {/* ── LEFT PANEL ───────────────────────────────────────────────────── */}
        <div
          className={`
            flex-none flex flex-col bg-white border-r border-gray-200 min-w-0
            absolute inset-y-0 left-0 z-20 w-72
            md:static md:z-auto
            transition-transform duration-200
            ${mobileLeftOpen ? 'translate-x-0' : '-translate-x-full'}
            md:translate-x-0
          `}
          style={{ width: `${leftWidth}px` }}
        >
          {/* Mobile backdrop */}
          <div
            className={`md:hidden fixed inset-0 bg-black/20 z-10 transition-opacity ${mobileLeftOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}
            onClick={() => setMobileLeftOpen(false)}
          />

          <div className="relative z-20 flex flex-col h-full bg-white">

            {/* ── Tabs ──────────────────────────────────────────────────── */}
            <div className="flex-none flex border-b border-gray-200">
              {(['files', 'history'] as LeftTab[]).map((tab) => (
                <button
                  key={tab}
                  onClick={() => {
                    setLeftTab(tab)
                    if (tab === 'history') history.fetchList()
                  }}
                  className={`flex-1 py-2.5 text-xs font-medium transition-colors capitalize
                    ${leftTab === tab
                      ? 'text-primary-700 border-b-2 border-primary-600'
                      : 'text-gray-500 hover:text-gray-700'
                    }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* ── Files tab ─────────────────────────────────────────────── */}
            {leftTab === 'files' && (
              <>
                <div className="flex-none border-b border-gray-100 p-4">
                  <FilePanel
                    projectId={pid}
                    activeFileId={activeFileId}
                    onSelectFile={(id) => {
                      handleSelectFile(id)
                      setActiveFilename('')
                    }}
                  />
                </div>

                <div className="flex-1 flex flex-col p-4 gap-3 min-h-0 overflow-y-auto">
                  <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wide">
                    Question
                  </label>

                  {!activeFileId && (
                    <div className="flex items-start gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-md px-2.5 py-2">
                      <svg className="flex-none mt-0.5" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                      </svg>
                      Select a file first.
                    </div>
                  )}

                  <form onSubmit={handleSubmit} className="flex flex-col gap-3">
                    <textarea
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder={activeFileId
                        ? 'e.g. "Which category has the most revenue?" (Enter to run)'
                        : 'Select a file to enable querying...'
                      }
                      disabled={!activeFileId || loading}
                      rows={5}
                      className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-xs placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-shadow resize-none disabled:bg-gray-50 disabled:text-gray-400"
                    />

                    {/* ── Stopwords editor — only when a file is selected ── */}
                    {activeFileId && (
                      <StopwordsEditor
                        value={stopwords}
                        onChange={setStopwords}
                      />
                    )}

                    <div className="flex flex-col gap-2">
                      <button
                        type="submit"
                        disabled={!activeFileId || loading}
                        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white text-xs font-medium rounded-md transition-colors disabled:opacity-50"
                      >
                        <IconSend loading={loading} />
                        {loading ? 'Analysing...' : 'Run'}
                      </button>
                      <p className="text-xs text-gray-400 text-center">Leave blank to auto-explore.</p>
                    </div>

                    {error && (
                      <p className="text-xs text-red-500 bg-red-50 border border-red-200 rounded-md px-3 py-2">{error}</p>
                    )}
                  </form>
                </div>
              </>
            )}

            {/* ── History tab ───────────────────────────────────────────── */}
            {leftTab === 'history' && (
              <div className="flex-1 overflow-y-auto p-3 min-h-0">
                <HistoryPanel
                  onSelect={handleSelectHistoryItem}
                  onRerun={handleRerun}
                  activeId={history.viewingId}
                />
              </div>
            )}
          </div>
        </div>

        {/* ── DRAG HANDLE ─────────────────────────────────────────────────── */}
        <div
          onMouseDown={onMouseDown}
          className={`hidden md:flex flex-none w-1.5 cursor-col-resize items-center justify-center hover:bg-primary-100 active:bg-primary-200 transition-colors ${dragging ? 'bg-primary-200' : 'bg-transparent'}`}
        >
          <div className="flex flex-col gap-1 opacity-30">
            {[...Array(4)].map((_, i) => <div key={i} className="w-1 h-1 rounded-full bg-gray-500" />)}
          </div>
        </div>

        {/* ── RIGHT PANEL ─────────────────────────────────────────────────── */}
        <div className="flex-1 overflow-y-auto min-w-0">

          {historicalResult && (
            <div className="flex items-center gap-2 px-5 py-2 bg-amber-50 border-b border-amber-100 text-xs text-amber-700">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
              </svg>
              Viewing historical result
              <button
                onClick={clearHistoricalResult}
                className="ml-auto text-amber-600 hover:text-amber-800 font-medium"
              >
                Back to live
              </button>
            </div>
          )}

          {loading ? (
            <div className="flex flex-col items-center justify-center h-full gap-3 text-center px-8">
              {liveData ? (
                <div className="w-full h-full relative">
                  <div className="absolute inset-0 bg-white/70 backdrop-blur-sm z-10 flex flex-col items-center justify-center gap-3">
                    <div className="w-10 h-10 rounded-full border-2 border-primary-600 border-t-transparent animate-spin" />
                    <p className="text-sm font-medium text-gray-700">Analysing your data...</p>
                    <p className="text-xs text-gray-400 max-w-xs">Running multi-pass exploration.</p>
                  </div>
                  <div className="p-5 opacity-40 pointer-events-none">
                    <ResultPanel data={liveData} />
                  </div>
                </div>
              ) : (
                <>
                  <div className="w-10 h-10 rounded-full border-2 border-primary-600 border-t-transparent animate-spin" />
                  <p className="text-sm font-medium text-gray-700">Analysing your data...</p>
                  <p className="text-xs text-gray-400 max-w-xs">Running multi-pass exploration. This may take a few seconds.</p>
                </>
              )}
            </div>
          ) : displayData ? (
            <div className="p-5">
              {displayQuestion && (
                <div className="mb-4 flex items-start gap-2">
                  <span className="mt-0.5 text-xs font-semibold text-primary-600 bg-primary-50 border border-primary-100 rounded px-1.5 py-0.5">Q</span>
                  <p className="text-sm text-gray-800 font-medium">{displayQuestion}</p>
                </div>
              )}
              <ResultPanel data={displayData} />
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center px-8 gap-3">
              <div className="w-14 h-14 bg-gray-100 rounded-2xl flex items-center justify-center text-gray-400">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  <line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/>
                </svg>
              </div>
              <p className="text-sm font-medium text-gray-700">Results will appear here</p>
              <p className="text-xs text-gray-400 max-w-xs">Select a file, type a question (or leave blank), then press Run.</p>
            </div>
          )}
        </div>

      </div>
    </div>
  )
}