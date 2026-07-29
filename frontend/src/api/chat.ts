import type { ChatRequest, ChatResponse } from '@/types/chat'
import { apiClient, getApiErrorMessage } from '@/lib/axios'

export async function sendChatMessage(repositoryId: number, payload: ChatRequest) {
  try {
    const { data } = await apiClient.post<ChatResponse>(
      `/api/v1/repositories/${repositoryId}/chat`,
      payload,
    )
    return data
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Chat request failed'))
  }
}
