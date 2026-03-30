import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { filesApi } from '../api/files'

export function useFiles(projectId: number) {
  return useQuery({
    queryKey: ['files', projectId],
    enabled: !!projectId,
    queryFn: async () => {
      const { data } = await filesApi.list(projectId)
      return data
    },
  })
}

export function useUploadFile(projectId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => filesApi.upload(projectId, file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['files', projectId] }),
  })
}

export function useDeleteFile(projectId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (fileId: number) => filesApi.delete(projectId, fileId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['files', projectId] }),
  })
}