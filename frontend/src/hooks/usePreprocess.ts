import { useState, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { preprocessApi, type OperationConfig, type PreprocessTask } from '../api/preprocess'

export function usePreprocess(fileId: number | null) {
  const qc = useQueryClient()
  const [taskId,       setTaskId]       = useState<string | null>(null)
  const [running,      setRunning]      = useState(false)
  const [runError,     setRunError]     = useState<string | null>(null)
  const [confirming,   setConfirming]   = useState(false)
  const [confirmError, setConfirmError] = useState<string | null>(null)
  const [confirmed,    setConfirmed]    = useState(false)

  const taskQuery = useQuery<PreprocessTask>({
    queryKey: ['preprocess-task', taskId],
    enabled: !!taskId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'done' || status === 'error' ? false : 1500
    },
    queryFn: async () => {
      const { data } = await preprocessApi.status(taskId!)
      return data
    },
  })

  const run = useCallback(async (steps: OperationConfig[]) => {
    if (!fileId) return
    setRunning(true)
    setRunError(null)
    setConfirmed(false)
    setConfirmError(null)
    setTaskId(null)
    qc.removeQueries({ queryKey: ['preprocess-task'] })

    try {
      const { data } = await preprocessApi.run(fileId, steps)
      setTaskId(data.task_id)
    } catch (err: any) {
      setRunError(err?.response?.data?.detail ?? err?.message ?? 'Failed to start preprocessing')
    } finally {
      setRunning(false)
    }
  }, [fileId, qc])

  const confirm = useCallback(async (onSuccess?: () => void) => {
    if (!taskId) return
    setConfirming(true)
    setConfirmError(null)

    try {
      await preprocessApi.confirm(taskId)
      setConfirmed(true)
      setTaskId(null)
      qc.removeQueries({ queryKey: ['preprocess-task'] })
      onSuccess?.()
    } catch (err: any) {
      setConfirmError(err?.response?.data?.detail ?? err?.message ?? 'Failed to confirm')
    } finally {
      setConfirming(false)
    }
  }, [taskId, qc])

  const discard = useCallback(async () => {
    if (taskId) {
      try { await preprocessApi.cancel(taskId) } catch { /* silent */ }
      qc.removeQueries({ queryKey: ['preprocess-task'] })
    }
    setTaskId(null)
    setRunError(null)
    setConfirmError(null)
    setConfirmed(false)
  }, [taskId, qc])

  const reset = useCallback(() => {
    setTaskId(null)
    setRunError(null)
    setConfirmError(null)
    setConfirmed(false)
    qc.removeQueries({ queryKey: ['preprocess-task'] })
  }, [qc])

  const task = taskQuery.data ?? null

  return {
    run,
    confirm,
    discard,
    reset,
    running,
    runError,
    confirming,
    confirmError,
    confirmed,
    taskId,
    task,
    status:    task?.status ?? null,
    step:      task?.step ?? null,
    progress:  task?.progress ?? 0,
    preview:   task?.preview ?? null,
    taskError: task?.error ?? null,
    isPending: task?.status === 'pending',
    isRunning: task?.status === 'pending' || task?.status === 'running',
    isDone:    task?.status === 'done',
    isError:   task?.status === 'error',
  }
}