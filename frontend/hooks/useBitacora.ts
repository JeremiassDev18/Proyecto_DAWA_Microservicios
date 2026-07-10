'use client'

import { useQuery } from '@tanstack/react-query'
import { tutoriasService } from '@/services/api/tutorias.service'
import { useAuth } from './useAuth'

export function useBitacora() {
  const { estudianteId } = useAuth()

  const result = useQuery({
    queryKey: ['bitacora', estudianteId],
    queryFn: async () => {
      const data = await tutoriasService.listarBitacorasEstudiante(estudianteId!)
      return data.bitacoras || data || []
    },
    enabled: !!estudianteId,
    staleTime: 30 * 1000,
  })

  return {
    ...result,
    data: result.data ?? [],
    isError: !!estudianteId ? result.isError : false,
  }
}
