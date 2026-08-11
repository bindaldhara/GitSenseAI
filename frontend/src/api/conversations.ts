import type { Conversation, ConversationMessage } from '@/types/conversation'
import { apiClient, getApiErrorMessage } from '@/lib/axios'

export async function fetchConversations(repositoryId?: number) {
  try {
    const params = repositoryId ? { repository_id: repositoryId } : undefined
    const { data } = await apiClient.get<{ conversations: Conversation[] }>(
      '/api/v1/conversations',
      { params },
    )
    return data.conversations
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Failed to load conversations'))
  }
}

export async function createConversation(repositoryId: number, title?: string) {
  try {
    const { data } = await apiClient.post<Conversation>('/api/v1/conversations', {
      repository_id: repositoryId,
      title,
    })
    return data
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Failed to create conversation'))
  }
}

export async function deleteConversation(conversationId: number) {
  try {
    await apiClient.delete(`/api/v1/conversations/${conversationId}`)
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Failed to delete conversation'))
  }
}

export async function fetchConversationMessages(conversationId: number) {
  try {
    const { data } = await apiClient.get<{
      conversation_id: number
      messages: ConversationMessage[]
    }>(`/api/v1/conversations/${conversationId}/messages`)
    return data.messages
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Failed to load messages'))
  }
}
