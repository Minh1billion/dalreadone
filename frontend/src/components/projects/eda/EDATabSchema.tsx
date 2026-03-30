import type { EDAReport } from './EDATypes'

const DTYPE_COLOR: Record<string, string> = {
  integer:  'bg-blue-50 text-blue-600',
  floating: 'bg-violet-50 text-violet-600',
  string:   'bg-green-50 text-green-600',
  boolean:  'bg-orange-50 text-orange-600',
}

export function EDATabSchema({ report }: { report: EDAReport }) {
  const { schema, missing_and_duplicates: m } = report

  return (
    <div className="rounded-xl border border-gray-100 overflow-hidden">
      <table className="w-full text-xs">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-100">
            {['Column', 'Type', 'Inferred', 'Nulls', 'Unique', 'Sample values'].map(h => (
              <th key={h} className="px-3 py-2.5 text-left font-semibold text-gray-500">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {schema.columns.map((col) => {
            const missing = m.columns[col.name]
            return (
              <tr key={col.name} className="hover:bg-gray-50/60 transition-colors">
                <td className="px-3 py-2.5 font-mono text-gray-800 font-medium">{col.name}</td>
                <td className="px-3 py-2.5 text-gray-500">{col.dtype}</td>
                <td className="px-3 py-2.5">
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${DTYPE_COLOR[col.inferred_type] ?? 'bg-gray-100 text-gray-500'}`}>
                    {col.inferred_type}
                  </span>
                </td>
                <td className="px-3 py-2.5">
                  {missing
                    ? <span className="text-amber-600 font-medium">{missing.null_count} ({missing.null_pct}%)</span>
                    : <span className="text-gray-400">0</span>
                  }
                </td>
                <td className="px-3 py-2.5 text-gray-600 tabular-nums">{col.n_unique}</td>
                <td className="px-3 py-2.5 text-gray-400 max-w-48 truncate">
                  {col.first_10_unique_values.filter(v => v !== null).slice(0, 4).map(String).join(', ')}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}