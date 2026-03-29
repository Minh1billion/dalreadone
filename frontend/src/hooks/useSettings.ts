import { useState, useEffect } from 'react'
import { settingsApi } from '../api/settings'
import type { SettingsResponse } from '../api/settings'

interface UseSettingsReturn {
  settings:  SettingsResponse | null
  loading:   boolean
  saving:    boolean
  error:     string | null
  success:   boolean
  save:      (use_own_key: boolean, groq_api_key?: string) => Promise<void>
  deleteKey: () => Promise<void>
}

export function useSettings(): UseSettingsReturn {
  const [settings, setSettings] = useState<SettingsResponse | null>(null)
  const [loading, setLoading]   = useState(true)
  const [saving, setSaving]     = useState(false)
  const [error, setError]       = useState<string | null>(null)
  const [success, setSuccess]   = useState(false)

  useEffect(() => {
    settingsApi.get()
      .then(res => setSettings(res.data))
      .catch(() => setError('Failed to load settings.'))
      .finally(() => setLoading(false))
  }, [])

  const save = async (use_own_key: boolean, groq_api_key?: string) => {
    setSaving(true)
    setError(null)
    setSuccess(false)
    try {
      const res = await settingsApi.update({
        use_own_key,
        ...(groq_api_key ? { groq_api_key } : {}),
      })
      setSettings(res.data)
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      const msg = Array.isArray(detail)
        ? detail.map((d: any) => d.msg).join(', ')
        : (typeof detail === 'string' ? detail : 'Failed to save settings.')
      setError(msg)
    } finally {
      setSaving(false)
    }
  }

  const deleteKey = async () => {
    setSaving(true)
    setError(null)
    try {
      const res = await settingsApi.deleteKey()
      setSettings(res.data)
    } catch {
      setError('Failed to delete API key.')
    } finally {
      setSaving(false)
    }
  }

  return { settings, loading, saving, error, success, save, deleteKey }
}