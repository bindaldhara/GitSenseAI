import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { useQuery } from '@tanstack/react-query'
import { BarChart3, FileCode2, SkipForward, Sparkles, X } from 'lucide-react'

import { fetchParseSummary } from '@/api/repositories'
import type { Repository } from '@/types/repository'

type ParseSummaryModalProps = {
  repository: Repository
  open: boolean
  onClose: () => void
}

const CLOSE_ANIMATION_MS = 220

function formatReason(reason: string) {
  return reason.replaceAll('_', ' ')
}

function CountBadge({
  label,
  value,
  delay,
}: {
  label: string
  value: number
  delay: string
}) {
  return (
    <div
      className="animate-fade-up ui-card rounded-xl border border-white/10 bg-slate-950/60 p-4"
      style={{ animationDelay: delay }}
    >
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-white">{value.toLocaleString()}</p>
    </div>
  )
}

function CountList({
  title,
  counts,
  emptyLabel,
  delay,
}: {
  title: string
  counts: Record<string, number>
  emptyLabel: string
  delay: string
}) {
  const entries = Object.entries(counts)

  return (
    <div
      className="animate-fade-up ui-card rounded-xl border border-white/10 bg-slate-950/40 p-4"
      style={{ animationDelay: delay }}
    >
      <p className="text-sm font-medium text-white">{title}</p>
      {entries.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {entries.map(([key, value], index) => (
            <span
              key={key}
              className="animate-fade-up rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-200"
              style={{ animationDelay: `${0.08 * index}s` }}
            >
              {formatReason(key)} · {value}
            </span>
          ))}
        </div>
      ) : (
        <p className="mt-3 text-sm text-slate-500">{emptyLabel}</p>
      )}
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-3">
        {[0, 1, 2].map((item) => (
          <div key={item} className="skeleton h-24 rounded-xl border border-white/10" />
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="skeleton h-28 rounded-xl border border-white/10" />
        <div className="skeleton h-28 rounded-xl border border-white/10" />
      </div>
      <div className="skeleton h-48 rounded-xl border border-white/10" />
    </div>
  )
}

export function ParseSummaryModal({ repository, open, onClose }: ParseSummaryModalProps) {
  const [isVisible, setIsVisible] = useState(open)
  const [isClosing, setIsClosing] = useState(false)

  const {
    data: summary,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['parse-summary', repository.id, 'modal'],
    queryFn: () => fetchParseSummary(repository.id, 100),
    enabled: open && repository.status === 'cloned',
  })

  useEffect(() => {
    if (open) {
      setIsVisible(true)
      setIsClosing(false)
    }
  }, [open])

  useEffect(() => {
    if (!isVisible) {
      return
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape' && !isClosing) {
        handleClose()
      }
    }

    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', handleKeyDown)

    return () => {
      document.body.style.overflow = ''
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [isVisible, isClosing])

  function handleClose() {
    if (isClosing) {
      return
    }
    setIsClosing(true)
    window.setTimeout(() => {
      setIsVisible(false)
      setIsClosing(false)
      onClose()
    }, CLOSE_ANIMATION_MS)
  }

  if (!isVisible || typeof document === 'undefined') {
    return null
  }

  return createPortal(
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <button
        type="button"
        aria-label="Close parse summary"
        className={`fixed inset-0 bg-slate-950/80 backdrop-blur-sm ${
          isClosing ? 'animate-fade-out' : 'animate-fade-in'
        }`}
        onClick={handleClose}
      />

      <div className="relative z-10 flex min-h-full items-start justify-center px-4 py-6 sm:items-center sm:py-8">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="parse-summary-title"
        className={`flex max-h-[min(90vh,880px)] w-full max-w-3xl flex-col overflow-hidden rounded-2xl border border-white/10 bg-slate-900 shadow-2xl shadow-black/40 ${
          isClosing ? 'animate-scale-out' : 'animate-scale-in'
        }`}
      >
        <div className="border-b border-white/10 bg-linear-to-r from-brand-600/20 via-transparent to-transparent px-6 py-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-brand-400/20 bg-brand-500/10 px-3 py-1 text-xs font-medium text-brand-100">
                <BarChart3 className="h-3.5 w-3.5" />
                Parse summary
              </div>
              <h2 id="parse-summary-title" className="text-xl font-semibold text-white">
                {repository.full_name}
              </h2>
              <p className="mt-1 text-sm text-slate-400">
                Parsed files, extracted symbols, and skipped paths from the latest clone.
              </p>
            </div>

            <button
              type="button"
              onClick={handleClose}
              className="ui-button rounded-lg border border-white/10 p-2 text-slate-300 hover:bg-white/5 hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="overflow-y-auto px-6 py-5">
          {repository.status !== 'cloned' ? (
            <p className="animate-fade-up rounded-xl border border-amber-500/20 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
              Parse summary is available after the repository reaches cloned status.
            </p>
          ) : isLoading || isFetching ? (
            <LoadingSkeleton />
          ) : isError || !summary ? (
            <div className="animate-fade-up rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3">
              <p className="text-sm text-red-200">
                {error instanceof Error ? error.message : 'Could not load parse summary.'}
              </p>
              <button
                type="button"
                onClick={() => refetch()}
                className="ui-button mt-3 rounded-md border border-red-400/30 px-3 py-1.5 text-xs font-medium text-red-100 hover:bg-red-500/10"
              >
                Retry
              </button>
            </div>
          ) : (
            <div className="space-y-5">
              <div className="grid gap-3 sm:grid-cols-3">
                <CountBadge label="Parsed files" value={summary.file_count} delay="0.04s" />
                <CountBadge label="Symbols" value={summary.symbol_count} delay="0.08s" />
                <CountBadge label="Skipped files" value={summary.skipped_count} delay="0.12s" />
              </div>

              <div className="grid gap-4 lg:grid-cols-2">
                <CountList
                  title="Languages"
                  counts={summary.by_language}
                  emptyLabel="No parsed source files yet."
                  delay="0.16s"
                />
                <CountList
                  title="Symbol kinds"
                  counts={summary.by_kind}
                  emptyLabel="No symbols extracted yet."
                  delay="0.2s"
                />
              </div>

              <CountList
                title="Skip reasons"
                counts={summary.by_skip_reason}
                emptyLabel="No skipped files recorded."
                delay="0.24s"
              />

              <div
                className="animate-fade-up ui-card rounded-xl border border-white/10 bg-slate-950/40"
                style={{ animationDelay: '0.28s' }}
              >
                <div className="flex items-center justify-between gap-3 border-b border-white/10 px-4 py-3">
                  <div className="flex items-center gap-2">
                    <SkipForward className="h-4 w-4 text-slate-400" />
                    <p className="text-sm font-medium text-white">Skipped files</p>
                  </div>
                  <span className="text-xs text-slate-500">
                    Showing {summary.skipped_returned} of {summary.skipped_count}
                  </span>
                </div>

                {summary.skipped_count > 0 ? (
                  <ul className="max-h-72 divide-y divide-white/5 overflow-y-auto">
                    {summary.skipped_files.map((item, index) => (
                      <li
                        key={`${item.path}:${item.reason}`}
                        className="animate-fade-up flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
                        style={{ animationDelay: `${0.04 * Math.min(index, 8)}s` }}
                      >
                        <div className="flex min-w-0 items-start gap-2">
                          <FileCode2 className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />
                          <span className="break-all font-mono text-sm text-slate-200">
                            {item.path}
                          </span>
                        </div>
                        <span className="shrink-0 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs capitalize text-slate-300">
                          {formatReason(item.reason)}
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="flex items-center gap-2 px-4 py-6 text-sm text-slate-500">
                    <Sparkles className="h-4 w-4" />
                    Every scanned file was parsed successfully.
                  </div>
                )}

                {summary.skipped_count > summary.skipped_returned ? (
                  <p className="border-t border-white/10 px-4 py-3 text-xs text-slate-500">
                    …and {summary.skipped_count - summary.skipped_returned} more skipped files not
                    shown in this view.
                  </p>
                ) : null}
              </div>
            </div>
          )}
        </div>
      </div>
      </div>
    </div>,
    document.body,
  )
}
