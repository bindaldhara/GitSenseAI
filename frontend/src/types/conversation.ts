export type Conversation = {
  id: number
  user_id: number
  repository_id: number
  title: string
  created_at: string
  updated_at: string
}

export type ConversationMessage = {
  id: number
  conversation_id: number
  role: 'user' | 'assistant'
  content: string
  metadata: Record<string, unknown>
  created_at: string
}
