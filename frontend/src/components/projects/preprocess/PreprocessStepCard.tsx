import { useRef, useEffect } from 'react'
import type { DraftStep, ColTypeMap } from './PreprocessTypes'
import { OPERATION_OPTIONS, STRATEGY_OPTIONS } from './PreprocessTypes'

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
  cols: string[]
  colTypeMap: ColTypeMap
  selected: string[] | null
  onChange: (cols: string[]) => void
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
  code: string
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

export function PreprocessStepCard({
  step, index, colTypeMap, onChange, onRemove, dragHandleProps,
}: Props) {
  const allCols       = Object.keys(colTypeMap)
  const isCustomCode  = step.operation === 'custom_code'
  const strategyOpts  = step.operation ? STRATEGY_OPTIONS[step.operation] : []

  const handleOperationChange = (op: string) => {
    const strategies = STRATEGY_OPTIONS[op as keyof typeof STRATEGY_OPTIONS] ?? []
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

  const needsCols = step.operation && !isCustomCode && step.strategy !== 'drop_row'
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

          {step.operation && !isCustomCode && (
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

      {/* Custom code editor */}
      {isCustomCode && (
        <div className='px-3 pb-3'>
          <CodeEditor
            code={(step.params.code as string) ?? DEFAULT_CUSTOM_CODE}
            onChange={code => onChange({ ...step, strategy: 'custom_code', params: { code } })}
          />
        </div>
      )}

      {/* Params for standard operations */}
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
                value={((step.params.feature_range as [number,number]) ?? [0, 1])[0]}
                onChange={e => onChange({ ...step, params: { ...step.params, feature_range: [parseFloat(e.target.value), ((step.params.feature_range as [number,number]) ?? [0, 1])[1]] } })}
                className='text-xs border border-gray-200 rounded px-2 py-1 w-16 focus:outline-none focus:ring-1 focus:ring-primary-400'
              />
              <span className='text-gray-400 text-xs'>to</span>
              <input
                type='number' step='0.1'
                value={((step.params.feature_range as [number,number]) ?? [0, 1])[1]}
                onChange={e => onChange({ ...step, params: { ...step.params, feature_range: [((step.params.feature_range as [number,number]) ?? [0, 1])[0], parseFloat(e.target.value)] } })}
                className='text-xs border border-gray-200 rounded px-2 py-1 w-16 focus:outline-none focus:ring-1 focus:ring-primary-400'
              />
            </div>
          )}
        </div>
      )}

      {/* Column selector - not shown for custom_code */}
      {needsCols && allCols.length > 0 && (
        <div className='px-3 pb-3'>
          <p className='text-[11px] text-gray-400 mt-2 mb-1'>
            Columns <span className='text-gray-300'>(all if none selected)</span>
          </p>
          <ColSelector
            cols={allCols}
            colTypeMap={colTypeMap}
            selected={step.cols}
            onChange={cols => onChange({ ...step, cols: cols.length ? cols : null })}
          />
        </div>
      )}
    </div>
  )
}