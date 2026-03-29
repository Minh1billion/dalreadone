import { useCallback, useRef } from 'react'
import { historyApi } from '../api/history'
import { useHistoryStore } from '../store/historyStore'
import type { QueryResponse } from '../api/query'
import type { HistoryListItem } from '../api/history'

export function useQueryHistory() {
  const listLoaded      = useHistoryStore(s => s.listLoaded)
  const needsRefresh    = useHistoryStore(s => s.needsRefresh)
  const detailCache     = useHistoryStore(s => s.detailCache)
  const setItems        = useHistoryStore(s => s.setItems)
  const setDetail       = useHistoryStore(s => s.setDetail)
  const removeItem      = useHistoryStore(s => s.removeItem)
  const prependItem     = useHistoryStore(s => s.prependItem)
  const setNeedsRefresh = useHistoryStore(s => s.setNeedsRefresh)
  const setViewingId    = useHistoryStore(s => s.setViewingId)
  const viewingId       = useHistoryStore(s => s.viewingId)
  const items           = useHistoryStore(s => s.items)

  // Tracks in-flight preload requests to prevent duplicate fetches
  const inFlight = useRef<Set<number>>(new Set())

  /**
   * Silently prefetch a single history detail into the cache.
   * No-ops if already cached or currently being fetched.
   */
  const preloadDetail = useCallback((id: number) => {
    if (detailCache[id]) return
    if (inFlight.current.has(id)) return
    inFlight.current.add(id)
    historyApi.get(id)
      .then(({ data }) => setDetail(id, data))
      .catch(() => {})
      .finally(() => inFlight.current.delete(id))
  }, [detailCache])

  /**
   * Fetch the history list, then immediately preload all details in parallel.
   * Skips fetch if list is already loaded and not stale, unless force=true.
   */
  const fetchList = useCallback(async (force = false) => {
    if (listLoaded && !needsRefresh && !force) return
    const { data } = await historyApi.list({ limit: 50 })
    setItems(data)
    setNeedsRefresh(false)

    // Fire-and-forget preload for all items - results land in cache as they arrive
    data.forEach((item: HistoryListItem) => preloadDetail(item.id))
  }, [listLoaded, needsRefresh, preloadDetail])

  /**
   * Fetch detail for a single item.
   * Returns from cache immediately if available, otherwise awaits the network request.
   */
  const fetchDetail = useCallback(async (id: number): Promise<QueryResponse> => {
    if (detailCache[id]) return detailCache[id]
    const { data } = await historyApi.get(id)
    setDetail(id, data)
    return data.result_json
  }, [detailCache])

  /**
   * Delete a history item from both the backend and local store.
   */
  const deleteItem = useCallback(async (id: number) => {
    await historyApi.delete(id)
    removeItem(id)
  }, [])

  /**
   * Optimistically prepend a new result to the history list.
   * Uses a temporary id (Date.now()) that will be replaced on next fetchList.
   * Also marks the list as stale so it refreshes on next History tab open.
   */
  const saveNewResult = useCallback((params: {
    project_id: number
    file_id:    number
    filename:   string
    question:   string | null
    result:     QueryResponse
  }) => {
    prependItem({
      id:         Date.now(),
      project_id: params.project_id,
      file_id:    params.file_id,
      filename:   params.filename,
      question:   params.question,
      insight:    params.result.insight?.slice(0, 160) ?? '',
      created_at: new Date().toISOString(),
    })
    setNeedsRefresh(true)
  }, [])

  return {
    items,
    listLoaded,
    viewingId,
    setViewingId,
    fetchList,
    fetchDetail,
    deleteItem,
    saveNewResult,
    preloadDetail,
  }
}