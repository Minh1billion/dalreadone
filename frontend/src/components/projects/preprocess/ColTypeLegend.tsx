const LEGEND_ITEMS = [
  { type: 'numeric',     label: 'Numeric',     className: 'bg-blue-50 text-blue-600 border-blue-200' },
  { type: 'categorical', label: 'Categorical',  className: 'bg-purple-50 text-purple-600 border-purple-200' },
  { type: 'datetime',    label: 'Datetime',     className: 'bg-amber-50 text-amber-600 border-amber-200' },
  { type: 'unknown',     label: 'Unknown',      className: 'bg-gray-50 text-gray-500 border-gray-200' },
  { type: 'selected',    label: 'Selected',     className: 'bg-primary-100 text-primary-700 border-primary-300 font-medium' },
] as const

export function ColTypeLegend() {
  return (
    <div className='flex flex-wrap items-center gap-2'>
      {LEGEND_ITEMS.map(item => (
        <span
          key={item.type}
          className={`text-[10px] px-2 py-0.5 rounded border ${item.className}`}
        >
          {item.label}
        </span>
      ))}
    </div>
  )
}