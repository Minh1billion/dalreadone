import { IconFolder, IconPlus } from '../ui/icons'

interface Props {
  onCreate: () => void
}

export default function EmptyState({ onCreate }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="w-14 h-14 bg-gray-100 rounded-2xl flex items-center justify-center mb-4 text-gray-400">
        <IconFolder />
      </div>
      <p className="text-sm font-medium text-gray-900 mb-1">No projects yet</p>
      <p className="text-sm text-gray-500 mb-6 max-w-xs">
        Create your first project to start uploading files and querying your data.
      </p>
      <button
        onClick={onCreate}
        className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium rounded-md transition-colors"
      >
        <IconPlus />
        New project
      </button>
    </div>
  )
}