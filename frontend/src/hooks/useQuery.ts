import { useState } from 'react'
import { queryApi } from '../api/query'

export function useRunQuery(projectId: number, fileId: number | null) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<any>(null)

  async function run(question: string) {
    if (!fileId) return
    setError('')
    setLoading(true)
    setResult(null)
    try {
      const { data } = await queryApi.run(projectId, fileId, question)
      setResult(data)
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Query failed')
    } finally {
      setLoading(false)
    }
  }

  return { run, loading, error, result }
}