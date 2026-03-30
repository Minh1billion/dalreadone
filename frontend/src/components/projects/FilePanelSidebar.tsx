import type { RefObject } from 'react'

interface FilePanelProps {
  files: any[]
  activeFileId: number | null
  isLoading: boolean
  isUploading: boolean
  uploadProgress: number
  uploadError: string | null
  inputRef: RefObject<HTMLInputElement | null>
  onSelectFile: (id: number) => void
  onDelete: (e: React.MouseEvent, id: number) => void
  onTriggerFilePicker: () => void
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void
}

export function FilePanelSidebar ({
  files,
  activeFileId,
  isLoading,
  isUploading,
  uploadProgress,
  uploadError,
  inputRef,
  onSelectFile,
  onDelete,
  onTriggerFilePicker,
  onFileChange
}: FilePanelProps) {
  return (
    <aside className='w-64 shrink-0 bg-white border-r border-gray-100 flex flex-col'>
      <div className='px-4 py-3 border-b border-gray-100 flex items-center justify-between'>
        <span className='text-xs font-semibold text-gray-500 uppercase tracking-wider'>
          Files
        </span>
        <button
          onClick={onTriggerFilePicker}
          disabled={isUploading}
          className='text-xs px-2 py-1 rounded bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 transition-colors'
        >
          + Upload
        </button>
        <input
          ref={inputRef}
          type='file'
          accept='.csv,.xlsx,.xls'
          className='hidden'
          onChange={onFileChange}
        />
      </div>

      {isUploading && (
        <div className='px-4 py-2 border-b border-gray-100'>
          <div className='flex justify-between text-xs text-gray-500 mb-1'>
            <span>Uploading…</span>
            <span>{uploadProgress}%</span>
          </div>
          <div className='h-1 bg-gray-100 rounded-full overflow-hidden'>
            <div
              className='h-full bg-primary-500 transition-all'
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {uploadError && (
        <p className='px-4 py-2 text-xs text-red-500 border-b border-gray-100'>
          {uploadError}
        </p>
      )}

      <ul className='flex-1 overflow-y-auto py-1'>
        {isLoading ? (
          <li className='px-4 py-3 text-xs text-gray-400'>Loading…</li>
        ) : files.length === 0 ? (
          <li className='px-4 py-6 text-xs text-gray-400 text-center'>
            No files yet
          </li>
        ) : (
          files.map((f: any) => (
            <li key={f.id} className='flex items-center justify-between group'>
              <button
                onClick={() => onSelectFile(f.id)}
                className={`flex-1 text-left px-4 py-2.5 ${
                  f.id === activeFileId
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <span className='text-sm truncate'>{f.filename}</span>
              </button>

              <button
                onClick={e => onDelete(e, f.id)}
                className='opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 ml-2 text-xs'
              >
                ✕
              </button>
            </li>
          ))
        )}
      </ul>
    </aside>
  )
}
