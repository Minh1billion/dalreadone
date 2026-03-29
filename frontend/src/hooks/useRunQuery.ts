import { useRef, useState } from 'react'
import { queryApi } from '../api/query'
import type { QueryResponse, StopwordsConfig } from '../api/query'

interface UseRunQueryOptions {
  onSuccess?: (fileId: number, question: string, result: QueryResponse) => void
}

export function useRunQuery(projectId: number, options?: UseRunQueryOptions) {
  const [data, setData] = useState<QueryResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [resultMeta, setResultMeta] = useState<{
    fileId: number
    question: string
  } | null>(null)

  const abortRef = useRef<AbortController | null>(null)

  async function run(fileId: number, question: string, stopwords?: StopwordsConfig) {
    abortRef.current?.abort()
    abortRef.current = new AbortController()

    setLoading(true)
    setError(null)

    try {
      const res = await queryApi.run(projectId, fileId, question, stopwords)
      setData(res.data)
      setResultMeta({ fileId, question })
      options?.onSuccess?.(fileId, question, res.data)
    } catch (e: any) {
      if (e?.code === 'ERR_CANCELED') return
      setError(e?.response?.data?.detail ?? 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  function reset() {
    abortRef.current?.abort()
    setData(null)
    setError(null)
    setResultMeta(null)
  }

  return { data, loading, error, resultMeta, run, reset }
}