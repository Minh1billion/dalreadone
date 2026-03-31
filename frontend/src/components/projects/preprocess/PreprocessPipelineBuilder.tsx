import { useState, useCallback } from 'react'
import { Plus } from 'lucide-react'
import type { StepConfig, StepName } from '../../../api/preprocess'
import { STEP_META, defaultStepConfig } from './PreprocessTypes'
import { StepCard } from './StepCard'
import {
  MissingParamsForm,
  EncodingParamsForm,
  OutlierParamsForm,
  ScalingParamsForm,
} from './StepParamForms'

interface PipelineStep {
  id:      string
  config:  StepConfig
  enabled: boolean
}

interface Props {
  onRun:     (steps: StepConfig[]) => void
  isRunning: boolean
  disabled?: boolean
  columns?:  string[]
}

let _id = 0
const uid = () => String(++_id)

function makeStep(name: StepName): PipelineStep {
  return { id: uid(), config: defaultStepConfig(name), enabled: true }
}

const DEFAULT_STEPS: PipelineStep[] = [
  makeStep('missing'),
  makeStep('encoding'),
  makeStep('outlier'),
  makeStep('scaling'),
]

export function PreprocessPipelineBuilder({ onRun, isRunning, disabled, columns = [] }: Props) {
  const [steps,    setSteps]    = useState<PipelineStep[]>(DEFAULT_STEPS)
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})
  const [dragIdx,  setDragIdx]  = useState<number | null>(null)
  const [overIdx,  setOverIdx]  = useState<number | null>(null)

  const usedNames = steps.map((s) => s.config.name)
  const available = STEP_META.filter((m) => !usedNames.includes(m.key))

  const toggleExpanded = (id: string) =>
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }))

  const toggleEnabled = (idx: number) =>
    setSteps((prev) =>
      prev.map((s, i) => (i === idx ? { ...s, enabled: !s.enabled } : s))
    )

  const removeStep = (idx: number) =>
    setSteps((prev) => prev.filter((_, i) => i !== idx))

  const addStep = (name: StepName) =>
    setSteps((prev) => [...prev, makeStep(name)])

  const updateParams = useCallback((idx: number, params: StepConfig['params']) =>
    setSteps((prev) =>
      prev.map((s, i) => (i === idx ? { ...s, config: { ...s.config, params } as StepConfig } : s))
    ), [])

  const handleDragStart = (idx: number) => setDragIdx(idx)
  const handleDragOver  = (e: React.DragEvent, idx: number) => { e.preventDefault(); setOverIdx(idx) }
  const handleDrop = () => {
    if (dragIdx === null || overIdx === null || dragIdx === overIdx) {
      setDragIdx(null); setOverIdx(null); return
    }
    setSteps((prev) => {
      const next = [...prev]
      const [moved] = next.splice(dragIdx, 1)
      next.splice(overIdx, 0, moved)
      return next
    })
    setDragIdx(null); setOverIdx(null)
  }

  const handleRun = () => {
    const active = steps.filter((s) => s.enabled).map((s) => s.config)
    onRun(active)
  }

  return (
    <div className="space-y-3">
      <div className="space-y-2">
        {steps.map((step, idx) => {
          const meta   = STEP_META.find((m) => m.key === step.config.name)!
          const isOver = overIdx === idx && dragIdx !== null && dragIdx !== idx
          return (
            <div
              key={step.id}
              draggable
              onDragStart={() => handleDragStart(idx)}
              onDragOver={(e) => handleDragOver(e, idx)}
              onDrop={handleDrop}
              onDragEnd={() => { setDragIdx(null); setOverIdx(null) }}
              className={`transition-all duration-150 ${isOver ? 'ring-2 ring-primary-400 ring-offset-1 rounded-xl' : ''}`}
            >
              <StepCard
                meta={meta}
                index={idx}
                enabled={step.enabled}
                expanded={!!expanded[step.id]}
                config={step.config}
                onToggleEnabled={() => toggleEnabled(idx)}
                onToggleExpanded={() => toggleExpanded(step.id)}
                onRemove={() => removeStep(idx)}
              >
                {step.config.name === 'missing' && (
                  <MissingParamsForm
                    params={step.config.params as any}
                    onChange={(p) => updateParams(idx, p)}
                    columns={columns}
                  />
                )}
                {step.config.name === 'encoding' && (
                  <EncodingParamsForm
                    params={step.config.params as any}
                    onChange={(p) => updateParams(idx, p)}
                    columns={columns}
                  />
                )}
                {step.config.name === 'outlier' && (
                  <OutlierParamsForm
                    params={step.config.params as any}
                    onChange={(p) => updateParams(idx, p)}
                    columns={columns}
                  />
                )}
                {step.config.name === 'scaling' && (
                  <ScalingParamsForm
                    params={step.config.params as any}
                    onChange={(p) => updateParams(idx, p)}
                    columns={columns}
                  />
                )}
              </StepCard>
            </div>
          )
        })}
      </div>

      {available.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-1">
          {available.map((m) => (
            <button
              key={m.key}
              onClick={() => addStep(m.key)}
              className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-md border border-dashed border-gray-300 text-gray-500 hover:border-primary-400 hover:text-primary-600 hover:bg-primary-50 transition-colors"
            >
              <Plus size={11} />
              {m.label}
            </button>
          ))}
        </div>
      )}

      <div className="pt-1 flex items-center justify-between">
        <p className="text-xs text-gray-400">
          {steps.filter((s) => s.enabled).length} of {steps.length} steps active
        </p>
        <button
          onClick={handleRun}
          disabled={isRunning || disabled || steps.filter((s) => s.enabled).length === 0}
          className="text-xs px-4 py-2 rounded-md bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {isRunning ? 'Running…' : 'Run pipeline'}
        </button>
      </div>
    </div>
  )
}