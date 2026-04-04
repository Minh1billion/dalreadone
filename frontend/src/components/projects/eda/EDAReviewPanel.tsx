import type { useReview } from '../../../hooks/useReview'
import type { ReviewResult } from '../../../api/eda'

const SEVERITY_STYLES = {
  critical: 'bg-red-50 border-red-200 text-red-700',
  warning:  'bg-amber-50 border-amber-200 text-amber-700',
  info:     'bg-blue-50 border-blue-200 text-blue-600',
}

const SEVERITY_DOT = {
  critical: 'bg-red-400',
  warning:  'bg-amber-400',
  info:     'bg-blue-400',
}

const CONFIDENCE_STYLES = {
  high:   'bg-green-50 text-green-700 border-green-200',
  medium: 'bg-amber-50 text-amber-700 border-amber-200',
  low:    'bg-red-50 text-red-600 border-red-200',
}

const RELATIONSHIP_STYLES: Record<string, string> = {
  redundant:  'bg-red-50 text-red-600 border-red-200',
  derived:    'bg-purple-50 text-purple-600 border-purple-200',
  leakage:    'bg-orange-50 text-orange-600 border-orange-200',
  correlated: 'bg-blue-50 text-blue-600 border-blue-200',
  group_key:  'bg-gray-50 text-gray-600 border-gray-200',
}

const SEMANTIC_BADGE: Record<string, string> = {
  target:              'bg-violet-100 text-violet-700',
  derived:             'bg-purple-100 text-purple-700',
  ordinal:             'bg-blue-100 text-blue-700',
  continuous:          'bg-teal-100 text-teal-700',
  categorical_nominal: 'bg-gray-100 text-gray-600',
  categorical_encoded: 'bg-gray-100 text-gray-600',
  datetime:            'bg-amber-100 text-amber-700',
  binary:              'bg-green-100 text-green-700',
  id:                  'bg-red-100 text-red-600',
  text:                'bg-orange-100 text-orange-700',
}

interface Props {
  review: ReturnType<typeof useReview>
}

