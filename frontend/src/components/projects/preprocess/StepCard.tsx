import { type ReactNode } from 'react'
import { GripVertical, ChevronDown, ChevronUp, X } from 'lucide-react'
import type { StepMeta } from './PreprocessTypes'
import type { StepConfig } from '../../../api/preprocess'

interface Props {
  meta:             StepMeta
  index:            number
  enabled:          boolean
  expanded:         boolean
  config:           StepConfig
  onToggleEnabled:  () => void
  onToggleExpanded: () => void
  onRemove:         () => void
  children:         ReactNode
  dragHandleProps?: Record<string, unknown>
}

function MissingSummary({ params }: { params: any }) {
  return (
    <div className="flex flex-wrap gap-1.5 mt-1.5">
      <Chip label={`num: ${params.num_strategy ?? 'median'}`} />
      <Chip label={`cat: ${params.cat_strategy ?? 'mode'}`} variant="neutral" />
      <Chip label={`drop col ≥ ${Math.round((params.drop_col_threshold ?? 0.5) * 100)}%`} variant="neutral" />
    </div>
  )
}

function EncodingSummary({ params }: { params: any }) {
  const skipCols: string[] = params.skip_cols ?? []
  const includedCount = skipCols.length > 0 ? `skip ${skipCols.length} col${skipCols.length > 1 ? 's' : ''}` : 'all cols'
  return (
    <div className="flex flex-wrap gap-1.5 mt-1.5">
      <Chip label={params.default_strategy ?? 'onehot'} />
      <Chip label={`cardinality ≤ ${params.max_onehot_cardinality ?? 20}`} variant="neutral" />
      <Chip label={includedCount} variant={skipCols.length > 0 ? 'skip' : 'neutral'} />
    </div>
  )
}

function OutlierSummary({ params }: { params: any }) {
  const skipCols: string[] = params.skip_cols ?? []
  const bounds: [number, number] = params.winsorize_bounds ?? [0.01, 0.99]
  return (
    <div className="flex flex-wrap gap-1.5 mt-1.5">
      <Chip label={params.default_strategy ?? 'clip'} />
      <Chip label={`IQR k=${params.iqr_k ?? 1.5}`} variant="neutral" />
      {params.default_strategy === 'winsorize' && (
        <Chip label={`${bounds[0]}–${bounds[1]}`} variant="neutral" />
      )}
      {skipCols.map((c) => <Chip key={c} label={c} variant="skip" />)}
    </div>
  )
}

function ScalingSummary({ params }: { params: any }) {
  const skipCols: string[] = params.skip_cols ?? []
  const range: [number, number] = params.feature_range ?? [0, 1]
  return (
    <div className="flex flex-wrap gap-1.5 mt-1.5">
      <Chip label={params.default_strategy ?? 'standard'} />
      {params.default_strategy === 'minmax' && (
        <Chip label={`range ${range[0]}–${range[1]}`} variant="neutral" />
      )}
      {skipCols.map((c) => <Chip key={c} label={c} variant="skip" />)}
    </div>
  )
}

function Chip({ label, variant = 'primary' }: { label: string; variant?: 'primary' | 'neutral' | 'skip' }) {
  const cls = {
    primary: 'bg-primary-50 border-primary-200 text-primary-700',
    neutral: 'bg-gray-100 border-gray-200 text-gray-500',
    skip:    'bg-amber-50 border-amber-200 text-amber-700',
  }[variant]
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded border text-[10px] font-medium ${cls}`}>
      {label}
    </span>
  )
}

function ConfigSummary({ config }: { config: StepConfig }) {
  const p = config.params as any
  if (config.name === 'missing')  return <MissingSummary params={p} />
  if (config.name === 'encoding') return <EncodingSummary params={p} />
  if (config.name === 'outlier')  return <OutlierSummary params={p} />
  if (config.name === 'scaling')  return <ScalingSummary params={p} />
  return null
}

export function StepCard({
  meta, index, enabled, expanded, config,
  onToggleEnabled, onToggleExpanded, onRemove,
  children, dragHandleProps,
}: Props) {
  return (
    <div className={`rounded-xl border transition-all duration-200 ${
      enabled
        ? 'border-gray-200 bg-white shadow-sm'
        : 'border-dashed border-gray-200 bg-gray-50 opacity-60'
    }`}>
      <div className="flex items-start gap-3 px-4 py-3">
        <span
          className="cursor-grab text-gray-300 hover:text-gray-500 touch-none shrink-0 mt-0.5"
          {...dragHandleProps}
        >
          <GripVertical size={16} />
        </span>

        <span className="w-5 h-5 rounded-full bg-gray-100 text-gray-500 text-[10px] font-semibold flex items-center justify-center shrink-0 mt-0.5">
          {index + 1}
        </span>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-800 leading-none">{meta.label}</p>
          <p className="text-xs text-gray-400 mt-0.5 truncate">{meta.description}</p>
          {enabled && !expanded && (
            <ConfigSummary config={config} />
          )}
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          <button
            onClick={onToggleEnabled}
            className={`relative w-9 h-5 rounded-full transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-400 ${
              enabled ? 'bg-primary-500' : 'bg-gray-200'
            }`}
            aria-label={enabled ? 'Disable step' : 'Enable step'}
          >
            <span className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform duration-200 ${
              enabled ? 'translate-x-4' : 'translate-x-0'
            }`} />
          </button>

          {enabled && (
            <button
              onClick={onToggleExpanded}
              className="p-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
              aria-label={expanded ? 'Collapse' : 'Expand'}
            >
              {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>
          )}

          <button
            onClick={onRemove}
            className="p-1 rounded-md text-gray-300 hover:text-red-400 hover:bg-red-50 transition-colors"
            aria-label="Remove step"
          >
            <X size={14} />
          </button>
        </div>
      </div>

      {enabled && expanded && (
        <div className="px-4 pb-4 border-t border-gray-100">
          <div className="pt-3">{children}</div>
        </div>
      )}
    </div>
  )
}