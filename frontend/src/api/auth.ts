import { api } from './axios'

export const authApi = {
  login: (username: string, password: string) =>
      api.post('/auth/login', { username, password }),

  register: (username: string, password: string) =>
      api.post('/auth/register', { username, password }),

  logout: () =>
      api.post('/auth/logout'),

  refresh: () =>
      api.post('/auth/refresh'),
}