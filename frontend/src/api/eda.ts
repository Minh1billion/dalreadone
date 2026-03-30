import { api } from './axios'

export type EDAStatus = 'pending' | 'running' | 'done' | 'error'

export type EDATask = {
  task_id: string
  status: EDAStatus
  step: string | null
  progress: number
  result: Record<string, unknown> | null
  error: string | null
}

export const edaApi = {
  start: (fileId: number) =>
    api.post<{ task_id: string }>(`/eda/files/${fileId}`),

  status: (taskId: string) =>
    api.get<EDATask>(`/eda/${taskId}`),
}