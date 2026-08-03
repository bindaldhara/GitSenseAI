import { useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Bot, Loader2, MessageSquare, Send, Trash2, User } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { Link, useSearchParams } from 'react-router-dom'

import { sendChatMessage } from '@/api/chat'
import { fetchRepositories } from '@/api/repositories'
import { ChatSourcesPanel } from '@/components/ChatSourcesPanel'
import { PageHeader } from '@/components/PageHeader'
import type { ConversationTurn } from '@/types/chat'

const EXAMPLE_QUESTIONS = [
  'What is the main entry point of this repository?',
  'How is authentication implemented?',
  'What API routes are exposed?',
  'Summarize the project architecture.',
]

function createTurnId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

export function ChatPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [selectedRepositoryId, setSelectedRepositoryId] = useState<number | null>(null)
  const [message, setMessage] = useState('')
  const [turns, setTurns] = useState<ConversationTurn[]>([])
  const [activeSources, setActiveSources] = useState<ConversationTurn['sources']>([])
  const [activeSourcesQuestion, setActiveSourcesQuestion] = useState<string>()
  const [selectedTurnId, setSelectedTurnId] = useState<string | null>(null)
  const [sourcesHighlightPulse, setSourcesHighlightPulse] = useState(0)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { data: repositoriesData, isLoading: repositoriesLoading } = useQuery({
    queryKey: ['repositories'],
    queryFn: fetchRepositories,
  })

  const readyRepositories = useMemo(
    () => repositoriesData?.repositories.filter((repo) => repo.status === 'cloned') ?? [],
    [repositoriesData],
  )

  const selectedRepository = readyRepositories.find((repo) => repo.id === selectedRepositoryId)

  useEffect(() => {
    if (readyRepositories.length === 0) {
      return
    }

    const repoParam = searchParams.get('repository')
    if (repoParam) {
      const parsedId = Number(repoParam)
      if (!Number.isNaN(parsedId) && readyRepositories.some((repo) => repo.id === parsedId)) {
        setSelectedRepositoryId(parsedId)
        return
      }
    }

    setSelectedRepositoryId((current) => current ?? readyRepositories[0].id)
  }, [readyRepositories, searchParams])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [turns])

  const chatMutation = useMutation({
    mutationFn: async (question: string) => {
      if (!selectedRepositoryId) {
        throw new Error('Select a repository before chatting.')
      }

      const history = turns.map((turn) => ({
        role: turn.role,
        content: turn.content,
      }))

      return sendChatMessage(selectedRepositoryId, {
        message: question,
        top_k: 5,
        history,
      })
    },
    onMutate: (question) => {
      const userTurn: ConversationTurn = {
        id: createTurnId(),
        role: 'user',
        content: question,
      }
      setTurns((current) => [...current, userTurn])
      setMessage('')
      setActiveSources([])
      setActiveSourcesQuestion(question)
      setSelectedTurnId(null)
    },
    onSuccess: (response, question) => {
      const assistantTurn: ConversationTurn = {
        id: createTurnId(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        model: response.model,
        retrievalMode: response.retrieval_mode,
        cacheHit: response.cache_hit,
        cacheSimilarity: response.cache_similarity,
      }
      setTurns((current) => [...current, assistantTurn])
      setActiveSources(response.sources)
      setActiveSourcesQuestion(question)
      setSelectedTurnId(assistantTurn.id)
    },
    onError: (error: Error) => {
      const errorTurn: ConversationTurn = {
        id: createTurnId(),
        role: 'assistant',
        content: `**Error:** ${error.message}`,
      }
      setTurns((current) => [...current, errorTurn])
      setActiveSources([])
      setActiveSourcesQuestion(undefined)
      setSelectedTurnId(null)
    },
  })

  function handleRepositoryChange(repositoryId: number) {
    setSelectedRepositoryId(repositoryId)
    setSearchParams({ repository: String(repositoryId) })
    setTurns([])
    setActiveSources([])
    setActiveSourcesQuestion(undefined)
    setSelectedTurnId(null)
    setMessage('')
  }

  function handleClearConversation() {
    setTurns([])
    setActiveSources([])
    setActiveSourcesQuestion(undefined)
    setSelectedTurnId(null)
    setMessage('')
  }

  function handleViewSources(turn: ConversationTurn, question: string) {
    if (!turn.sources?.length) {
      return
    }
    setActiveSources(turn.sources)
    setActiveSourcesQuestion(question)
    setSelectedTurnId(turn.id)
    setSourcesHighlightPulse((current) => current + 1)
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmed = message.trim()
    if (!trimmed || chatMutation.isPending || !selectedRepositoryId) {
      return
    }
    chatMutation.mutate(trimmed)
  }

  function handleExampleClick(question: string) {
    if (chatMutation.isPending || !selectedRepositoryId) {
      return
    }
    chatMutation.mutate(question)
  }

  return (
    <main className="mx-auto max-w-6xl px-6 py-12">
      <PageHeader
        eyebrow="Repository chat"
        title="Ask about your code"
        description="Pick an indexed repository, ask a question in plain English, and GitSense retrieves relevant code chunks from Qdrant before generating an answer."
      />

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,0.9fr)]">
        <section className="glass-panel animate-fade-up animate-delay-2 flex h-[640px] flex-col overflow-hidden rounded-2xl">
          <div className="border-b border-white/10 p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-white">
                <MessageSquare className="h-5 w-5 text-brand-300" />
                <h3 className="text-lg font-semibold">Chat</h3>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={handleClearConversation}
                  disabled={turns.length === 0 || chatMutation.isPending}
                  className="ui-button inline-flex items-center gap-1.5 rounded-md border border-white/10 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Clear
                </button>
              </div>
            </div>

            <div className="mt-4">
              <label
                htmlFor="chat-repository"
                className="mb-2 block text-sm font-medium text-slate-200"
              >
                Repository
              </label>
              {repositoriesLoading ? (
                <div className="skeleton h-11 rounded-lg bg-white/10" />
              ) : readyRepositories.length > 0 ? (
                <select
                  id="chat-repository"
                  value={selectedRepositoryId ?? ''}
                  onChange={(event) => handleRepositoryChange(Number(event.target.value))}
                  className="input-field ui-button"
                >
                  {readyRepositories.map((repository) => (
                    <option key={repository.id} value={repository.id}>
                      {repository.full_name}
                    </option>
                  ))}
                </select>
              ) : (
                <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
                  No indexed repositories yet.{' '}
                  <Link to="/repositories" className="font-medium underline">
                    Submit and index a repository
                  </Link>{' '}
                  first, then come back to chat.
                </div>
              )}
            </div>

            {selectedRepository ? (
              <p className="mt-3 text-xs text-slate-500">
                Chatting with <span className="font-medium text-slate-300">{selectedRepository.full_name}</span>
              </p>
            ) : null}
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto p-5">
            {turns.length === 0 ? (
              <div className="flex flex-col items-center px-2 pt-8 pb-4 text-center">
                <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500/30 to-violet-500/20 text-brand-100 ring-1 ring-brand-400/20">
                  <Bot className="h-7 w-7" />
                </div>
                <h4 className="text-lg font-semibold text-white">Start a conversation</h4>
                <p className="mt-2 max-w-md text-sm text-slate-400">
                  Ask how something works, where a feature lives, or what a module does. Answers are
                  grounded in retrieved code, not the whole repo at once.
                </p>

                {readyRepositories.length > 0 ? (
                  <div className="mt-6 flex flex-wrap justify-center gap-2">
                    {EXAMPLE_QUESTIONS.map((question) => (
                      <button
                        key={question}
                        type="button"
                        onClick={() => handleExampleClick(question)}
                        disabled={chatMutation.isPending}
                        className="ui-button rounded-full border border-brand-400/20 bg-brand-500/10 px-3 py-1.5 text-xs text-brand-100 hover:bg-brand-500/20 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : (
              <div className="space-y-4">
                {turns.map((turn, index) => {
                const previousTurn = index > 0 ? turns[index - 1] : null
                const pairedQuestion =
                  turn.role === 'assistant' && previousTurn?.role === 'user'
                    ? previousTurn.content
                    : undefined
                const isSelectedSourceTurn = turn.role === 'assistant' && turn.id === selectedTurnId

                return (
                <div
                  key={turn.id}
                  className={`flex gap-3 ${turn.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {turn.role === 'assistant' ? (
                    <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-600/20 text-brand-200">
                      <Bot className="h-4 w-4" />
                    </div>
                  ) : null}

                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
                      turn.role === 'user'
                        ? 'bg-gradient-to-br from-brand-500 to-brand-600 text-white shadow-brand-600/20'
                        : isSelectedSourceTurn
                          ? 'border border-brand-400/40 bg-slate-950/90 text-slate-200 ring-1 ring-brand-400/20'
                          : 'border border-white/10 bg-slate-950/70 text-slate-200'
                    }`}
                  >
                    {turn.role === 'assistant' ? (
                      <div className="chat-prose prose prose-invert prose-sm max-w-none">
                        <ReactMarkdown>{turn.content}</ReactMarkdown>
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap">{turn.content}</p>
                    )}

                    {turn.role === 'assistant' && turn.model ? (
                      <div className="mt-3 border-t border-white/10 pt-2 text-xs text-slate-500">
                        <p>
                          Model: {turn.model}
                          {turn.retrievalMode ? ` · ${turn.retrievalMode} search` : ''}
                          {turn.sources?.length ? ` · ${turn.sources.length} sources` : ''}
                          {turn.cacheHit ? (
                            <span className="text-emerald-300">
                              {' '}
                              · cached
                              {turn.cacheSimilarity != null
                                ? ` (${(turn.cacheSimilarity * 100).toFixed(0)}% similar)`
                                : ''}
                            </span>
                          ) : null}
                        </p>
                        {turn.sources?.length && pairedQuestion ? (
                          <button
                            type="button"
                            onClick={() => handleViewSources(turn, pairedQuestion)}
                            className="ui-button mt-1 font-medium text-brand-200 hover:text-brand-100"
                          >
                            View sources
                          </button>
                        ) : null}
                      </div>
                    ) : null}
                  </div>

                  {turn.role === 'user' ? (
                    <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/10 text-slate-200">
                      <User className="h-4 w-4" />
                    </div>
                  ) : null}
                </div>
                )
              })}
              </div>
            )}

            {turns.length > 0 && chatMutation.isPending ? (
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <Loader2 className="h-4 w-4 animate-spin" />
                Retrieving relevant code and generating an answer…
              </div>
            ) : null}

            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSubmit} className="border-t border-white/10 p-5">
            <div className="flex gap-3">
              <textarea
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault()
                    if (!chatMutation.isPending && message.trim() && selectedRepositoryId) {
                      chatMutation.mutate(message.trim())
                    }
                  }
                }}
                rows={2}
                placeholder={
                  selectedRepositoryId
                    ? 'Ask a question about this repository…'
                    : 'Index a repository first to start chatting'
                }
                disabled={!selectedRepositoryId || chatMutation.isPending}
                className="input-field ui-button min-h-[52px] flex-1 resize-none disabled:cursor-not-allowed disabled:opacity-60"
              />
              <button
                type="submit"
                disabled={!selectedRepositoryId || !message.trim() || chatMutation.isPending}
                className="btn-primary ui-button inline-flex h-[52px] w-[52px] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {chatMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </button>
            </div>
            <p className="mt-2 text-xs text-slate-500">Press Enter to send, Shift+Enter for a new line.</p>
          </form>
        </section>

        <aside className="animate-fade-up animate-delay-3 max-h-[640px] w-full space-y-4 self-start overflow-y-auto">
          <ChatSourcesPanel
            sources={activeSources ?? []}
            question={activeSourcesQuestion}
            isLoading={chatMutation.isPending}
            highlightPulse={sourcesHighlightPulse}
          />

          <div className="glass-panel rounded-2xl p-5">
            <h3 className="mb-2 text-sm font-semibold uppercase tracking-wider text-slate-400">
              How it works
            </h3>
            <ol className="space-y-2 text-sm text-slate-400">
              <li>1. Your question is embedded with Sentence Transformers.</li>
              <li>2. Qdrant (semantic) + BM25 (keyword) retrieve candidate chunks.</li>
              <li>3. Reciprocal Rank Fusion merges both ranked lists.</li>
              <li>4. A cross-encoder reranks candidates for sharper relevance.</li>
              <li>5. Top chunks are sent to the LLM; answer + sources are shown.</li>
              <li>6. Similar questions (same repo) may return a cached answer — skips retrieval and the LLM.</li>
            </ol>
          </div>
        </aside>
      </div>
    </main>
  )
}
