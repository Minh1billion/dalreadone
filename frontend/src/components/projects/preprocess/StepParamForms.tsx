import type {
  MissingStepParams,
  EncodingStepParams,
  OutlierStepParams,
  ScalingStepParams,
} from '../../../api/preprocess'
import {
  MISSING_STRATEGIES,
  ENCODE_STRATEGIES,
  OUTLIER_STRATEGIES,
  SCALE_STRATEGIES,
} from './PreprocessTypes'
import { SelectRow, NumberRow, TextRow, RangeRow, ParamSection } from './ParamRow'

// ─── Missing ────────────────────────────────────────────────────────────────

interface MissingFormProps {
  params:   MissingStepParams
  onChange: (p: MissingStepParams) => void
}

export function MissingParamsForm({ params, onChange }: MissingFormProps) {
  const set = (patch: Partial<MissingStepParams>) => onChange({ ...params, ...patch })
  return (
    <div className="space-y-4">
      <ParamSection title="Default strategy">
        <SelectRow
          label="Numeric columns"
          value={params.num_strategy ?? 'median'}
          options={MISSING_STRATEGIES}
          onChange={(v) => set({ num_strategy: v as any })}
        />
        <SelectRow
          label="Categorical columns"
          value={params.cat_strategy ?? 'mode'}
          options={MISSING_STRATEGIES}
          onChange={(v) => set({ cat_strategy: v as any })}
        />
      </ParamSection>

      <ParamSection title="Fill values (constant strategy)">
        <TextRow
          label="Numeric fill value"
          value={String(params.num_fill_value ?? 0)}
          onChange={(v) => set({ num_fill_value: isNaN(Number(v)) ? v : Number(v) })}
          hint="Used when strategy = constant"
        />
        <TextRow
          label="Categorical fill value"
          value={String(params.cat_fill_value ?? 'unknown')}
          onChange={(v) => set({ cat_fill_value: v })}
          hint="Used when strategy = constant"
        />
      </ParamSection>

      <ParamSection title="Column threshold">
        <NumberRow
          label="Drop column threshold"
          value={params.drop_col_threshold ?? 0.5}
          min={0} max={1} step={0.05}
          onChange={(v) => set({ drop_col_threshold: v })}
          hint="Drop column if null% ≥ this (0–1)"
        />
      </ParamSection>
    </div>
  )
}

// ─── Encoding ────────────────────────────────────────────────────────────────

interface EncodingFormProps {
  params:   EncodingStepParams
  onChange: (p: EncodingStepParams) => void
}

export function EncodingParamsForm({ params, onChange }: EncodingFormProps) {
  const set = (patch: Partial<EncodingStepParams>) => onChange({ ...params, ...patch })
  return (
    <div className="space-y-4">
      <ParamSection title="Default strategy">
        <SelectRow
          label="Strategy"
          value={params.default_strategy ?? 'onehot'}
          options={ENCODE_STRATEGIES}
          onChange={(v) => set({ default_strategy: v as any })}
        />
        <NumberRow
          label="Max one-hot cardinality"
          value={params.max_onehot_cardinality ?? 20}
          min={2} step={1}
          onChange={(v) => set({ max_onehot_cardinality: v })}
          hint="Columns with more unique values fall back to frequency encoding"
        />
      </ParamSection>

      <ParamSection title="Skip columns">
        <TextRow
          label="Skip cols (comma-separated)"
          value={(params.skip_cols ?? []).join(', ')}
          onChange={(v) => set({ skip_cols: v.split(',').map((s) => s.trim()).filter(Boolean) })}
          hint="These columns will not be encoded"
        />
      </ParamSection>
    </div>
  )
}

// ─── Outlier ────────────────────────────────────────────────────────────────

interface OutlierFormProps {
  params:   OutlierStepParams
  onChange: (p: OutlierStepParams) => void
}

export function OutlierParamsForm({ params, onChange }: OutlierFormProps) {
  const set = (patch: Partial<OutlierStepParams>) => onChange({ ...params, ...patch })
  const bounds = params.winsorize_bounds ?? [0.01, 0.99]
  return (
    <div className="space-y-4">
      <ParamSection title="Default strategy">
        <SelectRow
          label="Strategy"
          value={params.default_strategy ?? 'clip'}
          options={OUTLIER_STRATEGIES}
          onChange={(v) => set({ default_strategy: v as any })}
        />
        <NumberRow
          label="IQR multiplier (k)"
          value={params.iqr_k ?? 1.5}
          min={0.1} step={0.1}
          onChange={(v) => set({ iqr_k: v })}
          hint="Fence = Q1 − k·IQR, Q3 + k·IQR"
        />
      </ParamSection>

      <ParamSection title="Winsorize bounds">
        <RangeRow
          label="Percentile range"
          lo={bounds[0]}
          hi={bounds[1]}
          onChangeLo={(v) => set({ winsorize_bounds: [v, bounds[1]] })}
          onChangeHi={(v) => set({ winsorize_bounds: [bounds[0], v] })}
          min={0} max={1} step={0.005}
          hint="Used when strategy = winsorize"
        />
      </ParamSection>

      <ParamSection title="Skip columns">
        <TextRow
          label="Skip cols (comma-separated)"
          value={(params.skip_cols ?? []).join(', ')}
          onChange={(v) => set({ skip_cols: v.split(',').map((s) => s.trim()).filter(Boolean) })}
        />
      </ParamSection>
    </div>
  )
}

// ─── Scaling ────────────────────────────────────────────────────────────────

interface ScalingFormProps {
  params:   ScalingStepParams
  onChange: (p: ScalingStepParams) => void
}

export function ScalingParamsForm({ params, onChange }: ScalingFormProps) {
  const set = (patch: Partial<ScalingStepParams>) => onChange({ ...params, ...patch })
  const range = params.feature_range ?? [0.0, 1.0]
  return (
    <div className="space-y-4">
      <ParamSection title="Default strategy">
        <SelectRow
          label="Strategy"
          value={params.default_strategy ?? 'standard'}
          options={SCALE_STRATEGIES}
          onChange={(v) => set({ default_strategy: v as any })}
        />
      </ParamSection>

      <ParamSection title="Min-Max range">
        <RangeRow
          label="Feature range"
          lo={range[0]}
          hi={range[1]}
          onChangeLo={(v) => set({ feature_range: [v, range[1]] })}
          onChangeHi={(v) => set({ feature_range: [range[0], v] })}
          min={-10} max={10} step={0.1}
          hint="Used when strategy = minmax"
        />
      </ParamSection>

      <ParamSection title="Skip columns">
        <TextRow
          label="Skip cols (comma-separated)"
          value={(params.skip_cols ?? []).join(', ')}
          onChange={(v) => set({ skip_cols: v.split(',').map((s) => s.trim()).filter(Boolean) })}
        />
      </ParamSection>
    </div>
  )
}