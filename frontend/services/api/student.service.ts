import { api } from '@/services/api'
import type { Carrera, Estudiante } from '@/types/admin.types'
import { adminService } from './admin.service'

export interface StudentFullData {
  estudiante: Estudiante
  carrera: Carrera | null
  materias: any[]
  docentes: any[]
  tutoriasCount: number
}

export const studentService = {
  getFullProfile: async (estudianteId: number): Promise<StudentFullData> => {
    const estudiante = await adminService.getEstudiante(estudianteId)
    let carrera: Carrera | null = null
    try {
      carrera = await adminService.getCarrera(estudiante.carrera_id)
    } catch { /* ignore */ }

    let materias: any[] = []
    try {
      const materiasData = await api.admin.get<any>(`/internos/estudiantes/${estudianteId}/materias`)
      materias = Array.isArray(materiasData) ? materiasData : (materiasData.materias || [])
    } catch { /* ignore */ }

    let docentes: any[] = []
    try {
      const docentesData = await api.admin.get<any>(`/internos/estudiantes/${estudianteId}/docentes`)
      docentes = Array.isArray(docentesData) ? docentesData : (docentesData.docentes || [])
    } catch { /* ignore */ }

    let tutoriasCount = 0
    try {
      const tutoriasData = await api.tutorias.get<any>(`/solicitudes`, { params: { estudiante_id: estudianteId } })
      tutoriasCount = tutoriasData.cantidad || (tutoriasData.solicitudes?.length || 0)
    } catch { /* ignore */ }

    return { estudiante, carrera, materias, docentes, tutoriasCount }
  },
}
