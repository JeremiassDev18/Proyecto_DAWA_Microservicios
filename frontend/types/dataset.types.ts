export interface DatasetEntry {
  id: number
  texto_pregunta: string
  intencion: string
  respuesta: string
  activo: boolean
  validado: boolean
  creado_en?: string
}

export interface DatasetFilters {
  query?: string
  intencion?: string
  activo?: boolean
  page?: number
  page_size?: number
}

export interface TrainingStatus {
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress?: number
  message?: string
}

export interface PendingQuery {
  id: number
  pregunta: string
  respuesta_dada?: string
  confianza?: number
  intencion_detectada?: string
  resuelta: boolean
  creado_en?: string
}

export interface Document {
  id: number
  nombre: string
  categoria: string
  contenido?: string
  activo: boolean
  creado_en?: string
}

export interface ModelInfo {
  id: number
  version: string
  accuracy?: number
  activo: boolean
  creado_en?: string
}

export interface UsageMetrics {
  total_conversaciones: number
  total_mensajes: number
  resoluciones_exitosas: number
  escalaciones: number
  confianza_promedio: number
}
