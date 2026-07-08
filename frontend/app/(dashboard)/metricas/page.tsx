'use client'

import { Box, Grid, Typography, useTheme } from '@mui/material'
import { Chat, Message, TrendingUp, Warning } from '@mui/icons-material'
import { useUsageMetrics } from '@/hooks/useTraining'
import { StatCard } from '@/components/ui/StatCard'
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton'
import { ErrorState } from '@/components/ui/ErrorState'

export default function MetricasPage() {
  const { data: metrics, isLoading, isError, refetch } = useUsageMetrics()
  const theme = useTheme()

  if (isError) {
    return (
      <Box>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>Métricas</Typography>
          <Typography variant="body2" color="text.secondary">Estadísticas de uso del chatbot</Typography>
        </Box>
        <ErrorState
          title="No disponible"
          message="Las métricas de uso no están disponibles. El endpoint del chatbot puede no estar configurado."
          onRetry={() => refetch()}
        />
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>Métricas</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Estadísticas de uso del chatbot
      </Typography>

      {isLoading ? (
        <LoadingSkeleton type="card" count={4} />
      ) : (
        <>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <StatCard title="Conversaciones" value={(metrics as any)?.total_conversaciones ?? (metrics as any)?.conversaciones ?? '—'} icon={Chat} color={theme.palette.primary.main} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <StatCard title="Mensajes" value={(metrics as any)?.total_mensajes ?? (metrics as any)?.mensajes ?? '—'} icon={Message} color={theme.palette.secondary.main} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <StatCard title="Resoluciones" value={(metrics as any)?.resoluciones_exitosas ?? (metrics as any)?.resueltas ?? '—'} icon={TrendingUp} color={theme.palette.success.main} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <StatCard title="Escalaciones" value={(metrics as any)?.escalaciones ?? '—'} icon={Warning} color={theme.palette.warning.main} />
            </Grid>
          </Grid>

          <Box sx={{ mt: 4 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Indicadores</Typography>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Box sx={{ p: 3, bgcolor: 'background.paper', borderRadius: 3, border: '1px solid', borderColor: 'divider' }}>
                  <Typography variant="caption" color="text.secondary">Confianza promedio</Typography>
                  <Typography variant="h3" sx={{ fontWeight: 700, mt: 1 }}>
                    {metrics ? `${(((metrics as any)?.confianza_promedio ?? 0) * 100).toFixed(1)}%` : '—'}
                  </Typography>
                </Box>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Box sx={{ p: 3, bgcolor: 'background.paper', borderRadius: 3, border: '1px solid', borderColor: 'divider' }}>
                  <Typography variant="caption" color="text.secondary">Tasa de resolución</Typography>
                  <Typography variant="h3" sx={{ fontWeight: 700, mt: 1 }}>
                    {metrics ? (
                      `${((((metrics as any)?.resoluciones_exitosas ?? 0) / Math.max((metrics as any)?.total_mensajes ?? 1, 1)) * 100).toFixed(1)}%`
                    ) : '—'}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Box>
        </>
      )}
    </Box>
  )
}
