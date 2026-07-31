export type Repository = {
  id: number
  url: string
  full_name: string
  provider: string
  status: string
  clone_path: string
  default_branch: string | null
  created_at: string
  updated_at: string
}

export type SkippedFile = {
  path: string
  reason: string
}

export type RepositoryParseSummary = {
  repository_id: number
  file_count: number
  symbol_count: number
  skipped_count: number
  by_language: Record<string, number>
  by_kind: Record<string, number>
  by_skip_reason: Record<string, number>
  skipped_files: SkippedFile[]
  skipped_returned: number
  skipped_limit: number
}

export type EmbeddingSummary = {
  repository_id: number
  vector_count: number
  bm25_chunk_count: number
  hybrid_ready: boolean
}
