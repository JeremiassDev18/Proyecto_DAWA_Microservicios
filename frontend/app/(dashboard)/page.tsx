'use client'

import { Box, Grid, Typography, useTheme, Card, CardContent, Stack, Chip, Avatar } from '@mui/material'
import {
  School, Book, Group, Person,
  CalendarMonth, TrendingUp, Chat, Help,
} from '@mui/icons-material'
import { useDashboard } from '@/hooks/useDashboard'
import { useStudent } from '@/hooks/useStudent'
import { StatCard } from '@/components/ui/StatCard'
import { ChartCard } from '@/components/ui/ChartCard'
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton'
import { ErrorState } from '@/components/ui/ErrorState'
import { useAuth } from '@/hooks/useAuth'
import { ROLES } from '@/config/permissions'

export default function DashboardPage() {
  const { user } = useAuth()
  const { data: stats, isLoading, isError, refetch } = useDashboard()
  const { estudiante, carrera, tutoriasCount } = useStudent()
  const theme = useTheme()

  const isAdmin = user?.roles?.includes(ROLES.ADMIN)
  const isManager = user?.roles?.includes(ROLES.MANAGER)
  const isStudent = user?.roles?.includes(ROLES.ESTUDIANTE)
  const isTeacher = user?.roles?.includes(ROLES.PROFESOR)
  const canViewFullStats = isAdmin || isManager

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
  ] as const : [
    { title: 'Mis Tutorías', key: 'tutorias', icon: School, color: theme.palette.primary.main },
    { title: 'Chat', key: 'chat', icon: Chat, color: theme.palette.success.main },
  ] as const

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

      {isStudent && estudiante && (
        <Card variant="outlined" sx={{ mb: 3, borderRadius: 3 }}>
          <CardContent>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={3} sx={{ alignItems: 'center' }}>
              <Avatar sx={{ width: 64, height: 64, bgcolor: 'primary.main', fontSize: '1.5rem' }}>
                {estudiante.nombres?.[0]?.toUpperCase() || 'E'}
              </Avatar>
              <Box sx={{ flex: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>{estudiante.nombres} {estudiante.apellidos}</Typography>
                <Stack direction="row" spacing={1} sx={{ mt: 0.5, flexWrap: 'wrap' }}>
                  <Chip label={`Matrícula: ${estudiante.matricula || 'N/A'}`} size="small" variant="outlined" />
                  <Chip label={`Carrera: ${carrera?.nombre || 'N/A'}`} size="small" color="primary" variant="outlined" />
                  <Chip label={`Tutorías: ${tutoriasCount}`} size="small" color="info" variant="outlined" />
                </Stack>
              </Box>
            </Stack>
          </CardContent>
        </Card>
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

      {isTeacher && (
        <Card variant="outlined" sx={{ mb: 3, borderRadius: 3, bgcolor: 'secondary.main', color: 'white' }}>
          <CardContent sx={{ py: 3 }}>
            <Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>
              <School sx={{ fontSize: 40, opacity: 0.8 }} />
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>Panel de Docente</Typography>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Revisa las tutorías asignadas en la sección de Tutorías.
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <LoadingSkeleton type="card" count={canViewFullStats ? 6 : 2} />
      ) : canViewFullStats && stats ? (
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
        </Grid>
      ) : isStudent ? (
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, sm: 6 }}>
            <StatCard title="Mis Tutorías" value={tutoriasCount} icon={School} color={theme.palette.primary.main} />
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <StatCard title="Chat IA" value="Activo" icon={Chat} color={theme.palette.success.main} />
          </Grid>
        </Grid>
      ) : null}

      {canViewFullStats && stats && (
        <Grid container spacing={3} sx={{ mt: 1 }}>
          <Grid size={{ xs: 12, md: 6 }}>
            <ChartCard title="Distribución Académica" subtitle="Estudiantes vs Docentes por período">
              <Box sx={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}>
                {[
                  { label: 'Estudiantes', value: stats.total_estudiantes, color: theme.palette.primary.main, max: Math.max(stats.total_estudiantes, stats.total_docentes) },
                  { label: 'Docentes', value: stats.total_docentes, color: theme.palette.success.main, max: Math.max(stats.total_estudiantes, stats.total_docentes) },
                  { label: 'Carreras', value: stats.total_carreras, color: theme.palette.secondary.main, max: Math.max(stats.total_carreras, 1) },
                ].map((item) => (
                  <Box key={item.label} sx={{ textAlign: 'center' }}>
                    <Box sx={{ width: 64, height: Math.max(40, (item.value / item.max) * 160), bgcolor: item.color, borderRadius: 2, opacity: 0.85, transition: 'height 300ms ease', mx: 'auto', minHeight: 40, display: 'flex', alignItems: 'flex-end', justifyContent: 'center' }}>
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
      )}
    </Box>
  )
}
