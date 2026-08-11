import type { RetrievedSource } from '@/types/chat'

export type MultiRepoSearchResult = {
  repository_id: number
  full_name: string
  retrieval_mode: string
  hits: RetrievedSource[]
}

export type MultiRepoSearchResponse = {
  query: string
  repository_count: number
  results: MultiRepoSearchResult[]
}
