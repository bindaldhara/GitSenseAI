import { useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bot, Loader2, MessageSquare, Send, Trash2, User } from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'

import { sendChatMessage } from '@/api/chat'
import { fetchConversationMessages, fetchConversations } from '@/api/conversations'
import { fetchRepositories } from '@/api/repositories'
import { ChatSourcesPanel } from '@/components/ChatSourcesPanel'
import { MarkdownContent } from '@/components/MarkdownContent'
import { PageHeader } from '@/components/PageHeader'
import { ResizableColumns } from '@/components/ResizableColumns'
import { useAuth } from '@/context/AuthContext'
import type { ConversationTurn, RetrievedSource } from '@/types/chat'

const EXAMPLE_QUESTIONS = [
  'What is the main entry point of this repository?',
  'How is authentication implemented?',
  'What API routes are exposed?',
  'Draw a mermaid diagram of the main frontend components.',
]

function createTurnId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function formatAgentLabel(agent?: string | null) {
  if (!agent) return null
  if (agent === 'code') return 'Code Agent'
  if (agent === 'documentation') return 'Documentation Agent'
  if (agent === 'architecture') return 'Architecture Agent'
  return agent
}

const MIN_CONTROLS_HEIGHT = 96
const MAX_CONTROLS_HEIGHT = 260
const DEFAULT_CONTROLS_HEIGHT = 148

