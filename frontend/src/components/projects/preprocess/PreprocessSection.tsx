import { useState } from 'react'
import type { StepConfig, StepName } from '../../../api/preprocess'
import { usePreprocess } from '../../../hooks/usePreprocess'
import { PreprocessPipelineBuilder } from './PreprocessPipelineBuilder'
import { PreprocessProgress } from './PreprocessProgress'
import { PreprocessResultDashboard } from './PreprocessResultDashboard'

interface Props {
  fileId:    number | null
  projectId: number
  columns?:  string[]
}

export function PreprocessSection({ fileId, projectId, columns = [] }: Props) {
  const pp = usePreprocess(fileId)
  const [lastSteps, setLastSteps] = useState<StepName[]>([])

  function handleRun(steps: StepConfig[]) {
    setLastSteps(steps.map((s) => s.name))
    pp.start(steps)
  }

  const showBuilder = !pp.isRunning && !pp.isDone && !pp.isError

  return (
    <section className="bg-white rounded-xl border border-gray-100 shadow-sm">
      <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-700">Preprocessing</h2>
        {(pp.isError || pp.isDone) && (
          <button
            onClick={pp.reset}
            className="text-xs px-3 py-1.5 rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
          >
            Reconfigure
          </button>
        )}
      </div>

      <div className="p-5">
        {!fileId && (
          <p className="text-sm text-gray-400 text-center py-6">Select a file to configure preprocessing.</p>
        )}

        {fileId && showBuilder && (
          <PreprocessPipelineBuilder
            onRun={handleRun}
            isRunning={pp.starting}
            disabled={!fileId}
            columns={columns}
          />
        )}

        {pp.startError && (
          <p className="text-sm text-red-500 py-2">{pp.startError}</p>
        )}

        {(pp.isRunning || pp.starting) && (
          <PreprocessProgress
            step={pp.step}
            progress={pp.progress}
            activeSteps={lastSteps}
          />
        )}

        {pp.isError && (
          <div className="rounded-lg bg-red-50 border border-red-100 p-4 text-sm text-red-600">
            <p className="font-medium mb-1">Preprocessing failed</p>
            <p className="text-xs text-red-500">{pp.ppError}</p>
          </div>
        )}

        {pp.isDone && pp.result && (
          <PreprocessResultDashboard
            result={pp.result}
            saving={pp.saving}
            saved={pp.saved}
            saveError={pp.saveError}
            onSave={() => pp.save(projectId)}
          />
        )}
      </div>
    </section>
  )
}