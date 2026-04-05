import type { OperationConfig } from '../../../api/preprocess'

export type ColType = 'numeric' | 'categorical' | 'datetime' | 'unknown'
export type ColTypeMap = Record<string, ColType>

export type DraftStep = {
  id:        string
  operation: string | null
  strategy:  string | null
  params:    Record<string, unknown>
  cols:      string[] | null
}

export const OPERATION_OPTIONS = [
  { value: 'missing',     label: 'Missing values' },
  { value: 'outlier',     label: 'Outliers' },
  { value: 'scaling',     label: 'Scaling' },
  { value: 'encoding',    label: 'Encoding' },
  { value: 'drop',        label: 'Drop' },
  { value: 'cast',        label: 'Cast types' },
  { value: 'feature',     label: 'Feature engineering' },
  { value: 'custom_code', label: 'Custom code' },
] as const

export const STRATEGY_OPTIONS: Record<string, { value: string; label: string }[]> = {
  missing: [
    { value: 'mean',     label: 'Mean' },
    { value: 'median',   label: 'Median' },
    { value: 'mode',     label: 'Mode' },
    { value: 'constant', label: 'Constant' },
    { value: 'drop_row', label: 'Drop rows' },
    { value: 'drop_col', label: 'Drop columns' },
  ],
  outlier: [
    { value: 'iqr',             label: 'IQR' },
    { value: 'zscore',          label: 'Z-score' },
    { value: 'percentile_clip', label: 'Percentile clip' },
  ],
  scaling: [
    { value: 'minmax',   label: 'Min-Max' },
    { value: 'standard', label: 'Standard (Z)' },
    { value: 'robust',   label: 'Robust' },
  ],
  encoding: [
    { value: 'onehot',  label: 'One-Hot' },
    { value: 'ordinal', label: 'Ordinal' },
    { value: 'label',   label: 'Label' },
  ],
  drop: [
    { value: 'drop_columns',    label: 'Drop columns' },
    { value: 'drop_duplicates', label: 'Drop duplicates' },
  ],
  cast: [
    { value: 'cast', label: 'Cast' },
  ],
  feature: [
    { value: 'binning', label: 'Binning' },
    { value: 'lambda',  label: 'Lambda' },
  ],
  custom_code: [
    { value: 'custom_code', label: 'Custom code' },
  ],
}

const DATE_RE = /^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2})?)?$/

export function inferColTypes(
  columns: string[],
  rows: Record<string, unknown>[],
): ColTypeMap {
  const result: ColTypeMap = {}
  for (const col of columns) {
    const samples = rows.slice(0, 100).map(r => r[col]).filter(v => v != null)
    if (samples.length === 0) {
      result[col] = 'unknown'
      continue
    }
    const allNumeric = samples.every(v =>
      typeof v === 'number' ||
      (typeof v === 'string' && v.trim() !== '' && !isNaN(Number(v)))
    )
    if (allNumeric) {
      result[col] = 'numeric'
      continue
    }
    const allDate = samples.every(v => typeof v === 'string' && DATE_RE.test(v.trim()))
    if (allDate) {
      result[col] = 'datetime'
      continue
    }
    result[col] = 'categorical'
  }
  return result
}

