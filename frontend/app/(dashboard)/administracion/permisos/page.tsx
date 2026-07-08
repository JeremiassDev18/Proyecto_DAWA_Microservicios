'use client'

import { useQuery } from '@tanstack/react-query'
import { Box, Typography, Stack, Card, CardContent, Chip } from '@mui/material'
import { securityService } from '@/services/api/security.service'
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton'
import { ErrorState } from '@/components/ui/ErrorState'
import { useRoles } from '@/hooks/useRoles'

export default function PermisosPage() {
  const { roles, isLoading: isLoadingRoles } = useRoles()

  const { data: permissions, isLoading: isLoadingPerms, isError, refetch } = useQuery({
    queryKey: ['permissions'],
    queryFn: () => securityService.getPermissions(),
  })

  if (isError) {
    return <ErrorState title="Error al cargar permisos" message="No se pudieron cargar los permisos del sistema." onRetry={() => refetch()} />
  }

  const allPerms = Array.isArray(permissions) ? permissions : []

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>Gestión de Permisos</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Permisos disponibles en el sistema
      </Typography>

      {isLoadingPerms ? (
        <LoadingSkeleton type="list" count={5} />
      ) : (
        <Stack spacing={2}>
          {allPerms.map((perm: any) => (
            <Card key={perm.id} variant="outlined" sx={{ borderRadius: 3 }}>
              <CardContent sx={{ py: 2, '&:last-child': { pb: 2 } }}>
                <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>{perm.nombre}</Typography>
                    {perm.descripcion && (
                      <Typography variant="caption" color="text.secondary">{perm.descripcion}</Typography>
                    )}
                  </Box>
                  <Chip label={`ID: ${perm.id}`} size="small" variant="outlined" />
                </Stack>
              </CardContent>
            </Card>
          ))}
          {allPerms.length === 0 && (
            <Card variant="outlined" sx={{ p: 4, textAlign: 'center', borderRadius: 3 }}>
              <Typography variant="body2" color="text.secondary">No hay permisos definidos en el sistema.</Typography>
            </Card>
          )}
        </Stack>
      )}

      <Typography variant="h6" sx={{ fontWeight: 600, mt: 4, mb: 2 }}>Roles del sistema</Typography>
      {isLoadingRoles ? (
        <LoadingSkeleton type="card" count={3} />
      ) : (
        <Stack direction="row" spacing={2} sx={{ flexWrap: 'wrap' }}>
          {roles.map((role) => (
            <Card key={role.id} variant="outlined" sx={{ borderRadius: 3, minWidth: 200 }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>{role.nombre_rol}</Typography>
                {role.descripcion && (
                  <Typography variant="caption" color="text.secondary">{role.descripcion}</Typography>
                )}
              </CardContent>
            </Card>
          ))}
        </Stack>
      )}
    </Box>
  )
}
