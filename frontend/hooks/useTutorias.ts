'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tutoriasService } from '@/services/api/tutorias.service'
import { useToast } from './useToast'

export function useTutorias(estudianteId?: number, periodoId?: number, docenteId?: number) {
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const esModoAdmin = !estudianteId && !docenteId
  const esModoProfesor = !!docenteId

  const queryKey = esModoProfesor ? ['tutorias-docente', docenteId, periodoId]
    : esModoAdmin ? ['tutorias-admin', periodoId]
    : ['tutorias', estudianteId, periodoId]

  const queryFn = esModoProfesor
    ? () => tutoriasService.listarTutoriasPorDocente(docenteId!, periodoId).then(r => r.tutorias || [])
    : () => tutoriasService.listarSolicitudes(estudianteId, periodoId)

  const query = useQuery({
    queryKey,
    queryFn,
    enabled: !esModoAdmin || true,
  })

  // --- Sesiones abiertas (estudiantes buscan y se inscriben) ---
  const sesionesAbiertasQuery = useQuery({
    queryKey: ['sesiones-abiertas'],
    queryFn: () => tutoriasService.listarSesionesAbiertas(),
    enabled: !esModoProfesor,
  })

  // --- Inscripciones del estudiante ---
  const inscripcionesQuery = useQuery({
    queryKey: ['inscripciones-estudiante', estudianteId],
    queryFn: () => tutoriasService.listarInscripcionesEstudiante(estudianteId!),
    enabled: !!estudianteId,
  })

  const inscribirseMutation = useMutation({
    mutationFn: (sesionId: number) => {
      if (!estudianteId) throw new Error('No se encontró el ID del estudiante')
      return tutoriasService.inscribirseEnSesion(sesionId, estudianteId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sesiones-abiertas'] })
      queryClient.invalidateQueries({ queryKey })
      showToast('Te inscribiste correctamente en la sesión', 'success')
    },
    onError: (e: any) => showToast(e?.message || 'No se pudo inscribir', 'error'),
  })

  // --- Solicitudes pendientes (docente) ---
  const solicitudesPendientesQuery = useQuery({
    queryKey: ['solicitudes-pendientes-docente', docenteId],
    queryFn: () => tutoriasService.listarSolicitudesPendientes(docenteId!),
    enabled: esModoProfesor,
  })

  const aceptarSolicitudMutation = useMutation({
    mutationFn: (solicitudId: number) => tutoriasService.aceptarSolicitud(solicitudId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['solicitudes-pendientes-docente'] })
      queryClient.invalidateQueries({ queryKey: ['sesiones-docente'] })
      showToast('Solicitud aceptada — sesión creada', 'success')
    },
    onError: (e: any) => showToast(e?.message || 'No se pudo aceptar', 'error'),
  })

  const rechazarSolicitudMutation = useMutation({
    mutationFn: ({ solicitudId, motivo }: { solicitudId: number; motivo?: string }) =>
      tutoriasService.rechazarSolicitud(solicitudId, motivo),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['solicitudes-pendientes-docente'] })
      showToast('Solicitud rechazada', 'info')
    },
    onError: (e: any) => showToast(e?.message || 'No se pudo rechazar', 'error'),
  })

  // --- Sesiones del docente ---
  const sesionesDocenteQuery = useQuery({
    queryKey: ['sesiones-docente', docenteId],
    queryFn: () => tutoriasService.listarSesionesDocente(docenteId!),
    enabled: esModoProfesor,
  })

  const iniciarSesionMutation = useMutation({
    mutationFn: (sesionId: number) => tutoriasService.iniciarSesion(sesionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sesiones-docente'] })
      showToast('Sesión iniciada', 'success')
    },
    onError: (e: any) => showToast(e?.message || 'No se pudo iniciar la sesión', 'error'),
  })

  const finalizarSesionMutation = useMutation({
    mutationFn: (sesionId: number) => tutoriasService.finalizarSesion(sesionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sesiones-docente'] })
      showToast('Sesión finalizada', 'success')
    },
    onError: (e: any) => showToast(e?.message || 'No se pudo finalizar la sesión', 'error'),
  })

  // --- Legacy: confirmar, cancelar, asignar, atender ---
  const confirmarMutation = useMutation({
    mutationFn: (id: number) => tutoriasService.confirmarTutoria(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey })
      showToast('Tutoría confirmada correctamente', 'success')
    },
    onError: () => showToast('No se pudo confirmar la tutoría', 'error'),
  })

  const cancelarMutation = useMutation({
    mutationFn: ({ id, motivo }: { id: number; motivo?: string }) =>
      tutoriasService.cancelarTutoria(id, motivo),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey })
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
      queryClient.invalidateQueries({ queryKey })
      showToast('Solicitud creada correctamente', 'success')
    },
    onError: () => showToast('No se pudo crear la solicitud', 'error'),
  })

  const asignarMutation = useMutation({
    mutationFn: ({ id, docenteId: dId }: { id: number; docenteId: number }) =>
      tutoriasService.asignarTutoria(id, dId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey })
      showToast('Tutor asignado correctamente', 'success')
    },
    onError: () => showToast('No se pudo asignar el tutor', 'error'),
  })

  const atenderMutation = useMutation({
    mutationFn: ({ id, asistio, detalle }: { id: number; asistio: boolean; detalle?: string }) =>
      tutoriasService.atenderTutoria(id, asistio, detalle),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey })
      showToast('Tutoría atendida correctamente', 'success')
    },
    onError: () => showToast('No se pudo registrar la atención', 'error'),
  })

  // --- Admin: crear sesión ---
  const crearSesionAdminMutation = useMutation({
    mutationFn: (data: {
      docente_id: number; tema: string; estudiante_id?: number
      asignatura_id?: number; descripcion?: string; capacidad_maxima?: number
      fecha_agendada?: string
    }) => tutoriasService.crearSesionAdmin(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sesiones-abiertas'] })
      queryClient.invalidateQueries({ queryKey: ['sesiones-docente'] })
      showToast('Sesión de tutoría creada correctamente', 'success')
    },
    onError: (e: any) => showToast(e?.message || 'No se pudo crear la sesión', 'error'),
  })

  // --- Docente: bitácora y asistencia de sesión ---
  const bitacoraSesionMutation = useMutation({
    mutationFn: ({ sesionId, detalle, temas_detectados }: { sesionId: number; detalle: string; temas_detectados?: string }) =>
      tutoriasService.registrarBitacoraSesion(sesionId, { detalle, temas_detectados }),
    onSuccess: () => {
      showToast('Bitácora registrada correctamente', 'success')
    },
    onError: (e: any) => showToast(e?.message || 'No se pudo registrar la bitácora', 'error'),
  })

  const asistenciaSesionMutation = useMutation({
    mutationFn: ({ sesionId, estudianteId, asistio }: { sesionId: number; estudianteId: number; asistio: boolean }) =>
      tutoriasService.registrarAsistenciaSesion(sesionId, estudianteId, asistio),
    onSuccess: () => {
      showToast('Asistencia registrada', 'success')
    },
    onError: (e: any) => showToast(e?.message || 'No se pudo registrar la asistencia', 'error'),
  })

  return {
    solicitudes: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,

    // Sesiones abiertas (estudiantes)
    sesionesAbiertas: sesionesAbiertasQuery.data ?? [],
    isLoadingSesiones: sesionesAbiertasQuery.isLoading,
    inscribirseEnSesion: inscribirseMutation.mutate,
    isInscrebiendo: inscribirseMutation.isPending,

    // Inscripciones del estudiante
    inscripcionesEstudiante: inscripcionesQuery.data ?? [],
    isLoadingInscripciones: inscripcionesQuery.isLoading,

    // Solicitudes pendientes (docente)
    solicitudesPendientes: solicitudesPendientesQuery.data ?? [],
    isLoadingPendientes: solicitudesPendientesQuery.isLoading,
    aceptarSolicitud: aceptarSolicitudMutation.mutate,
    isAceptando: aceptarSolicitudMutation.isPending,
    rechazarSolicitud: rechazarSolicitudMutation.mutate,
    isRechazando: rechazarSolicitudMutation.isPending,

    // Sesiones del docente
    sesionesDocente: sesionesDocenteQuery.data ?? [],
    isLoadingSesionesDocente: sesionesDocenteQuery.isLoading,
    iniciarSesion: iniciarSesionMutation.mutate,
    isIniciando: iniciarSesionMutation.isPending,
    finalizarSesion: finalizarSesionMutation.mutate,
    isFinalizando: finalizarSesionMutation.isPending,

    // Legacy
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

    // Admin: crear sesión
    crearSesionAdmin: crearSesionAdminMutation.mutate,
    isCreandoSesion: crearSesionAdminMutation.isPending,

    // Docente: bitácora y asistencia
    registrarBitacoraSesion: bitacoraSesionMutation.mutate,
    isRegistrandoBitacora: bitacoraSesionMutation.isPending,
    registrarAsistenciaSesion: asistenciaSesionMutation.mutate,
    isRegistrandoAsistencia: asistenciaSesionMutation.isPending,
  }
}
