import { api } from '@/services/api'
import type { DatasetEntry, DatasetFilters } from '@/types/dataset.types'

export const datasetService = {
  list: async (filters?: DatasetFilters): Promise<DatasetEntry[]> => {
    const params = new URLSearchParams()
    if (filters?.query) params.set('query', filters.query)
    if (filters?.intencion) params.set('intencion', filters.intencion)
    if (filters?.activo !== undefined) params.set('activo', String(filters.activo))
    if (filters?.page) params.set('page', String(filters.page))
    if (filters?.page_size) params.set('page_size', String(filters.page_size))
    const data = await api.chatbot.get<any>(`/dataset?${params}`)
    return data.items || data.dataset || data
  },
  create: async (entry: Partial<DatasetEntry>): Promise<DatasetEntry> => {
    return api.chatbot.post<DatasetEntry>('/dataset', entry)
  },
  update: async (id: number, entry: Partial<DatasetEntry>): Promise<DatasetEntry> => {
    return api.chatbot.put<DatasetEntry>(`/dataset/${id}`, entry)
  },
  delete: async (id: number): Promise<void> => {
    await api.chatbot.delete(`/dataset/${id}`)
  },
  validate: async (id: number): Promise<DatasetEntry> => {
    return api.chatbot.put<DatasetEntry>(`/dataset/${id}/validar`, {})
  },
}
