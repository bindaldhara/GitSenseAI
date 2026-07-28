import type { Repository, RepositoryParseSummary } from '@/types/repository'
import { apiClient, getApiErrorMessage } from '@/lib/axios'

export async function fetchRepositories() {
  try {
    const { data } = await apiClient.get<{ repositories: Repository[] }>(
      '/api/v1/repositories',
    )
    return data
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Failed to load repositories'))
  }
}

export async function submitRepository(url: string) {
  try {
    const { data } = await apiClient.post<Repository>('/api/v1/repositories', {
      url,
    })
    return data
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Repository submission failed'))
  }
}

export async function deleteRepository(repositoryId: number) {
  try {
    await apiClient.delete(`/api/v1/repositories/${repositoryId}`)
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Repository delete failed'))
  }
}

export async function reindexRepository(repositoryId: number) {
  try {
    const { data } = await apiClient.post<Repository>(
      `/api/v1/repositories/${repositoryId}/reindex`,
    )
    return data
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Repository re-index failed'))
  }
}

export async function fetchParseSummary(repositoryId: number, skippedLimit = 20) {
  try {
    const { data } = await apiClient.get<RepositoryParseSummary>(
      `/api/v1/repositories/${repositoryId}/parse-summary`,
      { params: { skipped_limit: skippedLimit } },
    )
    return data
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Failed to load parse summary'))
  }
}
