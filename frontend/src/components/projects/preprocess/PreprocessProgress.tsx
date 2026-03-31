import type { StepName } from '../../../api/preprocess'
import { STEP_META } from './PreprocessTypes'

const ORDERED: StepName[] = ['missing', 'encoding', 'outlier', 'scaling']

interface Props {
  step:     string | null
  progress: number
  activeSteps: StepName[]
}

export function PreprocessProgress({ step, progress, activeSteps }: Props) {
  const visibleSteps = ORDERED.filter((k) => activeSteps.includes(k))
  const currentIdx   = visibleSteps.indexOf(step as StepName)

  return (
    <div className="space-y-4">
      <div>
        <div className="flex justify-between text-xs text-gray-500 mb-1.5">
          <span>
            {step === 'done'
              ? 'Complete'
              : step
              ? (STEP_META.find((s) => s.key === step)?.label ?? step)
              : 'Starting…'}
          </span>
          <span>{progress}%</span>
        </div>
        <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-primary-500 rounded-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <ol className="space-y-1.5">
        {visibleSteps.map((key, i) => {
          const meta   = STEP_META.find((m) => m.key === key)!
          const done   = i < currentIdx || step === 'done'
          const active = i === currentIdx && step !== 'done'
          return (
            <li key={key} className="flex items-center gap-3 text-xs">
              <span className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 text-[10px] font-medium transition-colors ${
                done   ? 'bg-primary-500 text-white'
                : active ? 'bg-primary-100 text-primary-700 ring-2 ring-primary-400'
                         : 'bg-gray-100 text-gray-400'
              }`}>
                {done ? '✓' : i + 1}
              </span>
              <span className={
                done   ? 'text-gray-400 line-through'
                : active ? 'text-primary-700 font-medium'
                         : 'text-gray-400'
              }>
                {meta.label}
              </span>
              {active && (
                <span className="ml-auto text-[10px] text-primary-500 animate-pulse">running</span>
              )}
            </li>
          )
        })}
      </ol>
    </div>
  )
}