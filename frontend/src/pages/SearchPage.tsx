import { useState } from 'react'
import type { FormEvent } from 'react'
import { Loader2, Search } from 'lucide-react'

import { searchAcrossRepositories } from '@/api/search'
import { PageHeader } from '@/components/PageHeader'
import type { MultiRepoSearchResponse } from '@/types/search'

export function SearchPage() {
  const [query, setQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [results, setResults] = useState<MultiRepoSearchResponse | null>(null)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!query.trim()) return
    setError(null)
    setIsSearching(true)
    try {
      const data = await searchAcrossRepositories(query.trim())
      setResults(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
      setResults(null)
    } finally {
      setIsSearching(false)
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <PageHeader
        eyebrow="Multi-repo"
        title="Multi-repository search"
        description="Run hybrid retrieval across all repositories you can access."
      />

      <form onSubmit={handleSubmit} className="mb-8 flex gap-3">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. authentication, Redis, API routes"
          className="flex-1 rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-white"
        />
        <button
          type="submit"
          disabled={isSearching}
          className="ui-button inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 font-medium text-white hover:bg-indigo-500"
        >
          {isSearching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
          Search
        </button>
      </form>

      {error ? <p className="mb-4 text-sm text-red-300">{error}</p> : null}

      {results ? (
        <div className="space-y-6">
          <p className="text-sm text-slate-400">
            Found matches in {results.repository_count} repository
            {results.repository_count === 1 ? '' : 's'} for “{results.query}”
          </p>
          {results.results.map((repoResult) => (
            <div
              key={repoResult.repository_id}
              className="ui-card rounded-2xl border border-white/10 bg-slate-950/50 p-5"
            >
              <h3 className="text-lg font-semibold text-white">{repoResult.full_name}</h3>
              <p className="mt-1 text-xs text-slate-500">{repoResult.retrieval_mode} search</p>
              <ul className="mt-4 space-y-3">
                {repoResult.hits.map((hit, index) => (
                  <li
                    key={`${hit.file_path}-${hit.start_line}-${index}`}
                    className="rounded-lg border border-white/5 bg-black/20 p-3"
                  >
                    <p className="text-sm font-medium text-slate-200">
                      {hit.file_path}:{hit.start_line}-{hit.end_line}
                      <span className="ml-2 text-xs text-slate-500">
                        {(hit.score * 100).toFixed(0)}%
                      </span>
                    </p>
                    <p className="mt-1 text-xs leading-relaxed text-slate-400">{hit.excerpt}</p>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  )
}
