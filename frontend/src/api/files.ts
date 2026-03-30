import { api } from './axios'

export type FileItem = {
  id: number
  filename: string
  s3_key: string
  project_id: number
  uploaded_by_id: number
  uploaded_at: string
}

export type FilePreview = {
  filename: string
  n_rows: number
  n_cols: number
  columns: string[]
  rows: Record<string, unknown>[]
}

export const filesApi = {
  list: (projectId: number) =>
    api.get<FileItem[]>(`/projects/${projectId}/files`),

  upload: (projectId: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post<FileItem>(`/projects/${projectId}/files`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  delete: (projectId: number, fileId: number) =>
    api.delete(`/projects/${projectId}/files/${fileId}`),

  preview: (projectId: number, fileId: number) =>
    api.get<FilePreview>(`/projects/${projectId}/files/${fileId}/preview`),
}