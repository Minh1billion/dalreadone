import { useState, useEffect } from 'react'
import { OPERATION_LABELS, STRATEGY_MAP, getFilteredCols } from './PreprocessTypes'
import type { DraftStep, ColTypeMap, OperationType } from './PreprocessTypes'

interface Props {
  step: DraftStep
  index: number
  colTypeMap: ColTypeMap
  onChange: (step: DraftStep) => void
  onRemove: () => void
  dragHandleProps?: React.HTMLAttributes<HTMLDivElement>
}

const OPERATIONS: OperationType[] = ['missing', 'encoding', 'outlier', 'scaling']

export function PreprocessStepCard({ step, index, colTypeMap, onChange, onRemove, dragHandleProps }: Props) {
  const [ordinalRaw,   setOrdinalRaw]   = useState<string>(step.params.order ? JSON.stringify(step.params.order) : '')
  const [ordinalError, setOrdinalError] = useState(false)

  useEffect(() => {
    if (step.strategy !== 'ordinal') {
      setOrdinalRaw('')
      setOrdinalError(false)
    }
  }, [step.strategy])

  const strategies    = step.operation ? STRATEGY_MAP[step.operation] : []
  const selectedMeta  = strategies.find(s => s.value === step.strategy) ?? null
  const availableCols = selectedMeta ? getFilteredCols(colTypeMap, selectedMeta.colFilter) : []
  const selectedCols  = step.cols ?? []

  function setOperation(op: OperationType) {
    onChange({ ...step, operation: op, strategy: null, params: {}, cols: null })
  }

  function setStrategy(value: string) {
    const meta = STRATEGY_MAP[step.operation!].find(s => s.value === value)!
    onChange({ ...step, strategy: value, params: { ...meta.defaultParams }, cols: null })
  }

  function toggleCol(col: string) {
    const next = selectedCols.includes(col)
      ? selectedCols.filter(c => c !== col)
      : [...selectedCols, col]
    onChange({ ...step, cols: next.length === 0 ? null : next })
  }

  function selectAllCols() {
    onChange({ ...step, cols: availableCols.length === selectedCols.length ? null : [...availableCols] })
  }

  function setParam(key: string, value: unknown) {
    onChange({ ...step, params: { ...step.params, [key]: value } })
  }

  function handleOrdinalChange(raw: string) {
    setOrdinalRaw(raw)
    if (!raw.trim()) {
      setOrdinalError(false)
      setParam('order', null)
      return
    }
    try {
      const parsed = JSON.parse(raw)
      setOrdinalError(false)
      setParam('order', parsed)
    } catch {
      setOrdinalError(true)
    }
  }

  const isComplete = !!step.operation && !!step.strategy

  return (
    <div className='rounded-lg border border-gray-100 bg-white shadow-sm overflow-hidden'>
      <div className='flex items-center gap-2 px-3 py-2 bg-gray-50 border-b border-gray-100'>
        <div
          {...dragHandleProps}
          className='cursor-grab active:cursor-grabbing text-gray-300 hover:text-gray-400 select-none px-0.5'
          title='Drag to reorder'
        >
          ⠿
        </div>
        <span className='text-[10px] font-semibold text-gray-400 uppercase tracking-wider'>Step {index + 1}</span>
        {step.operation && (
          <span className='text-[10px] font-medium text-primary-600 bg-primary-50 px-1.5 py-0.5 rounded'>
            {OPERATION_LABELS[step.operation]}
          </span>
        )}
        <button
          onClick={onRemove}
          className='ml-auto text-gray-300 hover:text-red-400 transition-colors text-sm leading-none'
          title='Remove step'
        >
          ×
        </button>
      </div>

      <div className='p-3 space-y-3'>
        <div className='grid grid-cols-2 gap-2'>
          <div>
            <label className='block text-[10px] font-medium text-gray-500 mb-1'>Operation</label>
            <select
              value={step.operation ?? ''}
              onChange={e => setOperation(e.target.value as OperationType)}
              className='w-full text-xs border border-gray-200 rounded-md px-2 py-1.5 bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-primary-400'
            >
              <option value=''>Select…</option>
              {OPERATIONS.map(op => (
                <option key={op} value={op}>{OPERATION_LABELS[op]}</option>
              ))}
            </select>
          </div>

          <div>
            <label className='block text-[10px] font-medium text-gray-500 mb-1'>Strategy</label>
            <select
              value={step.strategy ?? ''}
              onChange={e => setStrategy(e.target.value)}
              disabled={!step.operation}
              className='w-full text-xs border border-gray-200 rounded-md px-2 py-1.5 bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-primary-400 disabled:opacity-40 disabled:cursor-not-allowed'
            >
              <option value=''>Select…</option>
              {strategies.map(s => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>
        </div>

        {step.strategy === 'constant' && (
          <div>
            <label className='block text-[10px] font-medium text-gray-500 mb-1'>Fill value</label>
            <input
              type='text'
              value={String(step.params.fill_value ?? 0)}
              onChange={e => {
                const v = e.target.value
                setParam('fill_value', isNaN(Number(v)) ? v : Number(v))
              }}
              className='w-full text-xs border border-gray-200 rounded-md px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary-400'
            />
          </div>
        )}

        {step.strategy === 'zscore' && (
          <div className='grid grid-cols-2 gap-2'>
            <div>
              <label className='block text-[10px] font-medium text-gray-500 mb-1'>Threshold</label>
              <input
                type='number'
                step='0.1'
                value={Number(step.params.threshold ?? 3.0)}
                onChange={e => setParam('threshold', parseFloat(e.target.value))}
                className='w-full text-xs border border-gray-200 rounded-md px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary-400'
              />
            </div>
            <div>
              <label className='block text-[10px] font-medium text-gray-500 mb-1'>Action</label>
              <select
                value={String(step.params.action ?? 'clip')}
                onChange={e => setParam('action', e.target.value)}
                className='w-full text-xs border border-gray-200 rounded-md px-2 py-1.5 bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-primary-400'
              >
                <option value='clip'>Clip</option>
                <option value='drop'>Drop</option>
              </select>
            </div>
          </div>
        )}

        {step.strategy === 'iqr' && (
          <div>
            <label className='block text-[10px] font-medium text-gray-500 mb-1'>Action</label>
            <select
              value={String(step.params.action ?? 'clip')}
              onChange={e => setParam('action', e.target.value)}
              className='w-full text-xs border border-gray-200 rounded-md px-2 py-1.5 bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-primary-400'
            >
              <option value='clip'>Clip</option>
              <option value='drop'>Drop</option>
            </select>
          </div>
        )}

        {step.strategy === 'percentile_clip' && (
          <div className='grid grid-cols-2 gap-2'>
            <div>
              <label className='block text-[10px] font-medium text-gray-500 mb-1'>Lower (%)</label>
              <input
                type='number'
                step='0.01'
                min='0'
                max='0.5'
                value={Number(step.params.lower ?? 0.05)}
                onChange={e => setParam('lower', parseFloat(e.target.value))}
                className='w-full text-xs border border-gray-200 rounded-md px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary-400'
              />
            </div>
            <div>
              <label className='block text-[10px] font-medium text-gray-500 mb-1'>Upper (%)</label>
              <input
                type='number'
                step='0.01'
                min='0.5'
                max='1'
                value={Number(step.params.upper ?? 0.95)}
                onChange={e => setParam('upper', parseFloat(e.target.value))}
                className='w-full text-xs border border-gray-200 rounded-md px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary-400'
              />
            </div>
          </div>
        )}

        {step.strategy === 'minmax' && (
          <div className='grid grid-cols-2 gap-2'>
            <div>
              <label className='block text-[10px] font-medium text-gray-500 mb-1'>Range min</label>
              <input
                type='number'
                step='0.1'
                value={Number((step.params.feature_range as [number, number])?.[0] ?? 0)}
                onChange={e => setParam('feature_range', [parseFloat(e.target.value), (step.params.feature_range as [number, number])?.[1] ?? 1])}
                className='w-full text-xs border border-gray-200 rounded-md px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary-400'
              />
            </div>
            <div>
              <label className='block text-[10px] font-medium text-gray-500 mb-1'>Range max</label>
              <input
                type='number'
                step='0.1'
                value={Number((step.params.feature_range as [number, number])?.[1] ?? 1)}
                onChange={e => setParam('feature_range', [(step.params.feature_range as [number, number])?.[0] ?? 0, parseFloat(e.target.value)])}
                className='w-full text-xs border border-gray-200 rounded-md px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary-400'
              />
            </div>
          </div>
        )}

        {step.strategy === 'ordinal' && (
          <div>
            <label className='block text-[10px] font-medium text-gray-500 mb-1'>
              Order <span className='text-gray-400 font-normal'>(leave empty for auto)</span>
            </label>
            <textarea
              rows={2}
              placeholder='{"size": ["S","M","L","XL"]}'
              value={ordinalRaw}
              onChange={e => handleOrdinalChange(e.target.value)}
              className={`w-full text-xs border rounded-md px-2 py-1.5 font-mono focus:outline-none focus:ring-1 resize-none transition-colors ${
                ordinalError
                  ? 'border-red-300 focus:ring-red-300 bg-red-50'
                  : 'border-gray-200 focus:ring-primary-400'
              }`}
            />
            {ordinalError && (
              <p className='text-[10px] text-red-400 mt-1'>Invalid JSON — check your syntax</p>
            )}
          </div>
        )}

        {isComplete && availableCols.length > 0 && (
          <div>
            <div className='flex items-center justify-between mb-1.5'>
              <label className='text-[10px] font-medium text-gray-500'>
                Columns
                <span className='ml-1 text-gray-400 font-normal'>
                  ({selectedMeta?.colFilter === 'all' ? 'all types' : selectedMeta?.colFilter})
                </span>
              </label>
              <button
                onClick={selectAllCols}
                className='text-[10px] text-primary-500 hover:text-primary-700'
              >
                {selectedCols.length === availableCols.length ? 'Deselect all' : 'Select all'}
              </button>
            </div>
            <div className='flex flex-wrap gap-1.5 max-h-28 overflow-y-auto'>
              {availableCols.map(col => {
                const selected = selectedCols.includes(col)
                return (
                  <button
                    key={col}
                    onClick={() => toggleCol(col)}
                    className={`text-[10px] px-2 py-0.5 rounded-full border transition-colors truncate max-w-35 ${
                      selected
                        ? 'bg-primary-50 border-primary-300 text-primary-700 font-medium'
                        : 'bg-white border-gray-200 text-gray-500 hover:border-gray-300'
                    }`}
                    title={col}
                  >
                    {col}
                  </button>
                )
              })}
            </div>
            {selectedCols.length === 0 && (
              <p className='text-[10px] text-amber-500 mt-1'>
                No columns selected — all compatible columns will be processed.
              </p>
            )}
          </div>
        )}

        {isComplete && availableCols.length === 0 && (
          <p className='text-[10px] text-red-400'>
            No compatible columns found for this strategy.
          </p>
        )}
      </div>
    </div>
  )
}