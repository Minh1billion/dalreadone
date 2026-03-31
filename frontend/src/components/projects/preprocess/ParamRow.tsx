import { type ReactNode } from 'react'

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
  label:    string
  lo:       number
  hi:       number
  onChangeLo: (v: number) => void
  onChangeHi: (v: number) => void
  min?:     number
  max?:     number
  step?:    number
  hint?:    string
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