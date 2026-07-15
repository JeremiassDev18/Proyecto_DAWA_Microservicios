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


