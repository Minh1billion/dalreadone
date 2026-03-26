import { useState, useRef, useEffect } from 'react'
import { IconFolder, IconArrow, IconPencil, IconTrash, IconDots } from '../ui/icons'
import type { Project } from '../../api/project'

interface Props {
  project: Project
  onOpen: () => void
  onEdit: () => void
  onDelete: () => void
}

export default function ProjectCard({ project, onOpen, onEdit, onDelete }: Props) {
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!menuOpen) return
    function handleClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [menuOpen])

  return (
    <div
      className="group relative bg-white border border-gray-200 rounded-xl p-5 hover:border-primary-300 hover:shadow-sm transition-all cursor-pointer"
      onClick={onOpen}
    >
      <div className="w-10 h-10 bg-primary-50 rounded-lg flex items-center justify-center mb-4 text-primary-600 group-hover:bg-primary-100 transition-colors">
        <IconFolder />
      </div>

      <p className="text-sm font-medium text-gray-900 truncate pr-6">{project.name}</p>

      <div className="flex items-center gap-1 mt-1 text-xs text-gray-400 group-hover:text-primary-600 transition-colors">
        <span>Open project</span>
        <IconArrow />
      </div>

      {/* Action menu */}
      <div
        ref={menuRef}
        className="absolute top-4 right-4"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          className="w-7 h-7 flex items-center justify-center rounded-md text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors opacity-0 group-hover:opacity-100"
        >
          <IconDots />
        </button>

        {menuOpen && (
          <div className="absolute right-0 top-8 w-40 bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-10">
            <button
              onClick={() => { setMenuOpen(false); onEdit() }}
              className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
            >
              <IconPencil />
              Rename
            </button>
            <button
              onClick={() => { setMenuOpen(false); onDelete() }}
              className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-red-500 hover:bg-red-50 transition-colors"
            >
              <IconTrash />
              Delete
            </button>
          </div>
        )}
      </div>
    </div>
  )
}