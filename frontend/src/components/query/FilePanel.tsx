import { useFilePanel } from '../../hooks/useFilePanel'
import { IconTrash, IconUpload, IconFile } from '../ui/icons'

interface Props {
  projectId: number
  activeFileId: number | null
  onSelectFile: (id: number) => void
}

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
  } = useFilePanel({ projectId, activeFileId, onSelectFile })

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xs font-semibold text-gray-900 uppercase tracking-wide">Files</h2>
        <button
          onClick={triggerFilePicker}
          disabled={isUploading}
          className="flex items-center gap-1.5 px-2 py-1 text-xs font-medium text-primary-700 bg-primary-50 hover:bg-primary-100 rounded-md transition-colors disabled:opacity-50"
        >
          <IconUpload />
          {isUploading ? `${uploadProgress}%` : 'Upload'}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          className="hidden"
          onChange={handleFileChange}
        />
      </div>

      {isUploading && (
        <div className="mb-3">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Uploading...</span>
            <span>{uploadProgress}%</span>
          </div>
          <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-500 rounded-full transition-all duration-200"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {uploadError && (
        <div className="mb-3 text-xs text-red-600 bg-red-50 border border-red-200 rounded-md px-2.5 py-1.5">
          {uploadError}
        </div>
      )}

      <div className="flex-1 overflow-y-auto space-y-1 min-h-0">
        {isLoading ? (
          <div className="space-y-2">
            {[...Array(2)].map((_, i) => (
              <div key={i} className="h-9 bg-gray-100 rounded-lg animate-pulse" />
            ))}
          </div>
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
                  onClick={(e) => handleDelete(e, file.id)}
                  className="flex-none opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-all"
                >
                  <IconTrash />
                </button>
              </div>
            )
          })
        )}
      </div>

      {files.length > 0 && (
        <p className="mt-3 text-xs text-gray-400 text-center">CSV, XLSX · max 50 MB</p>
      )}
    </div>
  )
}