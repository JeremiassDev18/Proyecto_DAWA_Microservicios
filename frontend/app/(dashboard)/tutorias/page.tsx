'use client'

import { useState } from 'react'
import { Box, Button, Stack, TextField, Chip, Card, CardContent, Typography } from '@mui/material'
import { Add, CheckCircle, Cancel, School, Assignment, Person } from '@mui/icons-material'
import { PageContainer } from '@/components/ui/PageContainer'
import { DataTable } from '@/components/ui/DataTable'
import { FormModal } from '@/components/ui/FormModal'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { ErrorState } from '@/components/ui/ErrorState'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { useTutorias } from '@/hooks/useTutorias'
import { useAuth } from '@/hooks/useAuth'
import { useStudent } from '@/hooks/useStudent'
import { ROLES } from '@/config/permissions'

export default function TutoriasPage() {
  const { user, estudianteId, docenteId } = useAuth()
  const { materias } = useStudent()
  const isAdmin = user?.roles?.includes(ROLES.ADMIN)
  const isStudent = user?.roles?.includes(ROLES.ESTUDIANTE)
  const isTeacher = user?.roles?.includes(ROLES.PROFESOR)

  const [confirmOpen, setConfirmOpen] = useState(false)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [createForm, setCreateForm] = useState({ tema: '', asignatura_id: '', fecha_agendada: '' })
  const [asignarId, setAsignarId] = useState<number | null>(null)
  const [asignarDocente, setAsignarDocente] = useState('')

  const {
    solicitudes,
    isLoading,
    isError,
    refetch,
    confirmarTutoria,
    isConfirming,
    cancelarTutoria,
    isCancelling,
    crearSolicitud,
    isCreating,
    asignarTutor,
    isAssigning,
    atenderTutoria,
    isAttending,
  } = useTutorias(isStudent ? (estudianteId ?? undefined) : undefined, undefined, isTeacher ? (docenteId ?? undefined) : undefined)

  const handleConfirm = (id: number) => confirmarTutoria(id)

  const handleCancel = () => {
    if (selectedId) {
      cancelarTutoria({ id: selectedId, motivo: 'Cancelada desde la administración' })
      setConfirmOpen(false)
      setSelectedId(null)
    }
  }

  const handleCreate = () => {
    if (!estudianteId) return
    crearSolicitud({
      estudiante_id: estudianteId,
      tema: createForm.tema,
      asignatura_id: Number(createForm.asignatura_id) || undefined,
      fecha_agendada: createForm.fecha_agendada || undefined,
    })
    setCreateOpen(false)
    setCreateForm({ tema: '', asignatura_id: '', fecha_agendada: '' })
  }

  const handleAsignar = (id: number) => {
    const docenteIdNum = Number(asignarDocente)
    if (!docenteIdNum) return
    asignarTutor({ id, docenteId: docenteIdNum })
    setAsignarId(null)
    setAsignarDocente('')
  }

  const handleAtender = (id: number, asistio: boolean) => {
    atenderTutoria({ id, asistio })
  }

  const title = isTeacher ? 'Mis Tutorías (Docente)' : isStudent ? 'Mis Tutorías' : 'Tutorías'
  const subtitle = isTeacher
    ? 'Tutorías asignadas — marca la asistencia de los estudiantes'
    : isStudent
      ? 'Seguimiento de tus solicitudes de tutoría'
      : 'Administración de todas las solicitudes de tutoría'

  return (
    <Box>
      <PageContainer
        title={title}
        subtitle={subtitle}
        loading={isLoading}
        action={isStudent ? { label: 'Nueva solicitud', onClick: () => setCreateOpen(true), icon: <Add /> } : undefined}
      >
        {isStudent && (
          <Card variant="outlined" sx={{ mb: 3, borderRadius: 2, bgcolor: 'primary.main', color: 'white' }}>
            <CardContent sx={{ py: 2, '&:last-child': { pb: 2 } }}>
              <Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>
                <School sx={{ fontSize: 28, opacity: 0.8 }} />
                <Box>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Mis Solicitudes de Tutoría</Typography>
                  <Typography variant="caption" sx={{ opacity: 0.9 }}>
                    Estas son tus solicitudes registradas. Puedes crear una nueva solicitud desde el botón superior.
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        )}

        {isTeacher && docenteId && (
          <Card variant="outlined" sx={{ mb: 3, borderRadius: 2, bgcolor: 'secondary.main', color: 'white' }}>
            <CardContent sx={{ py: 2, '&:last-child': { pb: 2 } }}>
              <Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>
                <Assignment sx={{ fontSize: 28, opacity: 0.8 }} />
                <Box>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Tutorías Asignadas</Typography>
                  <Typography variant="caption" sx={{ opacity: 0.9 }}>
                    Marca si el estudiante asistió o no a cada tutoría.
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        )}

        {isError ? <ErrorState title="Error al cargar tutorías" message="No se pudieron cargar las solicitudes." onRetry={() => refetch()} /> : (
          <DataTable
            rows={solicitudes}
            columns={[
              { id: 'codigo', label: 'Código' },
              ...(isAdmin ? [{ id: 'estudiante_id', label: 'Estudiante ID' }] : []),
              { id: 'tema', label: 'Tema' },
              { id: 'estado', label: 'Estado', render: (row: any) => <StatusBadge status={row.estado} /> },
              { id: 'fecha_solicitud', label: 'Fecha' },
            ]}
            actions={(row: any) => (
              <Stack direction="row" spacing={1} sx={{ justifyContent: 'flex-end' }}>
                {/* Admin: confirmar / cancelar / asignar */}
                {isAdmin && (
                  <>
                    {row.estado === 'solicitada' && (
                      <Button size="small" variant="outlined" startIcon={<CheckCircle />} onClick={() => handleConfirm(row.id)} disabled={isConfirming}>Confirmar</Button>
                    )}
                    <Button size="small" color="error" variant="outlined" startIcon={<Cancel />} onClick={() => { setSelectedId(row.id); setConfirmOpen(true) }} disabled={isCancelling}>Cancelar</Button>
                    {asignarId === row.id ? (
                      <Stack direction="row" spacing={0.5}>
                        <TextField size="small" placeholder="Docente ID" value={asignarDocente} onChange={(e) => setAsignarDocente(e.target.value)} sx={{ width: 100 }} />
                        <Button size="small" variant="contained" onClick={() => handleAsignar(row.id)} disabled={isAssigning}>OK</Button>
                      </Stack>
                    ) : (
                      <Button size="small" variant="outlined" startIcon={<Person />} onClick={() => { setAsignarId(row.id); setAsignarDocente(String(row.docente_id || '')) }}>Asignar</Button>
                    )}
                  </>
                )}
                {/* Profesor: atender (asistió / no asistió) */}
                {isTeacher && row.docente_id === docenteId && row.estado !== 'atendida' && row.estado !== 'no_asistida' && row.estado !== 'cancelada' && (
                  <>
                    <Button size="small" color="success" variant="outlined" startIcon={<CheckCircle />} onClick={() => handleAtender(row.id, true)} disabled={isAttending}>Asistió</Button>
                    <Button size="small" color="error" variant="outlined" startIcon={<Cancel />} onClick={() => handleAtender(row.id, false)} disabled={isAttending}>No asistió</Button>
                  </>
                )}
                {/* Student: solo ver estado */}
                {isStudent && (
                  <Chip label={row.estado} size="small" color="info" variant="outlined" />
                )}
              </Stack>
            )}
            emptyTitle={isTeacher ? 'Sin tutorías asignadas' : 'Sin solicitudes'}
            emptyMessage={isTeacher ? 'No tienes tutorías asignadas actualmente.' : 'No hay solicitudes de tutoría para mostrar.'}
          />
        )}
      </PageContainer>

      {isStudent && estudianteId && (
        <FormModal
          open={createOpen}
          title="Nueva solicitud de tutoría"
          onCancel={() => { setCreateOpen(false); setCreateForm({ tema: '', asignatura_id: '', fecha_agendada: '' }) }}
          onSubmit={handleCreate}
          loading={isCreating}
          submitLabel="Crear solicitud"
        >
          <Stack spacing={2} sx={{ py: 1 }}>
            <TextField label="Tema / Descripción" value={createForm.tema} onChange={(e) => setCreateForm({ ...createForm, tema: e.target.value })} fullWidth multiline minRows={2} required />
            <TextField label="Asignatura ID" type="number" value={createForm.asignatura_id} onChange={(e) => setCreateForm({ ...createForm, asignatura_id: e.target.value })} fullWidth helperText={materias.length > 0 ? `Materias disponibles: ${materias.length}` : ''} />
            <TextField label="Fecha agendada" type="date" value={createForm.fecha_agendada} onChange={(e) => setCreateForm({ ...createForm, fecha_agendada: e.target.value })} fullWidth slotProps={{ inputLabel: { shrink: true } }} />
          </Stack>
        </FormModal>
      )}

      <ConfirmDialog
        open={confirmOpen}
        title="Cancelar tutoría"
        message="¿Deseas cancelar esta tutoría?"
        confirmLabel="Cancelar tutoría"
        onConfirm={handleCancel}
        onCancel={() => { setConfirmOpen(false); setSelectedId(null) }}
        severity="warning"
        loading={isCancelling}
      />
    </Box>
  )
}
