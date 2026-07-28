import { useQuery } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function fetchHealth() {
  const response = await fetch(`${API_BASE}/api/v1/health`)
  if (!response.ok) {
    throw new Error('Backend unreachable')
  }
  return response.json() as Promise<{ status: string }>
}

const introMarkdown = `
**GitSense AI** is an Agentic Software Intelligence Platform.

- Understand any GitHub repository
- Semantic code search & architecture insights
- Multi-Agent RAG with Graph RAG
- Real-time indexing & MCP-compatible tools
`

function App() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    retry: 3,
  })

  return (
    <div className="min-h-screen">
      <header className="border-b border-white/10 bg-black/20 backdrop-blur-sm">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-600 text-lg font-bold text-white">
              G
            </div>
            <div>
              <h1 className="text-xl font-semibold text-white">GitSense AI</h1>
              <p className="text-xs text-slate-400">Agentic Software Intelligence</p>
            </div>
          </div>
          <span className="rounded-full bg-brand-600/20 px-3 py-1 text-xs font-medium text-brand-100">
            Week 1 · Day 1 MVP
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-12">
        <section className="mb-10 text-center">
          <h2 className="mb-4 text-4xl font-bold tracking-tight text-white sm:text-5xl">
            Understand codebases with{' '}
            <span className="bg-linear-to-r from-brand-400 to-violet-400 bg-clip-text text-transparent">
              natural language
            </span>
          </h2>
          <p className="mx-auto max-w-2xl text-lg text-slate-400">
            Index, search, and reason over large-scale repositories using Multi-Agent RAG,
            Graph RAG, and intelligent code discovery.
          </p>
        </section>

        <div className="grid gap-6 md:grid-cols-2">
          <div className="rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm">
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-400">
              Platform Status
            </h3>
            <div className="flex items-center gap-3">
              <span
                className={`h-3 w-3 rounded-full ${
                  isLoading
                    ? 'animate-pulse bg-yellow-400'
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

          <div className="rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm">
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-400">
              Tech Stack
            </h3>
            <div className="flex flex-wrap gap-2">
              {['React', 'FastAPI', 'Qdrant', 'LangGraph', 'Redis'].map((tech) => (
                <span
                  key={tech}
                  className="rounded-md bg-brand-600/20 px-2.5 py-1 text-sm text-brand-100"
                >
                  {tech}
                </span>
              ))}
            </div>
          </div>
        </div>

        <section className="mt-8 rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm">
          <h3 className="mb-4 text-lg font-semibold text-white">About GitSense AI</h3>
          <div className="prose prose-invert prose-sm max-w-none text-slate-300">
            <ReactMarkdown>{introMarkdown}</ReactMarkdown>
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
