import { useRef, useState } from 'react'
import { queryApi } from '../api/query'
import type { QueryResponse } from '../api/query'

/**
 * Keeps the last result alive across file switches, deletes, and other
 * UI actions. Result is only cleared when:
 *   - A new run() starts (loading replaces it visually)
 *   - reset() is called explicitly (e.g. user logs out)
 */
export function useRunQuery(projectId: number) {
  const [data, setData] = useState<QueryResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Track the run that produced the current result for display context
  const [resultMeta, setResultMeta] = useState<{
    fileId: number
    question: string
  } | null>(null)

  // Abort controller so we can cancel in-flight requests if needed
  const abortRef = useRef<AbortController | null>(null)

  async function run(fileId: number, question: string) {
    // Cancel any in-flight request
    abortRef.current?.abort()
    abortRef.current = new AbortController()

    setLoading(true)
    setError(null)
    // Don't clear data here — keep old result visible while loading

    try {
      const res = await queryApi.run(projectId, fileId, question)
      setData(res.data)
      setResultMeta({ fileId, question })
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