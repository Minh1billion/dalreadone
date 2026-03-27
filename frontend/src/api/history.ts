import { api } from './axios'
import type { QueryResponse } from './query'

export interface HistoryListItem {
  id:         number
  project_id: number
  file_id:    number
  filename:   string
  question:   string | null
  insight:    string
  created_at: string
}

export interface HistoryDetail extends HistoryListItem {
  result_json: QueryResponse
}

export const historyApi = {
  list: (params?: { limit?: number; offset?: number }) =>
    api.get<HistoryListItem[]>('/history', { params }),

  get: (id: number) =>
    api.get<HistoryDetail>(`/history/${id}`),

  delete: (id: number) =>
    api.delete(`/history/${id}`),
}