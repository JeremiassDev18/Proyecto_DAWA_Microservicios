'use client'

import { useQuery } from '@tanstack/react-query'
import { Box, Typography, Stack, Card, CardContent, Chip } from '@mui/material'
import { History } from '@mui/icons-material'
import { api } from '@/services/api'
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton'
import { ErrorState } from '@/components/ui/ErrorState'

export default function LogsPage() {
  const { data: logs, isLoading, isError, refetch } = useQuery({
    queryKey: ['auditLogs'],
    queryFn: async () => {
      const data = await api.security.get<any>('/auditoria')
      return data.logs || data.registros || data || []
    },
  })

  if (isError) {
    return <ErrorState title="Error al cargar logs" message="No se pudieron cargar los registros de auditoría." onRetry={() => refetch()} />
  }

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>Logs</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Registro de auditoría del sistema
      </Typography>

      {isLoading ? (
        <LoadingSkeleton type="list" count={8} />
      ) : !logs || logs.length === 0 ? (
        <Card variant="outlined" sx={{ p: 6, textAlign: 'center', borderRadius: 3 }}>
          <History sx={{ fontSize: 56, color: 'text.disabled', mb: 1 }} />
          <Typography variant="h6" color="text.secondary">Sin registros</Typography>
          <Typography variant="body2" color="text.disabled">No hay registros de auditoría disponibles.</Typography>
        </Card>
      ) : (
        <Stack spacing={1}>
          {logs.map((log: any) => (
            <Card key={log.id} variant="outlined" sx={{ borderRadius: 2 }}>
              <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center' }}>
                  <Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>
                    <Chip label={log.accion || 'accion'} size="small" color="primary" variant="outlined" />
                    <Typography variant="body2">{log.detalle || 'Sin detalle'}</Typography>
                  </Stack>
                  <Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>
                    <Typography variant="caption" color="text.secondary">User #{log.usuario_id}</Typography>
                    <Typography variant="caption" color="text.disabled">{log.fecha}</Typography>
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
