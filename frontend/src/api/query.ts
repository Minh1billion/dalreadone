import { api } from './axios'

export interface Chart {
  type: 'bar' | 'line' | 'pie' | 'scatter' | 'histogram' | 'grouped_bar'
  title: string
  labels: string[]
  data: number[] | number[][] | [number, number][]
  series_labels?: string[] // grouped_bar only
}

export interface CostCall {
  stage: string
  prompt_tokens: number
  completion_tokens: number
  cost_usd: number
  latency_ms: number
  skipped?: boolean
  skip_reason?: string
}

export interface CostReport {
  total_tokens: number
  total_prompt_tokens: number
  total_completion_tokens: number
  total_cost_usd: number
  total_latency_ms: number
  skipped_stages: string[]
  calls: CostCall[]
}

export interface QueryResponse {
  user_question: string | null
  explore_reason: string
  result: string
  charts: Chart[]
  interesting_reason: string | null
  interesting_result: string | null
  interesting_charts: Chart[]
  insight: string
  code: string
  cost_report: CostReport
}

export const queryApi = {
  run: (projectId: number, fileId: number, question: string) =>
    api.post<QueryResponse>(
      `/projects/${projectId}/files/${fileId}/query`,
      { question },
    ),
}