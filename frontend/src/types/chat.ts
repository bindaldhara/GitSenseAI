export type ChatRole = 'user' | 'assistant'

export type ChatMessage = {
  role: ChatRole
  content: string
}

export type ChatRequest = {
  message: string
  top_k?: number
  history?: ChatMessage[]
  conversation_id?: number
}

export type RetrievedSource = {
  file_path: string
  language: string
  chunk_kind: string
  symbol_name: string | null
  start_line: number
  end_line: number
  score: number
  excerpt: string
}

export type AgentRoute = 'code' | 'documentation' | 'architecture'

export type ChatResponse = {
  repository_id: number
  answer: string
  sources: RetrievedSource[]
  model: string
  retrieval_mode: 'hybrid' | 'vector'
  cache_hit?: boolean
  cache_similarity?: number | null
  route?: AgentRoute | null
  agent?: AgentRoute | null
  agent_steps?: string[]
  conversation_id?: number | null
}

export type ConversationTurn = {
  id: string
  role: ChatRole
  content: string
  sources?: RetrievedSource[]
  model?: string
  retrievalMode?: 'hybrid' | 'vector'
  cacheHit?: boolean
  cacheSimilarity?: number | null
  route?: AgentRoute | null
  agent?: AgentRoute | null
  agentSteps?: string[]
}
