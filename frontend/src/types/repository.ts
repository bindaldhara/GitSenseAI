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
  graph_node_count: number
  graph_edge_count: number
  graph_ready: boolean
}

export type GraphSummary = {
  repository_id: number
  node_count: number
  edge_count: number
  nodes_by_type: Record<string, number>
  edges_by_type: Record<string, number>
  graph_ready: boolean
}

export type GraphDependency = {
  source_file: string
  target_label: string
  target_type: string
  edge_type: string
}

export type GraphDependencies = {
  repository_id: number
  dependency_count: number
  dependencies: GraphDependency[]
  limit: number
}
