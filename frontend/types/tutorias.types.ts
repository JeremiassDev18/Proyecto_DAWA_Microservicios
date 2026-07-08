export interface SolicitudTutoria {
  id: number
  codigo: string
  estudiante_id: number
  docente_id: number | null
  asignatura_id: number | null
  periodo_id: number | null
  tema: string
  estado: string
  fecha_solicitud: string | null
  fecha_agendada: string | null
  fecha_actualizacion: string | null
  motivo_cancelacion: string | null
}

export interface Bitacora {
  id: number
  observaciones: string | null
  asistio: boolean | null
  temas_detectados: string | null
  fecha_registro: string | null
}

export interface Notificacion {
  id: number
  solicitud_id: number
  destinatario_id: number
  destinatario_rol: string
  tipo: string
  mensaje: string
  leida: boolean
  fecha_creacion: string | null
  fecha_lectura: string | null
}
