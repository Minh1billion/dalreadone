import { useState } from 'react'
import { useFilePanel } from '../../hooks/useFilePanel'
import { IconTrash, IconUpload, IconFile } from '../ui/icons'
import type { FilePreview } from '../../api/files'

interface Props {
  projectId: number
  activeFileId: number | null
  onSelectFile: (id: number) => void
}

//  DTypeBadge 

function DTypeBadge({ dtype }: { dtype: string }) {
  const d = dtype.toLowerCase()
  const { label, cls } =
    d.startsWith('int')                             ? { label: 'int',   cls: 'bg-blue-100 text-blue-800 border-blue-200' } :
    d.startsWith('float')                           ? { label: 'float', cls: 'bg-violet-100 text-violet-800 border-violet-200' } :
    d.startsWith('bool')                            ? { label: 'bool',  cls: 'bg-amber-100 text-amber-800 border-amber-200' } :
    d.startsWith('datetime') || d.includes('date')  ? { label: 'date',  cls: 'bg-teal-100 text-teal-800 border-teal-200' } :
    d.startsWith('category')                        ? { label: 'cat',   cls: 'bg-orange-100 text-orange-800 border-orange-200' } :
                                                      { label: 'obj',   cls: 'bg-gray-100 text-gray-600 border-gray-200' }
  return (
    <span className={`shrink-0 inline-block px-1.5 py-0.5 rounded border text-[10px] font-semibold font-mono tracking-wide ${cls}`}>
      {label}
    </span>
  )
}

//  MissingBar 

