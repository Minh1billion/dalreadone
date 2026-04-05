import { useRef, useEffect } from 'react'
import type { DraftStep, ColTypeMap } from './PreprocessTypes'
import { OPERATION_OPTIONS, STRATEGY_OPTIONS } from './PreprocessTypes'
import { ColTypeLegend } from './ColTypeLegend'

const SUPPORTED_DTYPES = ['int', 'int32', 'int64', 'float', 'float32', 'float64', 'str', 'bool', 'datetime', 'category']

const DEFAULT_CUSTOM_CODE = `def transform(df):
    df = df.copy()
    # your transformation here
    # df['new_col'] = df['col_a'] + df['col_b']
    return df`

interface Props {
  step:            DraftStep
  index:           number
  colTypeMap:      ColTypeMap
  onChange:        (step: DraftStep) => void
  onRemove:        () => void
  dragHandleProps: Record<string, unknown>
}

function ColSelector({
  cols, colTypeMap, selected, onChange,
}: {
  cols:       string[]
  colTypeMap: ColTypeMap
  selected:   string[] | null
  onChange:   (cols: string[]) => void
}) {
  const sel = selected ?? []
  return (
    <div className='flex flex-wrap gap-1.5 mt-2'>
      {cols.map(col => {
        const active = sel.includes(col)
        const type   = colTypeMap[col] ?? 'unknown'
        const typeColor: Record<string, string> = {
          numeric:     'bg-blue-50 text-blue-600 border-blue-200',
          categorical: 'bg-purple-50 text-purple-600 border-purple-200',
          datetime:    'bg-amber-50 text-amber-600 border-amber-200',
          unknown:     'bg-gray-50 text-gray-500 border-gray-200',
        }
        return (
          <button
            key={col}
            type='button'
            onClick={() => onChange(active ? sel.filter(c => c !== col) : [...sel, col])}
            className={`text-[11px] px-2 py-0.5 rounded border transition-all ${
              active
                ? 'bg-primary-100 text-primary-700 border-primary-300 font-medium'
                : typeColor[type]
            }`}
          >
            {col}
          </button>
        )
      })}
    </div>
  )
}

function CodeEditor({
  code, onChange,
}: {
  code:     string
  onChange: (code: string) => void
}) {
  const ref = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (ref.current) {
      ref.current.style.height = 'auto'
      ref.current.style.height = `${ref.current.scrollHeight}px`
    }
  }, [code])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault()
      const ta    = e.currentTarget
      const start = ta.selectionStart
      const end   = ta.selectionEnd
      const next  = code.slice(0, start) + '    ' + code.slice(end)
      onChange(next)
      requestAnimationFrame(() => {
        ta.selectionStart = ta.selectionEnd = start + 4
      })
    }
  }

  return (
    <div className='mt-2 rounded-lg border border-gray-200 overflow-hidden bg-gray-50'>
      <div className='flex items-center justify-between px-3 py-1.5 border-b border-gray-200 bg-gray-100'>
        <span className='text-[10px] font-medium text-gray-500 tracking-wide uppercase'>Python</span>
        <span className='text-[10px] text-gray-400'>Tab = 4 spaces</span>
      </div>
      <textarea
        ref={ref}
        value={code}
        onChange={e => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        spellCheck={false}
        className='w-full bg-gray-50 font-mono text-[12px] text-gray-800 p-3 resize-none focus:outline-none leading-relaxed min-h-30'
        style={{ fontFamily: 'ui-monospace, "Cascadia Code", Menlo, Consolas, monospace' }}
      />
      <div className='px-3 py-1.5 border-t border-gray-200 bg-gray-100'>
        <p className='text-[10px] text-gray-400'>
          Must define <code className='text-gray-600'>transform(df: pd.DataFrame) -&gt; pd.DataFrame</code>. <code className='text-gray-600'>pd</code> is available.
        </p>
      </div>
    </div>
  )
}

