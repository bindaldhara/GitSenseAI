import { useEffect, useState } from 'react'
import { ChevronDown, FileCode2 } from 'lucide-react'

import type { RetrievedSource } from '@/types/chat'
import type { RetrievalModeResult } from '@/types/retrievalLab'
import { formatSourceScoresForDisplay, scoreDisplayFootnote } from '@/lib/retrievalScores'

type RetrievalResultCardProps = {
  result: RetrievalModeResult
}

function sourceRowKey(modeId: string, source: RetrievedSource, index: number) {
  return `${modeId}-${source.file_path}-${source.start_line}-${index}`
}

type SourceRowProps = {
  source: RetrievedSource
  scoreLabel: string
  isExpanded: boolean
  onToggle: () => void
}

function SourceRow({ source, scoreLabel, isExpanded, onToggle }: SourceRowProps) {
  const metadata = [
    source.language,
    source.chunk_kind,
    source.symbol_name,
    `L${source.start_line}-${source.end_line}`,
  ]
    .filter(Boolean)
    .join(' · ')

  return (
    <li className="overflow-hidden rounded-xl border border-white/10 bg-black/20">
      <button
        type="button"
        onClick={onToggle}
        className="ui-button flex w-full items-start gap-2 px-3 py-2.5 text-left hover:bg-white/5"
        aria-expanded={isExpanded}
      >
        <FileCode2 className="mt-0.5 h-4 w-4 shrink-0 text-brand-300" />
        <div className="min-w-0 flex-1">
          <p className="truncate font-mono text-xs font-medium text-brand-200" title={source.file_path}>
            {source.file_path}
          </p>
          <div className="mt-1 flex items-center justify-between gap-3">
            <p className="min-w-0 truncate text-xs text-slate-500" title={metadata}>
              {metadata}
            </p>
            <span className="shrink-0 text-xs font-medium text-slate-300">{scoreLabel}</span>
          </div>
        </div>
        <ChevronDown
          className={`mt-0.5 h-4 w-4 shrink-0 text-slate-400 transition-transform ${
            isExpanded ? 'rotate-180' : ''
          }`}
        />
      </button>

      {isExpanded ? (
        <div className="border-t border-white/10 px-3 py-3">
          <pre className="max-h-56 overflow-auto rounded-lg bg-black/35 p-3 font-mono text-xs leading-relaxed whitespace-pre-wrap text-slate-300">
            {source.excerpt}
          </pre>
        </div>
      ) : null}
    </li>
  )
}

export function RetrievalResultCard({ result }: RetrievalResultCardProps) {
  const topFile = result.sources[0]?.file_path
  const formattedScores = formatSourceScoresForDisplay(result.sources)
  const footnote = scoreDisplayFootnote(result.sources)
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set())

  useEffect(() => {
    setExpandedKeys(new Set())
  }, [result.mode_id, result.sources])

  function toggleRow(key: string) {
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

  return (
    <article className="glass-panel flex h-full flex-col rounded-2xl p-5">
      <div className="mb-4 border-b border-white/10 pb-4">
        <h3 className="text-base font-semibold text-white">{result.label}</h3>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-slate-300">
            {result.retrieval_ms} ms
          </span>
        </div>
        {topFile ? (
          <p className="mt-3 text-xs text-slate-500">
            Top hit:{' '}
            <span className="block truncate text-slate-300 sm:inline" title={topFile}>
              {topFile}
            </span>
          </p>
        ) : null}
      </div>

      {result.sources.length === 0 ? (
        <p className="text-sm text-slate-500">No chunks retrieved for this mode.</p>
      ) : (
        <>
          <ol className="space-y-2">
            {result.sources.map((source, index) => {
              const key = sourceRowKey(result.mode_id, source, index)
              return (
                <SourceRow
                  key={key}
                  source={source}
                  scoreLabel={formattedScores[index]?.label ?? '—'}
                  isExpanded={expandedKeys.has(key)}
                  onToggle={() => toggleRow(key)}
                />
              )
            })}
          </ol>
          <p className="mt-3 text-xs leading-relaxed text-slate-500">{footnote}</p>
        </>
      )}
    </article>
  )
}
