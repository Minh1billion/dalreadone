import { useState } from 'react'
import { queryApi } from '../api/query'
import type { QueryResponse } from '../api/query'

export function useRunQuery(projectId: number, fileId: number | null) {
  const [data, setData] = useState<QueryResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run(question: string) {
    if (!fileId) return
    setLoading(true)
    setError(null)
    try {
      const res = await queryApi.run(projectId, fileId, question)
      setData(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  function reset() {
    setData(null)
    setError(null)
  }

  return { data, loading, error, run, reset }
}