import { useCallback } from 'react'
import { historyApi } from '../api/history'
import { useHistoryStore } from '../store/historyStore'
import type { QueryResponse } from '../api/query'

export function useQueryHistory() {
  const listLoaded     = useHistoryStore(s => s.listLoaded)
  const needsRefresh   = useHistoryStore(s => s.needsRefresh)
  const detailCache    = useHistoryStore(s => s.detailCache)
  const setItems       = useHistoryStore(s => s.setItems)
  const setDetail      = useHistoryStore(s => s.setDetail)
  const removeItem     = useHistoryStore(s => s.removeItem)
  const prependItem    = useHistoryStore(s => s.prependItem)
  const setNeedsRefresh = useHistoryStore(s => s.setNeedsRefresh)
  const setViewingId   = useHistoryStore(s => s.setViewingId)
  const viewingId      = useHistoryStore(s => s.viewingId)
  const items          = useHistoryStore(s => s.items)

  const fetchList = useCallback(async (force = false) => {
    if (listLoaded && !needsRefresh && !force) return
    const { data } = await historyApi.list({ limit: 50 })
    setItems(data)
    setNeedsRefresh(false)
  }, [listLoaded, needsRefresh])

  const fetchDetail = useCallback(async (id: number): Promise<QueryResponse> => {
    if (detailCache[id]) return detailCache[id]
    const { data } = await historyApi.get(id)
    setDetail(id, data)
    return data.result_json
  }, [detailCache])

  const deleteItem = useCallback(async (id: number) => {
    await historyApi.delete(id)
    removeItem(id)
  }, [])

  const saveNewResult = useCallback((params: {
    project_id: number
    file_id:    number
    filename:   string
    question:   string | null
    result:     QueryResponse
  }) => {
    // Optimistically prepend to list so UI updates instantly
    prependItem({
      id:         Date.now(),  // temp id, replaced on next fetchList
      project_id: params.project_id,
      file_id:    params.file_id,
      filename:   params.filename,
      question:   params.question,
      insight:    params.result.insight?.slice(0, 160) ?? '',
      created_at: new Date().toISOString(),
    })
    // Flag for refetch on next History tab open to get real id from BE
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
  }
}