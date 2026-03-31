import { api } from './axios'
import type { FileItem } from './files'

export type PreprocessStatus = 'pending' | 'running' | 'done' | 'error'

export type StepName = 'missing' | 'encoding' | 'outlier' | 'scaling'

export type MissingStrategy = 'mean' | 'median' | 'mode' | 'constant' | 'drop_row' | 'drop_col'
export type EncodeStrategy  = 'onehot' | 'ordinal' | 'binary' | 'frequency' | 'skip'
export type OutlierStrategy = 'clip' | 'winsorize' | 'drop_row' | 'impute_median' | 'skip'
export type ScaleStrategy   = 'standard' | 'minmax' | 'robust' | 'log1p' | 'skip'

export interface MissingColumnOverride {
  strategy?: MissingStrategy
  fill_value?: unknown
  drop_col_threshold?: number
}

export interface MissingStepParams {
  num_strategy?: MissingStrategy
  cat_strategy?: MissingStrategy
  num_fill_value?: unknown
  cat_fill_value?: unknown
  drop_col_threshold?: number
  drop_row_subset?: string[]
  column_overrides?: Record<string, MissingColumnOverride>
}

export interface EncodingColumnOverride {
  strategy: EncodeStrategy
  ordinal_categories?: unknown[]
  max_onehot_cardinality?: number
}

export interface EncodingStepParams {
  default_strategy?: EncodeStrategy
  max_onehot_cardinality?: number
  column_overrides?: Record<string, EncodingColumnOverride>
  skip_cols?: string[]
}

export interface OutlierColumnOverride {
  strategy: OutlierStrategy
  iqr_k?: number
  winsorize_bounds?: [number, number]
}

export interface OutlierStepParams {
  default_strategy?: OutlierStrategy
  iqr_k?: number
  winsorize_bounds?: [number, number]
  column_overrides?: Record<string, OutlierColumnOverride>
  skip_cols?: string[]
}

export interface ScalingColumnOverride {
  strategy: ScaleStrategy
  feature_range?: [number, number]
}

export interface ScalingStepParams {
  default_strategy?: ScaleStrategy
  feature_range?: [number, number]
  column_overrides?: Record<string, ScalingColumnOverride>
  skip_cols?: string[]
}

export type StepParamsMap = {
  missing:  MissingStepParams
  encoding: EncodingStepParams
  outlier:  OutlierStepParams
  scaling:  ScalingStepParams
}

export interface StepConfig<N extends StepName = StepName> {
  name: N
  params: StepParamsMap[N]
}

export interface PreprocessTask {
  task_id:    string
  file_id:    number
  status:     PreprocessStatus
  step:       StepName | 'done' | null
  progress:   number
  result:     Record<string, unknown> | null
  error:      string | null
  created_at: string
}

export const preprocessApi = {
  start: (fileId: number, steps: StepConfig[]) =>
    api.post<PreprocessTask>('/preprocess/tasks', { file_id: fileId, steps }),

  status: (taskId: string) =>
    api.get<PreprocessTask>(`/preprocess/tasks/${taskId}`),

  save: (taskId: string) =>
    api.post<FileItem>(`/preprocess/tasks/${taskId}/save`),
}