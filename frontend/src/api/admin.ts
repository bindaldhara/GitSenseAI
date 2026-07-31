import type { OpsDashboardResponse } from '@/types/admin'
import { apiClient, getApiErrorMessage } from '@/lib/axios'

export async function fetchOpsDashboard() {
  try {
    const { data } = await apiClient.get<OpsDashboardResponse>('/api/v1/admin/ops')
    return data
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Failed to load ops dashboard'))
  }
}
