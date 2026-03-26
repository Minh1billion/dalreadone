import { api } from './axios'

export const projectsApi = {
  list: () =>
    api.get('/api/projects'),

  create: (name: string) =>
    api.post('/api/projects', { name }),

  update: (id: number, name: string) =>
    api.patch(`/api/projects/${id}`, { name }),

  delete: (id: number) =>
    api.delete(`/api/projects/${id}`),
}