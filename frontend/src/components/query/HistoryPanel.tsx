import { useEffect, useState } from 'react'
import { useQueryHistory } from '../../hooks/useQueryHistory'
import type { QueryResponse } from '../../api/query'
import type { HistoryListItem } from '../../api/history'

interface Props {
  onSelect: (result: QueryResponse, item: { id: number; question: string | null; filename: string; file_id: number }) => void
  onRerun:  (item: { file_id: number; question: string | null }) => void
  activeId: number | null
}

function TimeAgo({ iso }: { iso: string }) {
  const diff  = Date.now() - new Date(iso).getTime()
  const mins  = Math.floor(diff / 60_000)
  const hours = Math.floor(diff / 3_600_000)
  const days  = Math.floor(diff / 86_400_000)
  if (mins < 1)  return <span>just now</span>
  if (hours < 1) return <span>{mins}m ago</span>
  if (days < 1)  return <span>{hours}h ago</span>
  return <span>{days}d ago</span>
}

export default function HistoryPanel({ onSelect, onRerun, activeId }: Props) {
  const { items, listLoaded, fetchList, fetchDetail, deleteItem } = useQueryHistory()
  const [loadingId,   setLoadingId]   = useState<number | null>(null)
  const [deletingId,  setDeletingId]  = useState<number | null>(null)
  const [rerunningId, setRerunningId] = useState<number | null>(null)
  const [error, setError] = useState('')

  useEffect(() => { fetchList() }, [])

  async function handleSelect(item: HistoryListItem) {
    if (loadingId) return
    setLoadingId(item.id)
    setError('')
    try {
      const result = await fetchDetail(item.id)
      onSelect(result, { id: item.id, question: item.question, filename: item.filename, file_id: item.file_id })
    } catch {
      setError('Failed to load result.')
    } finally {
      setLoadingId(null)
    }
  }

  function handleRerun(e: React.MouseEvent, item: HistoryListItem) {
    e.stopPropagation()
    setRerunningId(item.id)
    setTimeout(() => setRerunningId(null), 800)
    onRerun({ file_id: item.file_id, question: item.question })
  }

  async function handleDelete(e: React.MouseEvent, id: number) {
    e.stopPropagation()
    setDeletingId(id)
    try { await deleteItem(id) } finally { setDeletingId(null) }
  }

  if (!listLoaded) {
    return (
      <div className="space-y-2 py-2">
        {[...Array(4)].map((_, i) => <div key={i} className="h-16 bg-gray-100 rounded-lg animate-pulse" />)}
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="py-8 text-center">
        <p className="text-xs text-gray-400">No query history yet.</p>
        <p className="text-xs text-gray-400 mt-0.5">Run a query to see it here.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-1">
      {error && (
        <p className="text-xs text-red-500 bg-red-50 border border-red-200 rounded px-2 py-1 mb-1">{error}</p>
      )}

      {items.map((item) => {
        const isActive    = item.id === activeId
        const isLoading   = loadingId   === item.id
        const isDeleting  = deletingId  === item.id
        const isRerunning = rerunningId === item.id

        return (
          <div
            key={item.id}
            onClick={() => !isLoading && handleSelect(item)}
            className={`
              group relative flex flex-col gap-0.5 px-2.5 py-2.5 rounded-lg cursor-pointer transition-colors border
              ${isActive   ? 'bg-primary-50 border-primary-200' : 'hover:bg-gray-50 border-transparent'}
              ${isDeleting ? 'opacity-40 pointer-events-none'   : ''}
            `}
          >
            {/* Filename + time */}
            <div className="flex items-center justify-between gap-2 min-w-0 pr-5">
              <span className={`text-xs font-medium truncate ${isActive ? 'text-primary-700' : 'text-gray-700'}`}>
                {item.filename}
              </span>
              <span className="flex-none text-xs text-gray-400"><TimeAgo iso={item.created_at} /></span>
            </div>

            {/* Question */}
            <p className="text-xs text-gray-500 truncate pr-5">
              {item.question
                ? <span className="italic">"{item.question}"</span>
                : <span className="text-gray-400">auto-explore</span>
              }
            </p>

            {/* Insight preview */}
            <p className="text-xs text-gray-400 line-clamp-2 leading-relaxed mt-0.5">{item.insight}</p>

            {/* Re-run button — only on active item */}
            {isActive && (
              <button
                onClick={(e) => handleRerun(e, item)}
                disabled={isRerunning}
                className={`
                  mt-2 flex items-center justify-center gap-1.5 w-full py-1.5 rounded-md text-xs font-medium transition-colors
                  ${isRerunning
                    ? 'bg-primary-100 text-primary-500 cursor-default'
                    : 'bg-primary-600 hover:bg-primary-700 text-white'
                  }
                `}
              >
                {isRerunning ? (
                  <><div className="w-3 h-3 rounded-full border border-primary-400 border-t-transparent animate-spin" />Starting…</>
                ) : (
                  <>
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="23 4 23 10 17 10"/>
                      <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
                    </svg>
                    Re-run this query
                  </>
                )}
              </button>
            )}

            {/* Spinner overlay while loading detail */}
            {isLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-white/60 rounded-lg">
                <div className="w-4 h-4 rounded-full border-2 border-primary-500 border-t-transparent animate-spin" />
              </div>
            )}

            {/* Delete on hover — hidden when active to avoid clutter with re-run button */}
            {!isActive && (
              <button
                onClick={(e) => handleDelete(e, item.id)}
                className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 text-gray-300 hover:text-red-400 transition-all p-0.5 rounded"
                aria-label="Delete"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                  <path d="M10 11v6M14 11v6"/>
                  <path d="M9 6V4h6v2"/>
                </svg>
              </button>
            )}
          </div>
        )
      })}
    </div>
  )
}