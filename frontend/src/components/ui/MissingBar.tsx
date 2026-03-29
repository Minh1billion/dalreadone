export default function MissingBar({ pct }: { pct: number }) {
  const fill =
    pct === 0 ? 'bg-emerald-400' :
    pct < 5   ? 'bg-amber-300'   :
    pct < 20  ? 'bg-amber-500'   :
    pct < 50  ? 'bg-orange-500'  :
                'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${fill}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-xs tabular-nums w-9 text-right font-medium ${pct > 0 ? 'text-amber-600' : 'text-emerald-600'}`}>
        {pct === 0 ? '✓' : `${pct}%`}
      </span>
    </div>
  )
}