import { api } from './axios'

export type PreprocessStatus = 'pending' | 'running' | 'done' | 'error'

export type PreprocessTask = {
  task_id: string
  file_id: number
  status: PreprocessStatus
  step: string | null
  progress: number
  preview: Record<string, unknown>[] | null
  error: string | null
  created_at: string
}

export type PreprocessConfirmed = {
  file_id: number
  filename: string
  project_id: number
}

export type OperationConfig =
  | { operation: 'missing'; strategy: MissingStrategyConfig; cols: string[] | null }
  | { operation: 'encoding'; strategy: EncodingStrategyConfig; cols: string[] | null }
  | { operation: 'outlier'; strategy: OutlierStrategyConfig; cols: string[] | null }
  | { operation: 'scaling'; strategy: ScalingStrategyConfig; cols: string[] | null }

export type MissingStrategyConfig =
  | { type: 'mean' }
  | { type: 'median' }
  | { type: 'mode' }
  | { type: 'constant'; fill_value: string | number }
  | { type: 'drop_row' }
  | { type: 'drop_col' }

export type EncodingStrategyConfig =
  | { type: 'onehot' }
  | { type: 'ordinal'; order: Record<string, unknown[]> | null }
  | { type: 'label' }

export type OutlierStrategyConfig =
  | { type: 'iqr'; action: 'clip' | 'drop' }
  | { type: 'zscore'; threshold: number; action: 'clip' | 'drop' }
  | { type: 'percentile_clip'; lower: number; upper: number }

export type ScalingStrategyConfig =
  | { type: 'minmax'; feature_range: [number, number] }
  | { type: 'standard' }
  | { type: 'robust' }

export const preprocessApi = {
  run: (fileId: number, steps: OperationConfig[]) =>
    api.post<PreprocessTask>('/preprocess/run', { file_id: fileId, steps }),

  status: (taskId: string) =>
    api.get<PreprocessTask>(`/preprocess/status/${taskId}`),

  confirm: (taskId: string) =>
    api.post<PreprocessConfirmed>(`/preprocess/confirm/${taskId}`),

  cancel: (taskId: string) =>
    api.delete(`/preprocess/cancel/${taskId}`),
}