import { ChevronDown, Network } from 'lucide-react'
import { useState } from 'react'
import ReactMarkdown from 'react-markdown'

import type { GraphRagModeResult } from '@/types/admin'

type GraphRagCompareCardProps = {
  result: GraphRagModeResult
}

export function GraphRagCompareCard({ result }: GraphRagCompareCardProps) {
  const [showGraph, setShowGraph] = useState(false)

  return (
    <article className="glass-panel flex h-full flex-col rounded-2xl p-5">
      <div className="mb-4 border-b border-white/10 pb-4">
        <h3 className="text-base font-semibold text-white">{result.label}</h3>
        <p className="mt-1 text-xs leading-relaxed text-slate-500">{result.description}</p>
        <div className="mt-3 flex flex-wrap gap-2 text-xs">
          <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-slate-300">
            {result.elapsed_ms} ms
          </span>
          <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-slate-300">
            {result.retrieval_mode}
          </span>
          {result.graph_context_count > 0 ? (
            <span className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2.5 py-1 text-emerald-200">
              {result.graph_context_count} graph blocks
            </span>
          ) : (
            <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-slate-400">
              no graph context
            </span>
          )}
        </div>
      </div>

      <div className="mb-4 rounded-xl border border-white/10 bg-black/25 p-4">
        <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">LLM answer</p>
        <div className="chat-prose prose prose-invert prose-sm max-w-none text-slate-200">
          <ReactMarkdown>{result.answer}</ReactMarkdown>
        </div>
        <p className="mt-3 text-xs text-slate-500">
          Model: {result.model} · {result.answer.length.toLocaleString()} characters
        </p>
      </div>

      {result.graph_context_count > 0 ? (
        <div>
          <button
            type="button"
            onClick={() => setShowGraph((current) => !current)}
            className="ui-button flex w-full items-center justify-between gap-2 rounded-xl border border-emerald-400/20 bg-emerald-500/5 px-3 py-2.5 text-left text-sm text-emerald-100 hover:bg-emerald-500/10"
          >
            <span className="inline-flex items-center gap-2">
              <Network className="h-4 w-4 text-emerald-300" />
              Graph context injected ({result.graph_context_count})
            </span>
            <ChevronDown
              className={`h-4 w-4 shrink-0 transition-transform ${showGraph ? 'rotate-180' : ''}`}
            />
          </button>
          {showGraph ? (
            <ul className="mt-2 space-y-2">
              {result.graph_context.map((block, index) => (
                <li
                  key={index}
                  className="rounded-lg border border-emerald-400/15 bg-emerald-500/5 px-3 py-2 font-mono text-xs leading-relaxed text-emerald-100/90"
                >
                  {block.replace(/^\[Graph context\]\n/, '')}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </article>
  )
}
