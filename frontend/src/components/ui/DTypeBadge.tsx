export default function DTypeBadge({ dtype }: { dtype: string }) {
  const d = dtype.toLowerCase()
  const { label, cls } =
    d.startsWith('int')                              ? { label: 'int',   cls: 'bg-blue-100 text-blue-800 border-blue-200' } :
    d.startsWith('float')                            ? { label: 'float', cls: 'bg-violet-100 text-violet-800 border-violet-200' } :
    d.startsWith('bool')                             ? { label: 'bool',  cls: 'bg-amber-100 text-amber-800 border-amber-200' } :
    d.startsWith('datetime') || d.includes('date')   ? { label: 'date',  cls: 'bg-teal-100 text-teal-800 border-teal-200' } :
    d.startsWith('category')                         ? { label: 'cat',   cls: 'bg-orange-100 text-orange-800 border-orange-200' } :
                                                       { label: 'obj',   cls: 'bg-gray-100 text-gray-600 border-gray-200' }
  return (
    <span className={`shrink-0 inline-block px-1.5 py-0.5 rounded border text-[10px] font-semibold font-mono tracking-wide ${cls}`}>
      {label}
    </span>
  )
}