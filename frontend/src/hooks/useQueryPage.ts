import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useRunQuery } from './useRunQuery'

/**
 * All stateful logic for QueryPage.
 * Component becomes a pure layout shell.
 */
export function useQueryPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()

  const pid = Number(projectId)
  const [activeFileId, setActiveFileId] = useState<number | null>(null)
  const [question, setQuestion] = useState('')

  const query = useRunQuery(pid)

  function handleSelectFile(id: number) {
    // Don't reset result — user might want to compare files
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
    // query state
    data: query.data,
    loading: query.loading,
    error: query.error,
    resultMeta: query.resultMeta,
    reset: query.reset,
  }
}