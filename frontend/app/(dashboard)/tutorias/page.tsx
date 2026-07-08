'use client'

import { useState, useMemo } from 'react'
import { Box, Button, Stack, TextField, Chip, Card, CardContent, Typography } from '@mui/material'
import { Add, Search, CheckCircle, Cancel, School } from '@mui/icons-material'
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
  const { user, estudianteId } = useAuth()
  const { materias } = useStudent()
  const isAdmin = user?.roles?.includes(ROLES.ADMIN)
  const isStudent = user?.roles?.includes(ROLES.ESTUDIANTE)

  const [estudianteIdInput, setEstudianteIdInput] = useState(isStudent && estudianteId ? String(estudianteId) : '')
  const [periodoId, setPeriodoId] = useState('')
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [createForm, setCreateForm] = useState({ tema: '', asignatura_id: '', fecha_agendada: '' })

  const effectiveEstudianteId = isStudent && estudianteId ? estudianteId : Number(estudianteIdInput || 0)

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
  } = useTutorias(effectiveEstudianteId, Number(periodoId || 0))

  const handleConfirm = (id: number) => confirmarTutoria(id)

  const handleCancel = () => {
    if (selectedId) {
      cancelarTutoria({ id: selectedId, motivo: 'Cancelada desde la administración' })
      setConfirmOpen(false)
      setSelectedId(null)
    }
  }

  const handleCreate = () => {
    crearSolicitud({
      estudiante_id: effectiveEstudianteId,
      tema: createForm.tema,
      asignatura_id: Number(createForm.asignatura_id) || undefined,
      fecha_agendada: createForm.fecha_agendada || undefined,
    })
    setCreateOpen(false)
    setCreateForm({ tema: '', asignatura_id: '', fecha_agendada: '' })
  }

  return (
    <Box>
      <PageContainer
        title="Tutorías"
        subtitle="Seguimiento de solicitudes de tutorías y estados"
        loading={isLoading}
        action={isStudent ? { label: 'Nueva solicitud', onClick: () => setCreateOpen(true), icon: <Add /> } : undefined}
      >
        {isStudent ? (
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
        ) : (
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mb: 3 }}>
            <TextField size="small" label="Estudiante ID" value={estudianteIdInput} onChange={(event) => setEstudianteIdInput(event.target.value)} sx={{ minWidth: 220 }} />
            <TextField size="small" label="Periodo ID" value={periodoId} onChange={(event) => setPeriodoId(event.target.value)} sx={{ minWidth: 220 }} />
            <Button variant="contained" startIcon={<Search />} onClick={() => refetch()}>Buscar</Button>
          </Stack>
        )}

        {isError ? <ErrorState title="Error al cargar tutorías" message="No se pudieron cargar las solicitudes." onRetry={() => refetch()} /> : (
          <DataTable
            rows={solicitudes}
            columns={[
              { id: 'codigo', label: 'Código' },
              { id: 'tema', label: 'Tema' },
              { id: 'estado', label: 'Estado', render: (row: any) => <StatusBadge status={row.estado} /> },
              { id: 'fecha_solicitud', label: 'Fecha' },
            ]}
            actions={(row: any) => (
              <Stack direction="row" spacing={1} sx={{ justifyContent: 'flex-end' }}>
                {isAdmin && (
                  <>
                    <Button size="small" variant="outlined" startIcon={<CheckCircle />} onClick={() => handleConfirm(row.id)} disabled={isConfirming}>Confirmar</Button>
                    <Button size="small" color="error" variant="outlined" startIcon={<Cancel />} onClick={() => { setSelectedId(row.id); setConfirmOpen(true) }} disabled={isCancelling}>Cancelar</Button>
                  </>
                )}
                {!isAdmin && (
                  <Chip label={row.estado} size="small" color="info" variant="outlined" />
                )}
              </Stack>
            )}
            emptyTitle="Sin solicitudes"
            emptyMessage="No hay solicitudes de tutoría para este estudiante."
          />
        )}
      </PageContainer>

      {isStudent && (
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
