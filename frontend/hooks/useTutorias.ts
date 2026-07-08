'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tutoriasService } from '@/services/api/tutorias.service'
import { useToast } from './useToast'

export function useTutorias(estudianteId?: number, periodoId?: number) {
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const query = useQuery({
    queryKey: ['tutorias', estudianteId, periodoId],
    queryFn: () => tutoriasService.listarSolicitudes(estudianteId ?? 0, periodoId),
    enabled: !!estudianteId,
  })

  const confirmarMutation = useMutation({
    mutationFn: (id: number) => tutoriasService.confirmarTutoria(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tutorias'] })
      showToast('Tutoría confirmada correctamente', 'success')
    },
    onError: () => showToast('No se pudo confirmar la tutoría', 'error'),
  })

  const cancelarMutation = useMutation({
    mutationFn: ({ id, motivo }: { id: number; motivo?: string }) =>
      tutoriasService.cancelarTutoria(id, motivo),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tutorias'] })
      showToast('Tutoría cancelada', 'info')
    },
    onError: () => showToast('No se pudo cancelar la tutoría', 'error'),
  })

  const crearMutation = useMutation({
    mutationFn: (data: {
      estudiante_id: number; asignatura_id?: number; periodo_id?: number
      tema: string; fecha_solicitud?: string; fecha_agendada?: string
    }) => tutoriasService.crearSolicitud(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tutorias'] })
      showToast('Solicitud creada correctamente', 'success')
    },
    onError: () => showToast('No se pudo crear la solicitud', 'error'),
  })

  const asignarMutation = useMutation({
    mutationFn: ({ id, docenteId }: { id: number; docenteId: number }) =>
      tutoriasService.asignarTutoria(id, docenteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tutorias'] })
      showToast('Tutor asignado correctamente', 'success')
    },
    onError: () => showToast('No se pudo asignar el tutor', 'error'),
  })

  const atenderMutation = useMutation({
    mutationFn: ({ id, asistio, detalle }: { id: number; asistio: boolean; detalle?: string }) =>
      tutoriasService.atenderTutoria(id, asistio, detalle),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tutorias'] })
      showToast('Tutoría atendida correctamente', 'success')
    },
    onError: () => showToast('No se pudo registrar la atención', 'error'),
  })

  return {
    solicitudes: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    confirmarTutoria: confirmarMutation.mutate,
    isConfirming: confirmarMutation.isPending,
    cancelarTutoria: cancelarMutation.mutate,
    isCancelling: cancelarMutation.isPending,
    crearSolicitud: crearMutation.mutate,
    isCreating: crearMutation.isPending,
    asignarTutor: asignarMutation.mutate,
    isAssigning: asignarMutation.isPending,
    atenderTutoria: atenderMutation.mutate,
    isAttending: atenderMutation.isPending,
  }
}
