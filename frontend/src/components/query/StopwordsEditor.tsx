import { useState, useRef, type KeyboardEvent } from 'react'
import type { StopwordsConfig } from '../../api/query'

const DEFAULT_STOPWORDS = [
  "this", "that", "with", "from", "have", "been", "were", "they",
  "their", "there", "what", "when", "will", "would", "could", "should",
  "which", "about", "into", "than", "then", "some", "your", "just",
  "also", "very", "more", "most", "such", "after", "before", "other",
]

interface Props {
  value: StopwordsConfig
  onChange: (v: StopwordsConfig) => void
}

export default function StopwordsEditor({ value, onChange }: Props) {
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const removed = new Set(value.remove ?? [])
  const added   = value.add ?? []

  function toggleDefault(word: string) {
    const next = new Set(removed)
    next.has(word) ? next.delete(word) : next.add(word)
    onChange({ ...value, remove: [...next] })
  }

  function addCustomWord() {
    const w = input.trim().toLowerCase()
    if (!w || added.includes(w) || DEFAULT_STOPWORDS.includes(w)) {
      setInput(''); return
    }
    onChange({ ...value, add: [...added, w] })
    setInput('')
    inputRef.current?.focus()
  }

  function removeCustomWord(w: string) {
    onChange({ ...value, add: added.filter(x => x !== w) })
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' || e.key === ',') { e.preventDefault(); addCustomWord() }
    if (e.key === 'Backspace' && input === '' && added.length > 0) {
      removeCustomWord(added[added.length - 1])
    }
  }

  const changed = removed.size > 0 || added.length > 0

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold text-gray-600 hover:bg-gray-50 transition-colors"
      >
        <span className="flex items-center gap-1.5">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 6h16M4 12h10M4 18h7"/>
          </svg>
          Stopwords
          {changed && (
            <span className="inline-flex items-center justify-center w-1.5 h-1.5 rounded-full bg-primary-500" />
          )}
        </span>
        <svg
          className={`transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
          width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
        >
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </button>

      {open && (
        <div className="border-t border-gray-200 p-3 space-y-3 bg-white">
          <p className="text-[10px] text-gray-400">
            Click to toggle. Add custom words below.
          </p>

          <div className="flex flex-wrap gap-1">
            {DEFAULT_STOPWORDS.map(w => {
              const isRemoved = removed.has(w)
              return (
                <button
                  key={w}
                  type="button"
                  onClick={() => toggleDefault(w)}
                  className={`px-1.5 py-0.5 rounded text-[10px] font-mono border transition-all ${
                    isRemoved
                      ? 'bg-gray-50 text-gray-300 border-gray-200 line-through'
                      : 'bg-white text-gray-600 border-gray-300 hover:border-red-300 hover:text-red-400'
                  }`}
                >
                  {w}
                </button>
              )
            })}
          </div>

          {added.length > 0 && (
            <div className="flex flex-wrap gap-1 pt-2 border-t border-gray-100">
              {added.map(w => (
                <span
                  key={w}
                  className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-primary-50 border border-primary-200 text-[10px] font-mono text-primary-700"
                >
                  {w}
                  <button
                    type="button"
                    onClick={() => removeCustomWord(w)}
                    className="text-primary-400 hover:text-red-500 transition-colors leading-none"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}

          <input
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={addCustomWord}
            placeholder="Add word… (Enter or comma)"
            className="w-full px-2 py-1.5 border border-gray-200 rounded text-[10px] font-mono placeholder-gray-300 focus:outline-none focus:ring-1 focus:ring-primary-400 bg-gray-50"
          />

          {changed && (
            <button
              type="button"
              onClick={() => onChange({})}
              className="text-[10px] text-gray-400 hover:text-red-500 transition-colors"
            >
              Reset to default
            </button>
          )}
        </div>
      )}
    </div>
  )
}