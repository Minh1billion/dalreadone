import { useEDA } from '../../../hooks/useEDA'
import { useReview } from '../../../hooks/useReview'
import { EDAResultDashboard } from './EDAResultDashboard'
import { EDAReviewPanel } from './EDAReviewPanel'

const EDA_STEPS = [
  { key: 'schema',                 label: 'Schema profile' },
  { key: 'missing_and_duplicates', label: 'Missing & duplicates' },
  { key: 'univariate',             label: 'Univariate stats' },
  { key: 'datetime',               label: 'Datetime analysis' },
  { key: 'correlations',           label: 'Correlations' },
  { key: 'distributions',          label: 'Distributions' },
  { key: 'data_quality_score',     label: 'Quality score' },
]

interface EDASectonProps {
  eda:        ReturnType<typeof useEDA>
  activeFile: any
}

export function EDASection({ eda, activeFile }: EDASectonProps) {
  const currentStepIdx = eda.step
    ? EDA_STEPS.findIndex(s => s.key === eda.step)
    : -1

  const review = useReview(eda.isDone ? eda.taskId : null)

  return (
    <section className='bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden'>

      {/* Header */}
      <div className='px-5 py-3 border-b border-gray-100 flex items-center justify-between'>
        <h2 className='text-sm font-semibold text-gray-700'>EDA Analysis</h2>
        <div className='flex items-center gap-2'>

          {/* AI Review button */}
          {eda.isDone && !eda.isRunning && (
            <button
              onClick={review.start}
              disabled={review.starting || review.isRunning}
              className='text-xs px-3 py-1.5 rounded-md border border-primary-300 text-primary-700
                         hover:bg-primary-50 disabled:opacity-50 transition-colors'
            >
              {review.starting  ? 'Starting…'  :
               review.isRunning ? 'Reviewing…' :
               review.isDone    ? 'Re-review'  : '✦ AI Review'}
            </button>
          )}

          {/* Run EDA button */}
          {!eda.isRunning && (
            <button
              onClick={() => { eda.start(); review.reset(); }}
              disabled={eda.starting}
              className='text-xs px-3 py-1.5 rounded-md bg-primary-600 text-white
                         hover:bg-primary-700 disabled:opacity-50 transition-colors'
            >
              {eda.starting ? 'Starting…' : eda.isDone ? 'Re-run' : 'Run EDA'}
            </button>
          )}

        </div>
      </div>

      <div className='p-5 space-y-5'>

        {/* idle state */}
        {!eda.taskId && !eda.starting && !eda.startError && (
          <p className='text-sm text-gray-400 text-center py-6'>
            Click "Run EDA" to analyze this file.
          </p>
        )}

        {eda.startError && (
          <p className='text-sm text-red-500 py-2'>{eda.startError}</p>
        )}

        {/* Progress */}
        {(eda.isRunning || eda.starting) && (
          <div className='space-y-4'>
            <div>
              <div className='flex justify-between text-xs text-gray-500 mb-1.5'>
                <span>
                  {eda.step
                    ? EDA_STEPS.find(s => s.key === eda.step)?.label ?? eda.step
                    : 'Starting…'}
                </span>
                <span>{eda.progress}%</span>
              </div>
              <div className='h-1.5 bg-gray-100 rounded-full overflow-hidden'>
                <div
                  className='h-full bg-primary-500 rounded-full transition-all duration-500'
                  style={{ width: `${eda.progress}%` }}
                />
              </div>
            </div>
            <ol className='grid grid-cols-2 gap-x-6 gap-y-1.5'>
              {EDA_STEPS.map((s, i) => {
                const done   = i < currentStepIdx
                const active = i === currentStepIdx
                return (
                  <li key={s.key} className='flex items-center gap-2 text-xs'>
                    <span className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0
                      text-[9px] font-medium transition-colors ${
                        done   ? 'bg-primary-500 text-white' :
                        active ? 'bg-primary-100 text-primary-700 ring-1 ring-primary-400' :
                                 'bg-gray-100 text-gray-400'
                      }`}>
                      {done ? '✓' : i + 1}
                    </span>
                    <span className={
                      done   ? 'text-gray-400 line-through' :
                      active ? 'text-primary-700 font-medium' :
                               'text-gray-400'
                    }>
                      {s.label}
                    </span>
                    {active && (
                      <span className='ml-auto text-[9px] text-primary-400 animate-pulse'>•</span>
                    )}
                  </li>
                )
              })}
            </ol>
          </div>
        )}

        {/* EDA error */}
        {eda.isError && (
          <div className='rounded-lg bg-red-50 border border-red-100 p-4 text-sm text-red-600'>
            <p className='font-medium mb-1'>Analysis failed</p>
            <p className='text-xs text-red-500'>{eda.edaError}</p>
            <button onClick={eda.start} className='mt-3 text-xs underline hover:text-red-700'>
              Retry
            </button>
          </div>
        )}

        {/* EDA result */}
        {eda.isDone && eda.result && (
          <EDAResultDashboard result={eda.result} filename={activeFile?.filename} />
        )}

        {/* Review panel */}
        {eda.isDone && review.reviewTaskId && (
          <EDAReviewPanel review={review} />
        )}

      </div>
    </section>
  )
}