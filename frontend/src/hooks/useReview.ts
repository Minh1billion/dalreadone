import { useState, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { reviewApi, type ReviewTask } from '../api/eda'

export function useReview(edaTaskId: string | null) {
  const qc = useQueryClient()
  const [reviewTaskId, setReviewTaskId] = useState<string | null>(null)
  const [starting, setStarting]         = useState(false)
  const [startError, setStartError]     = useState<string | null>(null)

  const taskQuery = useQuery<ReviewTask>({
    queryKey: ['review-task', reviewTaskId],
    enabled:  !!edaTaskId && !!reviewTaskId,
    refetchInterval: (query) => {
      const s = query.state.data?.status
      return s === 'done' || s === 'error' ? false : 1500
    },
    queryFn: async () => {
      const { data } = await reviewApi.status(edaTaskId!, reviewTaskId!)
      return data
    },
  })

  const start = useCallback(async () => {
    if (!edaTaskId) return
    setStarting(true)
    setStartError(null)
    setReviewTaskId(null)
    qc.removeQueries({ queryKey: ['review-task'] })

    try {
      const { data } = await reviewApi.start(edaTaskId)
      setReviewTaskId(data.task_id)
    } catch (err: any) {
      setStartError(
        err?.response?.data?.detail ?? err?.message ?? 'Failed to start review'
      )
    } finally {
      setStarting(false)
    }
  }, [edaTaskId, qc])

  const reset = useCallback(() => {
    setReviewTaskId(null)
    setStartError(null)
    qc.removeQueries({ queryKey: ['review-task'] })
  }, [qc])

  const task = taskQuery.data ?? null

  return {
    start,
    reset,
    starting,
    startError,
    reviewTaskId,
    task,
    status:    task?.status ?? null,
    progress:  task?.progress ?? 0,
    result:    task?.result ?? null,
    usage:     task?.usage ?? null,
    error:     task?.error ?? null,
    isRunning: task?.status === 'pending' || task?.status === 'running',
    isDone:    task?.status === 'done',
    isError:   task?.status === 'error',
  }
}