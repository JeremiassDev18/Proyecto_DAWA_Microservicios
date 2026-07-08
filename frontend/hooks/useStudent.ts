'use client'

import { useQuery } from '@tanstack/react-query'
import { studentService } from '@/services/api/student.service'
import { useAuth } from './useAuth'

export function useStudent() {
  const { estudianteId } = useAuth()

  const query = useQuery({
    queryKey: ['studentProfile', estudianteId],
    queryFn: () => studentService.getFullProfile(estudianteId!),
    enabled: !!estudianteId,
    staleTime: 60 * 1000,
  })

  return {
    ...query,
    estudiante: query.data?.estudiante,
    carrera: query.data?.carrera,
    materias: query.data?.materias ?? [],
    docentes: query.data?.docentes ?? [],
    tutoriasCount: query.data?.tutoriasCount ?? 0,
  }
}

export function useStudentMaterias() {
  const { estudianteId } = useAuth()

  return useQuery({
    queryKey: ['studentMaterias', estudianteId],
    queryFn: async () => {
      const { api } = await import('@/services/api')
      const data = await api.admin.get<any>(`/internos/estudiantes/${estudianteId}/materias`)
      return Array.isArray(data) ? data : (data.materias || [])
    },
    enabled: !!estudianteId,
    staleTime: 60 * 1000,
  })
}
