'use client'

import { useQuery } from '@tanstack/react-query'
import { tutoriasService } from '@/services/api/tutorias.service'
import { useAuth } from './useAuth'

export function useBitacora() {
  const { estudianteId } = useAuth()

  return useQuery({
    queryKey: ['bitacora', estudianteId],
    queryFn: async () => {
      const data = await tutoriasService.listarBitacorasEstudiante(estudianteId!)
      return data.bitacoras || data || []
    },
    enabled: !!estudianteId,
    staleTime: 30 * 1000,
  })
}
