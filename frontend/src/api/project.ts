import { api } from './axios'

export const projectsApi = {
  list: () =>
    api.get('/projects'),

  create: (name: string) =>
    api.post('/projects', { name }),

  update: (id: number, name: string) =>
    api.patch(`/projects/${id}`, { name }),

  delete: (id: number) =>
    api.delete(`/projects/${id}`),
}