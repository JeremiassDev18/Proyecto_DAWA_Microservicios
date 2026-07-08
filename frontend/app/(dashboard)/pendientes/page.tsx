'use client'

import { Box, Button, Card, CardContent, Stack, Typography, Chip } from '@mui/material'
import { CheckCircle, SwapHoriz, Help } from '@mui/icons-material'
import { usePending } from '@/hooks/useTraining'
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton'
import { ErrorState } from '@/components/ui/ErrorState'

export default function PendientesPage() {
  const { pending, isLoading, isError, refetch, convertToDataset, isConverting, resolve, isResolving } = usePending()

  if (isError) {
    return <ErrorState title="Error al cargar pendientes" message="No se pudieron cargar las consultas pendientes." onRetry={() => refetch()} />
  }

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>Pendientes IA</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Consultas que el chatbot no pudo resolver
      </Typography>

      {isLoading ? (
        <LoadingSkeleton type="list" count={5} />
      ) : pending.length === 0 ? (
        <Card variant="outlined" sx={{ p: 6, textAlign: 'center', borderRadius: 3 }}>
          <CheckCircle sx={{ fontSize: 56, color: 'success.main', mb: 1 }} />
          <Typography variant="h6" color="text.secondary">Sin pendientes</Typography>
          <Typography variant="body2" color="text.disabled">El chatbot está resolviendo todas las consultas.</Typography>
        </Card>
      ) : (
        <Stack spacing={2}>
          {pending.map((item: any) => (
            <Card key={item.id} variant="outlined" sx={{ borderRadius: 3 }}>
              <CardContent>
                <Stack direction={{ xs: 'column', md: 'row' }} sx={{ justifyContent: 'space-between' }} spacing={2}>
                  <Box sx={{ flex: 1 }}>
                    <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1 }}>
                      <Help sx={{ fontSize: 18, color: 'warning.main' }} />
                      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>{item.pregunta}</Typography>
                    </Stack>
                    {item.respuesta_dada && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                        Respuesta: {item.respuesta_dada}
                      </Typography>
                    )}
                    {item.confianza != null && (
                      <Chip label={`Confianza: ${(item.confianza * 100).toFixed(0)}%`} size="small" color={item.confianza > 0.5 ? 'warning' : 'error'} />
                    )}
                  </Box>
                  <Stack direction="row" spacing={1}>
                    <Button size="small" variant="outlined" startIcon={<SwapHoriz />} onClick={() => convertToDataset(item.id)} disabled={isConverting}>
                      Convertir
                    </Button>
                    <Button size="small" variant="contained" startIcon={<CheckCircle />} onClick={() => resolve(item.id)} disabled={isResolving}>
                      Resolver
                    </Button>
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
