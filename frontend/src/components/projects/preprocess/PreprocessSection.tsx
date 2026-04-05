import { useState, useCallback, useEffect } from 'react'
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import {
  SortableContext,
  verticalListSortingStrategy,
  arrayMove,
  useSortable,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

import type { usePreprocess } from '../../../hooks/usePreprocess'
import type { useSuggest } from '../../../hooks/useSuggest'
import type { DraftStep, ColTypeMap } from './PreprocessTypes'
import { draftToConfig, inferColTypes, suggestToSteps } from './PreprocessTypes'
import { PreprocessStepCard } from './PreprocessStepCard'
import { PreprocessPreview } from './PreprocessPreview'

function SortableStep({
  step, index, colTypeMap, onChange, onRemove,
}: {
  step:       DraftStep
  index:      number
  colTypeMap: ColTypeMap
  onChange:   (s: DraftStep) => void
  onRemove:   () => void
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: step.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <div ref={setNodeRef} style={style}>
      <PreprocessStepCard
        step={step}
        index={index}
        colTypeMap={colTypeMap}
        onChange={onChange}
        onRemove={onRemove}
        dragHandleProps={{ ...attributes, ...listeners }}
      />
    </div>
  )
}

let idCounter = 0
function newStep(): DraftStep {
  return { id: `step-${++idCounter}`, operation: null, strategy: null, params: {}, cols: null }
}

interface Props {
  preprocess:       ReturnType<typeof usePreprocess>
  suggest:          ReturnType<typeof useSuggest>
  reviewTaskId:     string | null
  edaTaskId:        string | null
  preview:          { columns: string[]; rows: Record<string, unknown>[] } | null
  onConfirmSuccess: () => void
  collapsed:        boolean
  onToggle:         () => void
}

const PREPROCESS_STEPS_LABELS: Record<string, string> = {
  loading_file:      'Loading file',
  building_pipeline: 'Building pipeline',
  running_pipeline:  'Running pipeline',
  saving_result:     'Saving result',
  done:              'Done',
}

export function PreprocessSection({
  preprocess,
  suggest,
  reviewTaskId,
  edaTaskId,
  preview,
  onConfirmSuccess,
  collapsed,
  onToggle,
}: Props) {
  const [steps,        setSteps]        = useState<DraftStep[]>([])
  const [dirty,        setDirty]        = useState(false)
  const [showProgress, setShowProgress] = useState(false)

  useEffect(() => {
    if (preprocess.isRunning) {
      setShowProgress(true)
    } else if (preprocess.isDone || preprocess.isError) {
      const t = setTimeout(() => setShowProgress(false), 400)
      return () => clearTimeout(t)
    }
  }, [preprocess.isRunning, preprocess.isDone, preprocess.isError])

  useEffect(() => {
    if (suggest.isDone && suggest.steps) {
      setSteps(suggestToSteps(suggest.steps))
      setDirty(false)
    }
  }, [suggest.isDone, suggest.steps])

  const colTypeMap: ColTypeMap =
    preview ? inferColTypes(preview.columns, preview.rows as Record<string, unknown>[]) : {}

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }))

  function addStep() {
    setSteps(prev => [...prev, newStep()])
  }

  function updateStep(id: string, updated: DraftStep) {
    setSteps(prev => prev.map(s => s.id === id ? updated : s))
    if (preprocess.isDone) setDirty(true)
  }

  function removeStep(id: string) {
    setSteps(prev => prev.filter(s => s.id !== id))
    if (preprocess.isDone) setDirty(true)
  }

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event
    if (over && active.id !== over.id) {
      setSteps(prev => {
        const oldIdx = prev.findIndex(s => s.id === active.id)
        const newIdx = prev.findIndex(s => s.id === over.id)
        return arrayMove(prev, oldIdx, newIdx)
      })
      if (preprocess.isDone) setDirty(true)
    }
  }

  const handleRun = useCallback(async () => {
    const configs = steps.map(draftToConfig).filter(Boolean) as ReturnType<typeof draftToConfig>[]
    if (configs.length !== steps.length) return
    setDirty(false)
    await preprocess.run(configs as any)
  }, [steps, preprocess])

  const handleDiscard = useCallback(() => {
    preprocess.discard()
    setDirty(false)
  }, [preprocess])

  const handleConfirm = useCallback(() => {
    preprocess.confirm(onConfirmSuccess)
  }, [preprocess, onConfirmSuccess])

  const handleSuggest = useCallback(() => {
    if (reviewTaskId) {
      suggest.start(reviewTaskId)
    } else if (edaTaskId) {
      suggest.startFromEda(edaTaskId)
    }
  }, [reviewTaskId, edaTaskId, suggest])

  const validSteps    = steps.filter(s => s.operation && s.strategy)
  const hasIncomplete = steps.some(s => !s.operation || !s.strategy)
  const canRun        = validSteps.length > 0 && !hasIncomplete && !preprocess.isRunning

  const previewCols = preprocess.preview?.length
    ? Object.keys(preprocess.preview[0])
    : preview?.columns ?? []

  const transformedCols = new Set<string>(
    steps.flatMap(s => {
      if (!s.strategy || s.strategy === 'drop_col') return []
      if (s.operation === 'custom_code') return previewCols
      return s.cols ?? (preview?.columns ?? [])
    })
  )
  const droppedCols = new Set<string>(
    steps.flatMap(s => {
      if (s.strategy === 'drop_col') return s.cols ?? []
      return []
    })
  )

  const displayProgress = preprocess.isRunning ? preprocess.progress : 100
  const displayStep     = preprocess.isRunning
    ? (PREPROCESS_STEPS_LABELS[preprocess.step ?? ''] ?? preprocess.step ?? 'Starting…')
    : 'Done'

  return (
    <section className='bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden'>
      <div className='px-5 py-3 border-b border-gray-100 flex items-center justify-between'>
        <h2 className='text-sm font-semibold text-gray-700'>Preprocessing Pipeline</h2>
        <div className='flex items-center gap-2'>


          {preview && !preprocess.isRunning && (
            <button
              onClick={handleSuggest}
              disabled={!edaTaskId || suggest.isRunning}
              className='text-xs px-3 py-1.5 rounded-md border border-primary-300 text-primary-700
                         hover:bg-primary-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors'
            >
              {suggest.isRunning ? 'Suggesting…' : suggest.isDone ? '✦ Re-suggest' : '✦ AI Suggest'}
            </button>
          )}

          {steps.length > 0 && !preprocess.isRunning && (
            <button
              onClick={addStep}
              className='text-xs px-2.5 py-1.5 rounded-md border border-gray-200 text-gray-500 hover:border-gray-300 hover:text-gray-700 transition-colors'
            >
              + Add step
            </button>
          )}

          {!preprocess.isRunning && !preprocess.isDone && (
            <button
              onClick={handleRun}
              disabled={!canRun}
              className='text-xs px-3 py-1.5 rounded-md bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors'
            >
              Run
            </button>
          )}

          {preprocess.isDone && !dirty && (
            <>
              <button
                onClick={handleDiscard}
                className='text-xs px-2.5 py-1.5 rounded-md border border-gray-200 text-gray-500 hover:border-red-200 hover:text-red-500 transition-colors'
              >
                Discard
              </button>
              <button
                onClick={handleConfirm}
                disabled={preprocess.confirming}
                className='text-xs px-3 py-1.5 rounded-md bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 transition-colors'
              >
                {preprocess.confirming ? 'Saving…' : 'Confirm & Save'}
              </button>
            </>
          )}

          {preprocess.isDone && dirty && (
            <button
              onClick={handleRun}
              disabled={!canRun}
              className='text-xs px-3 py-1.5 rounded-md bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors'
            >
              Re-run
            </button>
          )}

          <button
            onClick={onToggle}
            className='flex items-center justify-center w-6 h-6 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors ml-1'
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              {collapsed
                ? <path d="M5 3l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                : <path d="M3 5l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              }
            </svg>
          </button>
        </div>
      </div>

      {!collapsed && (
        <div className='p-5 space-y-4'>

          {!preview && (
            <p className='text-xs text-gray-400 text-center py-4'>Load a file preview first to start building a pipeline.</p>
          )}

          {preview && steps.length === 0 && !preprocess.isRunning && !preprocess.isDone && !preprocess.isError && !suggest.isRunning && (
            <div className='flex flex-col items-center gap-3 py-8'>
              <p className='text-sm text-gray-400'>Pipeline is empty</p>
              <div className='flex items-center gap-2'>
                {edaTaskId && (
                  <button
                    onClick={handleSuggest}
                    disabled={suggest.isRunning}
                    className='text-xs px-3 py-1.5 rounded-md border border-primary-300 text-primary-700 hover:bg-primary-50 transition-colors'
                  >
                    ✦ AI Suggest
                  </button>
                )}
                <button
                  onClick={addStep}
                  className='text-xs px-3 py-1.5 rounded-md bg-primary-600 text-white hover:bg-primary-700 transition-colors'
                >
                  + Add first step
                </button>
              </div>
            </div>
          )}

          {suggest.isRunning && (
            <div className='space-y-2'>
              <div className='flex justify-between text-xs text-gray-500 mb-1'>
                <span className='flex items-center gap-1.5'>
                  <span className='text-primary-500 animate-pulse'>✦</span>
                  Generating suggestions…
                </span>
                <span>{suggest.progress}%</span>
              </div>
              <div className='h-1.5 bg-gray-100 rounded-full overflow-hidden'>
                <div
                  className='h-full bg-primary-400 rounded-full transition-all duration-500'
                  style={{ width: `${suggest.progress}%` }}
                />
              </div>
            </div>
          )}

          {suggest.isError && (
            <div className='rounded-lg bg-red-50 border border-red-100 px-3 py-2.5 text-xs text-red-600 flex items-center justify-between'>
              <span>Suggest failed: {suggest.taskError ?? suggest.startError}</span>
              <button onClick={suggest.reset} className='underline hover:text-red-700'>Dismiss</button>
            </div>
          )}

          {suggest.isDone && suggest.astErrors && suggest.astErrors.length > 0 && (
            <div className='rounded-lg bg-amber-50 border border-amber-100 px-3 py-2.5 text-xs text-amber-700'>
              <p className='font-medium mb-1'>Some custom steps were skipped due to code errors:</p>
              <ul className='list-disc list-inside space-y-0.5'>
                {suggest.astErrors.map((e, i) => <li key={i}>{e}</li>)}
              </ul>
            </div>
          )}

          {suggest.isDone && steps.length > 0 && !preprocess.isDone && (
            <div className='flex items-center gap-2 rounded-lg bg-primary-50 border border-primary-100 px-3 py-2.5 text-xs text-primary-700'>
              <span className='text-primary-400'>✦</span>
              <span>Pipeline built from AI suggestions. Review and edit steps below, then run when ready.</span>
            </div>
          )}

          {dirty && preprocess.isDone && (
            <div className='flex items-start gap-2 rounded-lg bg-amber-50 border border-amber-100 px-3 py-2.5 text-xs text-amber-700'>
              <span className='shrink-0 mt-0.5'>⚠</span>
              <span>Pipeline has been modified since last run. The preview below is outdated - re-run to update results before saving.</span>
            </div>
          )}

          {hasIncomplete && (
            <p className='text-[11px] text-amber-500'>Some steps are incomplete - select operation and strategy for each step before running.</p>
          )}

          {preprocess.runError && (
            <div className='rounded-lg bg-red-50 border border-red-100 px-3 py-2.5 text-xs text-red-600'>
              {preprocess.runError}
            </div>
          )}

          {preprocess.confirmError && (
            <div className='rounded-lg bg-red-50 border border-red-100 px-3 py-2.5 text-xs text-red-600'>
              {preprocess.confirmError}
            </div>
          )}

          {preprocess.confirmed && (
            <div className='rounded-lg bg-green-50 border border-green-100 px-3 py-2.5 text-xs text-green-700'>
              File saved to project successfully.
            </div>
          )}

          {steps.length > 0 && !preprocess.isRunning && !suggest.isRunning && (
            <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
              <SortableContext items={steps.map(s => s.id)} strategy={verticalListSortingStrategy}>
                <div className='space-y-2'>
                  {steps.map((step, i) => (
                    <SortableStep
                      key={step.id}
                      step={step}
                      index={i}
                      colTypeMap={colTypeMap}
                      onChange={updated => updateStep(step.id, updated)}
                      onRemove={() => removeStep(step.id)}
                    />
                  ))}
                </div>
              </SortableContext>
            </DndContext>
          )}

          {showProgress && (
            <div className='space-y-2'>
              <div className='flex justify-between text-xs text-gray-500 mb-1'>
                <span>{displayStep}</span>
                <span>{displayProgress}%</span>
              </div>
              <div className='h-1.5 bg-gray-100 rounded-full overflow-hidden'>
                <div
                  className='h-full bg-primary-500 rounded-full transition-all duration-500'
                  style={{ width: `${displayProgress}%` }}
                />
              </div>
            </div>
          )}

          {preprocess.isError && (
            <div className='rounded-lg bg-red-50 border border-red-100 p-4 text-sm text-red-600'>
              <p className='font-medium mb-1'>Pipeline failed</p>
              <p className='text-xs text-red-500'>{preprocess.taskError}</p>
              <button onClick={() => preprocess.reset()} className='mt-3 text-xs underline hover:text-red-700'>
                Dismiss
              </button>
            </div>
          )}

          {preprocess.isDone && preprocess.preview && (
            <div className='space-y-2'>
              <p className='text-xs font-medium text-gray-600'>Result preview</p>
              <PreprocessPreview
                preview={preprocess.preview as Record<string, unknown>[]}
                transformedCols={transformedCols}
                droppedCols={droppedCols}
              />
            </div>
          )}

        </div>
      )}
    </section>
  )
}