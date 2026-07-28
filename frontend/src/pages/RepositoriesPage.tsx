import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { BarChart3 } from 'lucide-react'

import {
  deleteRepository,
  fetchRepositories,
  reindexRepository,
  submitRepository,
} from '@/api/repositories'
import { ParseSummaryModal } from '@/components/ParseSummaryModal'
import type { Repository } from '@/types/repository'

function RepositorySkeletonList() {
  return (
    <div className="space-y-3">
      {[0, 1].map((item) => (
        <div
          key={item}
          className="skeleton rounded-lg border border-white/10 bg-slate-950/40 p-4"
          style={{ animationDelay: `${item * 0.12}s` }}
        >
          <div className="mb-3 h-4 w-40 rounded bg-white/10" />
          <div className="mb-2 h-3 w-full rounded bg-white/10" />
          <div className="h-3 w-2/3 rounded bg-white/10" />
        </div>
      ))}
    </div>
  )
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

export function RepositoriesPage() {
  const queryClient = useQueryClient()
  const [repositoryUrl, setRepositoryUrl] = useState('')
  const [actionError, setActionError] = useState<string | null>(null)
  const [pendingActionId, setPendingActionId] = useState<number | null>(null)
  const [summaryRepository, setSummaryRepository] = useState<Repository | null>(null)

  const {
    data: repositoriesData,
    isLoading: repositoriesLoading,
    isError: repositoriesError,
  } = useQuery({
    queryKey: ['repositories'],
    queryFn: fetchRepositories,
  })

  const repositoryMutation = useMutation({
    mutationFn: submitRepository,
    onSuccess: async (repository) => {
      await queryClient.invalidateQueries({ queryKey: ['repositories'] })
      await queryClient.invalidateQueries({ queryKey: ['parse-summary', repository.id] })
      setRepositoryUrl('')
      setActionError(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteRepository,
    onMutate: (repositoryId) => {
      setPendingActionId(repositoryId)
      setActionError(null)
    },
    onSuccess: async (_data, repositoryId) => {
      await queryClient.invalidateQueries({ queryKey: ['repositories'] })
      queryClient.removeQueries({ queryKey: ['parse-summary', repositoryId] })
      if (summaryRepository?.id === repositoryId) {
        setSummaryRepository(null)
      }
    },
    onError: (error: Error) => {
      setActionError(error.message)
    },
    onSettled: () => {
      setPendingActionId(null)
    },
  })

  const reindexMutation = useMutation({
    mutationFn: reindexRepository,
    onMutate: (repositoryId) => {
      setPendingActionId(repositoryId)
      setActionError(null)
    },
    onSuccess: async (repository) => {
      await queryClient.invalidateQueries({ queryKey: ['repositories'] })
      await queryClient.invalidateQueries({ queryKey: ['parse-summary', repository.id] })
    },
    onError: (error: Error) => {
      setActionError(error.message)
    },
    onSettled: () => {
      setPendingActionId(null)
    },
  })

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setActionError(null)
    repositoryMutation.mutate(repositoryUrl)
  }

  return (
    <>
      <main className="mx-auto max-w-5xl px-6 py-12">
        <section className="animate-fade-up mb-8">
          <p className="mb-2 text-sm font-medium uppercase tracking-wider text-slate-400">
            Repository management
          </p>
          <h2 className="text-3xl font-bold tracking-tight text-white">Repositories</h2>
          <p className="animate-fade-up animate-delay-1 mt-2 max-w-2xl text-slate-400">
            Submit a public GitHub URL. The backend saves it in Postgres, clones it, and parses
            supported source files. Use re-index to re-clone and re-parse, or delete to remove the
            DB row and local clone.
          </p>
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="ui-card animate-fade-up animate-delay-2 rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm">
            <h3 className="mb-2 text-lg font-semibold text-white">Submit a GitHub Repository</h3>
            <p className="mb-4 text-sm text-slate-400">
              Only public GitHub repositories are supported for now.
            </p>

            <form className="space-y-4" onSubmit={handleSubmit}>
              <div>
                <label
                  htmlFor="repository-url"
                  className="mb-2 block text-sm font-medium text-slate-200"
                >
                  Public GitHub URL
                </label>
                <input
                  id="repository-url"
                  type="url"
                  value={repositoryUrl}
                  onChange={(event) => setRepositoryUrl(event.target.value)}
                  placeholder="https://github.com/owner/repository"
                  className="ui-button w-full rounded-lg border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-brand-400 focus:shadow-[0_0_0_3px_rgba(99,102,241,0.18)]"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={repositoryMutation.isPending}
                className="ui-button rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-brand-600/20 hover:bg-brand-500 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {repositoryMutation.isPending ? 'Cloning repository...' : 'Submit repository'}
              </button>
            </form>

            {repositoryMutation.isError ? (
              <p className="animate-fade-up mt-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                {repositoryMutation.error.message}
              </p>
            ) : null}

            {repositoryMutation.isSuccess ? (
              <p className="animate-fade-up mt-4 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
                Cloned <span className="font-semibold">{repositoryMutation.data.full_name}</span>{' '}
                into <span className="font-mono">{repositoryMutation.data.clone_path}</span>.
              </p>
            ) : null}
          </div>

          <div className="ui-card animate-fade-up animate-delay-3 rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm">
            <h3 className="mb-4 text-lg font-semibold text-white">Submitted Repositories</h3>

            {actionError ? (
              <p className="animate-fade-up mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                {actionError}
              </p>
            ) : null}

            {repositoriesLoading ? (
              <RepositorySkeletonList />
            ) : repositoriesError ? (
              <p className="text-sm text-red-300">Could not load repositories from the API.</p>
            ) : repositoriesData && repositoriesData.repositories.length > 0 ? (
              <div className="space-y-3">
                {repositoriesData.repositories.map((repository, index) => {
                  const isBusy =
                    pendingActionId === repository.id &&
                    (deleteMutation.isPending || reindexMutation.isPending)

                  return (
                    <div
                      key={repository.id}
                      className="ui-card animate-fade-up rounded-lg border border-white/10 bg-slate-950/40 p-4"
                      style={{ animationDelay: `${0.08 * index}s` }}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-medium text-white">{repository.full_name}</p>
                          <a
                            href={repository.url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-sm text-brand-200 transition hover:text-brand-100"
                          >
                            {repository.url}
                          </a>
                        </div>
                        <span
                          className={`rounded-full px-2.5 py-1 text-xs font-medium ${statusClass(repository.status)}`}
                        >
                          {repository.status}
                        </span>
                      </div>
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
                          onClick={() => setSummaryRepository(repository)}
                          className="ui-button inline-flex items-center gap-1.5 rounded-md border border-brand-400/30 bg-brand-500/10 px-3 py-1.5 text-xs font-medium text-brand-100 hover:bg-brand-500/20 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          <BarChart3 className="h-3.5 w-3.5" />
                          View parse summary
                        </button>
                        <button
                          type="button"
                          disabled={isBusy}
                          onClick={() => reindexMutation.mutate(repository.id)}
                          className="ui-button rounded-md border border-white/10 px-3 py-1.5 text-xs font-medium text-slate-100 hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          {isBusy && reindexMutation.isPending ? 'Re-indexing...' : 'Re-index'}
                        </button>
                        <button
                          type="button"
                          disabled={isBusy}
                          onClick={() => {
                            const confirmed = window.confirm(
                              `Are you sure you want to delete ${repository.full_name}?`,
                            )
                            if (confirmed) {
                              deleteMutation.mutate(repository.id)
                            }
                          }}
                          className="ui-button rounded-md border border-red-500/30 px-3 py-1.5 text-xs font-medium text-red-200 hover:bg-red-500/10 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          {isBusy && deleteMutation.isPending ? 'Deleting...' : 'Delete'}
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <p className="animate-fade-up text-sm text-slate-400">
                No repositories submitted yet. Start with a public GitHub URL.
              </p>
            )}
          </div>
        </section>
      </main>

      {summaryRepository ? (
        <ParseSummaryModal
          repository={summaryRepository}
          open={Boolean(summaryRepository)}
          onClose={() => setSummaryRepository(null)}
        />
      ) : null}
    </>
  )
}