export function draftToConfig(step: DraftStep): OperationConfig | null {
  if (!step.operation || !step.strategy) return null
  const p    = step.params
  const cols = step.cols

  switch (step.operation) {
    case 'missing': {
      const s = step.strategy
      let strategy: OperationConfig & { operation: 'missing' }
      switch (s) {
        case 'mean':     strategy = { operation: 'missing', strategy: { type: 'mean' },    cols }; break
        case 'median':   strategy = { operation: 'missing', strategy: { type: 'median' },  cols }; break
        case 'mode':     strategy = { operation: 'missing', strategy: { type: 'mode' },    cols }; break
        case 'drop_row': strategy = { operation: 'missing', strategy: { type: 'drop_row' }, cols }; break
        case 'drop_col': strategy = { operation: 'missing', strategy: { type: 'drop_col' }, cols }; break
        case 'constant': strategy = { operation: 'missing', strategy: { type: 'constant', fill_value: (p.fill_value as string | number) ?? 0 }, cols }; break
        default: return null
      }
      return strategy
    }

    case 'outlier': {
      const s = step.strategy
      switch (s) {
        case 'iqr':
          return { operation: 'outlier', strategy: { type: 'iqr', action: (p.action as 'clip' | 'drop') ?? 'clip' }, cols }
        case 'zscore':
          return { operation: 'outlier', strategy: { type: 'zscore', threshold: (p.threshold as number) ?? 3, action: (p.action as 'clip' | 'drop') ?? 'clip' }, cols }
        case 'percentile_clip':
          return { operation: 'outlier', strategy: { type: 'percentile_clip', lower: (p.lower as number) ?? 0.05, upper: (p.upper as number) ?? 0.95 }, cols }
        default: return null
      }
    }

    case 'scaling': {
      switch (step.strategy) {
        case 'minmax':
          return { operation: 'scaling', strategy: { type: 'minmax', feature_range: (p.feature_range as [number, number]) ?? [0, 1] }, cols }
        case 'standard':
          return { operation: 'scaling', strategy: { type: 'standard' }, cols }
        case 'robust':
          return { operation: 'scaling', strategy: { type: 'robust' }, cols }
        default: return null
      }
    }

    case 'encoding': {
      switch (step.strategy) {
        case 'onehot':
          return { operation: 'encoding', strategy: { type: 'onehot' }, cols }
        case 'ordinal':
          return { operation: 'encoding', strategy: { type: 'ordinal', order: (p.order as Record<string, unknown[]>) ?? null }, cols }
        case 'label':
          return { operation: 'encoding', strategy: { type: 'label' }, cols }
        default: return null
      }
    }

    case 'drop': {
      switch (step.strategy) {
        case 'drop_columns':
          return { operation: 'drop', strategy: { type: 'drop_columns' }, cols }
        case 'drop_duplicates':
          return { operation: 'drop', strategy: { type: 'drop_duplicates', keep: (p.keep as 'first' | 'last') ?? 'first' }, cols }
        default: return null
      }
    }

    case 'cast': {
      const dtype_map = (p.dtype_map as Record<string, string>) ?? {}
      if (!cols?.length) return null
      return { operation: 'cast', strategy: { type: 'cast', dtype_map }, cols }
    }

    case 'feature': {
      switch (step.strategy) {
        case 'binning': {
          const bins_map = (p.bins_map as Record<string, { output_col: string; bins: number | number[] }>) ?? {}
          return { operation: 'feature', strategy: { type: 'binning', bins_map }, cols }
        }
        case 'lambda': {
          const expressions = (p.expressions as { output_col: string; fn: string }[]) ?? []
          return { operation: 'feature', strategy: { type: 'lambda', expressions }, cols }
        }
        default: return null
      }
    }

    case 'custom_code':
      return { operation: 'custom_code', strategy: { type: 'custom_code', code: (p.code as string) ?? '' }, cols: null }

    default:
      return null
  }
}

export function suggestToSteps(configs: OperationConfig[]): DraftStep[] {
  let counter = 0
  return configs.map(cfg => {
    const id = `step-suggest-${++counter}`

    switch (cfg.operation) {
      case 'missing': {
        const s      = cfg.strategy
        const params: Record<string, unknown> = {}
        if (s.type === 'constant') params.fill_value = s.fill_value
        return { id, operation: cfg.operation, strategy: s.type, params, cols: cfg.cols }
      }
      case 'outlier': {
        const s      = cfg.strategy
        const params: Record<string, unknown> = {}
        if ('action' in s)    params.action    = s.action
        if ('threshold' in s) params.threshold = s.threshold
        if ('lower' in s)     params.lower     = s.lower
        if ('upper' in s)     params.upper     = s.upper
        return { id, operation: cfg.operation, strategy: s.type, params, cols: cfg.cols }
      }
      case 'scaling': {
        const s      = cfg.strategy
        const params: Record<string, unknown> = {}
        if ('feature_range' in s) params.feature_range = s.feature_range
        return { id, operation: cfg.operation, strategy: s.type, params, cols: cfg.cols }
      }
      case 'encoding': {
        const s      = cfg.strategy
        const params: Record<string, unknown> = {}
        if ('order' in s) params.order = s.order
        return { id, operation: cfg.operation, strategy: s.type, params, cols: cfg.cols }
      }
      case 'drop': {
        const s      = cfg.strategy
        const params: Record<string, unknown> = {}
        if ('keep' in s) params.keep = s.keep
        return { id, operation: cfg.operation, strategy: s.type, params, cols: cfg.cols }
      }
      case 'cast': {
        const s = cfg.strategy
        return { id, operation: cfg.operation, strategy: 'cast', params: { dtype_map: s.dtype_map }, cols: cfg.cols }
      }
      case 'feature': {
        const s      = cfg.strategy
        const params: Record<string, unknown> = {}
        if (s.type === 'binning') params.bins_map    = s.bins_map
        if (s.type === 'lambda')  params.expressions = s.expressions
        return { id, operation: cfg.operation, strategy: s.type, params, cols: cfg.cols }
      }
      case 'custom_code': {
        const s = cfg.strategy
        return { id, operation: cfg.operation, strategy: 'custom_code', params: { code: s.code }, cols: null }
      }
      default:
        return { id, operation: null, strategy: null, params: {}, cols: null }
    }
  })
}