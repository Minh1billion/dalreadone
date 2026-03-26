import { api } from './axios'

export const authApi = {
  login: (username: string, password: string) =>
    api.post('/api/auth/login', { username, password }),

  register: (username: string, password: string) =>
    api.post('/api/auth/register', { username, password }),

  logout: () =>
    api.post('/api/auth/logout'),

  refresh: () =>
    api.post('/api/auth/refresh'),
}