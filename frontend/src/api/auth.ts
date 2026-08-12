import type { User } from '@/types/auth'
import { apiClient, getApiErrorMessage } from '@/lib/axios'

export async function fetchCurrentUser() {
  try {
    const { data } = await apiClient.get<User>('/api/v1/auth/me')
    return data
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Failed to load user'))
  }
}