function MissingBar({ pct }: { pct: number }) {
  const fill =
    pct === 0  ? 'bg-emerald-400' :
    pct < 5    ? 'bg-amber-300'   :
    pct < 20   ? 'bg-amber-500'   :
    pct < 50   ? 'bg-orange-500'  :
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

//  fmt 

function fmt(v: number | null): string {
  if (v == null) return '—'
  return Math.abs(v) >= 1000
    ? v.toLocaleString(undefined, { maximumFractionDigits: 1 })
    : v.toLocaleString(undefined, { maximumFractionDigits: 3 })
}

//  FilePreviewPanel 

type Tab = 'overview' | 'missing' | 'sample'

function FilePreviewPanel({
  preview,
  loading,
}: {
  preview: FilePreview | null
  loading: boolean
}) {
  const [tab, setTab] = useState<Tab>('overview')

  if (loading && !preview) {
    return (
      <div className="mt-3 rounded-lg border border-gray-100 p-3 space-y-2">
        {[80, 60, 70].map((w, i) => (
          <div key={i} className="h-3 bg-gray-100 rounded animate-pulse" style={{ width: `${w}%` }} />
        ))}
      </div>
    )
  }

  if (!preview) return null

  const { shape, columns, dtypes, missing, describe, sample } = preview
  const totalNulls    = missing.reduce((s, c) => s + c.null_count, 0)
  const colsWithNulls = missing.filter(c => c.null_count > 0).length

  return (
    <div className="mt-3 rounded-lg border border-gray-100 overflow-hidden">

      {/*  Header  */}
      <div className="px-3 py-2 bg-gray-50 border-b border-gray-100 flex items-center gap-2 flex-wrap">
        <span className="text-xs font-medium text-gray-700 truncate max-w-[120px]" title={preview.filename}>
          {preview.filename}
        </span>
        <div className="ml-auto flex items-center gap-1.5 flex-wrap justify-end">
          <span className="px-1.5 py-0.5 bg-primary-50 text-primary-700 border border-primary-100 rounded text-xs font-mono">
            {shape.rows.toLocaleString()} × {shape.cols}
          </span>
          {totalNulls > 0 && (
            <span className="px-1.5 py-0.5 bg-amber-50 text-amber-700 border border-amber-100 rounded text-xs">
              {colsWithNulls} col{colsWithNulls > 1 ? 's' : ''} w/ nulls
            </span>
          )}
        </div>
      </div>

      {/*  Tabs  */}
      <div className="flex border-b border-gray-100 bg-gray-50">
        {(['overview', 'missing', 'sample'] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 py-1.5 text-xs font-medium capitalize transition-colors
              ${tab === t
                ? 'text-primary-700 border-b-2 border-primary-600 bg-white'
                : 'text-gray-400 hover:text-gray-600'
              }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/*  Overview  */}
      {tab === 'overview' && (
        <div className="max-h-60 overflow-y-auto">

          {/* dtype list 2 cột */}
          <div className="px-3 py-2 border-b border-gray-50">
            <div className="grid grid-cols-2 gap-x-4">
              {columns.map(col => (
                <div
                  key={col}
                  className="flex items-center justify-between gap-2 py-1 border-b border-gray-50"
                >
                  <span className="text-xs text-gray-700 truncate min-w-0 flex-1" title={col}>
                    {col}
                  </span>
                  <DTypeBadge dtype={dtypes[col]} />
                </div>
              ))}
            </div>
          </div>

          {/* describe table */}
          {describe.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-gray-400 bg-gray-50">
                    <th className="text-left px-3 py-1.5 font-medium sticky left-0 bg-gray-50 min-w-[72px]">column</th>
                    {(['mean', 'std', 'min', 'median', 'max'] as const).map(h => (
                      <th key={h} className="text-right px-2 py-1.5 font-medium whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {describe.map(row => (
                    <tr key={row.column} className="hover:bg-gray-50 transition-colors">
                      <td className="px-3 py-1.5 font-medium text-gray-700 sticky left-0 bg-white max-w-[72px] truncate" title={row.column}>
                        {row.column}
                      </td>
                      {(['mean', 'std', 'min', 'median', 'max'] as const).map(k => (
                        <td key={k} className="px-2 py-1.5 text-right text-gray-600 font-mono tabular-nums">
                          {fmt(row[k])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="px-3 py-3 text-xs text-gray-400">No numeric columns.</p>
          )}
        </div>
      )}

      {/*  Missing  */}
      {tab === 'missing' && (
        <div className="max-h-60 overflow-y-auto divide-y divide-gray-50">
          {missing.map(col => (
            <div key={col.column} className="px-3 py-2">
              <div className="flex items-center gap-1.5 mb-1.5">
                <span className="text-xs font-medium text-gray-700 truncate flex-1 min-w-0" title={col.column}>
                  {col.column}
                </span>
                <DTypeBadge dtype={col.dtype} />
                {col.null_count > 0 && (
                  <span className="text-xs text-amber-600 tabular-nums shrink-0">
                    {col.null_count.toLocaleString()}
                  </span>
                )}
              </div>
              <MissingBar pct={col.null_pct} />
            </div>
          ))}
        </div>
      )}

      {/*  Sample  */}
      {tab === 'sample' && (
        <div className="overflow-auto max-h-60">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-gray-50 text-gray-400">
                {columns.map(col => (
                  <th key={col} className="text-left px-3 py-1.5 font-medium whitespace-nowrap sticky top-0 bg-gray-50">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {sample.map((row, i) => (
                <tr key={i} className="hover:bg-gray-50 transition-colors">
                  {columns.map(col => (
                    <td key={col} className="px-3 py-1.5 font-mono text-gray-600 max-w-[100px] truncate" title={String(row[col] ?? '')}>
                      {row[col] == null
                        ? <span className="text-gray-300 italic">null</span>
                        : String(row[col])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* loading shimmer khi refetch */}
      {loading && preview && (
        <div className="px-3 py-1.5 bg-primary-50 text-primary-600 text-xs animate-pulse">
          Refreshing…
        </div>
      )}
    </div>
  )
}

//  Main FilePanel 

export default function FilePanel({ projectId, activeFileId, onSelectFile }: Props) {
  const {
    inputRef,
    files,
    isLoading,
    isUploading,
    uploadProgress,
    uploadError,
    triggerFilePicker,
    handleFileChange,
    handleDelete,
    preview,
    previewLoading,
  } = useFilePanel({ projectId, activeFileId, onSelectFile })

  return (
    <div className="flex flex-col h-full min-h-0">

      {/*  Header  */}
      <div className="flex-none flex items-center justify-between mb-3">
        <h2 className="text-xs font-semibold text-gray-900 uppercase tracking-wide">Files</h2>
        <button
          onClick={triggerFilePicker}
          disabled={isUploading}
          className="flex items-center gap-1.5 px-2 py-1 text-xs font-medium text-primary-700 bg-primary-50 hover:bg-primary-100 rounded-md transition-colors disabled:opacity-50"
        >
          <IconUpload />
          {isUploading ? `${uploadProgress}%` : 'Upload'}
        </button>
        <input ref={inputRef} type="file" accept=".csv,.xlsx,.xls" className="hidden" onChange={handleFileChange} />
      </div>

      {/*  Upload progress  */}
      {isUploading && (
        <div className="flex-none mb-3">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Uploading...</span><span>{uploadProgress}%</span>
          </div>
          <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div className="h-full bg-primary-500 rounded-full transition-all duration-200" style={{ width: `${uploadProgress}%` }} />
          </div>
        </div>
      )}

      {/*  Upload error  */}
      {uploadError && (
        <div className="flex-none mb-3 text-xs text-red-600 bg-red-50 border border-red-200 rounded-md px-2.5 py-1.5">
          {uploadError}
        </div>
      )}

      {/*  File list  */}
      <div className="flex-none space-y-1">
        {isLoading ? (
          [...Array(2)].map((_, i) => (
            <div key={i} className="h-9 bg-gray-100 rounded-lg animate-pulse" />
          ))
        ) : files.length === 0 ? (
          <div className="py-6 text-center">
            <p className="text-xs text-gray-400">No files yet.</p>
            <p className="text-xs text-gray-400 mt-0.5">Upload a CSV or Excel file.</p>
          </div>
        ) : (
          files.map((file: any) => {
            const isActive = file.id === activeFileId
            return (
              <div
                key={file.id}
                onClick={() => onSelectFile(file.id)}
                className={`group flex items-center gap-2 px-2.5 py-2 rounded-lg cursor-pointer transition-colors ${
                  isActive
                    ? 'bg-primary-50 border border-primary-200 text-primary-700'
                    : 'hover:bg-gray-50 text-gray-700 border border-transparent'
                }`}
              >
                <span className={`flex-none ${isActive ? 'text-primary-500' : 'text-gray-400'}`}>
                  <IconFile />
                </span>
                <span className="flex-1 text-xs font-medium truncate min-w-0">{file.filename}</span>
                <button
                  onClick={e => handleDelete(e, file.id)}
                  className="flex-none opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-all"
                >
                  <IconTrash />
                </button>
              </div>
            )
          })
        )}
      </div>

      {/* Divider */}
      {activeFileId && (
        <div className="flex-none my-3 border-t border-gray-100" />
      )}

      {/* Preview panel */}
      {activeFileId && (
        <div className="flex-1 overflow-y-auto min-h-0 pb-2">
          <FilePreviewPanel preview={preview} loading={previewLoading} />
        </div>
      )}

      {files.length > 0 && !activeFileId && (
        <p className="mt-auto pt-3 text-xs text-gray-400 text-center">CSV, XLSX · max 50 MB</p>
      )}
    </div>
  )
}