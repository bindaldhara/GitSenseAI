import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'

import { fetchHealth } from '@/api/health'

const introMarkdown = `
**GitSense AI** is an Agentic Software Intelligence Platform.

- Understand any GitHub repository
- Semantic code search & architecture insights
- Multi-Agent RAG with Graph RAG
- Real-time indexing & MCP-compatible tools
`

export function HomePage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    retry: 3,
  })

  return (
    <main className="mx-auto max-w-5xl px-6 py-12">
      <section className="animate-fade-up mb-10 text-center">
        <h2 className="mb-4 text-4xl font-bold tracking-tight text-white sm:text-5xl">
          Understand codebases with{' '}
          <span className="bg-linear-to-r from-brand-400 to-violet-400 bg-clip-text text-transparent">
            natural language
          </span>
        </h2>
        <p className="animate-fade-up animate-delay-1 mx-auto max-w-2xl text-lg text-slate-400">
          Index, search, and reason over large-scale repositories using Multi-Agent RAG,
          Graph RAG, and intelligent code discovery.
        </p>
        <div className="animate-fade-up animate-delay-2 mt-8 flex flex-wrap justify-center gap-3">
          <Link
            to="/repositories"
            className="ui-button inline-flex rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-brand-600/25 hover:bg-brand-500"
          >
            Open repository dashboard
          </Link>
          <Link
            to="/chat"
            className="ui-button inline-flex rounded-lg border border-white/10 bg-white/5 px-5 py-2.5 text-sm font-semibold text-white hover:bg-white/10"
          >
            Try repository chat
          </Link>
        </div>
      </section>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="ui-card animate-fade-up animate-delay-2 rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm">
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-400">
            Platform Status
          </h3>
          <div className="flex items-center gap-3">
            <span
              className={`h-3 w-3 rounded-full ${
                isLoading
                  ? 'status-pulse bg-yellow-400'
                  : isError
                    ? 'bg-red-500'
                    : 'bg-emerald-400'
              }`}
            />
            <span className="text-white">
              {isLoading
                ? 'Connecting to API…'
                : isError
                  ? 'Backend offline — start with docker compose up'
                  : `API ${data?.status ?? 'ready'}`}
            </span>
          </div>
        </div>

        <div className="ui-card animate-fade-up animate-delay-3 rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm">
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-400">
            Tech Stack
          </h3>
          <div className="flex flex-wrap gap-2">
            {['React', 'FastAPI', 'Qdrant', 'LangGraph', 'Redis'].map((tech, index) => (
              <span
                key={tech}
                className="animate-fade-up rounded-md bg-brand-600/20 px-2.5 py-1 text-sm text-brand-100"
                style={{ animationDelay: `${0.28 + index * 0.05}s` }}
              >
                {tech}
              </span>
            ))}
          </div>
        </div>
      </div>

      <section className="ui-card animate-fade-up animate-delay-4 mt-8 rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm">
        <h3 className="mb-4 text-lg font-semibold text-white">About GitSense AI</h3>
        <div className="prose prose-invert prose-sm max-w-none text-slate-300">
          <ReactMarkdown>{introMarkdown}</ReactMarkdown>
        </div>
      </section>
    </main>
  )
}
