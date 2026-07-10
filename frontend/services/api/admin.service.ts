import { api } from '@/services/api'
import type { DashboardStats, Facultad, Carrera, Docente, Estudiante } from '@/types/admin.types'

export const adminService = {
  getDashboardStats: async (): Promise<DashboardStats> => {
    return api.admin.get<DashboardStats>('/dashboard/')
  },

  getFacultades: async (): Promise<Facultad[]> => {
    const data = await api.admin.get<any>('/facultades/')
    return data.facultades || data
  },
  getFacultad: async (id: number): Promise<Facultad> => {
    return api.admin.get<Facultad>(`/facultades/${id}`)
  },
  createFacultad: async (data: Partial<Facultad>): Promise<Facultad> => {
    return api.admin.post<Facultad>('/facultades/', data)
  },
  updateFacultad: async (id: number, data: Partial<Facultad>): Promise<Facultad> => {
    return api.admin.put<Facultad>(`/facultades/${id}`, data)
  },
  deleteFacultad: async (id: number): Promise<void> => {
    await api.admin.delete(`/facultades/${id}`)
  },

  getCarreras: async (): Promise<Carrera[]> => {
    const data = await api.admin.get<any>('/carreras/')
    return data.carreras || data
  },
  getCarrera: async (id: number): Promise<Carrera> => {
    return api.admin.get<Carrera>(`/carreras/${id}`)
  },
  createCarrera: async (data: Partial<Carrera>): Promise<Carrera> => {
    const response = await api.admin.post<any>('/carreras/', data)
    return response.carrera || response
  },
  updateCarrera: async (id: number, data: Partial<Carrera>): Promise<Carrera> => {
    const response = await api.admin.put<any>(`/carreras/${id}`, data)
    return response.carrera || response
  },
  deleteCarrera: async (id: number): Promise<void> => {
    await api.admin.delete(`/carreras/${id}`)
  },

  getDocentes: async (): Promise<Docente[]> => {
    const data = await api.admin.get<any>('/docentes/')
    const items = data.docentes || data
    if (!Array.isArray(items)) return []
    return items.map((d: any) => ({
      ...d,
      email: d.email || d.correo,
    }))
  },
  getDocenteByEmail: async (email: string): Promise<Docente | null> => {
    const docentes = await adminService.getDocentes()
    return docentes.find((d: any) => (d.correo || d.email) === email) || null
  },
  getDocente: async (id: number): Promise<Docente> => {
    return api.admin.get<Docente>(`/docentes/${id}`)
  },
  createDocente: async (data: Partial<Docente>): Promise<Docente> => {
    const response = await api.admin.post<any>('/docentes/', data)
    return response.docente || response
  },
  updateDocente: async (id: number, data: Partial<Docente>): Promise<Docente> => {
    const response = await api.admin.put<any>(`/docentes/${id}`, data)
    return response.docente || response
  },
  deleteDocente: async (id: number): Promise<void> => {
    await api.admin.delete(`/docentes/${id}`)
  },

  getEstudiantes: async (): Promise<Estudiante[]> => {
    const data = await api.admin.get<any>('/estudiantes/')
    const items = data.estudiantes || data
    if (!Array.isArray(items)) return []
    return items.map((e: any) => ({
      id: e.id,
      nombres: e.nombres,
      apellidos: e.apellidos,
      email: e.email || e.correo || '',
      matricula: e.matricula || '',
      carrera_id: e.carrera_id,
      periodo_id: e.periodo_id,
      activo: e.estado ?? e.activo ?? true,
    }))
  },
  getEstudianteByEmail: async (email: string): Promise<Estudiante | null> => {
    const estudiantes = await adminService.getEstudiantes()
    return estudiantes.find((e) => e.email === email) || null
  },
  getEstudiante: async (id: number): Promise<Estudiante> => {
    return api.admin.get<Estudiante>(`/estudiantes/${id}`)
  },
  createEstudiante: async (data: Partial<Estudiante>): Promise<Estudiante> => {
    const response = await api.admin.post<any>('/estudiantes/', data)
    return response.estudiante || response
  },
  updateEstudiante: async (id: number, data: Partial<Estudiante>): Promise<Estudiante> => {
    const response = await api.admin.put<any>(`/estudiantes/${id}`, data)
    return response.estudiante || response
  },
  deleteEstudiante: async (id: number): Promise<void> => {
    await api.admin.delete(`/estudiantes/${id}`)
  },
}
