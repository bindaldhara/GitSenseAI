import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { FlaskConical, Loader2, Play } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'

import { compareRetrievalModes } from '@/api/retrievalLab'
import { fetchRepositories } from '@/api/repositories'
import { PageHeader } from '@/components/PageHeader'
import { RetrievalResultCard } from '@/components/RetrievalResultCard'

const EXAMPLE_QUESTIONS = [
  'Summarize the project architecture.',
  'Where is the main React component defined?',
  'What API routes are exposed?',
  'How is authentication implemented?',
]

export function RetrievalLabPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [selectedRepositoryId, setSelectedRepositoryId] = useState<number | null>(null)
  const [question, setQuestion] = useState('')
  const [topK, setTopK] = useState(5)

  const { data: repositoriesData, isLoading: repositoriesLoading } = useQuery({
    queryKey: ['repositories'],
    queryFn: fetchRepositories,
  })

  const readyRepositories = useMemo(
    () => repositoriesData?.repositories.filter((repo) => repo.status === 'cloned') ?? [],
    [repositoriesData],
  )

  useEffect(() => {
    if (readyRepositories.length === 0) {
      return
    }

    const repoParam = searchParams.get('repository')
    const questionParam = searchParams.get('question')

    if (repoParam) {
      const parsedId = Number(repoParam)
      if (!Number.isNaN(parsedId) && readyRepositories.some((repo) => repo.id === parsedId)) {
        setSelectedRepositoryId(parsedId)
      }
    } else {
      setSelectedRepositoryId((current) => current ?? readyRepositories[0].id)
    }

    if (questionParam) {
      setQuestion(questionParam)
    }
  }, [readyRepositories, searchParams])

  const compareMutation = useMutation({
    mutationFn: async () => {
      if (!selectedRepositoryId) {
        throw new Error('Select a repository before comparing retrieval modes.')
      }
      if (!question.trim()) {
        throw new Error('Enter a question to compare retrieval modes.')
      }

      return compareRetrievalModes(selectedRepositoryId, {
        message: question.trim(),
        top_k: topK,
      })
    },
  })

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selectedRepositoryId) {
      return
    }

    const nextParams = new URLSearchParams()
    nextParams.set('repository', String(selectedRepositoryId))
    if (question.trim()) {
      nextParams.set('question', question.trim())
    }
    setSearchParams(nextParams, { replace: true })
    compareMutation.mutate()
  }

  return (
    <div>
      <PageHeader
        eyebrow="Retrieval Lab"
        title="Vector vs hybrid + rerank"
        description="Compare vector-only search against the full production pipeline: BM25 + vector fusion, then cross-encoder reranking. No LLM call — sources and latency only."
        className="mb-6"
      />

      <form onSubmit={handleSubmit} className="glass-panel mb-8 space-y-6 rounded-2xl p-6">
        <div className="grid gap-5 md:grid-cols-2">
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-300">Repository</span>
            <select
              value={selectedRepositoryId ?? ''}
              onChange={(event) => setSelectedRepositoryId(Number(event.target.value))}
              disabled={repositoriesLoading || readyRepositories.length === 0}
              className="ui-input w-full"
            >
              {readyRepositories.length === 0 ? (
                <option value="">No indexed repositories</option>
              ) : (
                readyRepositories.map((repo) => (
                  <option key={repo.id} value={repo.id}>
                    {repo.full_name}
                  </option>
                ))
              )}
            </select>
          </label>

          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-300">Top-k chunks</span>
            <select
              value={topK}
              onChange={(event) => setTopK(Number(event.target.value))}
              className="ui-input w-full"
            >
              {[3, 5, 8, 10].map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-300">Question</span>
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={3}
            placeholder="Ask the same question you used in chat…"
            className="ui-input w-full resize-y"
          />
        </label>

        <div className="flex flex-wrap gap-2">
          {EXAMPLE_QUESTIONS.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => setQuestion(example)}
              className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300 transition hover:border-brand-400/30 hover:text-white"
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
          Run comparison
        </button>

        {compareMutation.isError ? (
          <p className="text-sm text-red-300">{compareMutation.error.message}</p>
        ) : null}
      </form>

      {compareMutation.data ? (
        <section className="space-y-5">
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <FlaskConical className="h-4 w-4" />
            <span>
              Vector only vs hybrid + rerank for &ldquo;{compareMutation.data.question}&rdquo;
            </span>
          </div>

          <div className="grid gap-5 xl:grid-cols-2">
            {compareMutation.data.results.map((result) => (
              <RetrievalResultCard key={result.mode_id} result={result} />
            ))}
          </div>
        </section>
      ) : (
        <div className="glass-panel rounded-2xl p-8 text-center text-sm text-slate-500">
          Enter a question and run a comparison to see vector-only vs hybrid + rerank side by side.
        </div>
      )}
    </div>
  )
}
