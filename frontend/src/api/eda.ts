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

export type ReviewIssue = {
  col:      string
  severity: 'high' | 'medium' | 'low'
  detail:   string
  impact:   string
}

export type ReviewPrepStep = {
  priority:  'must' | 'should' | 'optional'
  col:       string | null
  action:    string
  rationale: string
}

export type ReviewResult = {
  issues:        ReviewIssue[]
  prep_steps:    ReviewPrepStep[]
  opportunities: string[]
}

export type ReviewUsage = {
  summary: {
    total_tokens:            number
    total_prompt_tokens:     number
    total_completion_tokens: number
    total_cost_usd:          number
  }
}

export type ReviewTask = {
  task_id:     string
  eda_task_id: string
  status:      ReviewStatus
  progress:    number
  result:      ReviewResult | null
  usage:       ReviewUsage | null
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