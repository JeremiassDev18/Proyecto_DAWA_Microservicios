export interface Conversation {
  id: number
  usuario_id: number
  nombre_cliente: string
  iniciado_en: string
  activa: boolean
  total_mensajes?: number
}

export interface Message {
  id: number
  conversacion_id: number
  rol: 'usuario' | 'bot'
  contenido: string
  tipo_resolucion?: string
  confianza?: number
  creado_en: string
}

export interface ChatRequest {
  usuario_id: number
  mensaje: string
  id_conversacion?: number
  nueva_conversacion?: boolean
  nombre?: string
  estudiante_id?: number
}

export interface ChatResponse {
  id_conversacion: number
  id_mensaje: number
  respuesta: string
  intencion: string
  confianza: number
  tipo_resolucion: string
}

export interface FeedbackRequest {
  id_mensaje: number
  util: boolean
}

export interface FeedbackResponse {
  id: number
  mensaje: string
  already_exists?: boolean
}
