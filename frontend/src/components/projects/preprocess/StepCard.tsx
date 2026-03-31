import { type ReactNode } from 'react'
import { GripVertical, ChevronDown, ChevronUp, X } from 'lucide-react'
import type { StepMeta } from './PreprocessTypes'

interface Props {
  meta:      StepMeta
  index:     number
  enabled:   boolean
  expanded:  boolean
  onToggleEnabled:  () => void
  onToggleExpanded: () => void
  onRemove:  () => void
  children:  ReactNode
  dragHandleProps?: Record<string, unknown>
}

export function StepCard({
  meta, index, enabled, expanded,
  onToggleEnabled, onToggleExpanded, onRemove,
  children, dragHandleProps,
}: Props) {
  return (
    <div className={`rounded-xl border transition-all duration-200 ${
      enabled
        ? 'border-gray-200 bg-white shadow-sm'
        : 'border-dashed border-gray-200 bg-gray-50 opacity-60'
    }`}>
      <div className="flex items-center gap-3 px-4 py-3">
        <span
          className="cursor-grab text-gray-300 hover:text-gray-500 touch-none shrink-0"
          {...dragHandleProps}
        >
          <GripVertical size={16} />
        </span>

        <span className="w-5 h-5 rounded-full bg-gray-100 text-gray-500 text-[10px] font-semibold flex items-center justify-center shrink-0">
          {index + 1}
        </span>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-800 leading-none">{meta.label}</p>
          <p className="text-xs text-gray-400 mt-0.5 truncate">{meta.description}</p>
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