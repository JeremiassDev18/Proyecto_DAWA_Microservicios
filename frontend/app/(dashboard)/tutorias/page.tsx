'use client'

import { useState } from 'react'
import { Box, Button, Stack, TextField, Chip, Card, CardContent, Typography, Tabs, Tab, Select, MenuItem, FormControl, InputLabel, FormControlLabel, Switch } from '@mui/material'
import { Add, CheckCircle, Cancel, School, Group, PlayArrow, Stop, PersonSearch, Search, EditNote, HowToReg } from '@mui/icons-material'
import { PageContainer } from '@/components/ui/PageContainer'
import { DataTable } from '@/components/ui/DataTable'
import { FormModal } from '@/components/ui/FormModal'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { ErrorState } from '@/components/ui/ErrorState'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { useTutorias } from '@/hooks/useTutorias'
import { useAuth } from '@/hooks/useAuth'
import { tutoriasService } from '@/services/api/tutorias.service'

const estadoColor = (e: string) => {
  if (e === 'abierta' || e === 'en_curso') return 'success'
  if (e === 'solicitada' || e === 'pendiente') return 'warning'
  if (e === 'aceptada' || e === 'inscrita') return 'info'
  if (e === 'rechazada' || e === 'cancelada' || e === 'cancelada' as any) return 'error'
  return 'default'
}

