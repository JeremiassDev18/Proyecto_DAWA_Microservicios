export interface SolicitudTutoria {
  id: number
  codigo: string
  estudiante_id: number
  docente_id: number | null
  asignatura_id: number | null
  periodo_id: number | null
  sesion_id: number | null
  tema: string
  estado: string
  motivo_rechazo: string | null
  fecha_solicitud: string | null
  fecha_agendada: string | null
  fecha_actualizacion: string | null
  motivo_cancelacion: string | null
  estudiante_nombre?: string
  materia_nombre?: string
}

export interface SesionTutoria {
  id: number
  codigo: string
  docente_id: number
  docente_nombre: string
  materia_id: number | null
  materia_nombre: string
  tema: string
  descripcion: string | null
  estado: string
  capacidad_maxima: number | null
  inscritos_count: number
  fecha_inicio: string | null
  fecha_fin: string | null
  fecha_creacion: string | null
}

export interface InscripcionSesion {
  id: number
  sesion_id: number
  estudiante_id: number
  estudiante_nombre: string
  estado: string
  fecha_inscripcion: string | null
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
