import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useRunQuery } from '../hooks/useRunQuery'
import FilePanel from '../components/query/FilePanel'
import ResultPanel from '../components/query/ResultPanel'
import { IconBack, IconSend } from '../components/ui/icons'

export default function QueryPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()

  const [activeFileId, setActiveFileId] = useState<number | null>(null)
  const [question, setQuestion] = useState('')

  const pid = Number(projectId)
  const { data, loading, error, run, reset } = useRunQuery(pid, activeFileId)

  function handleSelectFile(id: number) {
    setActiveFileId(id || null)
    reset()
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!activeFileId) return
    await run(question)
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as any)
    }
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">

      {/* ── Top bar ── */}
      <div className="flex-none border-b border-gray-200 bg-white px-5 py-3 flex items-center gap-3">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-900 transition-colors"
        >
          <IconBack />
          Projects
        </button>
        <span className="text-gray-300">/</span>
        <span className="text-sm font-medium text-gray-900">Query</span>
      </div>

      {/* ── Split layout: 25 / 75 ── */}
      <div className="flex-1 flex overflow-hidden">

        {/* ── LEFT 25%: Files + Query input ── */}
        <div className="w-1/4 border-r border-gray-200 flex flex-col bg-white min-w-0">

          {/* File panel */}
          <div className="flex-none border-b border-gray-100 p-4">
            <FilePanel
              projectId={pid}
              activeFileId={activeFileId}
              onSelectFile={handleSelectFile}
            />
          </div>

          {/* Query input */}
          <div className="flex-1 flex flex-col p-4 min-h-0">
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">
              Question
            </label>

            {!activeFileId && (
              <div className="mb-3 flex items-start gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-md px-2.5 py-2">
                <svg className="flex-none mt-0.5" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                Select a file first.
              </div>
            )}

            <form onSubmit={handleSubmit} className="flex flex-col gap-3 flex-1 min-h-0">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  activeFileId
                    ? 'e.g. "Which category has the most revenue?" (Enter to run)'
                    : 'Select a file to enable querying...'
                }
                disabled={!activeFileId || loading}
                rows={5}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-xs placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-shadow resize-none disabled:bg-gray-50 disabled:text-gray-400"
              />

              <div className="flex flex-col gap-2">
                <button
                  type="submit"
                  disabled={!activeFileId || loading}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white text-xs font-medium rounded-md transition-colors disabled:opacity-50"
                >
                  <IconSend loading={loading} />
                  {loading ? 'Analysing...' : 'Run'}
                </button>
                <p className="text-xs text-gray-400 text-center">
                  Leave blank to auto-explore.
                </p>
              </div>

              {error && (
                <p className="text-xs text-red-500 bg-red-50 border border-red-200 rounded-md px-3 py-2">
                  {error}
                </p>
              )}
            </form>
          </div>
        </div>

        {/* ── RIGHT 75%: Results ── */}
        <div className="w-3/4 overflow-y-auto">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-full gap-3 text-center px-8">
              <div className="w-10 h-10 rounded-full border-2 border-primary-600 border-t-transparent animate-spin" />
              <p className="text-sm font-medium text-gray-700">Analysing your data...</p>
              <p className="text-xs text-gray-400 max-w-xs">
                Running multi-pass exploration. This may take a few seconds.
              </p>
            </div>
          ) : data ? (
            <div className="p-5">
              {data.user_question && (
                <div className="mb-4 flex items-start gap-2">
                  <span className="mt-0.5 text-xs font-semibold text-primary-600 bg-primary-50 border border-primary-100 rounded px-1.5 py-0.5">Q</span>
                  <p className="text-sm text-gray-800 font-medium">{data.user_question}</p>
                </div>
              )}
              <ResultPanel data={data} />
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
              <p className="text-xs text-gray-400 max-w-xs">
                Select a file, type a question (or leave blank), then press Run.
              </p>
            </div>
          )}
        </div>

      </div>
    </div>
  )
}