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
  titulo: string
  contenido?: string
  tags?: string[]
  activo: boolean
  fecha_actualizacion?: string
}

export interface UsageMetrics {
  total_conversaciones: number
  total_mensajes: number
  resoluciones_exitosas: number
  escalaciones: number
  confianza_promedio: number
}
