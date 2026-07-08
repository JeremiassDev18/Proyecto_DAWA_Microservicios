import { api } from '@/services/api'
import type { TrainingStatus, PendingQuery, Document, ModelInfo, UsageMetrics } from '@/types/dataset.types'

export const trainingService = {
  train: async (): Promise<{ task_id: string }> => {
    return api.chatbot.post<{ task_id: string }>('/train', {})
  },
  getStatus: async (taskId: string): Promise<TrainingStatus> => {
    return api.chatbot.get<TrainingStatus>(`/train/status/${taskId}`)
  },

  getPending: async (page = 1, pageSize = 20): Promise<PendingQuery[]> => {
    const data = await api.chatbot.get<any>(`/pending?resuelta=false&page=${page}&page_size=${pageSize}`)
    return data.items || data.pendientes || data
  },
  convertPending: async (id: number): Promise<void> => {
    await api.chatbot.post(`/pending/${id}/convert`, {})
  },
  resolvePending: async (id: number): Promise<void> => {
    await api.chatbot.put(`/pending/${id}/resolver`, {})
  },

  getDocuments: async (page = 1, pageSize = 20): Promise<Document[]> => {
    const data = await api.chatbot.get<any>(`/documents?page=${page}&page_size=${pageSize}`)
    return data.items || data.documents || data
  },
  createDocument: async (doc: Partial<Document>): Promise<Document> => {
    return api.chatbot.post<Document>('/documents', doc)
  },
  updateDocument: async (id: number, doc: Partial<Document>): Promise<Document> => {
    return api.chatbot.put<Document>(`/documents/${id}`, doc)
  },
  deleteDocument: async (id: number): Promise<void> => {
    await api.chatbot.delete(`/documents/${id}`)
  },

  getModels: async (): Promise<ModelInfo[]> => {
    const data = await api.chatbot.get<any>('/modelos?limit=10&page=1&page_size=20')
    return data.items || data.modelos || data
  },
  getModelMetrics: async (): Promise<any> => {
    return api.chatbot.get('/metrics/model')
  },
  getUsageMetrics: async (): Promise<UsageMetrics> => {
    return api.chatbot.get<UsageMetrics>('/metrics/usage')
  },
}
