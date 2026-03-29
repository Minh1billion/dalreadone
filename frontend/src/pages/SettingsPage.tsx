import { useState } from 'react'
import { Eye, EyeOff, Trash2, ExternalLink } from 'lucide-react'
import { useSettings } from '../hooks/useSettings'

export default function SettingsPage () {
  const { settings, loading, saving, error, success, save, deleteKey } =
    useSettings()

  const [inputKey, setInputKey] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [useOwn, setUseOwn] = useState<boolean | null>(null)
  const [confirmDelete, setConfirmDelete] = useState(false)

  const effectiveUseOwn =
    useOwn !== null ? useOwn : settings?.use_own_key ?? false

  const handleSave = () => {
    console.log('saving:', effectiveUseOwn, inputKey.trim() || undefined)
    save(effectiveUseOwn, inputKey.trim() || undefined)
    setInputKey('')
  }

  const handleDelete = async () => {
    await deleteKey()
    setConfirmDelete(false)
    setUseOwn(false)
  }

  if (loading)
    return (
      <div className='flex items-center justify-center h-64 text-sm text-gray-400'>
        Loading...
      </div>
    )

  return (
    <div className='max-w-xl mx-auto px-6 py-10 space-y-8'>
      {/* Header */}
      <div>
        <h1 className='text-xl font-semibold text-gray-900'>Settings</h1>
        <p className='text-sm text-gray-500 mt-1'>
          Manage your account preferences.
        </p>
      </div>

      {/* Card */}
      <div className='border border-gray-200 rounded-xl p-6 space-y-5 bg-white shadow-sm'>
        {/* Title */}
        <div>
          <h2 className='text-sm font-semibold text-gray-800'>Groq API Key</h2>
          <p className='text-xs text-gray-500 mt-0.5'>
            Use your own key instead of the shared one.
          </p>
          <a
            href='https://console.groq.com/keys'
            target='_blank'
            rel='noreferrer'
            className='text-xs text-primary-600 hover:underline inline-flex items-center gap-0.5 mt-0.5'
          >
            Get a key <ExternalLink size={11} />
          </a>
        </div>

        {/* Toggle */}
        <div className='flex items-center justify-between'>
          <span className='text-sm text-gray-700'>Use my own Groq API key</span>
          <button
            role='switch'
            aria-checked={effectiveUseOwn}
            onClick={() => setUseOwn(!effectiveUseOwn)}
            className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors
              ${effectiveUseOwn ? 'bg-primary-600' : 'bg-gray-200'}`}
          >
            <span
              className={`inline-block h-3.5 w-3.5 rounded-full bg-white shadow transition-transform
              ${effectiveUseOwn ? 'translate-x-4' : 'translate-x-1'}`}
            />
          </button>
        </div>

        {/* Key section - only when toggle on */}
        {effectiveUseOwn && (
          <div className='space-y-3'>
            {/* Existing masked key */}
            {settings?.groq_api_key && !inputKey && (
              <div className='flex items-center justify-between rounded-lg bg-gray-50 border border-gray-200 px-3 py-2'>
                <span className='text-sm font-mono text-gray-600'>
                  {settings.groq_api_key}
                </span>
                <button
                  onClick={() => setConfirmDelete(true)}
                  className='text-gray-400 hover:text-red-500 transition-colors ml-2'
                  title='Remove key'
                >
                  <Trash2 size={14} />
                </button>
              </div>
            )}

            {/* Confirm delete */}
            {confirmDelete && (
              <div className='rounded-lg bg-red-50 border border-red-200 px-3 py-2.5 flex items-center justify-between'>
                <span className='text-xs text-red-700'>
                  Remove this API key?
                </span>
                <div className='flex gap-2 ml-3'>
                  <button
                    onClick={() => setConfirmDelete(false)}
                    className='text-xs text-gray-500 hover:text-gray-700'
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleDelete}
                    className='text-xs text-red-600 font-medium hover:text-red-800'
                  >
                    Remove
                  </button>
                </div>
              </div>
            )}

            {/* Input */}
            <div>
              <label className='block text-xs text-gray-500 mb-1'>
                {settings?.groq_api_key
                  ? 'Replace with new key'
                  : 'Enter your API key'}
              </label>
              <div className='relative'>
                <input
                  type={showKey ? 'text' : 'password'}
                  value={inputKey}
                  onChange={e => setInputKey(e.target.value)}
                  placeholder='gsk_...'
                  className='w-full rounded-lg border border-gray-200 bg-white px-3 py-2 pr-9
                    text-sm font-mono placeholder:text-gray-300
                    focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent'
                />
                <button
                  type='button'
                  onClick={() => setShowKey(!showKey)}
                  className='absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600'
                >
                  {showKey ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Feedback */}
        {error && <p className='text-xs text-red-500'>{error}</p>}
        {success && <p className='text-xs text-green-600'>Settings saved.</p>}

        {/* Save button */}
        <div className='pt-1'>
          <button
            onClick={handleSave}
            disabled={saving}
            className='px-4 py-2 rounded-lg bg-gray-900 text-white text-sm font-medium
              hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
          >
            {saving ? 'Saving...' : 'Save changes'}
          </button>
        </div>
      </div>
    </div>
  )
}