export function ChatPage() {
  const { isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const [selectedRepositoryId, setSelectedRepositoryId] = useState<number | null>(null)
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null)
  const [message, setMessage] = useState('')
  const [turns, setTurns] = useState<ConversationTurn[]>([])
  const [activeSources, setActiveSources] = useState<ConversationTurn['sources']>([])
  const [activeSourcesQuestion, setActiveSourcesQuestion] = useState<string>()
  const [selectedTurnId, setSelectedTurnId] = useState<string | null>(null)
  const [sourcesHighlightPulse, setSourcesHighlightPulse] = useState(0)
  const [controlsHeight, setControlsHeight] = useState(DEFAULT_CONTROLS_HEIGHT)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { data: repositoriesData, isLoading: repositoriesLoading } = useQuery({
    queryKey: ['repositories'],
    queryFn: fetchRepositories,
  })

  const readyRepositories = useMemo(
    () => repositoriesData?.repositories.filter((repo) => repo.status === 'cloned') ?? [],
    [repositoriesData],
  )

  const { data: savedConversations = [] } = useQuery({
    queryKey: ['conversations', selectedRepositoryId],
    queryFn: () => fetchConversations(selectedRepositoryId!),
    enabled: isAuthenticated && selectedRepositoryId !== null,
  })

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

      const history = activeConversationId
        ? []
        : turns.map((turn) => ({
            role: turn.role,
            content: turn.content,
          }))

      return sendChatMessage(selectedRepositoryId, {
        message: question,
        top_k: 5,
        history,
        conversation_id: activeConversationId ?? undefined,
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
        route: response.route,
        agent: response.agent,
        agentSteps: response.agent_steps,
      }
      setTurns((current) => [...current, assistantTurn])
      setActiveSources(response.sources)
      setActiveSourcesQuestion(question)
      setSelectedTurnId(assistantTurn.id)
      if (response.conversation_id) {
        setActiveConversationId(response.conversation_id)
        void queryClient.invalidateQueries({ queryKey: ['conversations', selectedRepositoryId] })
      }
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
    setActiveConversationId(null)
    setTurns([])
    setActiveSources([])
    setActiveSourcesQuestion(undefined)
    setSelectedTurnId(null)
    setMessage('')
  }

  function handleClearConversation() {
    setActiveConversationId(null)
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

  async function handleConversationSelect(value: string) {
    if (value === 'new') {
      handleClearConversation()
      return
    }
    const conversationId = Number(value)
    if (Number.isNaN(conversationId)) return
    setActiveConversationId(conversationId)
    try {
      const messages = await fetchConversationMessages(conversationId)
      const loadedTurns: ConversationTurn[] = messages.map((item) => {
        const meta = item.metadata as {
          sources?: RetrievedSource[]
          model?: string
          retrieval_mode?: 'hybrid' | 'vector'
          route?: ConversationTurn['route']
          agent?: ConversationTurn['agent']
          cache_hit?: boolean
        }
        return {
          id: createTurnId(),
          role: item.role,
          content: item.content,
          sources: meta.sources,
          model: meta.model,
          retrievalMode: meta.retrieval_mode,
          route: meta.route,
          agent: meta.agent,
          cacheHit: meta.cache_hit,
        }
      })
      setTurns(loadedTurns)
      setActiveSources([])
      setActiveSourcesQuestion(undefined)
      setSelectedTurnId(null)
    } catch {
      setTurns([])
    }
  }

  function handleControlsResizeStart(event: React.MouseEvent<HTMLDivElement>) {
    event.preventDefault()
    const startY = event.clientY
    const startHeight = controlsHeight

    function onMouseMove(moveEvent: MouseEvent) {
      const delta = moveEvent.clientY - startY
      setControlsHeight(
        Math.min(MAX_CONTROLS_HEIGHT, Math.max(MIN_CONTROLS_HEIGHT, startHeight + delta)),
      )
    }

    function onMouseUp() {
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('mouseup', onMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }

    document.body.style.cursor = 'row-resize'
    document.body.style.userSelect = 'none'
    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', onMouseUp)
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
        <section className="glass-panel animate-fade-up animate-delay-2 flex min-h-[36rem] h-[calc(100vh-11rem)] max-h-[44rem] flex-col overflow-hidden rounded-2xl">
          <div
            className="shrink-0 overflow-y-auto px-4 py-3"
            style={{ height: controlsHeight }}
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2 text-white">
                <MessageSquare className="h-4 w-4 text-brand-300" />
                <h3 className="text-base font-semibold">Chat</h3>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={handleClearConversation}
                  disabled={turns.length === 0 || chatMutation.isPending}
                  className="ui-button inline-flex items-center gap-1.5 rounded-md border border-white/10 px-2.5 py-1 text-xs font-medium text-slate-200 hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Clear
                </button>
              </div>
            </div>

            <ResizableColumns
              className="mt-2"
              left={
                <div>
                  <label
                    htmlFor="chat-repository"
                    className="mb-1 block text-xs font-medium text-slate-400"
                  >
                    Repository
                  </label>
                  {repositoriesLoading ? (
                    <div className="skeleton h-9 rounded-lg bg-white/10" />
                  ) : readyRepositories.length > 0 ? (
                    <select
                      id="chat-repository"
                      value={selectedRepositoryId ?? ""}
                      onChange={(event) =>
                        handleRepositoryChange(Number(event.target.value))
                      }
                      className="input-field ui-button py-2 text-sm"
                    >
                      {readyRepositories.map((repository) => (
                        <option key={repository.id} value={repository.id}>
                          {repository.full_name}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-100">
                      No indexed repositories yet.{" "}
                      <Link to="/repositories" className="font-medium underline">
                        Submit and index a repository
                      </Link>{" "}
                      first, then come back to chat.
                    </div>
                  )}
                </div>
              }
              right={
                isAuthenticated && selectedRepositoryId
                  ? (
                    <div>
                      <label
                        htmlFor="chat-conversation"
                        className="mb-1 block text-xs font-medium text-slate-400"
                      >
                        Saved conversation
                      </label>
                      <select
                        id="chat-conversation"
                        value={activeConversationId ?? 'new'}
                        onChange={(event) => handleConversationSelect(event.target.value)}
                        className="input-field ui-button py-2 text-sm"
                      >
                        <option value="new">New conversation</option>
                        {savedConversations.map((conversation) => (
                          <option key={conversation.id} value={conversation.id}>
                            {conversation.title}
                          </option>
                        ))}
                      </select>
                    </div>
                  )
                  : null
              }
            />
          </div>

          <div
            role="separator"
            aria-orientation="horizontal"
            aria-label="Resize chat controls"
            onMouseDown={handleControlsResizeStart}
            className="chat-row-resize-handle shrink-0"
          />

          <div className="min-h-0 flex-1 overflow-y-auto p-5">
            {turns.length === 0 ? (
              <div className="flex flex-col items-center px-2 pt-8 pb-4 text-center">
                <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-linear-to-br from-brand-500/30 to-violet-500/20 text-brand-100 ring-1 ring-brand-400/20">
                  <Bot className="h-7 w-7" />
                </div>
                <h4 className="text-lg font-semibold text-white">
                  Start a conversation
                </h4>
                <p className="mt-2 max-w-md text-sm text-slate-400">
                  Ask how something works, where a feature lives, or what a
                  module does. Answers are grounded in retrieved code, not the
                  whole repo at once.
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
                  const previousTurn = index > 0 ? turns[index - 1] : null;
                  const pairedQuestion =
                    turn.role === "assistant" && previousTurn?.role === "user"
                      ? previousTurn.content
                      : undefined;
                  const isSelectedSourceTurn =
                    turn.role === "assistant" && turn.id === selectedTurnId;

                  return (
                    <div
                      key={turn.id}
                      className={`flex gap-3 ${turn.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                      {turn.role === "assistant" ? (
                        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-600/20 text-brand-200">
                          <Bot className="h-4 w-4" />
                        </div>
                      ) : null}

                      <div
                        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
                          turn.role === "user"
                            ? "bg-linear-to-br from-brand-500 to-brand-600 text-white shadow-brand-600/20"
                            : isSelectedSourceTurn
                              ? "border border-brand-400/40 bg-slate-950/90 text-slate-200 ring-1 ring-brand-400/20"
                              : "border border-white/10 bg-slate-950/70 text-slate-200"
                        }`}
                      >
                        {turn.role === "assistant" ? (
                          <MarkdownContent
                            content={turn.content}
                            className="chat-prose prose prose-invert prose-sm max-w-none"
                          />
                        ) : (
                          <p className="whitespace-pre-wrap">{turn.content}</p>
                        )}

                        {turn.role === "assistant" &&
                        (turn.model || turn.agent) ? (
                          <div className="mt-3 border-t border-white/10 pt-2 text-xs text-slate-500">
                            <p>
                              {formatAgentLabel(turn.agent) ? (
                                <span className="text-violet-300">
                                  {formatAgentLabel(turn.agent)}
                                </span>
                              ) : null}
                              {formatAgentLabel(turn.agent) && turn.model
                                ? " · "
                                : null}
                              {turn.model ? `Model: ${turn.model}` : null}
                              {turn.route ? ` · route: ${turn.route}` : ""}
                              {turn.retrievalMode
                                ? ` · ${turn.retrievalMode} search`
                                : ""}
                              {turn.sources?.length
                                ? ` · ${turn.sources.length} sources`
                                : ""}
                              {turn.cacheHit ? (
                                <span className="text-emerald-300">
                                  {" "}
                                  · cached
                                  {turn.cacheSimilarity != null
                                    ? ` (${(turn.cacheSimilarity * 100).toFixed(0)}% similar)`
                                    : ""}
                                </span>
                              ) : null}
                            </p>
                            {turn.sources?.length && pairedQuestion ? (
                              <button
                                type="button"
                                onClick={() =>
                                  handleViewSources(turn, pairedQuestion)
                                }
                                className="ui-button mt-1 font-medium text-brand-200 hover:text-brand-100"
                              >
                                View sources
                              </button>
                            ) : null}
                          </div>
                        ) : null}
                      </div>

                      {turn.role === "user" ? (
                        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/10 text-slate-200">
                          <User className="h-4 w-4" />
                        </div>
                      ) : null}
                    </div>
                  );
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

          <form
            onSubmit={handleSubmit}
            className="border-t border-white/10 p-5"
          >
            <div className="flex gap-3">
              <textarea
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    if (
                      !chatMutation.isPending &&
                      message.trim() &&
                      selectedRepositoryId
                    ) {
                      chatMutation.mutate(message.trim());
                    }
                  }
                }}
                rows={2}
                placeholder={
                  selectedRepositoryId
                    ? "Ask a question about this repository…"
                    : "Index a repository first to start chatting"
                }
                disabled={!selectedRepositoryId || chatMutation.isPending}
                className="input-field ui-button min-h-13 flex-1 resize-none disabled:cursor-not-allowed disabled:opacity-60"
              />
              <button
                type="submit"
                disabled={
                  !selectedRepositoryId ||
                  !message.trim() ||
                  chatMutation.isPending
                }
                className="btn-primary ui-button inline-flex h-13 w-13 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {chatMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </button>
            </div>
            <p className="mt-2 text-xs text-slate-500">
              Press Enter to send, Shift+Enter for a new line.
            </p>
          </form>
        </section>

        <aside className="animate-fade-up animate-delay-3 max-h-[min(44rem,calc(100vh-11rem))] w-full space-y-4 self-start overflow-y-auto">
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
              <li>
                1. Router Agent classifies intent (code, documentation, or
                architecture).
              </li>
              <li>
                2. Specialist agent runs: Code, Documentation, or Architecture.
              </li>
              <li>
                3. Semantic cache check, then hybrid retrieval + cross-encoder
                rerank.
              </li>
              <li>
                4. Agent-specific prompt generates the grounded answer (architecture
                answers may include Mermaid diagrams).
              </li>
              <li>
                5. Similar questions may return a cached answer instantly.
              </li>
            </ol>
          </div>
        </aside>
      </div>
    </main>
  );
}
