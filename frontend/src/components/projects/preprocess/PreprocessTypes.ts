import type {
  StepName,
  MissingStrategy,
  EncodeStrategy,
  OutlierStrategy,
  ScaleStrategy,
  StepConfig,
  MissingStepParams,
  EncodingStepParams,
  OutlierStepParams,
  ScalingStepParams,
} from '../../../api/preprocess'

export type { StepName, MissingStrategy, EncodeStrategy, OutlierStrategy, ScaleStrategy }

export interface StepMeta {
  key:   StepName
  label: string
  description: string
}

export const STEP_META: StepMeta[] = [
  { key: 'missing',  label: 'Missing values',  description: 'Impute or drop columns/rows with nulls' },
  { key: 'encoding', label: 'Encoding',         description: 'Encode categorical features' },
  { key: 'outlier',  label: 'Outliers',         description: 'Detect and treat numeric outliers' },
  { key: 'scaling',  label: 'Scaling',          description: 'Normalise or standardise numeric features' },
]

export const MISSING_STRATEGIES: { value: MissingStrategy; label: string }[] = [
  { value: 'median',   label: 'Median' },
  { value: 'mean',     label: 'Mean' },
  { value: 'mode',     label: 'Mode' },
  { value: 'constant', label: 'Constant' },
  { value: 'drop_row', label: 'Drop rows' },
  { value: 'drop_col', label: 'Drop column' },
]

export const ENCODE_STRATEGIES: { value: EncodeStrategy; label: string }[] = [
  { value: 'onehot',    label: 'One-hot' },
  { value: 'ordinal',   label: 'Ordinal' },
  { value: 'binary',    label: 'Binary' },
  { value: 'frequency', label: 'Frequency' },
  { value: 'skip',      label: 'Skip' },
]

export const OUTLIER_STRATEGIES: { value: OutlierStrategy; label: string }[] = [
  { value: 'clip',          label: 'Clip (IQR fence)' },
  { value: 'winsorize',     label: 'Winsorize' },
  { value: 'drop_row',      label: 'Drop rows' },
  { value: 'impute_median', label: 'Impute median' },
  { value: 'skip',          label: 'Skip' },
]

export const SCALE_STRATEGIES: { value: ScaleStrategy; label: string }[] = [
  { value: 'standard', label: 'Standard (z-score)' },
  { value: 'minmax',   label: 'Min-Max' },
  { value: 'robust',   label: 'Robust (IQR)' },
  { value: 'log1p',    label: 'Log1p' },
  { value: 'skip',     label: 'Skip' },
]

export function defaultStepConfig(name: StepName): StepConfig {
  const defaults: Record<StepName, StepConfig> = {
    missing: {
      name: 'missing',
      params: {
        num_strategy: 'median',
        cat_strategy: 'mode',
        num_fill_value: 0,
        cat_fill_value: 'unknown',
        drop_col_threshold: 0.5,
        column_overrides: {},
      } satisfies MissingStepParams,
    },
    encoding: {
      name: 'encoding',
      params: {
        default_strategy: 'onehot',
        max_onehot_cardinality: 20,
        column_overrides: {},
        skip_cols: [],
      } satisfies EncodingStepParams,
    },
    outlier: {
      name: 'outlier',
      params: {
        default_strategy: 'clip',
        iqr_k: 1.5,
        winsorize_bounds: [0.01, 0.99],
        column_overrides: {},
        skip_cols: [],
      } satisfies OutlierStepParams,
    },
    scaling: {
      name: 'scaling',
      params: {
        default_strategy: 'standard',
        feature_range: [0.0, 1.0],
        column_overrides: {},
        skip_cols: [],
      } satisfies ScalingStepParams,
    },
  }
  return defaults[name]
}