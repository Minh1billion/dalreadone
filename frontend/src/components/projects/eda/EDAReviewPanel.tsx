import { useReview } from '../../../hooks/useReview'

const SEV_STYLE = {
  high:   'bg-red-50   text-red-700   border-red-200',
  medium: 'bg-amber-50 text-amber-700 border-amber-200',
  low:    'bg-green-50 text-green-700 border-green-200',
}
const PRI_STYLE = {
  must:     'bg-red-100   text-red-700',
  should:   'bg-amber-100 text-amber-700',
  optional: 'bg-gray-100  text-gray-600',
}

interface Props {
  review: ReturnType<typeof useReview>
}

export function EDAReviewPanel({ review }: Props) {

  if (review.isRunning || review.starting) {
    return (
      <div className='rounded-xl border border-primary-100 bg-primary-50/40 p-5'>
        <div className='flex items-center gap-3 mb-3'>
          <span className='text-sm font-medium text-primary-700'>AI Review</span>
          <span className='text-xs text-primary-400 animate-pulse'>Analyzing…</span>
        </div>
        <div className='h-1.5 bg-primary-100 rounded-full overflow-hidden'>
          <div
            className='h-full bg-primary-400 rounded-full transition-all duration-500'
            style={{ width: `${review.progress}%` }}
          />
        </div>
      </div>
    )
  }

  if (review.isError) {
    return (
      <div className='rounded-xl border border-red-100 bg-red-50 p-4 text-sm text-red-600'>
        <p className='font-medium mb-1'>Review failed</p>
        <p className='text-xs'>{review.error}</p>
        <button onClick={review.start} className='mt-2 text-xs underline'>Retry</button>
      </div>
    )
  }

  if (!review.isDone || !review.result) return null

  const { issues, prep_steps, opportunities } = review.result
  const usage = review.usage?.summary

  return (
    <div className='rounded-xl border border-primary-100 overflow-hidden'>

      {/* Header */}
      <div className='px-5 py-3 bg-primary-50 border-b border-primary-100 flex items-center justify-between'>
        <span className='text-sm font-semibold text-primary-800'>✦ AI Review</span>
        {usage && (
          <span className='text-[11px] text-primary-400'>
            {usage.total_tokens.toLocaleString()} tokens · ${usage.total_cost_usd.toFixed(6)}
          </span>
        )}
      </div>

      <div className='divide-y divide-gray-50'>

        {/* Issues */}
        {issues.length > 0 && (
          <div className='p-5 space-y-2'>
            <p className='text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3'>
              Issues ({issues.length})
            </p>
            {issues.map((issue, i) => (
              <div
                key={i}
                className={`rounded-lg border p-3 text-xs ${SEV_STYLE[issue.severity]}`}
              >
                <div className='flex items-center gap-2 mb-1'>
                  <code className='font-mono font-semibold'>{issue.col}</code>
                  <span className='uppercase text-[10px] font-medium opacity-70'>
                    {issue.severity}
                  </span>
                </div>
                <p className='mb-0.5'>{issue.detail}</p>
                <p className='opacity-70'>Impact: {issue.impact}</p>
              </div>
            ))}
          </div>
        )}

        {/* Prep steps */}
        {prep_steps.length > 0 && (
          <div className='p-5 space-y-2'>
            <p className='text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3'>
              Preprocessing ({prep_steps.length})
            </p>
            {prep_steps.map((step, i) => (
              <div key={i} className='flex items-start gap-3 text-xs'>
                <span className={`shrink-0 px-1.5 py-0.5 rounded text-[10px] font-medium ${PRI_STYLE[step.priority]}`}>
                  {step.priority}
                </span>
                <div>
                  <code className='font-mono text-gray-700'>{step.action}</code>
                  {step.col && (
                    <span className='text-gray-400'> → {step.col}</span>
                  )}
                  <p className='text-gray-500 mt-0.5'>{step.rationale}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Opportunities */}
        {opportunities.length > 0 && (
          <div className='p-5'>
            <p className='text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3'>
              Opportunities
            </p>
            <ul className='space-y-1.5'>
              {opportunities.map((opp, i) => (
                <li key={i} className='text-xs text-gray-600 flex gap-2'>
                  <span className='text-primary-400 shrink-0'>→</span>
                  {opp}
                </li>
              ))}
            </ul>
          </div>
        )}

      </div>
    </div>
  )
}