import { api } from '@/services/api'
import type { SolicitudTutoria, SesionTutoria } from '@/types/tutorias.types'

export const tutoriasService = {
  // --- Solicitudes ---
  listarSolicitudes: async (estudianteId?: number, periodoId?: number): Promise<SolicitudTutoria[]> => {
    const params: Record<string, any> = {}
    if (estudianteId != null) params.estudiante_id = estudianteId
    if (periodoId) params.periodo_id = periodoId
    const data = await api.tutorias.get<any>('/solicitudes', { params })
    return data.solicitudes || data
  },
  crearSolicitud: async (data: {
    estudiante_id: number; asignatura_id?: number; periodo_id?: number
    tema: string; fecha_solicitud?: string; fecha_agendada?: string
  }): Promise<SolicitudTutoria> => {
    return api.tutorias.post<SolicitudTutoria>('/solicitudes', data)
  },
  asignarTutoria: async (id: number, docenteId: number, usuarioId?: number): Promise<any> => {
    return api.tutorias.put(`/solicitudes/${id}/asignar`, { docente_id: docenteId, usuario_id: usuarioId })
  },
  confirmarTutoria: async (id: number, usuarioId?: number): Promise<SolicitudTutoria> => {
    return api.tutorias.put<SolicitudTutoria>(`/solicitudes/${id}/confirmar`, { usuario_id: usuarioId })
  },
  cancelarTutoria: async (id: number, motivo?: string, usuarioId?: number): Promise<SolicitudTutoria> => {
    return api.tutorias.put<SolicitudTutoria>(`/solicitudes/${id}/cancelar`, { motivo, usuario_id: usuarioId })
  },
  atenderTutoria: async (id: number, asistio: boolean, detalle?: string): Promise<any> => {
    return api.tutorias.put(`/solicitudes/${id}/atender`, { asistio, detalle })
  },

  // --- Sesiones ---
  listarSesionesAbiertas: async (materiaNombre?: string, tipo?: string): Promise<SesionTutoria[]> => {
    const params: Record<string, any> = {}
    if (materiaNombre) params.materia_nombre = materiaNombre
    if (tipo) params.tipo = tipo
    const data = await api.tutorias.get<any>('/sesiones/abiertas', { params })
    return data.sesiones || []
  },
  inscribirseEnSesion: async (sesionId: number, estudianteId: number): Promise<any> => {
    return api.tutorias.post(`/sesiones/${sesionId}/inscribir`, { estudiante_id: estudianteId })
  },
  listarInscripcionesEstudiante: async (estudianteId: number): Promise<any[]> => {
    const data = await api.tutorias.get<any>(`/estudiantes/${estudianteId}/inscripciones`)
    return data.inscripciones || []
  },
  listarSesionesDocente: async (docenteId: number): Promise<SesionTutoria[]> => {
    const data = await api.tutorias.get<any>('/sesiones/docente', { params: { docente_id: docenteId } })
    return data.sesiones || []
  },
  listarSolicitudesPendientes: async (docenteId: number): Promise<SolicitudTutoria[]> => {
    const data = await api.tutorias.get<any>('/sesiones/solicitudes-pendientes', { params: { docente_id: docenteId } })
    return data.solicitudes || []
  },
  aceptarSolicitud: async (solicitudId: number, docenteId: number): Promise<SesionTutoria> => {
    return api.tutorias.put<SesionTutoria>(`/sesiones/aceptar/${solicitudId}`, { docente_id: docenteId })
  },
  rechazarSolicitud: async (solicitudId: number, docenteId: number, motivo?: string): Promise<any> => {
    return api.tutorias.put(`/sesiones/rechazar/${solicitudId}`, { docente_id: docenteId, motivo })
  },
  iniciarSesion: async (sesionId: number): Promise<SesionTutoria> => {
    return api.tutorias.put<SesionTutoria>(`/sesiones/${sesionId}/iniciar`, {})
  },
  finalizarSesion: async (sesionId: number): Promise<SesionTutoria> => {
    return api.tutorias.put<SesionTutoria>(`/sesiones/${sesionId}/finalizar`, {})
  },

  // --- Notificaciones ---
  listarBitacorasEstudiante: async (estudianteId: number): Promise<{ cantidad: number; bitacoras: any[] }> => {
    return api.tutorias.get<any>(`/estudiantes/${estudianteId}/bitacoras`)
  },
  listarTutoriasPorDocente: async (docenteId: number, periodoId?: number): Promise<{ cantidad: number; tutorias: any[] }> => {
    const params: any = { docente_id: docenteId }
    if (periodoId) params.periodo_id = periodoId
    return api.tutorias.get<any>('/reportes/por-docente', { params })
  },

  // --- Admin: crear sesión directamente ---
  crearSesionAdmin: async (data: {
    docente_id: number; tema: string; estudiante_id?: number
    asignatura_id?: number; descripcion?: string; capacidad_maxima?: number
    fecha_agendada?: string
  }): Promise<SesionTutoria> => {
    return api.tutorias.post<SesionTutoria>('/sesiones/crear', data)
  },

  // --- Docente: bitácora y asistencia de sesión ---
  registrarBitacoraSesion: async (sesionId: number, data: {
    detalle: string; temas_detectados?: string
  }): Promise<any> => {
    return api.tutorias.post(`/sesiones/${sesionId}/bitacora`, data)
  },
  registrarAsistenciaSesion: async (sesionId: number, estudianteId: number, asistio: boolean): Promise<any> => {
    return api.tutorias.post(`/sesiones/${sesionId}/asistencia`, { estudiante_id: estudianteId, asistio })
  },
  listarInscritosSesion: async (sesionId: number): Promise<any[]> => {
    const data = await api.tutorias.get<any>(`/sesiones/${sesionId}/inscritos`)
    return data.inscritos || []
  },
}