export default function TutoriasPage() {
  const { user, estudianteId, docenteId } = useAuth()
  const isAdmin = user?.roles?.includes('admin')
  const isStudent = user?.roles?.includes('estudiante')
  const isTeacher = user?.roles?.includes('docente')

  const [tab, setTab] = useState(0)
  const [busqueda, setBusqueda] = useState('')
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [createForm, setCreateForm] = useState({ tema: '', asignatura_id: '', fecha_agendada: '' })
  const [rechazoMotivo, setRechazoMotivo] = useState('')

  // Admin: crear sesión
  const [adminCreateOpen, setAdminCreateOpen] = useState(false)
  const [adminForm, setAdminForm] = useState({
    docente_id: '', tema: '', asignatura_id: '', descripcion: '', capacidad_maxima: '20', fecha_agendada: '',
  })

  // Docente: bitácora
  const [bitacoraOpen, setBitacoraOpen] = useState(false)
  const [bitacoraForm, setBitacoraForm] = useState({ sesionId: 0, detalle: '', temas_detectados: '' })

  // Docente: asistencia
  const [asistenciaOpen, setAsistenciaOpen] = useState(false)
  const [asistenciaSesionId, setAsistenciaSesionId] = useState(0)
  const [inscritos, setInscritos] = useState<any[]>([])
  const [asistenciaMap, setAsistenciaMap] = useState<Record<number, boolean>>({})

  const {
    sesionesAbiertas, isLoadingSesiones, inscribirseEnSesion, isInscrebiendo,
    solicitudes, isLoading: isLoadingSolicitudes, isError: isErrorSolicitudes,
    crearSolicitud, isCreating,
    solicitudesPendientes, isLoadingPendientes,
    aceptarSolicitud, isAceptando,
    rechazarSolicitud, isRechazando,
    sesionesDocente, isLoadingSesionesDocente,
    iniciarSesion, isIniciando,
    finalizarSesion, isFinalizando,
    cancelarTutoria, isCancelling, refetch,
    crearSesionAdmin, isCreandoSesion,
    registrarBitacoraSesion, isRegistrandoBitacora,
    registrarAsistenciaSesion, isRegistrandoAsistencia,
  } = useTutorias(
    isStudent ? (estudianteId ?? undefined) : undefined,
    undefined,
    isTeacher ? (docenteId ?? undefined) : undefined,
  )

  const sesionesFiltradas = sesionesAbiertas.filter((s: any) =>
    !busqueda ||
    s.materia_nombre?.toLowerCase().includes(busqueda.toLowerCase()) ||
    s.tema?.toLowerCase().includes(busqueda.toLowerCase()) ||
    s.docente_nombre?.toLowerCase().includes(busqueda.toLowerCase())
  )

  const handleInscribirse = (sesionId: number) => inscribirseEnSesion(sesionId)

  const handleAceptar = (solicitudId: number) => aceptarSolicitud(solicitudId)

  const handleRechazar = (solicitudId: number) => {
    rechazarSolicitud({ solicitudId, motivo: rechazoMotivo || 'Sin motivo especificado' })
    setConfirmOpen(false)
    setSelectedId(null)
    setRechazoMotivo('')
  }

  const handleCrear = () => {
    if (!estudianteId || !createForm.tema) return
    crearSolicitud({
      estudiante_id: estudianteId,
      tema: createForm.tema,
      asignatura_id: Number(createForm.asignatura_id) || undefined,
      fecha_agendada: createForm.fecha_agendada || undefined,
    })
    setCreateOpen(false)
    setCreateForm({ tema: '', asignatura_id: '', fecha_agendada: '' })
  }

  const handleCancelar = () => {
    if (selectedId) {
      cancelarTutoria({ id: selectedId, motivo: 'Cancelada por el usuario' })
      setConfirmOpen(false)
      setSelectedId(null)
    }
  }

  const handleAdminCrear = () => {
    if (!adminForm.docente_id || !adminForm.tema) return
    crearSesionAdmin({
      docente_id: Number(adminForm.docente_id),
      tema: adminForm.tema,
      asignatura_id: Number(adminForm.asignatura_id) || undefined,
      descripcion: adminForm.descripcion || undefined,
      capacidad_maxima: Number(adminForm.capacidad_maxima) || 20,
      fecha_agendada: adminForm.fecha_agendada || undefined,
    })
    setAdminCreateOpen(false)
    setAdminForm({ docente_id: '', tema: '', asignatura_id: '', descripcion: '', capacidad_maxima: '20', fecha_agendada: '' })
  }

  const handleBitacora = () => {
    if (!bitacoraForm.sesionId || !bitacoraForm.detalle) return
    registrarBitacoraSesion({
      sesionId: bitacoraForm.sesionId,
      detalle: bitacoraForm.detalle,
      temas_detectados: bitacoraForm.temas_detectados || undefined,
    })
    setBitacoraOpen(false)
    setBitacoraForm({ sesionId: 0, detalle: '', temas_detectados: '' })
  }

  const handleAsistenciaOpen = async (sesionId: number) => {
    setAsistenciaSesionId(sesionId)
    try {
      const inscritosData = await tutoriasService.listarInscritosSesion(sesionId)
      setInscritos(inscritosData)
      const map: Record<number, boolean> = {}
      inscritosData.forEach((i: any) => { map[i.estudiante_id] = i.asistio ?? true })
      setAsistenciaMap(map)
    } catch {
      setInscritos([])
    }
    setAsistenciaOpen(true)
  }

  const handleAsistenciaGuardar = () => {
    const promises = Object.entries(asistenciaMap).map(([estId, asistio]) =>
      registrarAsistenciaSesion({ sesionId: asistenciaSesionId, estudianteId: Number(estId), asistio })
    )
    Promise.all(promises).then(() => {
      setAsistenciaOpen(false)
      setInscritos([])
      setAsistenciaMap({})
    })
  }

  return (
    <Box>
      <PageContainer
        title={isTeacher ? 'Sesiones y Solicitudes' : isStudent ? 'Tutorías Grupales' : 'Gestión de Tutorías'}
        subtitle={isTeacher
          ? 'Acepta solicitudes y gestiona tus sesiones grupales'
          : isStudent
            ? 'Busca sesiones abiertas o solicita una nueva tutoría'
            : 'Administra todas las tutorías y sesiones del sistema'}
        action={isStudent
          ? { label: 'Nueva solicitud', onClick: () => setCreateOpen(true), icon: <Add /> }
          : isAdmin
            ? { label: 'Crear sesión', onClick: () => setAdminCreateOpen(true), icon: <Add /> }
            : undefined}
      >
        {/* Tabs */}
        <Tabs
          value={tab}
          onChange={(_, v) => setTab(v)}
          sx={{ mb: 3, borderBottom: 1, borderColor: 'divider' }}
        >
          {isStudent && <Tab label="Sesiones abiertas" icon={<Group />} />}
          {isStudent && <Tab label="Mis solicitudes" icon={<School />} />}
          {isTeacher && <Tab label="Solicitudes pendientes" icon={<PersonSearch />} />}
          {isTeacher && <Tab label="Mis sesiones" icon={<PlayArrow />} />}
          {isAdmin && <Tab label="Todas las sesiones" icon={<Group />} />}
        </Tabs>

        {/* ===== ESTUDIANTE: Sesiones abiertas ===== */}
        {isStudent && tab === 0 && (
          <Box>
            <Card variant="outlined" sx={{ mb: 3, borderRadius: 2, bgcolor: '#e3f2fd' }}>
              <CardContent sx={{ py: 2, '&:last-child': { pb: 2 } }}>
                <Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>
                  <Group sx={{ fontSize: 28, color: 'primary.main' }} />
                  <Box>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Sesiones abiertas</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Inscríbete en una sesión de tutoría grupal. El docente aceptará tu solicitud.
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>

            <TextField
              fullWidth
              size="small"
              placeholder="Buscar por materia, tema o docente..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              slotProps={{ input: { startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} /> } }}
              sx={{ mb: 2 }}
            />

            {isLoadingSesiones ? (
              <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>Cargando sesiones...</Typography>
            ) : sesionesFiltradas.length === 0 ? (
              <ErrorState title="No hay sesiones disponibles" message="No se encontraron sesiones abiertas." />
            ) : (
              <Stack spacing={2}>
                {sesionesFiltradas.map((sesion: any) => (
                  <Card key={sesion.id} variant="outlined" sx={{ borderRadius: 2 }}>
                    <CardContent sx={{ py: 2, '&:last-child': { pb: 2 } }}>
                      <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box sx={{ flex: 1 }}>
                          <Stack direction="row" spacing={1} sx={{ mb: 0.5, alignItems: 'center' }}>
                            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                              {sesion.materia_nombre || 'Sin materia'}
                            </Typography>
                            <Chip label={sesion.estado} size="small" color={estadoColor(sesion.estado)} variant="outlined" />
                          </Stack>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                            {sesion.tema}
                          </Typography>
                          <Stack direction="row" spacing={2} sx={{ mt: 0.5 }}>
                            <Typography variant="caption" color="text.secondary">
                              Docente: <strong>{sesion.docente_nombre || '—'}</strong>
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Inscritos: <strong>{sesion.inscritos_count || 0}</strong>
                              {sesion.capacidad_maxima ? ` / ${sesion.capacidad_maxima}` : ''}
                            </Typography>
                          </Stack>
                        </Box>
                        <Button
                          size="small"
                          variant="contained"
                          startIcon={<Add />}
                          onClick={() => handleInscribirse(sesion.id)}
                          disabled={isInscrebiendo}
                        >
                          Inscribirme
                        </Button>
                      </Stack>
                    </CardContent>
                  </Card>
                ))}
              </Stack>
            )}
          </Box>
        )}

        {/* ===== ESTUDIANTE: Mis solicitudes ===== */}
        {isStudent && tab === 1 && (
          <Box>
            {isErrorSolicitudes ? (
              <ErrorState title="Error al cargar solicitudes" message="No se pudieron cargar tus solicitudes." onRetry={() => refetch()} />
            ) : (
              <DataTable
                rows={solicitudes}
                columns={[
                  { id: 'codigo', label: 'Código' },
                  { id: 'tema', label: 'Tema' },
                  { id: 'estado', label: 'Estado', render: (row: any) => <StatusBadge status={row.estado} /> },
                  { id: 'fecha_solicitud', label: 'Fecha solicitud' },
                  { id: 'fecha_agendada', label: 'Fecha agendada' },
                ]}
                actions={(row: any) => (
                  <Stack direction="row" spacing={1}>
                    {row.estado === 'solicitada' && (
                      <Button size="small" color="error" variant="outlined" startIcon={<Cancel />}
                        onClick={() => { setSelectedId(row.id); setConfirmOpen(true) }} disabled={isCancelling}>
                        Cancelar
                      </Button>
                    )}
                    {row.estado !== 'cancelada' && row.estado !== 'rechazada' && (
                      <Chip label={row.estado} size="small" color={estadoColor(row.estado)} variant="outlined" />
                    )}
                  </Stack>
                )}
                emptyTitle="Sin solicitudes"
                emptyMessage="No has creado solicitudes de tutoría aún."
              />
            )}
          </Box>
        )}

        {/* ===== DOCENTE: Solicitudes pendientes ===== */}
        {isTeacher && tab === 0 && (
          <Box>
            <Card variant="outlined" sx={{ mb: 3, borderRadius: 2, bgcolor: '#fff3e0' }}>
              <CardContent sx={{ py: 2, '&:last-child': { pb: 2 } }}>
                <Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>
                  <PersonSearch sx={{ fontSize: 28, color: 'warning.main' }} />
                  <Box>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Solicitudes pendientes</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Acepta o rechaza solicitudes de tutoría de tus estudiantes.
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>

            {isLoadingPendientes ? (
              <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>Cargando solicitudes...</Typography>
            ) : solicitudesPendientes.length === 0 ? (
              <ErrorState title="Sin solicitudes pendientes" message="No hay solicitudes pendientes de atención." />
            ) : (
              <DataTable
                rows={solicitudesPendientes}
                columns={[
                  { id: 'codigo', label: 'Código' },
                  { id: 'estudiante_nombre', label: 'Estudiante', render: (row: any) => row.estudiante_nombre || `Est. #${row.estudiante_id}` },
                  { id: 'materia_nombre', label: 'Materia', render: (row: any) => row.materia_nombre || '—' },
                  { id: 'tema', label: 'Tema' },
                  { id: 'fecha_solicitud', label: 'Fecha solicitud' },
                ]}
                actions={(row: any) => (
                  <Stack direction="row" spacing={1}>
                    <Button size="small" variant="contained" color="success" startIcon={<CheckCircle />}
                      onClick={() => handleAceptar(row.id)} disabled={isAceptando}>
                      Aceptar
                    </Button>
                    <Button size="small" variant="outlined" color="error" startIcon={<Cancel />}
                      onClick={() => { setSelectedId(row.id); setConfirmOpen(true) }} disabled={isRechazando}>
                      Rechazar
                    </Button>
                  </Stack>
                )}
                emptyTitle="Sin solicitudes"
                emptyMessage="No hay solicitudes pendientes."
              />
            )}
          </Box>
        )}

        {/* ===== DOCENTE: Mis sesiones ===== */}
        {isTeacher && tab === 1 && (
          <Box>
            <Card variant="outlined" sx={{ mb: 3, borderRadius: 2, bgcolor: '#e8f5e9' }}>
              <CardContent sx={{ py: 2, '&:last-child': { pb: 2 } }}>
                <Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>
                  <PlayArrow sx={{ fontSize: 28, color: 'success.main' }} />
                  <Box>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Mis sesiones de tutoría</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Inicia, finaliza sesiones, registra bitácoras y asistencia.
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>

            {isLoadingSesionesDocente ? (
              <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>Cargando sesiones...</Typography>
            ) : sesionesDocente.length === 0 ? (
              <ErrorState title="Sin sesiones" message="No tienes sesiones creadas. Acepta una solicitud para crear una sesión." />
            ) : (
              <DataTable
                rows={sesionesDocente}
                columns={[
                  { id: 'codigo', label: 'Código' },
                  { id: 'materia_nombre', label: 'Materia', render: (row: any) => row.materia_nombre || '—' },
                  { id: 'tema', label: 'Tema' },
                  { id: 'estado', label: 'Estado', render: (row: any) => <StatusBadge status={row.estado} /> },
                  { id: 'inscritos_count', label: 'Inscritos', render: (row: any) => `${row.inscritos_count || 0}${row.capacidad_maxima ? ` / ${row.capacidad_maxima}` : ''}` },
                  { id: 'fecha_creacion', label: 'Creada' },
                ]}
                actions={(row: any) => (
                  <Stack direction="row" spacing={1}>
                    {row.estado === 'abierta' && (
                      <Button size="small" variant="contained" color="success" startIcon={<PlayArrow />}
                        onClick={() => iniciarSesion(row.id)} disabled={isIniciando}>
                        Iniciar
                      </Button>
                    )}
                    {row.estado === 'en_curso' && (
                      <>
                        <Button size="small" variant="outlined" color="info" startIcon={<EditNote />}
                          onClick={() => { setBitacoraForm({ sesionId: row.id, detalle: '', temas_detectados: '' }); setBitacoraOpen(true) }}>
                          Bitácora
                        </Button>
                        <Button size="small" variant="outlined" color="secondary" startIcon={<HowToReg />}
                          onClick={() => handleAsistenciaOpen(row.id)}>
                          Asistencia
                        </Button>
                        <Button size="small" variant="contained" color="warning" startIcon={<Stop />}
                          onClick={() => finalizarSesion(row.id)} disabled={isFinalizando}>
                          Finalizar
                        </Button>
                      </>
                    )}
                  </Stack>
                )}
                emptyTitle="Sin sesiones"
                emptyMessage="No tienes sesiones creadas aún."
              />
            )}
          </Box>
        )}

        {/* ===== ADMIN: Todas las sesiones ===== */}
        {isAdmin && tab === 0 && (
          <Box>
            <Card variant="outlined" sx={{ mb: 3, borderRadius: 2, bgcolor: '#f3e5f5' }}>
              <CardContent sx={{ py: 2, '&:last-child': { pb: 2 } }}>
                <Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>
                  <Group sx={{ fontSize: 28, color: 'secondary.main' }} />
                  <Box>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Todas las sesiones</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Visualiza todas las sesiones de tutoría del sistema.
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>

            {isLoadingSesiones ? (
              <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>Cargando sesiones...</Typography>
            ) : sesionesAbiertas.length === 0 ? (
              <ErrorState title="Sin sesiones" message="No hay sesiones en el sistema." />
            ) : (
              <DataTable
                rows={sesionesAbiertas}
                columns={[
                  { id: 'codigo', label: 'Código' },
                  { id: 'materia_nombre', label: 'Materia', render: (row: any) => row.materia_nombre || '—' },
                  { id: 'tema', label: 'Tema' },
                  { id: 'docente_nombre', label: 'Docente', render: (row: any) => row.docente_nombre || `Doc. #${row.docente_id}` },
                  { id: 'estado', label: 'Estado', render: (row: any) => <StatusBadge status={row.estado} /> },
                  { id: 'inscritos_count', label: 'Inscritos', render: (row: any) => `${row.inscritos_count || 0}${row.capacidad_maxima ? ` / ${row.capacidad_maxima}` : ''}` },
                  { id: 'fecha_creacion', label: 'Creada' },
                ]}
                emptyTitle="Sin sesiones"
                emptyMessage="No hay sesiones en el sistema."
              />
            )}
          </Box>
        )}
      </PageContainer>

      {/* Modal: Crear solicitud (estudiante) */}
      {isStudent && (
        <FormModal
          open={createOpen}
          title="Nueva solicitud de tutoría"
          onCancel={() => { setCreateOpen(false); setCreateForm({ tema: '', asignatura_id: '', fecha_agendada: '' }) }}
          onSubmit={handleCrear}
          loading={isCreating}
          submitLabel="Enviar solicitud"
        >
          <Stack spacing={2} sx={{ py: 1 }}>
            <TextField
              label="¿Qué necesitas?"
              value={createForm.tema}
              onChange={(e) => setCreateForm({ ...createForm, tema: e.target.value })}
              fullWidth multiline minRows={2} required
              helperText="Describe el tema o duda que tienes"
            />
            <TextField
              label="Asignatura ID (opcional)"
              type="number"
              value={createForm.asignatura_id}
              onChange={(e) => setCreateForm({ ...createForm, asignatura_id: e.target.value })}
              fullWidth
            />
            <TextField
              label="Fecha preferida (opcional)"
              type="date"
              value={createForm.fecha_agendada}
              onChange={(e) => setCreateForm({ ...createForm, fecha_agendada: e.target.value })}
              fullWidth
              slotProps={{ inputLabel: { shrink: true } }}
            />
          </Stack>
        </FormModal>
      )}

      {/* Modal: Admin crear sesión */}
      {isAdmin && (
        <FormModal
          open={adminCreateOpen}
          title="Crear sesión de tutoría"
          onCancel={() => { setAdminCreateOpen(false); setAdminForm({ docente_id: '', tema: '', asignatura_id: '', descripcion: '', capacidad_maxima: '20', fecha_agendada: '' }) }}
          onSubmit={handleAdminCrear}
          loading={isCreandoSesion}
          submitLabel="Crear sesión"
        >
          <Stack spacing={2} sx={{ py: 1 }}>
            <TextField
              label="ID del docente"
              type="number"
              value={adminForm.docente_id}
              onChange={(e) => setAdminForm({ ...adminForm, docente_id: e.target.value })}
              fullWidth required
              helperText="ID del docente que impartirá la tutoría"
            />
            <TextField
              label="Tema"
              value={adminForm.tema}
              onChange={(e) => setAdminForm({ ...adminForm, tema: e.target.value })}
              fullWidth required
              helperText="Tema de la sesión de tutoría"
            />
            <TextField
              label="ID de asignatura (opcional)"
              type="number"
              value={adminForm.asignatura_id}
              onChange={(e) => setAdminForm({ ...adminForm, asignatura_id: e.target.value })}
              fullWidth
            />
            <TextField
              label="Descripción (opcional)"
              value={adminForm.descripcion}
              onChange={(e) => setAdminForm({ ...adminForm, descripcion: e.target.value })}
              fullWidth multiline minRows={2}
            />
            <TextField
              label="Capacidad máxima"
              type="number"
              value={adminForm.capacidad_maxima}
              onChange={(e) => setAdminForm({ ...adminForm, capacidad_maxima: e.target.value })}
              fullWidth
            />
            <TextField
              label="Fecha (opcional)"
              type="date"
              value={adminForm.fecha_agendada}
              onChange={(e) => setAdminForm({ ...adminForm, fecha_agendada: e.target.value })}
              fullWidth
              slotProps={{ inputLabel: { shrink: true } }}
            />
          </Stack>
        </FormModal>
      )}

      {/* Modal: Docente bitácora */}
      <FormModal
        open={bitacoraOpen}
        title="Registrar bitácora de sesión"
        onCancel={() => { setBitacoraOpen(false); setBitacoraForm({ sesionId: 0, detalle: '', temas_detectados: '' }) }}
        onSubmit={handleBitacora}
        loading={isRegistrandoBitacora}
        submitLabel="Guardar bitácora"
      >
        <Stack spacing={2} sx={{ py: 1 }}>
          <TextField
            label="Observaciones / Detalle"
            value={bitacoraForm.detalle}
            onChange={(e) => setBitacoraForm({ ...bitacoraForm, detalle: e.target.value })}
            fullWidth multiline minRows={3} required
            helperText="Describe lo tratado en la sesión"
          />
          <TextField
            label="Temas detectados (opcional)"
            value={bitacoraForm.temas_detectados}
            onChange={(e) => setBitacoraForm({ ...bitacoraForm, temas_detectados: e.target.value })}
            fullWidth
            helperText="Ej: Derivadas, Integrales, Álgebra"
          />
        </Stack>
      </FormModal>

      {/* Modal: Docente asistencia */}
      <FormModal
        open={asistenciaOpen}
        title="Registrar asistencia"
        onCancel={() => { setAsistenciaOpen(false); setInscritos([]); setAsistenciaMap({}) }}
        onSubmit={handleAsistenciaGuardar}
        loading={isRegistrandoAsistencia}
        submitLabel="Guardar asistencia"
      >
        <Stack spacing={2} sx={{ py: 1 }}>
          {inscritos.length === 0 ? (
            <Typography color="text.secondary">No hay estudiantes inscritos en esta sesión.</Typography>
          ) : (
            inscritos.map((ins: any) => (
              <FormControlLabel
                key={ins.estudiante_id}
                control={
                  <Switch
                    checked={asistenciaMap[ins.estudiante_id] ?? true}
                    onChange={(e) => setAsistenciaMap({ ...asistenciaMap, [ins.estudiante_id]: e.target.checked })}
                    color="success"
                  />
                }
                label={`Estudiante #${ins.estudiante_id}`}
              />
            ))
          )}
        </Stack>
      </FormModal>

      {/* Modal: Rechazar solicitud (docente) */}
      <ConfirmDialog
        open={confirmOpen}
        title={isTeacher ? 'Rechazar solicitud' : 'Cancelar tutoría'}
        message={isTeacher
          ? '¿Deseas rechazar esta solicitud?'
          : '¿Deseas cancelar esta tutoría?'}
        confirmLabel={isTeacher ? 'Rechazar' : 'Cancelar tutoría'}
        onConfirm={isTeacher ? () => handleRechazar(selectedId!) : handleCancelar}
        onCancel={() => { setConfirmOpen(false); setSelectedId(null); setRechazoMotivo('') }}
        severity="warning"
        loading={isTeacher ? isRechazando : isCancelling}
      />
    </Box>
  )
}
