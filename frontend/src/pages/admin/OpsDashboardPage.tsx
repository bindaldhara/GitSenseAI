import { useQuery } from '@tanstack/react-query'
import { AlertCircle, CheckCircle2, Loader2, Server } from 'lucide-react'

import { fetchOpsDashboard } from '@/api/admin'
import { PageHeader } from '@/components/PageHeader'

function StatusBadge({ status }: { status: string }) {
  const healthy = status === 'healthy'
  return (
    <span
      className={[
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium',
        healthy
          ? 'border border-emerald-400/20 bg-emerald-400/10 text-emerald-200'
          : 'border border-red-400/20 bg-red-400/10 text-red-200',
      ].join(' ')}
    >
      {healthy ? <CheckCircle2 className="h-3.5 w-3.5" /> : <AlertCircle className="h-3.5 w-3.5" />}
      {status}
    </span>
  )
}

function StatCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <div className="glass-panel rounded-2xl p-5">
      <p className="text-xs uppercase tracking-wider text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
      {hint ? <p className="mt-1 text-xs text-slate-500">{hint}</p> : null}
    </div>
  )
}

export function OpsDashboardPage() {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['admin', 'ops'],
    queryFn: fetchOpsDashboard,
    refetchInterval: 30_000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-slate-400">
        <Loader2 className="h-5 w-5 animate-spin" />
        Loading platform status…
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="glass-panel rounded-2xl p-6 text-sm text-red-300">
        {error instanceof Error ? error.message : 'Failed to load ops dashboard.'}
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        eyebrow="Ops"
        title="Platform dashboard"
        description="Service health, repository readiness, and runtime configuration. Internal view for operations and interview demos."
        className="mb-6"
      />

      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Server className="h-4 w-4" />
          Live platform snapshot
        </div>
        <button
          type="button"
          onClick={() => refetch()}
          disabled={isFetching}
          className="ui-button text-sm text-brand-200 hover:text-brand-100"
        >
          {isFetching ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      <section className="mb-8">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-400">Services</h3>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {data.services.map((service) => (
            <div key={service.name} className="glass-panel rounded-2xl p-4">
              <div className="flex items-center justify-between gap-2">
                <p className="font-medium capitalize text-white">{service.name}</p>
                <StatusBadge status={service.status} />
              </div>
              {service.detail ? (
                <p className="mt-2 text-xs leading-relaxed text-slate-500">{service.detail}</p>
              ) : null}
            </div>
          ))}
        </div>
      </section>

      <section className="mb-8">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-400">Overview</h3>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Repositories" value={data.totals.repository_count} hint="Added to GitSense" />
          <StatCard
            label="Cloned"
            value={data.totals.cloned_repository_count}
            hint="Downloaded and parsed on disk"
          />
          <StatCard
            label="Chat-ready"
            value={data.totals.chat_ready_repository_count}
            hint="Embeddings built — can use Chat"
          />
          <StatCard
            label="Hybrid-ready"
            value={data.totals.hybrid_ready_repository_count}
            hint="Full retrieval pipeline (re-index if missing)"
          />
        </div>
      </section>

      <section className="mb-8">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-400">Runtime config</h3>
        <div className="glass-panel overflow-hidden rounded-2xl">
          <dl className="divide-y divide-white/10 text-sm">
            {[
              ['App version', data.config.app_version],
              ['LLM provider', data.config.llm_provider],
              ['Ollama model', data.config.ollama_model],
              ['OpenAI model', data.config.openai_model],
              ['Embedding model', `${data.config.embedding_model} (${data.config.embedding_dimension}d)`],
              ['Rerank model', data.config.rerank_model],
              ['Hybrid search', data.config.hybrid_search_enabled ? 'enabled' : 'disabled'],
              ['Cross-encoder rerank', data.config.rerank_enabled ? 'enabled' : 'disabled'],
            ].map(([label, value]) => (
              <div key={label} className="grid gap-1 px-4 py-3 sm:grid-cols-[200px_1fr]">
                <dt className="text-slate-500">{label}</dt>
                <dd className="font-medium text-slate-200">{value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      <section>
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-400">Repositories</h3>
        <div className="glass-panel overflow-hidden rounded-2xl">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-white/10 text-xs uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-medium">Repository</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Chat</th>
                  <th className="px-4 py-3 font-medium">Hybrid</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {data.repositories.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-4 py-6 text-slate-500">
                      No repositories yet.
                    </td>
                  </tr>
                ) : (
                  data.repositories.map((repo) => (
                    <tr key={repo.repository_id} className="text-slate-300">
                      <td className="px-4 py-3 font-medium text-white">{repo.full_name}</td>
                      <td className="px-4 py-3 capitalize">{repo.status}</td>
                      <td className="px-4 py-3">
                        {repo.chat_ready ? (
                          <span className="text-emerald-300">ready</span>
                        ) : (
                          <span className="text-amber-300">embed first</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {repo.hybrid_ready ? (
                          <span className="text-emerald-300">ready</span>
                        ) : (
                          <span className="text-amber-300">re-index</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  )
}
