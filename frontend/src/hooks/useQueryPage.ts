import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useRunQuery } from './useRunQuery'
import { useQueryHistory } from './useQueryHistory'

export function useQueryPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()

  const pid = Number(projectId)
  const [activeFileId, setActiveFileId] = useState<number | null>(null)
  const [question, setQuestion] = useState('')

  const qc = useQueryClient()
  const { saveNewResult } = useQueryHistory()

  const query = useRunQuery(pid, {
    onSuccess: (fileId, q, result) => {
      // Read filename from React Query cache - FilePanel already fetched it
      const files: any[] = qc.getQueryData(['files', pid]) ?? []
      const filename = files.find(f => f.id === fileId)?.filename ?? ''
      saveNewResult({
        project_id: pid,
        file_id:    fileId,
        filename,
        question:   q || null,
        result,
      })
    },
  })

  function handleSelectFile(id: number) {
    setActiveFileId(id || null)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!activeFileId) return
    await query.run(activeFileId, question)
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as any)
    }
  }

  function handleBack() {
    navigate('/')
  }

  return {
    pid,
    activeFileId,
    question,
    setQuestion,
    handleSelectFile,
    handleSubmit,
    handleKeyDown,
    handleBack,
    data:       query.data,
    loading:    query.loading,
    error:      query.error,
    resultMeta: query.resultMeta,
    reset:      query.reset,
  }
}