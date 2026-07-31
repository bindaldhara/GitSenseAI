export type ServiceHealth = {
  name: string
  status: string
  detail?: string | null
}

export type RepositoryOpsRow = {
  repository_id: number
  full_name: string
  status: string
  chat_ready: boolean
  hybrid_ready: boolean
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
}

export type PlatformTotals = {
  repository_count: number
  cloned_repository_count: number
  chat_ready_repository_count: number
  hybrid_ready_repository_count: number
}

export type OpsDashboardResponse = {
  services: ServiceHealth[]
  totals: PlatformTotals
  config: PlatformConfig
  repositories: RepositoryOpsRow[]
}
