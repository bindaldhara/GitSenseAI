import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, BrainCircuit, Database, MessageSquare, Search, Sparkles } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

import { fetchHealth } from '@/api/health'

const introMarkdown = `
**GitSense AI** is an Agentic Software Intelligence Platform.

- Understand any GitHub repository
- Semantic code search & architecture insights
- Multi-Agent RAG with Graph RAG
- Real-time indexing & MCP-compatible tools
`

const features = [
  {
    icon: Database,
    title: 'Index repositories',
    description: 'Clone, parse, chunk, and embed code into Qdrant for semantic search.',
  },
  {
    icon: Search,
    title: 'Retrieve context',
    description: 'Find the most relevant code chunks for each question automatically.',
  },
  {
    icon: BrainCircuit,
    title: 'Grounded answers',
    description: 'LLM responses cite real files from your indexed codebase.',
  },
]

export function HomePage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    retry: 3,
  })

  return (
    <main className="mx-auto max-w-6xl px-6 py-12">
      <section className="animate-fade-up relative mb-14 overflow-hidden rounded-3xl border border-white/10 glass-panel px-8 py-14 text-center sm:px-12">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgb(99_102_241/0.15),transparent_55%)]" />
        <div className="relative">
          <span className="mb-6 inline-flex items-center gap-2 rounded-full border border-brand-400/20 bg-brand-500/10 px-3 py-1 text-xs font-medium text-brand-100">
            <Sparkles className="h-3.5 w-3.5" />
            RAG-powered repository intelligence
          </span>
          <h2 className="mb-4 text-4xl font-bold tracking-tight text-white sm:text-5xl">
            Understand codebases with <span className="gradient-text">natural language</span>
          </h2>
          <p className="animate-fade-up animate-delay-1 mx-auto max-w-2xl text-lg leading-relaxed text-slate-400">
            Index, search, and reason over large-scale repositories using retrieval-augmented
            generation and intelligent code discovery.
          </p>
          <div className="animate-fade-up animate-delay-2 mt-8 flex flex-wrap justify-center gap-3">
            <Link to="/repositories" className="btn-primary ui-button">
              Open repositories
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link to="/chat" className="btn-secondary ui-button">
              <MessageSquare className="h-4 w-4" />
              Try chat
            </Link>
          </div>
        </div>
      </section>

      <div className="mb-8 grid gap-4 md:grid-cols-3">
        {features.map((feature, index) => (
          <div
            key={feature.title}
            className="ui-card-interactive glass-panel animate-fade-up rounded-2xl p-5"
            style={{ animationDelay: `${0.08 * index}s` }}
          >
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-brand-500/15 text-brand-200">
              <feature.icon className="h-5 w-5" />
            </div>
            <h3 className="mb-2 font-semibold text-white">{feature.title}</h3>
            <p className="text-sm leading-relaxed text-slate-400">{feature.description}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="glass-panel ui-card-interactive animate-fade-up animate-delay-2 rounded-2xl p-6">
          <h3 className="section-eyebrow mb-4">Platform status</h3>
          <div className="flex items-center gap-3">
            <span
              className={`h-3 w-3 rounded-full ${
                isLoading
                  ? 'status-pulse bg-yellow-400'
                  : isError
                    ? 'bg-red-500'
                    : 'bg-emerald-400 shadow-[0_0_12px_rgb(52_211_153/0.6)]'
              }`}
            />
            <span className="text-white">
              {isLoading
                ? 'Connecting to API…'
                : isError
                  ? 'Backend offline — run docker compose up'
                  : `API ${data?.status ?? 'ready'}`}
            </span>
          </div>
        </div>

        <div className="glass-panel ui-card-interactive animate-fade-up animate-delay-3 rounded-2xl p-6">
          <h3 className="section-eyebrow mb-4">Tech stack</h3>
          <div className="flex flex-wrap gap-2">
            {['React', 'FastAPI', 'Qdrant', 'Ollama', 'PostgreSQL'].map((tech, index) => (
              <span
                key={tech}
                className="animate-fade-up rounded-full border border-brand-400/20 bg-brand-500/10 px-3 py-1 text-xs font-medium text-brand-100"
                style={{ animationDelay: `${0.28 + index * 0.05}s` }}
              >
                {tech}
              </span>
            ))}
          </div>
        </div>
      </div>

      <section className="glass-panel ui-card-interactive animate-fade-up animate-delay-4 mt-8 rounded-2xl p-6">
        <h3 className="mb-4 text-lg font-semibold text-white">About GitSense AI</h3>
        <div className="chat-prose prose prose-invert prose-sm max-w-none">
          <ReactMarkdown>{introMarkdown}</ReactMarkdown>
        </div>
      </section>
    </main>
  )
}
