import { apiClient, getApiErrorMessage } from '@/lib/axios'

export async function fetchHealth() {
  try {
    const { data } = await apiClient.get<{ status: string }>('/api/v1/health')
    return data
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Backend unreachable'))
  }
}
