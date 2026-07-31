import type { RetrievedSource } from '@/types/chat'

export type RetrievalCompareRequest = {
  message: string
  top_k?: number
}

export type RetrievalModeResult = {
  mode_id: string
  label: string
  retrieval_mode: 'hybrid' | 'vector'
  retrieval_ms: number
  sources: RetrievedSource[]
}

export type RetrievalCompareResponse = {
  repository_id: number
  question: string
  top_k: number
  results: RetrievalModeResult[]
}
