import { api } from '@/services/api'
import type { ChatRequest, ChatResponse, FeedbackRequest, FeedbackResponse, Conversation, Message } from '@/types/chat.types'

function mapConversation(item: any): Conversation {
  return {
    id: item.id_conversacion ?? item.id,
    usuario_id: item.id_usuario ?? item.usuario_id,
    nombre_cliente: item.nombre_cliente || '',
    iniciado_en: item.iniciado_en,
    activa: item.activa ?? true,
    total_mensajes: item.total_mensajes,
  }
}

function mapMessage(item: any): Message {
  return {
    id: item.id,
    conversacion_id: item.id_conversacion ?? item.conversacion_id,
    rol: item.rol,
    contenido: item.contenido,
    tipo_resolucion: item.tipo_resolucion,
    confianza: item.confianza_ml != null ? Number(item.confianza_ml) : undefined,
    creado_en: item.enviado_en ?? item.creado_en,
  }
}

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
    const data = await api.chatbot.get<any>(`/conversations?usuario_id=${usuarioId}`)
    const raw = Array.isArray(data) ? data : (data.conversations || data || [])
    return raw.map(mapConversation)
  },
  getConversationMessages: async (conversationId: number): Promise<Message[]> => {
    const data = await api.chatbot.get<any>(`/conversations/${conversationId}/messages`)
    const raw = Array.isArray(data) ? data : (data.mensajes || [])
    return raw.map(mapMessage)
  },
}
