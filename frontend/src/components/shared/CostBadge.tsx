type UsageSummary = {
  summary: {
    total_tokens:            number
    total_prompt_tokens:     number
    total_completion_tokens: number
    total_cost_usd:          number
  }
}

interface Props {
  usage: UsageSummary | Record<string, unknown> | null | undefined
  label?: string
}

function isUsage(u: unknown): u is UsageSummary {
  return (
    typeof u === 'object' && u !== null &&
    'summary' in u &&
    typeof (u as any).summary?.total_tokens === 'number'
  )
}

export function CostBadge({ usage, label }: Props) {
  if (!isUsage(usage)) return null

  const { total_tokens, total_prompt_tokens, total_completion_tokens, total_cost_usd } =
    usage.summary

  const fmtTokens = (n: number) =>
    n >= 1_000 ? `${(n / 1_000).toFixed(1)}k` : String(n)

  const fmtCost = (n: number) =>
    n < 0.0001 ? '<$0.0001' : `$${n.toFixed(4)}`

  return (
    <div
      title={
        `${label ? label + ' · ' : ''}` +
        `Prompt: ${total_prompt_tokens.toLocaleString()} tokens · ` +
        `Completion: ${total_completion_tokens.toLocaleString()} tokens · ` +
        `Total: ${total_tokens.toLocaleString()} tokens`
      }
      className='inline-flex items-center gap-1.5 rounded-md border border-gray-100
                 bg-gray-50 px-2 py-1 text-[11px] text-gray-400 select-none'
    >
      {label && (
        <span className='text-gray-300 font-medium uppercase tracking-wide text-[9px]'>
          {label}
        </span>
      )}
      <span className='font-mono'>{fmtTokens(total_tokens)} tok</span>
      <span className='text-gray-200'>·</span>
      <span className='font-mono text-gray-500'>{fmtCost(total_cost_usd)}</span>
    </div>
  )
}