import { create } from 'zustand'
import type { HistoryListItem, HistoryDetail } from '../api/history'
import type { QueryResponse } from '../api/query'

interface HistoryStore {
  items:        HistoryListItem[]
  listLoaded:   boolean
  needsRefresh: boolean
  setItems:         (items: HistoryListItem[]) => void
  prependItem:      (item: HistoryListItem)    => void
  removeItem:       (id: number)               => void
  setNeedsRefresh:  (v: boolean)               => void

  detailCache: Record<number, QueryResponse>
  setDetail:   (id: number, data: HistoryDetail) => void

  viewingId:    number | null
  setViewingId: (id: number | null) => void
}

export const useHistoryStore = create<HistoryStore>((set) => ({
  items:        [],
  listLoaded:   false,
  needsRefresh: false,

  setItems: (items) => set({ items, listLoaded: true }),

  prependItem: (item) =>
    set((s) => ({ items: [item, ...s.items] })),

  removeItem: (id) =>
    set((s) => ({
      items:       s.items.filter((i) => i.id !== id),
      detailCache: Object.fromEntries(
        Object.entries(s.detailCache).filter(([k]) => Number(k) !== id)
      ),
      viewingId: s.viewingId === id ? null : s.viewingId,
    })),

  setNeedsRefresh: (v) => set({ needsRefresh: v }),

  detailCache: {},
  setDetail: (id, data) =>
    set((s) => ({ detailCache: { ...s.detailCache, [id]: data.result_json } })),

  viewingId:    null,
  setViewingId: (id) => set({ viewingId: id }),
}))