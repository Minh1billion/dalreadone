import { api } from './axios'

export type EDAStatus    = 'pending' | 'running' | 'done' | 'error'
export type ReviewStatus = 'pending' | 'running' | 'done' | 'error'

export type EDATask = {
  task_id:  string
  status:   EDAStatus
  step:     string | null
  progress: number
  result:   Record<string, unknown> | null
  error:    string | null
}

export type ReviewResult = {
  domain: {
    prediction:          string
    confidence:          'high' | 'medium' | 'low'
    reasoning:           string
    data_characteristics: string[]
  }
  issues: {
    column:   string | null
    type:     string
    severity: 'critical' | 'warning' | 'info'
    detail:   string
  }[]
  semantic_types: {
    column:        string
    dtype_in_data: string
    semantic_type: string
    needs_cast:    boolean
    cast_to:       string | null
    reasoning:     string
  }[]
  column_relationships: {
    columns:           string[]
    relationship_type: 'redundant' | 'derived' | 'leakage' | 'correlated' | 'group_key'
    strength:          number
    reasoning:         string
  }[]
  keep_columns:    string[]
  drop_candidates: { column: string; reason: string }[]
}

export type ReviewTask = {
  task_id:     string
  eda_task_id: string
  status:      ReviewStatus
  progress:    number
  result:      ReviewResult | null
  error:       string | null
}

export const edaApi = {
  start:  (fileId: number) =>
    api.post<{ task_id: string }>(`/eda/files/${fileId}`),
  status: (taskId: string) =>
    api.get<EDATask>(`/eda/${taskId}`),
}

export const reviewApi = {
  start:  (edaTaskId: string) =>
    api.post<{ task_id: string }>(`/eda/${edaTaskId}/review`),
  status: (edaTaskId: string, reviewTaskId: string) =>
    api.get<ReviewTask>(`/eda/${edaTaskId}/review/${reviewTaskId}`),
}