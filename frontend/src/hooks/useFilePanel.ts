import { useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../store/authStore'
import { useFiles, useDeleteFile } from './useFiles'

interface Options {
  projectId: number
  activeFileId: number | null
  onSelectFile: (id: number) => void
}

/**
 * Encapsulates all FilePanel logic:
 *   - file list fetching
 *   - XHR upload with progress tracking
 *   - delete with active-file guard
 */
export function useFilePanel({ projectId, activeFileId, onSelectFile }: Options) {
  const inputRef = useRef<HTMLInputElement>(null)
  const queryClient = useQueryClient()

  const filesQuery = useFiles(projectId)
  const deleteMutation = useDeleteFile(projectId)

  const [uploadProgress, setUploadProgress] = useState<number | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)

  const isUploading = uploadProgress !== null

  function triggerFilePicker() {
    inputRef.current?.click()
  }

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    setUploadError(null)
    setUploadProgress(0)

    const formData = new FormData()
    formData.append('file', file)

    try {
      await new Promise<void>((resolve, reject) => {
        const xhr = new XMLHttpRequest()

        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            setUploadProgress(Math.round((event.loaded / event.total) * 100))
          }
        })

        xhr.addEventListener('load', () => {
          xhr.status >= 200 && xhr.status < 300 ? resolve() : reject(new Error(xhr.statusText))
        })
        xhr.addEventListener('error', () => reject(new Error('Network error')))
        xhr.addEventListener('abort', () => reject(new Error('Upload cancelled')))

        const token = useAuthStore.getState().accessToken
        const baseURL = import.meta.env.VITE_API_BASE_URL ?? ''

        xhr.open('POST', `${baseURL}/projects/${projectId}/files`)
        if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)
        xhr.withCredentials = true
        xhr.send(formData)
      })

      await queryClient.invalidateQueries({ queryKey: ['files', projectId] })
    } catch (err: any) {
      setUploadError(err.message ?? 'Upload failed')
    } finally {
      setUploadProgress(null)
      e.target.value = ''
    }
  }

  async function handleDelete(e: React.MouseEvent, fileId: number) {
    e.stopPropagation()
    if (activeFileId === fileId) onSelectFile(0)
    await deleteMutation.mutateAsync(fileId)
  }

  return {
    inputRef,
    files: filesQuery.data ?? [],
    isLoading: filesQuery.isLoading,
    isUploading,
    uploadProgress,
    uploadError,
    triggerFilePicker,
    handleFileChange,
    handleDelete,
  }
}