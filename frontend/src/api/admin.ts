import type { CacheAnalyticsResponse, CacheClearResponse, OpsDashboardResponse } from '@/types/admin'
import { apiClient, getApiErrorMessage } from '@/lib/axios'

export async function fetchOpsDashboard() {
  try {
    const { data } = await apiClient.get<OpsDashboardResponse>('/api/v1/admin/ops')
    return data
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Failed to load ops dashboard'))
  }
}

export async function fetchCacheAnalytics() {
  try {
    const { data } = await apiClient.get<CacheAnalyticsResponse>('/api/v1/admin/cache')
    return data
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Failed to load cache analytics'))
  }
}

export async function clearSemanticCache() {
  try {
    const { data } = await apiClient.delete<CacheClearResponse>('/api/v1/admin/cache')
    return data
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Failed to clear semantic cache'))
  }
}
