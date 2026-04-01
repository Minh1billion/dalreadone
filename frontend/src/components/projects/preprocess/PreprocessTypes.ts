import type {
  OperationConfig,
  MissingStrategyConfig,
  EncodingStrategyConfig,
  OutlierStrategyConfig,
  ScalingStrategyConfig,
} from '../../../api/preprocess'

export type ColType = 'numeric' | 'categorical'
export type ColTypeMap = Record<string, ColType>

export function inferColTypes(columns: string[], rows: Record<string, unknown>[]): ColTypeMap {
  return columns.reduce((acc, col) => {
    const values = rows.map(r => r[col]).filter(v => v != null)
    acc[col] = values.length > 0 && values.every(v => typeof v === 'number') ? 'numeric' : 'categorical'
    return acc
  }, {} as ColTypeMap)
}

export type OperationType = OperationConfig['operation']

export type StrategyMeta = {
  value: string
  label: string
  colFilter: ColType | 'all'
  defaultParams: Record<string, unknown>
}

export const STRATEGY_MAP: Record<OperationType, StrategyMeta[]> = {
  missing: [
    { value: 'mean',     label: 'Mean',         colFilter: 'numeric',     defaultParams: {} },
    { value: 'median',   label: 'Median',       colFilter: 'numeric',     defaultParams: {} },
    { value: 'mode',     label: 'Mode',         colFilter: 'all',         defaultParams: {} },
    { value: 'constant', label: 'Constant',     colFilter: 'all',         defaultParams: { fill_value: 0 } },
    { value: 'drop_row', label: 'Drop rows',    colFilter: 'all',         defaultParams: {} },
    { value: 'drop_col', label: 'Drop columns', colFilter: 'all',         defaultParams: {} },
  ],
  encoding: [
    { value: 'onehot',  label: 'One-Hot',  colFilter: 'categorical', defaultParams: {} },
    { value: 'ordinal', label: 'Ordinal',  colFilter: 'categorical', defaultParams: { order: null } },
    { value: 'label',   label: 'Label',    colFilter: 'categorical', defaultParams: {} },
  ],
  outlier: [
    { value: 'iqr',             label: 'IQR',             colFilter: 'numeric', defaultParams: { action: 'clip' } },
    { value: 'zscore',          label: 'Z-Score',         colFilter: 'numeric', defaultParams: { threshold: 3.0, action: 'clip' } },
    { value: 'percentile_clip', label: 'Percentile Clip', colFilter: 'numeric', defaultParams: { lower: 0.05, upper: 0.95 } },
  ],
  scaling: [
    { value: 'minmax',   label: 'Min-Max',  colFilter: 'numeric', defaultParams: { feature_range: [0, 1] } },
    { value: 'standard', label: 'Standard', colFilter: 'numeric', defaultParams: {} },
    { value: 'robust',   label: 'Robust',   colFilter: 'numeric', defaultParams: {} },
  ],
}

export const OPERATION_LABELS: Record<OperationType, string> = {
  missing:  'Missing Values',
  encoding: 'Encoding',
  outlier:  'Outlier',
  scaling:  'Scaling',
}

export type DraftStep = {
  id: string
  operation: OperationType | null
  strategy: string | null
  params: Record<string, unknown>
  cols: string[] | null
}

export function draftToConfig(step: DraftStep): OperationConfig | null {
  if (!step.operation || !step.strategy) return null
  const strategy = { type: step.strategy, ...step.params } as
    MissingStrategyConfig & EncodingStrategyConfig & OutlierStrategyConfig & ScalingStrategyConfig
  return { operation: step.operation, strategy, cols: step.cols } as OperationConfig
}

export function getFilteredCols(colTypeMap: ColTypeMap, colFilter: ColType | 'all'): string[] {
  if (colFilter === 'all') return Object.keys(colTypeMap)
  return Object.entries(colTypeMap).filter(([, t]) => t === colFilter).map(([c]) => c)
}