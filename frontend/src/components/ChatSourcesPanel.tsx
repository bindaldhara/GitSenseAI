import { useEffect, useRef, useState, type ReactNode, type RefObject } from 'react'
import { ChevronDown, FileCode2 } from 'lucide-react'

import type { RetrievedSource } from '@/types/chat'
import { formatSourceScoresForDisplay, scoreDisplayFootnote } from '@/lib/retrievalScores'

type ChatSourcesPanelProps = {
  sources: RetrievedSource[]
  question?: string
  isLoading?: boolean
  highlightPulse?: number
}

function sourceKey(source: RetrievedSource, index: number) {
  return `${source.file_path}-${source.start_line}-${index}`
}

function PanelShell({
  children,
  highlighted = false,
  panelRef,
}: {
  children: ReactNode
  highlighted?: boolean
  panelRef?: RefObject<HTMLDivElement | null>
}) {
  return (
    <div
      ref={panelRef}
      className={[
        'glass-panel rounded-2xl p-5',
        highlighted ? 'animate-highlight-bump ring-2 ring-brand-400/40' : '',
      ].join(' ')}
    >
      {children}
    </div>
  )
}

export function ChatSourcesPanel({
  sources,
  question,
  isLoading = false,
  highlightPulse = 0,
}: ChatSourcesPanelProps) {
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set())
  const [highlighted, setHighlighted] = useState(false)
  const panelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setExpandedKeys(new Set())
  }, [sources])

  useEffect(() => {
    if (!highlightPulse) {
      return
    }

    setHighlighted(true)
    panelRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })

    const timer = window.setTimeout(() => setHighlighted(false), 600)
    return () => window.clearTimeout(timer)
  }, [highlightPulse])

  function toggleSource(key: string) {
    setExpandedKeys((current) => {
      const next = new Set(current)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }

  if (isLoading) {
    return (
      <PanelShell panelRef={panelRef} highlighted={highlighted}>
        <h3 className="section-eyebrow mb-3">Sources</h3>
        <p className="text-sm text-slate-400">Retrieving new sources for your latest question…</p>
      </PanelShell>
    )
  }

  if (sources.length === 0) {
    return (
      <PanelShell panelRef={panelRef} highlighted={highlighted}>
        <h3 className="section-eyebrow mb-3">Sources</h3>
        <p className="text-sm text-slate-500">
          Retrieved code chunks will appear here after you ask a question.
        </p>
      </PanelShell>
    )
  }

  const scoreLabels = formatSourceScoresForDisplay(sources)

  return (
    <PanelShell panelRef={panelRef} highlighted={highlighted}>
      <h3 className="section-eyebrow mb-3">Sources</h3>
      <p className="mb-4 text-xs text-slate-500">
        Code chunks retrieved to ground the answer.
      </p>

      {question ? (
        <p className="mb-4 rounded-xl border border-white/10 bg-black/20 px-3 py-2.5 text-xs leading-relaxed text-slate-300">
          Sources for: <span className="font-medium text-white">&ldquo;{question}&rdquo;</span>
        </p>
      ) : null}

      <div className="space-y-2">
        {sources.map((source, index) => {
          const key = sourceKey(source, index)
          const isExpanded = expandedKeys.has(key)

          return (
            <div
              key={key}
              className="overflow-hidden rounded-xl border border-white/10 bg-slate-950/50"
            >
              <button
                type="button"
                onClick={() => toggleSource(key)}
                className="ui-button flex w-full items-center gap-2 px-3 py-2.5 text-left hover:bg-white/5"
                aria-expanded={isExpanded}
              >
                <FileCode2 className="h-4 w-4 shrink-0 text-brand-300" />
                <span className="min-w-0 flex-1 truncate font-mono text-xs text-white">
                  {source.file_path}
                </span>
                <span className="shrink-0 rounded-full bg-brand-600/20 px-2 py-0.5 text-xs font-medium text-brand-100">
                  {scoreLabels[index]?.label ?? '—'}
                </span>
                <ChevronDown
                  className={`h-4 w-4 shrink-0 text-slate-400 transition-transform ${
                    isExpanded ? 'rotate-180' : ''
                  }`}
                />
              </button>

              {isExpanded ? (
                <div className="border-t border-white/10 px-3 py-3">
                  <p className="text-xs text-slate-400">
                    lines {source.start_line}–{source.end_line}
                    {source.symbol_name ? ` · ${source.symbol_name}` : ''} · {source.language} ·{' '}
                    {source.chunk_kind}
                  </p>
                  <pre className="mt-2 max-h-48 overflow-auto rounded-lg bg-black/35 p-2 font-mono text-xs leading-relaxed text-slate-300">
                    {source.excerpt}
                  </pre>
                </div>
              ) : null}
            </div>
          )
        })}
      </div>
      <p className="mt-3 text-xs leading-relaxed text-slate-500">{scoreDisplayFootnote(sources)}</p>
    </PanelShell>
  )
}
