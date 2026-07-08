import { apiClient } from '../axios.config';
import { Conversation, Message, ChatRequest, ChatResponse, FeedbackRequest, FeedbackResponse } from '@/types/chat.types';

const client = apiClient.getClient('chatbot');

export const chatService = {
  // Conversaciones
  getConversations: async (usuarioId: number): Promise<Conversation[]> => {
    const response = await client.get(`/conversations?usuario_id=${usuarioId}`);
    return response.data;
  },

  createConversation: async (usuarioId: number, nombre?: string): Promise<Conversation> => {
    const response = await client.post('/conversations', { usuario_id: usuarioId, nombre });
    return response.data;
  },

  deleteConversation: async (conversationId: number): Promise<void> => {
    await client.delete(`/conversations/${conversationId}`);
  },

  // Mensajes
  getMessages: async (conversationId: number): Promise<Message[]> => {
    const response = await client.get(`/conversations/${conversationId}/messages`);
    return response.data;
  },

  sendMessage: async (data: ChatRequest): Promise<ChatResponse> => {
    const response = await client.post('/chat', data);
    return response.data;
  },

  sendFeedback: async (data: FeedbackRequest): Promise<FeedbackResponse> => {
    const response = await client.post('/chat/feedback', data);
    return response.data;
  },

  getFeedbackStatus: async (messageId: number): Promise<{ feedback_exists: boolean; fue_util?: boolean }> => {
    const response = await client.get(`/chat/feedback/${messageId}`);
    return response.data;
  },

  // ✅ NUEVO: Regenerar mensaje
  regenerateMessage: async (messageId: number): Promise<ChatResponse> => {
    const response = await client.post(`/messages/${messageId}/regenerate`);
    return response.data;
  },
};