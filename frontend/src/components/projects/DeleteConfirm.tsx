interface Props {
  projectName: string
  loading?: boolean
  onConfirm: () => void
  onClose: () => void
}

export default function DeleteConfirm({ projectName, loading, onConfirm, onClose }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      <div className="absolute inset-0 bg-black/20 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-sm bg-white rounded-xl shadow-xl border border-gray-100 p-6">
        <h3 className="text-base font-semibold text-gray-900 mb-2">Delete project?</h3>
        <p className="text-sm text-gray-500 mb-6">
          <span className="font-medium text-gray-700">"{projectName}"</span> and all its files will be
          permanently deleted. This cannot be undone.
        </p>
        <div className="flex gap-2 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white text-sm font-medium rounded-md transition-colors disabled:opacity-50"
          >
            {loading ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  )
}