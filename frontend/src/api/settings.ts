import { api } from './axios'

export type SettingsResponse = {
  use_own_key:  boolean
  groq_api_key: string | null
}

export type UpdateSettingsRequest = {
  use_own_key:  boolean
  groq_api_key?: string | null
}

export const settingsApi = {
  get:       ()                            => api.get<SettingsResponse>('/settings'),
  update:    (body: UpdateSettingsRequest) => api.put<SettingsResponse>('/settings', body),
  deleteKey: ()                            => api.delete<SettingsResponse>('/settings/groq-key'),
}