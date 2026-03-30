import { useState, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { edaApi, type EDATask } from '../api/eda'

export function useEDA(fileId: number | null) {
  const qc = useQueryClient()
  const [taskId, setTaskId] = useState<string | null>(null)
  const [starting, setStarting] = useState(false)
  const [startError, setStartError] = useState<string | null>(null)

  const taskQuery = useQuery<EDATask>({
    queryKey: ['eda-task', taskId],
    enabled: !!taskId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'done' || status === 'error' ? false : 1500
    },
    queryFn: async () => {
      const { data } = await edaApi.status(taskId!)
      return data
    },
  })

  const start = useCallback(async () => {
    if (!fileId) return
    setStarting(true)
    setStartError(null)
    setTaskId(null)
    qc.removeQueries({ queryKey: ['eda-task'] })

    try {
      const { data } = await edaApi.start(fileId)
      setTaskId(data.task_id)
    } catch (err: any) {
      setStartError(
        err?.response?.data?.detail ?? err?.message ?? 'Failed to start EDA'
      )
    } finally {
      setStarting(false)
    }
  }, [fileId, qc])

  const reset = useCallback(() => {
    setTaskId(null)
    setStartError(null)
    qc.removeQueries({ queryKey: ['eda-task'] })
  }, [qc])

  const task = taskQuery.data ?? null

  return {
    start,
    reset,
    starting,
    startError,
    taskId,
    task,
    status:   task?.status ?? null,
    step:     task?.step ?? null,
    progress: task?.progress ?? 0,
    result:   task?.result ?? null,
    edaError: task?.error ?? null,
    isRunning: task?.status === 'pending' || task?.status === 'running',
    isDone:    task?.status === 'done',
    isError:   task?.status === 'error',
  }
}