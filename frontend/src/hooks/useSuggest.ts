import { useState, useCallback, useRef, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { suggestApi, type SuggestTask, type OperationConfig } from '../api/preprocess'

export function useSuggest() {
  const qc = useQueryClient()
  const [taskId,      setTaskId]      = useState<string | null>(null)
  const [starting,    setStarting]    = useState(false)
  const [startError,  setStartError]  = useState<string | null>(null)
  const [finalTask,   setFinalTask]   = useState<SuggestTask | null>(null)
  const fetchingFinal = useRef(false)

  const taskQuery = useQuery<SuggestTask>({
    queryKey: ['suggest-task', taskId],
    enabled:  !!taskId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'done' || status === 'error' ? false : 1500
    },
    queryFn: async () => {
      const { data } = await suggestApi.status(taskId!)
      return data
    },
  })

  useEffect(() => {
    const data = taskQuery.data
    if (!data) return
    if ((data.status === 'done' || data.status === 'error') && !fetchingFinal.current) {
      fetchingFinal.current = true
      suggestApi.status(data.task_id).then(res => {
        setFinalTask(res.data)
      }).catch(() => {
        setFinalTask(data)
      })
    }
  }, [taskQuery.data?.status, taskQuery.data?.task_id])

  const _doStart = useCallback(async (fn: () => Promise<{ data: { task_id: string } }>) => {
    setStarting(true)
    setStartError(null)
    setTaskId(null)
    setFinalTask(null)
    fetchingFinal.current = false
    qc.removeQueries({ queryKey: ['suggest-task'] })

    try {
      const { data } = await fn()
      setTaskId(data.task_id)
    } catch (err: any) {
      setStartError(err?.response?.data?.detail ?? err?.message ?? 'Failed to start suggest')
    } finally {
      setStarting(false)
    }
  }, [qc])

  const start        = useCallback((reviewTaskId: string) =>
    _doStart(() => suggestApi.start(reviewTaskId)), [_doStart])

  const startFromEda = useCallback((edaTaskId: string) =>
    _doStart(() => suggestApi.startFromEda(edaTaskId)), [_doStart])

  const reset = useCallback(() => {
    if (taskId) {
      try { suggestApi.cancel(taskId) } catch { /* silent */ }
    }
    setTaskId(null)
    setFinalTask(null)
    fetchingFinal.current = false
    setStartError(null)
    qc.removeQueries({ queryKey: ['suggest-task'] })
  }, [taskId, qc])

  const task = finalTask ?? taskQuery.data ?? null

  return {
    start,
    startFromEda,
    reset,
    starting,
    startError,
    taskId,
    status:    task?.status ?? null,
    progress:  task?.progress ?? 0,
    steps:     task?.steps ?? null as OperationConfig[] | null,
    astErrors: task?.ast_errors ?? null,
    taskError: task?.error ?? null,
    usage:     task?.usage ?? null,
    isRunning: starting || task?.status === 'pending' || task?.status === 'running',
    isDone:    task?.status === 'done',
    isError:   task?.status === 'error',
  }
}