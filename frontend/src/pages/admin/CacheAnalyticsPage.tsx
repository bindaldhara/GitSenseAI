import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Database, Loader2, Trash2, Zap } from 'lucide-react'

import { clearSemanticCache, fetchCacheAnalytics } from '@/api/admin'
import { PageHeader } from '@/components/PageHeader'

function StatCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <div className="glass-panel rounded-2xl p-5">
      <p className="text-xs uppercase tracking-wider text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
      {hint ? <p className="mt-1 text-xs text-slate-500">{hint}</p> : null}
    </div>
  )
}

function eventLabel(type: string) {
  if (type === 'hit') return 'Cache hit'
  if (type === 'miss') return 'Cache miss'
  if (type === 'store') return 'Stored'
  return type
}

function eventColor(type: string) {
  if (type === 'hit') return 'text-emerald-300 bg-emerald-400/10 border-emerald-400/20'
  if (type === 'miss') return 'text-amber-200 bg-amber-400/10 border-amber-400/20'
  return 'text-sky-200 bg-sky-400/10 border-sky-400/20'
}

export function CacheAnalyticsPage() {
  const queryClient = useQueryClient()
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['admin', 'cache'],
    queryFn: fetchCacheAnalytics,
    refetchInterval: 15_000,
  })

  const clearMutation = useMutation({
    mutationFn: clearSemanticCache,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'cache'] })
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-slate-400">
        <Loader2 className="h-5 w-5 animate-spin" />
        Loading cache analytics…
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="glass-panel rounded-2xl p-6 text-sm text-red-300">
        {error instanceof Error ? error.message : 'Failed to load cache analytics.'}
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        eyebrow="Cache"
        title="Semantic cache analytics"
        description="Track how often similar questions reuse prior answers instead of running full retrieval + LLM generation."
        className="mb-6"
      />

      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Database className="h-4 w-4" />
          Redis-backed semantic cache
          <span
            className={[
              'rounded-full border px-2 py-0.5 text-xs',
              data.enabled
                ? 'border-emerald-400/20 bg-emerald-400/10 text-emerald-200'
                : 'border-slate-500/30 bg-slate-500/10 text-slate-300',
            ].join(' ')}
          >
            {data.enabled ? 'enabled' : 'disabled'}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => refetch()}
            disabled={isFetching}
            className="ui-button text-sm text-brand-200 hover:text-brand-100"
          >
            {isFetching ? 'Refreshing…' : 'Refresh'}
          </button>
          <button
            type="button"
            onClick={() => clearMutation.mutate()}
            disabled={clearMutation.isPending}
            className="ui-button inline-flex items-center gap-1.5 rounded-lg border border-red-400/30 px-3 py-1.5 text-sm text-red-200 hover:bg-red-400/10 disabled:opacity-60"
          >
            {clearMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Trash2 className="h-4 w-4" />
            )}
            Clear cache
          </button>
        </div>
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Hit rate" value={`${data.hit_rate_percent}%`} hint={`${data.hits} hits / ${data.lookups} lookups`} />
        <StatCard label="Cache hits" value={data.hits} hint="Similar question matched" />
        <StatCard label="Cache misses" value={data.misses} hint="Full RAG pipeline ran" />
        <StatCard label="Cached entries" value={data.entries} hint={`Max ${data.max_entries_per_repo} per repo`} />
      </div>

      <div className="mb-6 glass-panel rounded-2xl p-5">
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-slate-400">
          <Zap className="h-4 w-4" />
          Configuration
        </h3>
        <dl className="grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-slate-500">Similarity threshold</dt>
            <dd className="font-medium text-white">{data.similarity_threshold}</dd>
          </div>
          <div>
            <dt className="text-slate-500">TTL</dt>
            <dd className="font-medium text-white">{Math.round(data.ttl_seconds / 3600)} hours</dd>
          </div>
          <div>
            <dt className="text-slate-500">Stores</dt>
            <dd className="font-medium text-white">{data.stores}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Scope</dt>
            <dd className="font-medium text-white">Per repository, per question</dd>
          </div>
        </dl>
      </div>

      <div className="glass-panel rounded-2xl p-5">
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">Recent events</h3>
        {data.recent_events.length === 0 ? (
          <p className="text-sm text-slate-500">
            No cache activity yet. Ask a question in chat, then ask a similar one to see a hit.
          </p>
        ) : (
          <ul className="space-y-3">
            {data.recent_events.map((event, index) => (
              <li
                key={`${event.timestamp}-${index}`}
                className="rounded-xl border border-white/10 bg-slate-950/50 px-4 py-3"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={[
                      'rounded-full border px-2 py-0.5 text-xs font-medium',
                      eventColor(event.type),
                    ].join(' ')}
                  >
                    {eventLabel(event.type)}
                  </span>
                  <span className="text-xs text-slate-500">repo #{event.repository_id}</span>
                  {event.similarity != null ? (
                    <span
                      className={
                        event.type === 'miss'
                          ? 'text-xs text-amber-300'
                          : 'text-xs text-emerald-300'
                      }
                    >
                      {event.type === 'miss' ? 'best match ' : ''}
                      {(event.similarity * 100).toFixed(1)}% similar
                    </span>
                  ) : null}
                  <span className="text-xs text-slate-600">{new Date(event.timestamp).toLocaleString()}</span>
                </div>
                <p className="mt-2 text-sm text-slate-300">{event.question}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
