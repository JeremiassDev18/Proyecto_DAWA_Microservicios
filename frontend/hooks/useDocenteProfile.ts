'use client'

import { useQuery } from '@tanstack/react-query'
import { adminService } from '@/services/api/admin.service'

export function useDocenteProfile(docenteId: number | null | undefined) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['docente-profile', docenteId],
    queryFn: async () => {
      if (!docenteId) return null
      const docentes = await adminService.getDocentes()
      return docentes.find((d) => d.id === docenteId) || null
    },
    enabled: !!docenteId,
    staleTime: 60_000,
  })

  return {
    docente: data ?? null,
    isLoading,
    isError,
  }
}
