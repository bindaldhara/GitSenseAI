export type ServiceHealth = {
  name: string
  status: string
  detail?: string | null
}

export type RepositoryOpsRow = {
  repository_id: number
  full_name: string
  status: string
  user_id?: number | null
  owner_email?: string | null
  chat_ready: boolean
  hybrid_ready: boolean
  graph_ready: boolean
}

export type PlatformConfig = {
  app_version: string
  llm_provider: string
  ollama_model: string
  openai_model: string
  embedding_model: string
  embedding_dimension: number
  rerank_model: string
  hybrid_search_enabled: boolean
  rerank_enabled: boolean
  graph_rag_enabled: boolean
  agents_enabled: boolean
}

export type PlatformTotals = {
  repository_count: number
  cloned_repository_count: number
  chat_ready_repository_count: number
  hybrid_ready_repository_count: number
  graph_ready_repository_count: number
}

export type OpsDashboardResponse = {
  services: ServiceHealth[]
  totals: PlatformTotals
  config: PlatformConfig
  repositories: RepositoryOpsRow[]
}

export type CacheEvent = {
  type: 'hit' | 'miss' | 'store'
  repository_id: number
  question: string
  similarity: number | null
  timestamp: string
}

export type CacheAnalyticsResponse = {
  enabled: boolean
  similarity_threshold: number
  ttl_seconds: number
  max_entries_per_repo: number
  hits: number
  misses: number
  stores: number
  entries: number
  lookups: number
  hit_rate_percent: number
  recent_events: CacheEvent[]
  error?: string | null
}

export type CacheClearResponse = {
  removed_keys: number
  message: string
}

export type GraphRagCompareRequest = {
  message: string
  top_k?: number
}

export type GraphRagModeResult = {
  mode_id: string
  label: string
  description: string
  answer: string
  model: string
  retrieval_mode: string
  sources: Array<{
    file_path: string
    language: string | null
    chunk_kind: string | null
    symbol_name: string | null
    start_line: number | null
    end_line: number | null
    score: number | null
    excerpt: string
  }>
  graph_context: string[]
  graph_context_count: number
  elapsed_ms: number
}

export type GraphRagCompareResponse = {
  repository_id: number
  question: string
  top_k: number
  graph_node_count: number
  graph_edge_count: number
  results: GraphRagModeResult[]
}
