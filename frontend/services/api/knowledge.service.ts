import { api } from '@/services/api'
import type { PendingQuery, Document, UsageMetrics } from '@/types/knowledge.types'

export const knowledgeService = {
  getPending: async (page = 1, pageSize = 20): Promise<PendingQuery[]> => {
    const data = await api.chatbot.get<any>(`/pending?resuelta=false&page=${page}&page_size=${pageSize}`)
    return data.items || data.pendientes || data
  },
  resolvePending: async (id: number): Promise<void> => {
    await api.chatbot.patch(`/pending/${id}/resolver`, {})
  },

  getDocuments: async (page = 1, pageSize = 20): Promise<Document[]> => {
    const data = await api.chatbot.get<any>(`/knowledge?page=${page}&page_size=${pageSize}`)
    return data.items || data.documents || data
  },
  createDocument: async (doc: Partial<Document>): Promise<Document> => {
    return api.chatbot.post<Document>('/knowledge', doc)
  },
  updateDocument: async (id: number, doc: Partial<Document>): Promise<Document> => {
    return api.chatbot.put<Document>(`/knowledge/${id}`, doc)
  },
  deleteDocument: async (id: number): Promise<void> => {
    await api.chatbot.delete(`/knowledge/${id}`)
  },

  getUsageMetrics: async (): Promise<UsageMetrics> => {
    return api.chatbot.get<UsageMetrics>('/metrics/usage')
  },
}
