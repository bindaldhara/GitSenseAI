export type DiagramRequest = {
  message: string
  limit?: number
}

export type DiagramResponse = {
  repository_id: number
  question: string
  title: string
  description: string
  mermaid: string
  model: string
  sources: Array<{
    file_path: string
    language: string
    chunk_kind: string
    symbol_name: string | null
    start_line: number
    end_line: number
    score: number
    excerpt: string
  }>
}
