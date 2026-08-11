import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Loader2, Network, Play } from 'lucide-react'

import { compareGraphRagModes, fetchOpsDashboard } from '@/api/admin'
import { GraphRagCompareCard } from '@/components/admin/GraphRagCompareCard'
import { formatRepositorySelectLabel } from '@/lib/repoOwner'

const EXAMPLE_QUESTIONS = [
  'What files import react?',
  'What modules does the chat page depend on?',
  'How is the API layer connected to repository services?',
  'Which components define the main routing structure?',
]

const DEFAULT_TOP_K = 5

export function GraphRagCompareSection() {
  const [selectedRepositoryId, setSelectedRepositoryId] = useState<number | null>(null)
  const [question, setQuestion] = useState('')

  const { data: opsData, isLoading: repositoriesLoading } = useQuery({
    queryKey: ['admin', 'ops'],
    queryFn: fetchOpsDashboard,
  })

  const graphReadyRepositories = useMemo(
    () =>
      opsData?.repositories.filter(
        (repo) => repo.status === 'cloned' && repo.graph_ready,
      ) ?? [],
    [opsData],
  )

  useEffect(() => {
    if (graphReadyRepositories.length === 0) {
      setSelectedRepositoryId(null)
      return
    }

    const stillValid = graphReadyRepositories.some(
      (repo) => repo.repository_id === selectedRepositoryId,
    )
    if (!stillValid) {
      setSelectedRepositoryId(graphReadyRepositories[0].repository_id)
    }
  }, [graphReadyRepositories, selectedRepositoryId])

  const compareMutation = useMutation({
    mutationFn: async () => {
      if (!selectedRepositoryId) {
        throw new Error('Select a repository before comparing Graph RAG.')
      }
      if (!question.trim()) {
        throw new Error('Enter a question to compare Graph RAG vs traditional RAG.')
      }

      return compareGraphRagModes(selectedRepositoryId, {
        message: question.trim(),
        top_k: DEFAULT_TOP_K,
      })
    },
  })

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    compareMutation.mutate()
  }

  return (
    <section>
      <form onSubmit={handleSubmit} className="glass-panel mb-6 space-y-5 rounded-2xl p-5">
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-300">Repository</span>
          <select
            value={selectedRepositoryId ?? ''}
            onChange={(event) => setSelectedRepositoryId(Number(event.target.value))}
            disabled={repositoriesLoading || graphReadyRepositories.length === 0}
            className="ui-input w-full"
          >
            {graphReadyRepositories.length === 0 ? (
              <option value="">No graph-ready repositories — re-index with GRAPH_RAG_ENABLED</option>
            ) : (
              graphReadyRepositories.map((repo) => (
                <option key={repo.repository_id} value={repo.repository_id}>
                  {formatRepositorySelectLabel(repo)}
                </option>
              ))
            )}
          </select>
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-300">
            Architecture / dependency question
          </span>
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={3}
            placeholder="e.g. What files import express?"
            className="ui-input w-full resize-y"
          />
        </label>

        <div className="flex flex-wrap gap-2">
          {EXAMPLE_QUESTIONS.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => setQuestion(example)}
              className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300 transition hover:border-violet-400/30 hover:text-white"
            >
              {example}
            </button>
          ))}
        </div>

        <button
          type="submit"
          disabled={compareMutation.isPending || !selectedRepositoryId || !question.trim()}
          className="ui-button-primary inline-flex items-center gap-2"
        >
          {compareMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          Compare answers
        </button>

        {compareMutation.isError ? (
          <p className="text-sm text-red-300">{compareMutation.error.message}</p>
        ) : null}
      </form>

      {compareMutation.data ? (
        <div className="space-y-5">
          <div className="flex flex-wrap items-center gap-2 text-sm text-slate-400">
            <Network className="h-4 w-4 text-emerald-300" />
            <span>
              Graph: {compareMutation.data.graph_node_count.toLocaleString()} nodes ·{' '}
              {compareMutation.data.graph_edge_count.toLocaleString()} edges
            </span>
          </div>

          <div className="grid gap-5 xl:grid-cols-2">
            {compareMutation.data.results.map((result) => (
              <GraphRagCompareCard key={result.mode_id} result={result} />
            ))}
          </div>
        </div>
      ) : (
        <div className="glass-panel rounded-2xl p-6 text-sm text-slate-500">
          Pick a graph-ready repository (re-index if needed), ask a dependency or architecture
          question, then compare how Graph RAG changes the answer.
        </div>
      )}
    </section>
  )
}
