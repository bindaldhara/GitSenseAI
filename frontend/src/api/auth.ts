import type { AuthTokenResponse, User } from '@/types/auth'
import { apiClient, getApiErrorMessage } from '@/lib/axios'
import { setStoredToken } from '@/lib/authStorage'

export async function registerUser(email: string, password: string) {
  try {
    const { data } = await apiClient.post<AuthTokenResponse>('/api/v1/auth/register', {
      email,
      password,
    })
    setStoredToken(data.access_token)
    return data
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Registration failed'))
  }
}

export async function loginUser(email: string, password: string) {
  try {
    const { data } = await apiClient.post<AuthTokenResponse>('/api/v1/auth/login', {
      email,
      password,
    })
    setStoredToken(data.access_token)
    return data
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Login failed'))
  }
}

export async function fetchCurrentUser() {
  try {
    const { data } = await apiClient.get<User>('/api/v1/auth/me')
    return data
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Failed to load user'))
  }
}

export function logoutUser() {
  setStoredToken(null)
}
