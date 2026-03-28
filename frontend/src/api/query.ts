import { api } from './axios'


/** Standard Chart.js chart types */
export interface StandardChart {
  type: 'bar' | 'line' | 'pie' | 'scatter' | 'histogram' | 'grouped_bar'
  title: string
  labels: string[]
  data: number[] | number[][] | [number, number][]
  series_labels?: string[]   // grouped_bar only
}

/** Word cloud — list of word/weight pairs */
export interface WordCloudChart {
  type: 'wordcloud_data'
  title: string
  items: { word: string; weight: number }[]
}

/** Sentiment donut — pos/neg/neu percentages */
export interface SentimentDistributionChart {
  type: 'sentiment_distribution'
  title: string
  positive: number
  negative: number
  neutral: number
}

/** Top phrases — horizontal bar of bigrams/keywords */
export interface TopPhrasesChart {
  type: 'top_phrases'
  title: string
  labels: string[]
  data: number[]
}

export type Chart =
  | StandardChart
  | WordCloudChart
  | SentimentDistributionChart
  | TopPhrasesChart


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