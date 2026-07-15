'use client'

import { useState, useEffect } from 'react'
import { Box, Grid, Typography, useTheme, Card, CardContent, Stack, Chip, Avatar, Divider } from '@mui/material'
import {
  School, Book, Group, Person,
  CalendarMonth, TrendingUp, Chat, Help, Assignment,
  AutoStories, PersonSearch,
} from '@mui/icons-material'
import { useDashboard } from '@/hooks/useDashboard'
import { useStudent } from '@/hooks/useStudent'
import { useDocenteProfile } from '@/hooks/useDocenteProfile'
import { StatCard } from '@/components/ui/StatCard'
import { ChartCard } from '@/components/ui/ChartCard'
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton'
import { ErrorState } from '@/components/ui/ErrorState'
import { useAuth } from '@/hooks/useAuth'
import { ROLES } from '@/config/permissions'
import { tutoriasService } from '@/services/api/tutorias.service'
import { useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { ROUTES } from '@/config/routes'

export default function DashboardPage() {
  const { user, docenteId } = useAuth()
  const { data: stats, isLoading, isError, refetch } = useDashboard()
  const { estudiante, carrera, materias, tutoriasCount } = useStudent()
  const { docente: docenteProfile } = useDocenteProfile(docenteId)
  const [tutoriasDocente, setTutoriasDocente] = useState<number>(0)
  const [sesionesDocente, setSesionesDocente] = useState<any[]>([])
  const theme = useTheme()
  const router = useRouter()

  const roles = user?.roles ?? []
  const isAdmin = roles.includes(ROLES.ADMIN)
  const isManager = roles.includes(ROLES.MANAGER)
  const isStudent = !isAdmin && roles.includes(ROLES.ESTUDIANTE)
  const isTeacher = !isAdmin && !isStudent && roles.includes(ROLES.PROFESOR)
  const canViewFullStats = isAdmin || isManager

  useEffect(() => {
    if (isTeacher && docenteId) {
      tutoriasService.listarTutoriasPorDocente(docenteId).then((r) => {
        setTutoriasDocente(r.cantidad ?? 0)
      }).catch(() => {})
      tutoriasService.listarSesionesDocente(docenteId).then((r) => {
        setSesionesDocente(Array.isArray(r) ? r : [])
      }).catch(() => {})
    }
  }, [isTeacher, docenteId])

  const { data: pendientesSolicitudes = 0 } = useQuery({
    queryKey: ['solicitudes', 'admin', 'pendientes'],
    queryFn: () => tutoriasService.listarSolicitudes().then(
      (s) => s.filter((x: any) => ['solicitada', 'sin_asignar'].includes(x.estado)).length
    ),
    enabled: isAdmin,
  })

  if (isError) {
    return (
      <Box>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>Dashboard</Typography>
          <Typography variant="body2" color="text.secondary">Bienvenido, {user?.nombre || 'Usuario'}</Typography>
        </Box>
        <ErrorState title="Error al cargar datos" message="No se pudieron cargar las estadísticas" onRetry={() => refetch()} />
      </Box>
    )
  }

  const statsConfig = canViewFullStats ? [
    { title: 'Total Estudiantes', key: 'total_estudiantes', icon: Person, color: theme.palette.primary.main },
    { title: 'Docentes Activos', key: 'total_docentes', icon: School, color: theme.palette.success.main },
    { title: 'Carreras', key: 'total_carreras', icon: Book, color: theme.palette.secondary.main },
    { title: 'Facultades', key: 'total_facultades', icon: Group, color: theme.palette.warning.main },
    { title: 'Asignaturas', key: 'total_asignaturas', icon: TrendingUp, color: theme.palette.info.main },
    { title: 'Períodos Activos', key: 'periodos_activos', icon: CalendarMonth, color: theme.palette.error.main },
  ] as const : []

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, letterSpacing: '-0.02em' }}>
          Dashboard
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
          <Typography variant="body2" color="text.secondary">
            Bienvenido, {user?.nombre || 'Usuario'}
          </Typography>
          <Chip label={user?.roles?.[0] || 'usuario'} size="small" variant="outlined" color="primary" />
        </Box>
      </Box>

      {/* ── ESTUDIANTE ── */}
      {isStudent && estudiante && (
        <>
          <Card variant="outlined" sx={{ mb: 3, borderRadius: 3 }}>
            <CardContent>
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={3} sx={{ alignItems: 'center' }}>
                <Avatar sx={{ width: 72, height: 72, bgcolor: 'primary.main', fontSize: '1.8rem' }}>
                  {estudiante.nombres?.[0]?.toUpperCase() || 'E'}
                </Avatar>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>{estudiante.nombres} {estudiante.apellidos}</Typography>
                  <Stack direction="row" spacing={1} sx={{ mt: 0.5, flexWrap: 'wrap' }}>
                    <Chip label={`Matrícula: ${estudiante.matricula || 'N/A'}`} size="small" variant="outlined" />
                    <Chip label={`Carrera: ${carrera?.nombre || 'N/A'}`} size="small" color="primary" variant="outlined" />
                    <Chip label={`Nivel: ${estudiante.nivel || 'N/A'}`} size="small" color="info" variant="outlined" />
                  </Stack>
                </Box>
              </Stack>
            </CardContent>
          </Card>

          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <StatCard title="Materias Inscritas" value={materias.length} icon={AutoStories} color={theme.palette.info.main} onClick={() => router.push(ROUTES.ACADEMICO_MATERIAS)} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <StatCard title="Tutorías" value={tutoriasCount} icon={Assignment} color={theme.palette.primary.main} onClick={() => router.push(ROUTES.TUTORIAS)} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <StatCard title="Chat IA" value="Activo" icon={Chat} color={theme.palette.success.main} onClick={() => router.push(ROUTES.CHAT)} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <StatCard title="Bitácora" value="Ver registros" icon={Book} color={theme.palette.warning.main} onClick={() => router.push(ROUTES.ACADEMICO_BITACORA)} />
            </Grid>
          </Grid>
        </>
      )}

      {isStudent && !estudiante && (
        <Card variant="outlined" sx={{ mb: 3, borderRadius: 3, bgcolor: 'primary.main', color: 'white' }}>
          <CardContent sx={{ py: 3 }}>
            <Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>
              <Help sx={{ fontSize: 40, opacity: 0.8 }} />
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>Panel de Estudiante</Typography>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Usa la sección de Tutorías para ver tus solicitudes y el Chat para consultar al asistente IA.
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>
      )}

      {/* ── PROFESOR ── */}
      {isTeacher && (
        <>
          <Card variant="outlined" sx={{ mb: 3, borderRadius: 3 }}>
            <CardContent>
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={3} sx={{ alignItems: 'center' }}>
                <Avatar sx={{ width: 72, height: 72, bgcolor: 'secondary.main', fontSize: '1.8rem' }}>
                  {docenteProfile?.nombres?.[0]?.toUpperCase() || user?.nombre?.[0]?.toUpperCase() || 'D'}
                </Avatar>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    {docenteProfile ? `${docenteProfile.nombres} ${docenteProfile.apellidos}` : user?.nombre || 'Docente'}
                  </Typography>
                  <Stack direction="row" spacing={1} sx={{ mt: 0.5, flexWrap: 'wrap' }}>
                    {docenteProfile?.especialidad && (
                      <Chip label={`Especialidad: ${docenteProfile.especialidad}`} size="small" variant="outlined" />
                    )}
                    {docenteProfile?.facultad_nombre && (
                      <Chip label={`Facultad: ${docenteProfile.facultad_nombre}`} size="small" color="primary" variant="outlined" />
                    )}
                    <Chip label={`${tutoriasDocente} tutorías asignadas`} size="small" color="info" variant="outlined" />
                  </Stack>
                </Box>
              </Stack>
            </CardContent>
          </Card>

          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <StatCard title="Tutorías Asignadas" value={tutoriasDocente} icon={Assignment} color={theme.palette.primary.main} onClick={() => router.push(ROUTES.TUTORIAS)} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <StatCard title="Materias" value={docenteProfile?.total_asignaturas ?? 0} icon={AutoStories} color={theme.palette.info.main} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <StatCard title="Sesiones activas" value={sesionesDocente.filter((s: any) => s.estado === 'abierta' || s.estado === 'en_curso').length} icon={Group} color={theme.palette.success.main} onClick={() => router.push(ROUTES.TUTORIAS)} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <StatCard title="Chat IA" value="Activo" icon={Chat} color={theme.palette.success.main} onClick={() => router.push(ROUTES.CHAT)} />
            </Grid>
          </Grid>

          {/* Materias asignadas */}
          {docenteProfile?.asignaturas && docenteProfile.asignaturas.length > 0 && (
            <Card variant="outlined" sx={{ mb: 3, borderRadius: 3 }}>
              <CardContent>
                <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>Mis materias</Typography>
                <Divider sx={{ mb: 1.5 }} />
                <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
                  {docenteProfile.asignaturas.map((a: any) => (
                    <Chip
                      key={a.id}
                      label={`${a.nombre}${a.num_estudiantes ? ` — ${a.num_estudiantes} estudiantes` : ''}`}
                      color="primary"
                      variant="outlined"
                      size="small"
                    />
                  ))}
                </Stack>
              </CardContent>
            </Card>
          )}

          {/* Últimas sesiones */}
          {sesionesDocente.length > 0 && (
            <Card variant="outlined" sx={{ borderRadius: 3 }}>
              <CardContent>
                <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>Últimas sesiones</Typography>
                <Divider sx={{ mb: 1.5 }} />
                <Stack spacing={1}>
                  {sesionesDocente.slice(0, 5).map((s: any) => (
                    <Stack key={s.id} direction="row" spacing={2} sx={{ alignItems: 'center', py: 0.5 }}>
                      <Chip
                        label={s.estado}
                        size="small"
                        color={s.estado === 'abierta' || s.estado === 'en_curso' ? 'success' : s.estado === 'atendida' ? 'info' : 'default'}
                        variant="outlined"
                      />
                      <Typography variant="body2" sx={{ flex: 1, fontWeight: 500 }}>
                        {s.materia_nombre || 'Sin materia'} — {s.tema || 'Sin tema'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {s.inscritos_count || 0} inscritos
                      </Typography>
                    </Stack>
                  ))}
                </Stack>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* ── LOADING / ADMIN ── */}
      {isLoading ? (
        <LoadingSkeleton type="card" count={canViewFullStats ? 6 : 2} />
      ) : canViewFullStats && stats ? (
        <>
          <Grid container spacing={3}>
            {statsConfig.map((stat) => (
              <Grid size={{ xs: 12, sm: 6, md: 4 }} key={stat.key}>
                <StatCard
                  title={stat.title}
                  value={(stats as unknown as Record<string, number>)[stat.key] ?? '—'}
                  icon={stat.icon}
                  color={stat.color}
                />
              </Grid>
            ))}
            <Grid size={{ xs: 12, sm: 6, md: 4 }}>
              <StatCard
                title="Solicitudes Pendientes"
                value={pendientesSolicitudes}
                icon={PersonSearch}
                color="warning.main"
                onClick={() => router.push(ROUTES.TUTORIAS)}
              />
            </Grid>
          </Grid>

          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12, md: 6 }}>
              <ChartCard title="Distribución Académica" subtitle="Estudiantes vs Docentes">
                <Box sx={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}>
                  {[
                    { label: 'Estudiantes', value: stats.total_estudiantes, color: theme.palette.primary.main, max: Math.max(stats.total_estudiantes, stats.total_docentes || 1) },
                    { label: 'Docentes', value: stats.total_docentes, color: theme.palette.success.main, max: Math.max(stats.total_estudiantes, stats.total_docentes || 1) },
                    { label: 'Carreras', value: stats.total_carreras, color: theme.palette.secondary.main, max: Math.max(stats.total_carreras, 1) },
                  ].map((item) => (
                    <Box key={item.label} sx={{ textAlign: 'center' }}>
                      <Box sx={{ width: 64, height: Math.max(40, (item.value / item.max) * 160), bgcolor: item.color, borderRadius: 2, opacity: 0.85, mx: 'auto', minHeight: 40, display: 'flex', alignItems: 'flex-end', justifyContent: 'center' }}>
                        <Typography variant="caption" sx={{ color: 'white', fontWeight: 700, pb: 0.5 }}>{item.value}</Typography>
                      </Box>
                      <Typography variant="caption" sx={{ mt: 1, display: 'block', fontWeight: 500 }}>{item.label}</Typography>
                    </Box>
                  ))}
                </Box>
              </ChartCard>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <ChartCard title="Vista General" subtitle="Resumen del sistema">
                <Box sx={{ width: '100%' }}>
                  {[
                    { label: 'Facultades', value: stats.total_facultades, max: Math.max(stats.total_facultades, 1) },
                    { label: 'Carreras', value: stats.total_carreras, max: Math.max(stats.total_carreras, 1) },
                    { label: 'Asignaturas', value: stats.total_asignaturas, max: Math.max(stats.total_asignaturas, 1) },
                    { label: 'Docentes', value: stats.total_docentes, max: Math.max(stats.total_docentes, 1) },
                    { label: 'Estudiantes', value: stats.total_estudiantes, max: Math.max(stats.total_estudiantes, 1) },
                    { label: 'Períodos', value: stats.periodos_activos, max: Math.max(stats.periodos_activos, 1) },
                  ].map((item) => {
                    const pct = Math.max(8, (item.value / item.max) * 100)
                    return (
                      <Box key={item.label} sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1.5 }}>
                        <Typography variant="caption" sx={{ minWidth: 100, fontWeight: 500, color: 'text.secondary' }}>{item.label}</Typography>
                        <Box sx={{ flex: 1, bgcolor: 'grey.100', borderRadius: 2, height: 10, overflow: 'hidden' }}>
                          <Box sx={{ width: `${pct}%`, bgcolor: 'primary.main', height: '100%', borderRadius: 2, transition: 'width 500ms ease' }} />
                        </Box>
                        <Typography variant="caption" sx={{ minWidth: 30, fontWeight: 600, textAlign: 'right' }}>{item.value}</Typography>
                      </Box>
                    )
                  })}
                </Box>
              </ChartCard>
            </Grid>
          </Grid>
        </>
      ) : null}
    </Box>
  )
}
