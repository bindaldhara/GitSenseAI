import type { MultiRepoSearchResponse } from '@/types/search'
import { apiClient, getApiErrorMessage } from '@/lib/axios'

export async function searchAcrossRepositories(query: string, topK = 5) {
  try {
    const { data } = await apiClient.post<MultiRepoSearchResponse>('/api/v1/search', {
      query,
      top_k: topK,
    })
    return data
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Search failed'))
  }
}
