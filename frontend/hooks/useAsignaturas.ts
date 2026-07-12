'use client'

import { useQuery } from '@tanstack/react-query'
import { adminService, type Asignatura } from '@/services/api/admin.service'

export function useAsignaturas() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['asignaturas'],
    queryFn: () => adminService.getAsignaturas(),
    staleTime: 60_000,
  })

  return {
    asignaturas: data ?? [],
    isLoading,
    isError,
  }
}
