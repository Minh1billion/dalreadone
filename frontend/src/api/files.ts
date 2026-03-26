import { api } from './axios'

export const filesApi = {
  list: (projectId: number) =>
    api.get(`/api/projects/${projectId}/files`),

  upload: (projectId: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/api/projects/${projectId}/files`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  delete: (projectId: number, fileId: number) =>
    api.delete(`/api/projects/${projectId}/files/${fileId}`),
}