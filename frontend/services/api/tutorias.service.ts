import { api } from '@/services/api'
import type { SolicitudTutoria, Notificacion } from '@/types/tutorias.types'

export const tutoriasService = {
  listarSolicitudes: async (estudianteId: number, periodoId?: number): Promise<SolicitudTutoria[]> => {
    const params: any = { estudiante_id: estudianteId }
    if (periodoId) params.periodo_id = periodoId
    const data = await api.tutorias.get<any>('/solicitudes', { params })
    return data.solicitudes || data
  },
  obtenerSolicitud: async (id: number): Promise<SolicitudTutoria> => {
    return api.tutorias.get<SolicitudTutoria>(`/solicitudes/${id}`)
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
  listarBitacorasEstudiante: async (estudianteId: number): Promise<{ cantidad: number; bitacoras: any[] }> => {
    return api.tutorias.get<any>(`/estudiantes/${estudianteId}/bitacoras`)
  },
  listarNotificaciones: async (destinatarioId: number, soloNoLeidas = false): Promise<Notificacion[]> => {
    const data = await api.tutorias.get<any>('/notificaciones', {
      params: { destinatario_id: destinatarioId, solo_no_leidas: soloNoLeidas },
    })
    return data.notificaciones || data
  },
}
