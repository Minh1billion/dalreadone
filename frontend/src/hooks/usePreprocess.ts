import { useState, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { preprocessApi, type StepConfig, type PreprocessTask } from '../api/preprocess'

export function usePreprocess(fileId: number | null) {
  const qc = useQueryClient()
  const [taskId,     setTaskId]     = useState<string | null>(null)
  const [starting,   setStarting]   = useState(false)
  const [startError, setStartError] = useState<string | null>(null)
  const [saving,     setSaving]     = useState(false)
  const [saveError,  setSaveError]  = useState<string | null>(null)
  const [saved,      setSaved]      = useState(false)

  const taskQuery = useQuery<PreprocessTask>({
    queryKey: ['preprocess-task', taskId],
    enabled:  !!taskId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'done' || status === 'error' ? false : 1500
    },
    queryFn: async () => {
      const { data } = await preprocessApi.status(taskId!)
      return data
    },
  })

  const start = useCallback(async (steps: StepConfig[]) => {
    if (!fileId) return
    setStarting(true)
    setStartError(null)
    setSaveError(null)
    setSaved(false)
    setTaskId(null)
    qc.removeQueries({ queryKey: ['preprocess-task'] })

    try {
      const { data } = await preprocessApi.start(fileId, steps)
      setTaskId(data.task_id)
    } catch (err: any) {
      setStartError(
        err?.response?.data?.detail ?? err?.message ?? 'Failed to start preprocessing'
      )
    } finally {
      setStarting(false)
    }
  }, [fileId, qc])

  const save = useCallback(async (projectId: number) => {
    if (!taskId) return
    setSaving(true)
    setSaveError(null)
    try {
      await preprocessApi.save(taskId)
      setSaved(true)
      // Invalidate file list so sidebar refreshes
      qc.invalidateQueries({ queryKey: ['files', projectId] })
    } catch (err: any) {
      setSaveError(
        err?.response?.data?.detail ?? err?.message ?? 'Failed to save file'
      )
    } finally {
      setSaving(false)
    }
  }, [taskId, qc])

  const reset = useCallback(() => {
    setTaskId(null)
    setStartError(null)
    setSaveError(null)
    setSaved(false)
    qc.removeQueries({ queryKey: ['preprocess-task'] })
  }, [qc])

  const task = taskQuery.data ?? null

  return {
    start,
    save,
    reset,
    starting,
    startError,
    saving,
    saveError,
    saved,
    taskId,
    task,
    status:    task?.status ?? null,
    step:      task?.step ?? null,
    progress:  task?.progress ?? 0,
    result:    task?.result ?? null,
    ppError:   task?.error ?? null,
    isRunning: task?.status === 'pending' || task?.status === 'running',
    isDone:    task?.status === 'done',
    isError:   task?.status === 'error',
  }
}