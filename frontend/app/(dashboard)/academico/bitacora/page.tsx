'use client'

import { Box, Typography, Card, CardContent, Stack, Chip, Grid } from '@mui/material'
import { Assignment, CheckCircle, Cancel, AccessTime } from '@mui/icons-material'
import { useBitacora } from '@/hooks/useBitacora'
import { useAuth } from '@/hooks/useAuth'
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton'
import { ErrorState } from '@/components/ui/ErrorState'
import { StatusBadge } from '@/components/ui/StatusBadge'

export default function BitacoraPage() {
  const { user } = useAuth()
  const { data: bitacoras = [], isLoading, isError, refetch } = useBitacora()

  if (isError) {
    return (
      <Box>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>Mi Bitácora</Typography>
          <Typography variant="body2" color="text.secondary">Registro de tutorías atendidas</Typography>
        </Box>
        <ErrorState title="Error al cargar bitácora" message="No se pudieron cargar los registros." onRetry={() => refetch()} />
      </Box>
    )
  }

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>Mi Bitácora</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          Registro de tutorías atendidas — {user?.nombre || 'Estudiante'}
        </Typography>
      </Box>

      {isLoading ? (
        <LoadingSkeleton type="list" count={4} />
      ) : bitacoras.length === 0 ? (
        <Card variant="outlined" sx={{ p: 6, textAlign: 'center', borderRadius: 3 }}>
          <Assignment sx={{ fontSize: 56, color: 'text.disabled', mb: 1 }} />
          <Typography variant="h6" color="text.secondary">Sin registros</Typography>
          <Typography variant="body2" color="text.disabled">
            Aún no tienes tutorías atendidas. Cuando tengas una, aparecerá aquí.
          </Typography>
        </Card>
      ) : (
        <Stack spacing={2}>
          {bitacoras.map((item: any) => (
            <Card key={item.bitacora_id ?? item.solicitud_id} variant="outlined" sx={{ borderRadius: 3 }}>
              <CardContent>
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ justifyContent: 'space-between' }}>
                  <Box sx={{ flex: 1 }}>
                    <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>{item.tema}</Typography>
                      <Chip label={`Código: ${item.codigo}`} size="small" variant="outlined" />
                    </Stack>
                    <Stack direction="row" spacing={2} sx={{ mb: 1, flexWrap: 'wrap' }}>
                      <StatusBadge status={item.estado || 'atendida'} />
                      {item.asistio !== null && item.asistio !== undefined && (
                        <Chip
                          icon={item.asistio ? <CheckCircle /> : <Cancel />}
                          label={item.asistio ? 'Asistió' : 'No asistió'}
                          color={item.asistio ? 'success' : 'error'}
                          size="small"
                        />
                      )}
                    </Stack>
                    {item.observaciones && (
                      <Typography variant="body2" color="text.secondary">
                        Observaciones: {item.observaciones}
                      </Typography>
                    )}
                    {item.temas_detectados && (
                      <Typography variant="caption" color="text.secondary">
                        Temas detectados: {item.temas_detectados}
                      </Typography>
                    )}
                  </Box>
                  <Stack direction="row" spacing={1} sx={{ alignItems: 'center', minWidth: 120, justifyContent: 'flex-end' }}>
                    <AccessTime sx={{ fontSize: 16, color: 'text.disabled' }} />
                    <Typography variant="caption" color="text.disabled">
                      {item.fecha_registro ? new Date(item.fecha_registro).toLocaleDateString('es-ES') : item.fecha_solicitud ? new Date(item.fecha_solicitud).toLocaleDateString('es-ES') : '—'}
                    </Typography>
                  </Stack>
                </Stack>
              </CardContent>
            </Card>
          ))}
        </Stack>
      )}
    </Box>
  )
}