function CastParamsEditor({
  cols, dtypeMap, onChange,
}: {
  cols:     string[]
  dtypeMap: Record<string, string>
  onChange: (map: Record<string, string>) => void
}) {
  if (!cols.length) return (
    <p className='text-[11px] text-gray-400 mt-2'>Select columns above first.</p>
  )
  return (
    <div className='mt-2 space-y-1.5'>
      {cols.map(col => (
        <div key={col} className='flex items-center gap-2'>
          <span className='text-[11px] text-gray-600 w-32 truncate shrink-0'>{col}</span>
          <select
            value={dtypeMap[col] ?? ''}
            onChange={e => onChange({ ...dtypeMap, [col]: e.target.value })}
            className='text-xs border border-gray-200 rounded px-2 py-0.5 bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-primary-400'
          >
            <option value='' disabled>dtype…</option>
            {SUPPORTED_DTYPES.map(d => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>
      ))}
    </div>
  )
}

function BinningParamsEditor({
  cols, binsMap, onChange,
}: {
  cols:    string[]
  binsMap: Record<string, { output_col: string; bins: number }>
  onChange: (map: Record<string, { output_col: string; bins: number }>) => void
}) {
  if (!cols.length) return (
    <p className='text-[11px] text-gray-400 mt-2'>Select columns above first.</p>
  )
  return (
    <div className='mt-2 space-y-2'>
      {cols.map(col => {
        const cfg = binsMap[col] ?? { output_col: `${col}_bin`, bins: 5 }
        return (
          <div key={col} className='flex items-center gap-2 flex-wrap'>
            <span className='text-[11px] text-gray-600 w-24 truncate shrink-0'>{col}</span>
            <div className='flex items-center gap-1'>
              <label className='text-[11px] text-gray-400'>→</label>
              <input
                type='text'
                value={cfg.output_col}
                onChange={e => onChange({ ...binsMap, [col]: { ...cfg, output_col: e.target.value } })}
                placeholder='output_col'
                className='text-xs border border-gray-200 rounded px-2 py-0.5 w-28 focus:outline-none focus:ring-1 focus:ring-primary-400'
              />
            </div>
            <div className='flex items-center gap-1'>
              <label className='text-[11px] text-gray-400'>bins</label>
              <input
                type='number'
                min={2}
                value={cfg.bins}
                onChange={e => onChange({ ...binsMap, [col]: { ...cfg, bins: parseInt(e.target.value) || 5 } })}
                className='text-xs border border-gray-200 rounded px-2 py-0.5 w-16 focus:outline-none focus:ring-1 focus:ring-primary-400'
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}

export function PreprocessStepCard({
  step, index, colTypeMap, onChange, onRemove, dragHandleProps,
}: Props) {
  const allCols      = Object.keys(colTypeMap)
  const isCustomCode = step.operation === 'custom_code'
  const isCast       = step.operation === 'cast'
  const isBinning    = step.strategy === 'binning'
  const strategyOpts = step.operation ? STRATEGY_OPTIONS[step.operation] ?? [] : []

  const handleOperationChange = (op: string) => {
    const strategies   = STRATEGY_OPTIONS[op as keyof typeof STRATEGY_OPTIONS] ?? []
    const autoStrategy = strategies.length === 1 ? strategies[0].value : null
    onChange({
      ...step,
      operation: op as DraftStep['operation'],
      strategy:  autoStrategy,
      params:    op === 'custom_code' ? { code: DEFAULT_CUSTOM_CODE } : {},
      cols:      null,
    })
  }

  const handleStrategyChange = (s: string) => {
    onChange({ ...step, strategy: s, params: {}, cols: null })
  }

  const handleColsChange = (cols: string[]) => {
    const selected = cols.length ? cols : null
    if (isCast) {
      const prevMap   = (step.params.dtype_map as Record<string, string>) ?? {}
      const dtype_map = Object.fromEntries((selected ?? []).map(c => [c, prevMap[c] ?? '']))
      onChange({ ...step, cols: selected, params: { dtype_map } })
    } else if (isBinning) {
      const prevMap = (step.params.bins_map as Record<string, { output_col: string; bins: number }>) ?? {}
      const bins_map = Object.fromEntries(
        (selected ?? []).map(c => [c, prevMap[c] ?? { output_col: `${c}_bin`, bins: 5 }])
      )
      onChange({ ...step, cols: selected, params: { bins_map } })
    } else {
      onChange({ ...step, cols: selected })
    }
  }

  const needsCols  = step.operation && !isCustomCode && step.strategy !== 'drop_row' && step.strategy !== 'drop_duplicates'
  const showParams = step.strategy && !isCustomCode

  return (
    <div className='rounded-lg border border-gray-200 bg-white overflow-hidden'>
      <div className='flex items-center gap-2 px-3 py-2 bg-gray-50 border-b border-gray-100'>
        <button
          {...dragHandleProps}
          className='cursor-grab active:cursor-grabbing text-gray-300 hover:text-gray-500 transition-colors'
          aria-label='Drag to reorder'
        >
          <svg width='12' height='16' viewBox='0 0 12 16' fill='currentColor'>
            <circle cx='3' cy='3'  r='1.5'/><circle cx='9' cy='3'  r='1.5'/>
            <circle cx='3' cy='8'  r='1.5'/><circle cx='9' cy='8'  r='1.5'/>
            <circle cx='3' cy='13' r='1.5'/><circle cx='9' cy='13' r='1.5'/>
          </svg>
        </button>
        <span className='text-[11px] font-medium text-gray-400'>Step {index + 1}</span>
        <div className='flex-1 flex items-center gap-2'>
          <select
            value={step.operation ?? ''}
            onChange={e => handleOperationChange(e.target.value)}
            className='text-xs border border-gray-200 rounded-md px-2 py-1 bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-primary-400'
          >
            <option value='' disabled>Operation…</option>
            {OPERATION_OPTIONS.map(o => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>

          {step.operation && !isCustomCode && strategyOpts.length > 1 && (
            <select
              value={step.strategy ?? ''}
              onChange={e => handleStrategyChange(e.target.value)}
              className='text-xs border border-gray-200 rounded-md px-2 py-1 bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-primary-400'
            >
              <option value='' disabled>Strategy…</option>
              {strategyOpts.map(s => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          )}
        </div>
        <button
          onClick={onRemove}
          className='text-gray-300 hover:text-red-400 transition-colors ml-1'
          aria-label='Remove step'
        >
          <svg width='14' height='14' viewBox='0 0 14 14' fill='none'>
            <path d='M2 2l10 10M12 2L2 12' stroke='currentColor' strokeWidth='1.5' strokeLinecap='round'/>
          </svg>
        </button>
      </div>

      {needsCols && allCols.length > 0 && (
        <div className='px-3 py-2 border-b border-gray-100 flex items-center justify-between'>
          <span className='text-[11px] text-gray-400'>
            Columns <span className='text-gray-300'>(all if none selected)</span>
          </span>
          <ColTypeLegend />
        </div>
      )}

      {isCustomCode && (
        <div className='px-3 pb-3'>
          <CodeEditor
            code={(step.params.code as string) ?? DEFAULT_CUSTOM_CODE}
            onChange={code => onChange({ ...step, strategy: 'custom_code', params: { code } })}
          />
        </div>
      )}

      {showParams && (
        <div className='px-3 pb-1'>
          {step.strategy === 'constant' && (
            <div className='mt-2 flex items-center gap-2'>
              <label className='text-[11px] text-gray-500 shrink-0'>Fill value</label>
              <input
                type='text'
                value={(step.params.fill_value as string) ?? ''}
                onChange={e => onChange({ ...step, params: { ...step.params, fill_value: e.target.value } })}
                placeholder='0'
                className='text-xs border border-gray-200 rounded px-2 py-1 w-32 focus:outline-none focus:ring-1 focus:ring-primary-400'
              />
            </div>
          )}

          {(step.strategy === 'iqr' || step.strategy === 'zscore') && (
            <div className='mt-2 flex items-center gap-3'>
              <label className='text-[11px] text-gray-500'>Action</label>
              {(['clip', 'drop'] as const).map(a => (
                <label key={a} className='flex items-center gap-1 text-xs text-gray-600 cursor-pointer'>
                  <input
                    type='radio'
                    name={`action-${step.id}`}
                    value={a}
                    checked={(step.params.action ?? 'clip') === a}
                    onChange={() => onChange({ ...step, params: { ...step.params, action: a } })}
                  />
                  {a}
                </label>
              ))}
              {step.strategy === 'zscore' && (
                <>
                  <label className='text-[11px] text-gray-500 ml-2'>Threshold</label>
                  <input
                    type='number'
                    step='0.5'
                    min='1'
                    value={(step.params.threshold as number) ?? 3}
                    onChange={e => onChange({ ...step, params: { ...step.params, threshold: parseFloat(e.target.value) } })}
                    className='text-xs border border-gray-200 rounded px-2 py-1 w-16 focus:outline-none focus:ring-1 focus:ring-primary-400'
                  />
                </>
              )}
            </div>
          )}

          {step.strategy === 'percentile_clip' && (
            <div className='mt-2 flex items-center gap-3'>
              <label className='text-[11px] text-gray-500'>Lower</label>
              <input
                type='number' step='0.01' min='0' max='0.49'
                value={(step.params.lower as number) ?? 0.05}
                onChange={e => onChange({ ...step, params: { ...step.params, lower: parseFloat(e.target.value) } })}
                className='text-xs border border-gray-200 rounded px-2 py-1 w-20 focus:outline-none focus:ring-1 focus:ring-primary-400'
              />
              <label className='text-[11px] text-gray-500'>Upper</label>
              <input
                type='number' step='0.01' min='0.51' max='1'
                value={(step.params.upper as number) ?? 0.95}
                onChange={e => onChange({ ...step, params: { ...step.params, upper: parseFloat(e.target.value) } })}
                className='text-xs border border-gray-200 rounded px-2 py-1 w-20 focus:outline-none focus:ring-1 focus:ring-primary-400'
              />
            </div>
          )}

          {step.strategy === 'minmax' && (
            <div className='mt-2 flex items-center gap-3'>
              <label className='text-[11px] text-gray-500'>Range</label>
              <input
                type='number' step='0.1'
                value={((step.params.feature_range as [number, number]) ?? [0, 1])[0]}
                onChange={e => onChange({ ...step, params: { ...step.params, feature_range: [parseFloat(e.target.value), ((step.params.feature_range as [number, number]) ?? [0, 1])[1]] } })}
                className='text-xs border border-gray-200 rounded px-2 py-1 w-16 focus:outline-none focus:ring-1 focus:ring-primary-400'
              />
              <span className='text-gray-400 text-xs'>to</span>
              <input
                type='number' step='0.1'
                value={((step.params.feature_range as [number, number]) ?? [0, 1])[1]}
                onChange={e => onChange({ ...step, params: { ...step.params, feature_range: [((step.params.feature_range as [number, number]) ?? [0, 1])[0], parseFloat(e.target.value)] } })}
                className='text-xs border border-gray-200 rounded px-2 py-1 w-16 focus:outline-none focus:ring-1 focus:ring-primary-400'
              />
            </div>
          )}

          {step.strategy === 'drop_duplicates' && (
            <div className='mt-2 flex items-center gap-3'>
              <label className='text-[11px] text-gray-500'>Keep</label>
              {(['first', 'last'] as const).map(k => (
                <label key={k} className='flex items-center gap-1 text-xs text-gray-600 cursor-pointer'>
                  <input
                    type='radio'
                    name={`keep-${step.id}`}
                    value={k}
                    checked={(step.params.keep ?? 'first') === k}
                    onChange={() => onChange({ ...step, params: { ...step.params, keep: k } })}
                  />
                  {k}
                </label>
              ))}
              <p className='text-[11px] text-gray-400 ml-1'>(columns below = subset, empty = all)</p>
            </div>
          )}
        </div>
      )}

      {needsCols && allCols.length > 0 && (
        <div className='px-3 pb-2'>
          {(isCast || isBinning) && (
            <p className='text-[11px] text-gray-400 mt-2 mb-1'>
              {isCast ? 'Select columns to cast' : 'Select columns to bin'}
            </p>
          )}
          <ColSelector
            cols={allCols}
            colTypeMap={colTypeMap}
            selected={step.cols}
            onChange={handleColsChange}
          />

          {isCast && step.cols && step.cols.length > 0 && (
            <CastParamsEditor
              cols={step.cols}
              dtypeMap={(step.params.dtype_map as Record<string, string>) ?? {}}
              onChange={dtype_map => onChange({ ...step, params: { dtype_map } })}
            />
          )}

          {isBinning && step.cols && step.cols.length > 0 && (
            <BinningParamsEditor
              cols={step.cols}
              binsMap={(step.params.bins_map as Record<string, { output_col: string; bins: number }>) ?? {}}
              onChange={bins_map => onChange({ ...step, params: { bins_map } })}
            />
          )}
        </div>
      )}
    </div>
  )
}