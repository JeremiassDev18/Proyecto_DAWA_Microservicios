export interface DashboardStats {
  total_facultades: number
  total_carreras: number
  total_asignaturas: number
  total_docentes: number
  total_estudiantes: number
  total_paralelos: number
  periodos_activos: number
  tutorias_activas?: number
  tutorias_pendientes?: number
  modelo_version?: string
  dataset_size?: number
}

export interface Facultad {
  id: number
  nombre: string
  codigo: string
  activo?: boolean
}

export interface Carrera {
  id: number
  nombre: string
  codigo: string
  facultad_id: number
  activo?: boolean
}

export interface Asignatura {
  id: number
  nombre: string
  codigo: string
  carrera_id: number
  activo?: boolean
}

export interface Periodo {
  id: number
  nombre: string
  fecha_inicio: string
  fecha_fin: string
  activo?: boolean
}

export interface Docente {
  id: number
  nombres: string
  apellidos: string
  email: string
  activo?: boolean
}

export interface Estudiante {
  id: number
  nombres: string
  apellidos: string
  email: string
  matricula: string
  carrera_id: number
  periodo_id: number
  activo?: boolean
}

export interface Role {
  id: number
  nombre_rol: string
  descripcion?: string
}

export interface Permission {
  id: number
  nombre: string
  descripcion?: string
}

export interface DatasetEntry {
  id: number
  texto_pregunta: string
  intencion: string
  respuesta: string
  activo: boolean
  validado: boolean
  creado_en?: string
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

export interface AuditLog {
  id: number
  usuario_id: number
  accion: string
  detalle?: string
  fecha: string
}
