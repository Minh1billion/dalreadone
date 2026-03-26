import { api } from './axios'

export const queryApi = {
  run: (projectId: number, fileId: number, question: string) =>
    api.post(
      `/projects/${projectId}/files/${fileId}/query`,
      { question },
      { timeout: 60_000 }
    ),
}