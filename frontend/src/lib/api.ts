import type { Repository } from '@/types/repository'

export const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export async function fetchHealth() {
  const response = await fetch(`${API_BASE}/api/v1/health`)
  if (!response.ok) {
    throw new Error('Backend unreachable')
  }
  return response.json() as Promise<{ status: string }>
}

export async function fetchRepositories() {
  const response = await fetch(`${API_BASE}/api/v1/repositories`)
  if (!response.ok) {
    throw new Error('Failed to load repositories')
  }
  return response.json() as Promise<{ repositories: Repository[] }>
}

export async function submitRepository(url: string) {
  const response = await fetch(`${API_BASE}/api/v1/repositories`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ url }),
  })

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => null)) as
      | { detail?: string }
      | null
    throw new Error(errorBody?.detail ?? 'Repository submission failed')
  }

  return response.json() as Promise<Repository>
}
