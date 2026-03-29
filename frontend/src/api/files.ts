import { api } from './axios'

export type FilePreview = {
  filename: string
  shape: { rows: number; cols: number }
  columns: string[]
  dtypes: Record<string, string>
  missing: {
    column: string
    dtype: string
    null_count: number
    null_pct: number
  }[]
  describe: {
    column: string
    count: number | null
    mean: number | null
    std: number | null
    min: number | null
    p25: number | null
    median: number | null
    p75: number | null
    max: number | null
  }[]
  sample: Record<string, unknown>[]
  strategy: 'nlp' | 'structured'
  text_cols: string[]
}

export const filesApi = {
  list: (projectId: number) =>
    api.get(`/projects/${projectId}/files`),

  upload: (projectId: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/projects/${projectId}/files`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  delete: (projectId: number, fileId: number) =>
    api.delete(`/projects/${projectId}/files/${fileId}`),

  preview: (projectId: number, fileId: number) =>
    api.get<FilePreview>(`/projects/${projectId}/files/${fileId}/preview`),
}