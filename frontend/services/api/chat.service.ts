import { api } from '@/services/api'
import type { ChatRequest, ChatResponse, FeedbackRequest, FeedbackResponse, Conversation } from '@/types/chat.types'

export const chatService = {
  sendMessage: async (data: ChatRequest): Promise<ChatResponse> => {
    return api.chatbot.post<ChatResponse>('/chat', data)
  },
  sendFeedback: async (data: FeedbackRequest): Promise<FeedbackResponse> => {
    return api.chatbot.post<FeedbackResponse>('/chat/feedback', data)
  },
  getFeedbackStatus: async (messageId: number): Promise<{ feedback_exists: boolean; fue_util?: boolean }> => {
    return api.chatbot.get<{ feedback_exists: boolean; fue_util?: boolean }>(`/chat/feedback/${messageId}`)
  },
  getConversations: async (usuarioId: number): Promise<Conversation[]> => {
    const data = await api.chatbot.get<any>(`/summary/conversations?usuario_id=${usuarioId}`)
    return Array.isArray(data) ? data : (data.conversations || data || [])
  },
}
