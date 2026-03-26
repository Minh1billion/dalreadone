import { useRef } from 'react'
import { useFiles, useUploadFile, useDeleteFile } from '../../hooks/useFiles'
import { IconTrash, IconUpload, IconFile } from '../ui/icons'

interface Props {
  projectId: number
  activeFileId: number | null
  onSelectFile: (id: number) => void
}

export default function FilePanel({ projectId, activeFileId, onSelectFile }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const { data: files = [], isLoading } = useFiles(projectId)
  const upload = useUploadFile(projectId)
  const deleteFile = useDeleteFile(projectId)

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    await upload.mutateAsync(file)
    e.target.value = ''
  }

  async function handleDelete(e: React.MouseEvent, fileId: number) {
    e.stopPropagation()
    if (activeFileId === fileId) onSelectFile(0)
    await deleteFile.mutateAsync(fileId)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-gray-900">Files</h2>
        <button
          onClick={() => inputRef.current?.click()}
          disabled={upload.isPending}
          className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-primary-700 bg-primary-50 hover:bg-primary-100 rounded-md transition-colors disabled:opacity-50"
        >
          <IconUpload />
          {upload.isPending ? 'Uploading...' : 'Upload'}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          className="hidden"
          onChange={handleUpload}
        />
      </div>

      {/* File list */}
      <div className="flex-1 overflow-y-auto space-y-1">
        {isLoading ? (
          <div className="space-y-2">
            {[...Array(2)].map((_, i) => (
              <div key={i} className="h-9 bg-gray-100 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : files.length === 0 ? (
          <div className="py-8 text-center">
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
                className={`group flex items-center gap-2.5 px-3 py-2 rounded-lg cursor-pointer transition-colors ${
                  isActive
                    ? 'bg-primary-50 border border-primary-200 text-primary-700'
                    : 'hover:bg-gray-50 text-gray-700 border border-transparent'
                }`}
              >
                <span className={isActive ? 'text-primary-500' : 'text-gray-400'}>
                  <IconFile />
                </span>
                <span className="flex-1 text-xs font-medium truncate">{file.filename}</span>
                <button
                  onClick={(e) => handleDelete(e, file.id)}
                  className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-all"
                >
                  <IconTrash />
                </button>
              </div>
            )
          })
        )}
      </div>

      {/* Upload hint */}
      {files.length > 0 && (
        <p className="mt-4 text-xs text-gray-400 text-center">
          Max 5 files · CSV, XLSX
        </p>
      )}
    </div>
  )
}