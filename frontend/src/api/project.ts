import { api } from './axios'

export interface Project {
  id: number
  name: string
}

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