export function EDAReviewPanel({ review }: Props) {
  if (review.starting || (review.isRunning && !review.result)) {
    return (
      <div className="rounded-xl border border-violet-100 bg-violet-50/40 p-5 space-y-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-violet-700 tracking-wide uppercase">AI Review</span>
          <span className="text-[10px] text-violet-400 animate-pulse">running…</span>
        </div>
        <div>
          <div className="flex justify-between text-xs text-violet-400 mb-1.5">
            <span>Analyzing dataset…</span>
            <span>{review.progress}%</span>
          </div>
          <div className="h-1.5 bg-violet-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-violet-500 rounded-full transition-all duration-500"
              style={{ width: `${review.progress}%` }}
            />
          </div>
        </div>
      </div>
    )
  }

  if (review.isError) {
    return (
      <div className="rounded-xl border border-red-100 bg-red-50 p-4 space-y-1.5">
        <p className="text-xs font-semibold text-red-600">AI Review failed</p>
        <p className="text-xs text-red-500">{review.reviewError}</p>
        <button onClick={review.start} className="text-xs underline text-red-500 hover:text-red-700 mt-1">
          Retry
        </button>
      </div>
    )
  }

  if (review.startError) {
    return (
      <div className="rounded-xl border border-red-100 bg-red-50 p-4 space-y-1.5">
        <p className="text-xs font-semibold text-red-600">Could not start review</p>
        <p className="text-xs text-red-500">{review.startError}</p>
      </div>
    )
  }

  if (!review.isDone || !review.result) return null

  const r: ReviewResult = review.result

  return (
    <div className="space-y-4 pt-1">

      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-violet-700 tracking-wide uppercase">AI Review</span>
        <span className="w-px h-3 bg-gray-200" />
        <span className="text-xs text-gray-400">powered by LLM</span>
      </div>

      {/* Domain */}
      <div className="rounded-xl border border-gray-100 bg-white p-4 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-gray-600">Domain</span>
          <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${CONFIDENCE_STYLES[r.domain.confidence]}`}>
            {r.domain.confidence} confidence
          </span>
        </div>
        <p className="text-sm font-semibold text-gray-800">{r.domain.prediction}</p>
        <p className="text-xs text-gray-500 leading-relaxed">{r.domain.reasoning}</p>
        {r.domain.data_characteristics.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {r.domain.data_characteristics.map(c => (
              <span key={c} className="text-[10px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">{c}</span>
            ))}
          </div>
        )}
      </div>

      {/* Issues */}
      {r.issues.length > 0 && (
        <div className="rounded-xl border border-gray-100 bg-white p-4 space-y-3">
          <span className="text-xs font-semibold text-gray-600">Issues detected</span>
          <div className="space-y-2">
            {r.issues.map((issue, i) => (
              <div key={i} className={`rounded-lg border px-3 py-2.5 flex gap-2.5 items-start ${SEVERITY_STYLES[issue.severity]}`}>
                <span className={`mt-1 w-1.5 h-1.5 rounded-full shrink-0 ${SEVERITY_DOT[issue.severity]}`} />
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    {issue.column && (
                      <code className="text-[10px] font-mono font-medium">{issue.column}</code>
                    )}
                    <span className="text-[10px] opacity-70">{issue.type.replace(/_/g, ' ')}</span>
                  </div>
                  <p className="text-xs">{issue.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Drop candidates */}
      {r.drop_candidates.length > 0 && (
        <div className="rounded-xl border border-red-100 bg-red-50/50 p-4 space-y-2">
          <span className="text-xs font-semibold text-red-600">Columns to drop</span>
          <div className="space-y-2">
            {r.drop_candidates.map(d => (
              <div key={d.column} className="flex items-start gap-2">
                <code className="text-[10px] font-mono bg-red-100 text-red-600 px-1.5 py-0.5 rounded shrink-0">{d.column}</code>
                <span className="text-xs text-red-500">{d.reason}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Keep columns */}
      {r.keep_columns.length > 0 && (
        <div className="rounded-xl border border-gray-100 bg-white p-4 space-y-2">
          <span className="text-xs font-semibold text-gray-600">Columns to keep</span>
          <div className="flex flex-wrap gap-1.5">
            {r.keep_columns.map(col => (
              <span key={col} className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-green-50 border border-green-200 text-green-700">
                {col}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Semantic types */}
      <div className="rounded-xl border border-gray-100 bg-white p-4 space-y-3">
        <span className="text-xs font-semibold text-gray-600">Semantic types</span>
        <div className="divide-y divide-gray-50">
          {r.semantic_types.map(s => (
            <div key={s.column} className="py-2.5 flex items-start gap-3">
              <code className="text-[10px] font-mono text-gray-500 w-32 shrink-0 pt-0.5 truncate">{s.column}</code>
              <div className="flex flex-wrap items-center gap-1.5 flex-1">
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${SEMANTIC_BADGE[s.semantic_type] ?? 'bg-gray-100 text-gray-600'}`}>
                  {s.semantic_type}
                </span>
                {s.needs_cast && s.cast_to && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-50 border border-amber-200 text-amber-600">
                    cast → {s.cast_to}
                  </span>
                )}
                <span className="text-[10px] text-gray-400 leading-relaxed">{s.reasoning}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Column relationships */}
      {r.column_relationships.length > 0 && (
        <div className="rounded-xl border border-gray-100 bg-white p-4 space-y-3">
          <span className="text-xs font-semibold text-gray-600">Column relationships</span>
          <div className="space-y-2.5">
            {r.column_relationships.map((rel, i) => (
              <div key={i} className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  {rel.columns.map(col => (
                    <code key={col} className="text-[10px] font-mono bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                      {col}
                    </code>
                  ))}
                  <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium ${RELATIONSHIP_STYLES[rel.relationship_type] ?? 'bg-gray-50 text-gray-500 border-gray-200'}`}>
                    {rel.relationship_type}
                  </span>
                  <span className="text-[10px] text-gray-400 ml-auto">
                    {rel.strength > 0 ? (rel.strength < 0 ? '' : '') : ''}{rel.strength.toFixed(2)}
                  </span>
                </div>
                <p className="text-xs text-gray-500 leading-relaxed pl-0.5">{rel.reasoning}</p>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  )
}