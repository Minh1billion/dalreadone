import { type ReactNode, useState, useRef, useEffect } from 'react'
import { X, ChevronDown, Check } from 'lucide-react'

interface SelectProps {
  label:    string
  value:    string
  onChange: (v: string) => void
  options:  { value: string; label: string }[]
  hint?:    string
}

export function SelectRow({ label, value, onChange, options, hint }: SelectProps) {
  return (
    <div className="flex items-center gap-3">
      <label className="w-44 shrink-0 text-xs text-gray-500">{label}</label>
      <div className="flex-1">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full text-xs rounded-md border border-gray-200 bg-white px-2.5 py-1.5 text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-300 focus:border-primary-400"
        >
          {options.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        {hint && <p className="text-[10px] text-gray-400 mt-0.5">{hint}</p>}
      </div>
    </div>
  )
}

interface NumberProps {
  label:    string
  value:    number
  onChange: (v: number) => void
  min?:     number
  max?:     number
  step?:    number
  hint?:    string
}

export function NumberRow({ label, value, onChange, min, max, step = 0.01, hint }: NumberProps) {
  return (
    <div className="flex items-center gap-3">
      <label className="w-44 shrink-0 text-xs text-gray-500">{label}</label>
      <div className="flex-1">
        <input
          type="number"
          value={value}
          min={min}
          max={max}
          step={step}
          onChange={(e) => onChange(Number(e.target.value))}
          className="w-full text-xs rounded-md border border-gray-200 bg-white px-2.5 py-1.5 text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-300 focus:border-primary-400"
        />
        {hint && <p className="text-[10px] text-gray-400 mt-0.5">{hint}</p>}
      </div>
    </div>
  )
}

interface TextProps {
  label:    string
  value:    string
  onChange: (v: string) => void
  hint?:    string
}

export function TextRow({ label, value, onChange, hint }: TextProps) {
  return (
    <div className="flex items-center gap-3">
      <label className="w-44 shrink-0 text-xs text-gray-500">{label}</label>
      <div className="flex-1">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full text-xs rounded-md border border-gray-200 bg-white px-2.5 py-1.5 text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-300 focus:border-primary-400"
        />
        {hint && <p className="text-[10px] text-gray-400 mt-0.5">{hint}</p>}
      </div>
    </div>
  )
}

interface RangeProps {
  label:      string
  lo:         number
  hi:         number
  onChangeLo: (v: number) => void
  onChangeHi: (v: number) => void
  min?:       number
  max?:       number
  step?:      number
  hint?:      string
}

export function RangeRow({ label, lo, hi, onChangeLo, onChangeHi, min = 0, max = 1, step = 0.01, hint }: RangeProps) {
  return (
    <div className="flex items-center gap-3">
      <label className="w-44 shrink-0 text-xs text-gray-500">{label}</label>
      <div className="flex-1 flex items-center gap-2">
        <input
          type="number"
          value={lo}
          min={min}
          max={hi}
          step={step}
          onChange={(e) => onChangeLo(Number(e.target.value))}
          className="w-full text-xs rounded-md border border-gray-200 bg-white px-2.5 py-1.5 text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-300"
        />
        <span className="text-xs text-gray-400 shrink-0">–</span>
        <input
          type="number"
          value={hi}
          min={lo}
          max={max}
          step={step}
          onChange={(e) => onChangeHi(Number(e.target.value))}
          className="w-full text-xs rounded-md border border-gray-200 bg-white px-2.5 py-1.5 text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-300"
        />
        {hint && <p className="text-[10px] text-gray-400 mt-0.5">{hint}</p>}
      </div>
    </div>
  )
}

interface SectionProps { title: string; children: ReactNode }

export function ParamSection({ title, children }: SectionProps) {
  return (
    <div className="space-y-2.5">
      <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{title}</p>
      {children}
    </div>
  )
}

interface TagInputProps {
  label:        string
  value:        string[]
  onChange:     (v: string[]) => void
  suggestions?: string[]   // danh sách cột từ file, optional
  hint?:        string
}

export function TagInputRow({ label, value, onChange, suggestions = [], hint }: TagInputProps) {
  const [inputVal, setInputVal] = useState('')
  const [open, setOpen]         = useState(false)
  const inputRef                = useRef<HTMLInputElement>(null)
  const containerRef            = useRef<HTMLDivElement>(null)

  const filtered = suggestions.filter(
    (s) => !value.includes(s) && s.toLowerCase().includes(inputVal.toLowerCase())
  )

  const addTag = (tag: string) => {
    const t = tag.trim()
    if (t && !value.includes(t)) onChange([...value, t])
    setInputVal('')
    setOpen(false)
    inputRef.current?.focus()
  }

  const removeTag = (tag: string) => onChange(value.filter((v) => v !== tag))

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      if (inputVal.trim()) addTag(inputVal)
    } else if (e.key === 'Backspace' && !inputVal && value.length > 0) {
      removeTag(value[value.length - 1])
    } else if (e.key === 'Escape') {
      setOpen(false)
    }
  }

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  return (
    <div className="flex gap-3">
      <label className="w-44 shrink-0 text-xs text-gray-500 pt-1.5">{label}</label>

      <div className="flex-1 relative" ref={containerRef}>
        {/* Tag box */}
        <div
          className="min-h-7.5 w-full flex flex-wrap gap-1 rounded-md border border-gray-200 bg-white px-2 py-1 cursor-text focus-within:ring-2 focus-within:ring-primary-300 focus-within:border-primary-400 transition-shadow"
          onClick={() => { inputRef.current?.focus(); if (suggestions.length > 0) setOpen(true) }}
        >
          {value.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-primary-50 border border-primary-200 text-primary-700 text-[11px] font-medium"
            >
              {tag}
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); removeTag(tag) }}
                className="text-primary-400 hover:text-primary-700 transition-colors leading-none"
              >
                <X size={9} strokeWidth={2.5} />
              </button>
            </span>
          ))}

          <div className="flex items-center flex-1 min-w-20 gap-0.5">
            <input
              ref={inputRef}
              value={inputVal}
              onChange={(e) => { setInputVal(e.target.value); setOpen(true) }}
              onKeyDown={handleKeyDown}
              onFocus={() => { if (suggestions.length > 0) setOpen(true) }}
              placeholder={value.length === 0 ? 'Chọn hoặc gõ rồi Enter…' : ''}
              className="flex-1 text-xs bg-transparent outline-none text-gray-700 placeholder:text-gray-300 py-0.5"
            />
            {suggestions.length > 0 && (
              <button
                type="button"
                tabIndex={-1}
                onClick={(e) => { e.stopPropagation(); setOpen((o) => !o) }}
                className="text-gray-300 hover:text-gray-500 transition-colors shrink-0 p-0.5"
              >
                <ChevronDown size={12} className={`transition-transform duration-150 ${open ? 'rotate-180' : ''}`} />
              </button>
            )}
          </div>
        </div>

        {/* Dropdown */}
        {open && filtered.length > 0 && (
          <ul className="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg max-h-44 overflow-y-auto">
            {filtered.map((s) => (
              <li
                key={s}
                onMouseDown={(e) => { e.preventDefault(); addTag(s) }}
                className="flex items-center justify-between px-3 py-1.5 text-xs text-gray-700 hover:bg-primary-50 hover:text-primary-700 cursor-pointer"
              >
                <span className="font-mono">{s}</span>
                {value.includes(s) && <Check size={11} className="text-primary-500" />}
              </li>
            ))}
          </ul>
        )}

        {hint && <p className="text-[10px] text-gray-400 mt-0.5">{hint}</p>}
      </div>
    </div>
  )
}