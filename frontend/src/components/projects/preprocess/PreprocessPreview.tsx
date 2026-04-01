interface Props {
  preview: Record<string, unknown>[]
  transformedCols: Set<string>
  droppedCols: Set<string>
}

export function PreprocessPreview({ preview, transformedCols, droppedCols }: Props) {
  if (!preview.length) return null

  const allCols = Object.keys(preview[0])
  const visibleCols = allCols.filter(c => !droppedCols.has(c))

  return (
    <div className='space-y-2'>
      {droppedCols.size > 0 && (
        <div className='flex flex-wrap gap-1.5'>
          {[...droppedCols].map(col => (
            <span key={col} className='text-[10px] px-2 py-0.5 rounded-full bg-red-50 border border-red-100 text-red-400 line-through'>
              {col}
            </span>
          ))}
          <span className='text-[10px] text-gray-400 self-center'>dropped</span>
        </div>
      )}

      <div className='overflow-x-auto rounded-lg border border-gray-100'>
        <table className='w-full text-xs'>
          <thead>
            <tr className='bg-gray-50'>
              {visibleCols.map(col => (
                <th
                  key={col}
                  className={`px-3 py-2 text-left font-medium whitespace-nowrap border-b ${
                    transformedCols.has(col)
                      ? 'text-primary-700 bg-primary-50 border-primary-100'
                      : 'text-gray-500 border-gray-100'
                  }`}
                >
                  {col}
                  {transformedCols.has(col) && (
                    <span className='ml-1 text-[8px] text-primary-400 font-normal'>✦</span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {preview.map((row, i) => (
              <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}>
                {visibleCols.map(col => (
                  <td
                    key={col}
                    className={`px-3 py-1.5 whitespace-nowrap max-w-32 truncate border-b border-gray-50 ${
                      transformedCols.has(col) ? 'bg-primary-50/40' : ''
                    }`}
                  >
                    {row[col] == null
                      ? <span className='text-gray-300'>—</span>
                      : String(row[col])
                    }
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className='text-[10px] text-gray-400'>
        <span className='text-primary-500'>✦</span> highlighted columns were transformed
        {' · '}showing {preview.length} rows
      </p>
    </div>
  )
}