import { useState, useRef, useEffect, type RefObject } from 'react'

interface FilePanelProps {
  files: any[]
  activeFileId: number | null
  isLoading: boolean
  isUploading: boolean
  uploadProgress: number
  uploadError: string | null
  inputRef: RefObject<HTMLInputElement | null>
  onSelectFile: (id: number) => void
  onDelete: (id: number) => void
  onTriggerFilePicker: () => void
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void
}

function ContextMenu({
  x, y, onDelete, onClose,
}: { x: number; y: number; onDelete: () => void; onClose: () => void }) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose()
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [onClose])

  return (
    <div
      ref={ref}
      style={{ top: y, left: x }}
      className='fixed z-50 min-w-35 bg-white border border-gray-200 rounded-lg shadow-lg py-1 text-sm'
    >
      <button
        onClick={() => { onDelete(); onClose() }}
        className='w-full text-left px-3 py-2 text-red-500 hover:bg-red-50 transition-colors flex items-center gap-2'
      >
        <svg className='w-3.5 h-3.5' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
          <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2}
            d='M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16' />
        </svg>
        Delete file
      </button>
    </div>
  )
}

export function FilePanelSidebar({
  files, activeFileId, isLoading, isUploading, uploadProgress,
  uploadError, inputRef, onSelectFile, onDelete, onTriggerFilePicker, onFileChange,
}: FilePanelProps) {
  const [menu, setMenu] = useState<{ x: number; y: number; fileId: number } | null>(null)

  const openMenu = (e: React.MouseEvent, fileId: number) => {
    e.stopPropagation()
    setMenu({ x: e.clientX, y: e.clientY, fileId })
  }

  return (
    <>
      <aside className='h-full bg-white border-r border-gray-100 flex flex-col overflow-hidden'>
        <div className='px-4 py-3 border-b border-gray-100 flex items-center justify-between shrink-0'>
          <span className='text-xs font-semibold text-gray-500 uppercase tracking-wider'>Files</span>
          <button
            onClick={onTriggerFilePicker}
            disabled={isUploading}
            className='text-xs px-2 py-1 rounded bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 transition-colors'
          >
            + Upload
          </button>
          <input ref={inputRef} type='file' accept='.csv,.xlsx,.xls' className='hidden' onChange={onFileChange} />
        </div>

        {isUploading && (
          <div className='px-4 py-2 border-b border-gray-100 shrink-0'>
            <div className='flex justify-between text-xs text-gray-500 mb-1'>
              <span>Uploading…</span><span>{uploadProgress}%</span>
            </div>
            <div className='h-1 bg-gray-100 rounded-full overflow-hidden'>
              <div className='h-full bg-primary-500 transition-all' style={{ width: `${uploadProgress}%` }} />
            </div>
          </div>
        )}

        {uploadError && (
          <p className='px-4 py-2 text-xs text-red-500 border-b border-gray-100 shrink-0'>{uploadError}</p>
        )}

        <ul className='flex-1 overflow-y-auto py-1'>
          {isLoading ? (
            <li className='px-4 py-3 text-xs text-gray-400'>Loading…</li>
          ) : files.length === 0 ? (
            <li className='px-4 py-6 text-xs text-gray-400 text-center'>No files yet</li>
          ) : (
            files.map((f: any) => (
              <li key={f.id} className='flex items-center group'>
                <button
                  onClick={() => onSelectFile(f.id)}
                  className={`flex-1 text-left px-4 py-2.5 text-sm truncate transition-colors ${
                    f.id === activeFileId
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {f.filename}
                </button>
                <button
                  onClick={(e) => openMenu(e, f.id)}
                  className='opacity-0 group-hover:opacity-100 px-2 py-2 text-gray-400 hover:text-gray-600 transition-all'
                >
                  <svg className='w-4 h-4' fill='currentColor' viewBox='0 0 24 24'>
                    <circle cx='12' cy='5' r='1.5' /><circle cx='12' cy='12' r='1.5' /><circle cx='12' cy='19' r='1.5' />
                  </svg>
                </button>
              </li>
            ))
          )}
        </ul>
      </aside>

      {menu && (
        <ContextMenu
          x={menu.x} y={menu.y}
          onDelete={() => onDelete(menu.fileId)}
          onClose={() => setMenu(null)}
        />
      )}
    </>
  )
}