import { useState } from 'react'
import { BarChart3, ChevronDown, MessageSquare } from 'lucide-react'
import { Link } from 'react-router-dom'

import type { Repository } from '@/types/repository'

type RepositoryCardProps = {
  repository: Repository
  isBusy: boolean
  isReindexing: boolean
  isDeleting: boolean
  onViewSummary: (repository: Repository) => void
  onReindex: (repositoryId: number) => void
  onDelete: (repository: Repository) => void
}

function statusClass(status: string) {
  if (status === 'cloned') {
    return 'bg-emerald-500/15 text-emerald-100'
  }
  if (status === 'failed') {
    return 'bg-red-500/15 text-red-100'
  }
  return 'status-pulse bg-brand-600/20 text-brand-100'
}

export function RepositoryCard({
  repository,
  isBusy,
  isReindexing,
  isDeleting,
  onViewSummary,
  onReindex,
  onDelete,
}: RepositoryCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div className="overflow-hidden rounded-lg border border-white/10 bg-slate-950/40">
      <button
        type="button"
        onClick={() => setIsExpanded((current) => !current)}
        className="ui-button flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-white/5"
        aria-expanded={isExpanded}
      >
        <div className="min-w-0 flex-1">
          <p className="truncate font-medium text-white">{repository.full_name}</p>
        </div>
        <span
          className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${statusClass(repository.status)}`}
        >
          {repository.status}
        </span>
        <ChevronDown
          className={`h-4 w-4 shrink-0 text-slate-400 transition-transform ${
            isExpanded ? 'rotate-180' : ''
          }`}
        />
      </button>

      {isExpanded ? (
        <div className="border-t border-white/10 px-4 py-3">
          <a
            href={repository.url}
            target="_blank"
            rel="noreferrer"
            className="text-sm text-brand-200 transition hover:text-brand-100"
          >
            {repository.url}
          </a>
          <p className="mt-3 text-xs text-slate-400">
            Clone path: <span className="font-mono">{repository.clone_path}</span>
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Default branch: {repository.default_branch ?? 'unknown'}
          </p>

          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              disabled={repository.status !== 'cloned' || isBusy}
              onClick={() => onViewSummary(repository)}
              className="ui-button inline-flex items-center gap-1.5 rounded-md border border-brand-400/30 bg-brand-500/10 px-3 py-1.5 text-xs font-medium text-brand-100 hover:bg-brand-500/20 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <BarChart3 className="h-3.5 w-3.5" />
              View parse summary
            </button>
            <Link
              to={`/chat?repository=${repository.id}`}
              className={`ui-button inline-flex items-center gap-1.5 rounded-md border border-emerald-400/30 bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-100 hover:bg-emerald-500/20 ${
                repository.status !== 'cloned' || isBusy ? 'pointer-events-none opacity-60' : ''
              }`}
              aria-disabled={repository.status !== 'cloned' || isBusy}
              tabIndex={repository.status !== 'cloned' || isBusy ? -1 : 0}
            >
              <MessageSquare className="h-3.5 w-3.5" />
              Chat
            </Link>
            <button
              type="button"
              disabled={isBusy}
              onClick={() => onReindex(repository.id)}
              className="ui-button rounded-md border border-white/10 px-3 py-1.5 text-xs font-medium text-slate-100 hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isBusy && isReindexing ? 'Re-indexing...' : 'Re-index'}
            </button>
            <button
              type="button"
              disabled={isBusy}
              onClick={() => onDelete(repository)}
              className="ui-button rounded-md border border-red-500/30 px-3 py-1.5 text-xs font-medium text-red-200 hover:bg-red-500/10 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isBusy && isDeleting ? 'Deleting...' : 'Delete'}
            </button>
          </div>
        </div>
      ) : null}
    </div>
  )
}
