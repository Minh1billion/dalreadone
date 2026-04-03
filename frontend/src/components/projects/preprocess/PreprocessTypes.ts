import type { OperationConfig } from '../../../api/preprocess'

export type ColType = 'numeric' | 'categorical' | 'datetime' | 'unknown'
export type ColTypeMap = Record<string, ColType>

export type Operation = 'missing' | 'encoding' | 'outlier' | 'scaling' | 'custom_code'

export interface DraftStep {
  id:        string
  operation: Operation | null
  strategy:  string | null
  params:    Record<string, unknown>
  cols:      string[] | null
}

export function inferColTypes(
  columns: string[],
  rows: Record<string, unknown>[],
): ColTypeMap {
  const result: ColTypeMap = {}
  for (const col of columns) {
    const samples = rows.slice(0, 20).map(r => r[col]).filter(v => v != null)
    if (samples.length === 0) { result[col] = 'unknown'; continue }
    if (samples.every(v => typeof v === 'number' || (typeof v === 'string' && !isNaN(Number(v))))) {
      result[col] = 'numeric'
    } else if (samples.some(v => typeof v === 'string' && /\d{4}-\d{2}-\d{2}/.test(String(v)))) {
      result[col] = 'datetime'
    } else {
      result[col] = 'categorical'
    }
  }
  return result
}

export function draftToConfig(step: DraftStep): OperationConfig | null {
  if (!step.operation || !step.strategy) return null

  if (step.operation === 'custom_code') {
    const code = step.params.code as string | undefined
    if (!code?.trim()) return null
    return {
      operation: 'custom_code',
      strategy:  { type: 'custom_code', code },
      cols:      null,
    }
  }

  const cols = step.cols && step.cols.length > 0 ? step.cols : null

  switch (step.operation) {
    case 'missing':
      switch (step.strategy) {
        case 'mean':     return { operation: 'missing', strategy: { type: 'mean' },     cols }
        case 'median':   return { operation: 'missing', strategy: { type: 'median' },   cols }
        case 'mode':     return { operation: 'missing', strategy: { type: 'mode' },     cols }
        case 'drop_row': return { operation: 'missing', strategy: { type: 'drop_row' }, cols }
        case 'drop_col': return { operation: 'missing', strategy: { type: 'drop_col' }, cols }
        case 'constant': return {
          operation: 'missing',
          strategy:  { type: 'constant', fill_value: step.params.fill_value as string | number ?? 0 },
          cols,
        }
      }
      break

    case 'encoding':
      switch (step.strategy) {
        case 'onehot':  return { operation: 'encoding', strategy: { type: 'onehot' },                cols }
        case 'label':   return { operation: 'encoding', strategy: { type: 'label' },                 cols }
        case 'ordinal': return { operation: 'encoding', strategy: { type: 'ordinal', order: null },  cols }
      }
      break

    case 'outlier':
      switch (step.strategy) {
        case 'iqr':             return { operation: 'outlier', strategy: { type: 'iqr',             action:    step.params.action    as 'clip' | 'drop' ?? 'clip' },            cols }
        case 'zscore':          return { operation: 'outlier', strategy: { type: 'zscore',          threshold: step.params.threshold as number ?? 3.0, action: step.params.action as 'clip' | 'drop' ?? 'clip' }, cols }
        case 'percentile_clip': return { operation: 'outlier', strategy: { type: 'percentile_clip', lower:     step.params.lower    as number ?? 0.05, upper:  step.params.upper as number ?? 0.95 }, cols }
      }
      break

    case 'scaling':
      switch (step.strategy) {
        case 'minmax':   return { operation: 'scaling', strategy: { type: 'minmax', feature_range: step.params.feature_range as [number, number] ?? [0, 1] }, cols }
        case 'standard': return { operation: 'scaling', strategy: { type: 'standard' }, cols }
        case 'robust':   return { operation: 'scaling', strategy: { type: 'robust' },   cols }
      }
      break
  }

  return null
}

let _suggestCounter = 0

export function suggestToSteps(configs: OperationConfig[]): DraftStep[] {
  return configs.map(cfg => {
    const id = `suggest-${++_suggestCounter}`

    if (cfg.operation === 'custom_code') {
      return {
        id,
        operation: 'custom_code' as Operation,
        strategy:  'custom_code',
        params:    { code: cfg.strategy.code },
        cols:      null,
      }
    }

    const s = cfg.strategy as any

    return {
      id,
      operation: cfg.operation as Operation,
      strategy:  s.type,
      cols:      cfg.cols,
      params:    (({ type, ...rest }) => rest)(s),
    }
  })
}

export const OPERATION_OPTIONS: { value: Operation; label: string }[] = [
  { value: 'missing',     label: 'Missing values' },
  { value: 'encoding',    label: 'Encoding' },
  { value: 'outlier',     label: 'Outlier handling' },
  { value: 'scaling',     label: 'Scaling' },
  { value: 'custom_code', label: 'Custom code' },
]

export const STRATEGY_OPTIONS: Record<Operation, { value: string; label: string }[]> = {
  missing: [
    { value: 'mean',     label: 'Fill - mean' },
    { value: 'median',   label: 'Fill - median' },
    { value: 'mode',     label: 'Fill - mode' },
    { value: 'constant', label: 'Fill - constant' },
    { value: 'drop_row', label: 'Drop rows' },
    { value: 'drop_col', label: 'Drop columns' },
  ],
  encoding: [
    { value: 'onehot',  label: 'One-hot' },
    { value: 'ordinal', label: 'Ordinal' },
    { value: 'label',   label: 'Label' },
  ],
  outlier: [
    { value: 'iqr',             label: 'IQR' },
    { value: 'zscore',          label: 'Z-score' },
    { value: 'percentile_clip', label: 'Percentile clip' },
  ],
  scaling: [
    { value: 'minmax',   label: 'Min-max' },
    { value: 'standard', label: 'Standard (z-score)' },
    { value: 'robust',   label: 'Robust' },
  ],
  custom_code: [
    { value: 'custom_code', label: 'Python function' },
  ],
}