'use client'

import { Box, Card, CardContent, Typography, Stack, TextField, Divider } from '@mui/material'
import { useAuth } from '@/hooks/useAuth'
import { APP_NAME, APP_DESCRIPTION } from '@/config/constants'

export default function ConfiguracionPage() {
  const { user } = useAuth()

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>Configuración</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Preferencias del sistema
      </Typography>

      <Stack spacing={3}>
        <Card variant="outlined" sx={{ borderRadius: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Información del sistema</Typography>
            <Stack spacing={1.5}>
              <Stack direction="row" sx={{ justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">Aplicación</Typography>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>{APP_NAME}</Typography>
              </Stack>
              <Divider />
              <Stack direction="row" sx={{ justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">Descripción</Typography>
                <Typography variant="body2">{APP_DESCRIPTION}</Typography>
              </Stack>
              <Divider />
              <Stack direction="row" sx={{ justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">Usuario</Typography>
                <Typography variant="body2">{user?.email}</Typography>
              </Stack>
              <Divider />
              <Stack direction="row" sx={{ justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">Roles</Typography>
                <Typography variant="body2">{user?.roles?.join(', ') || 'Sin roles'}</Typography>
              </Stack>
            </Stack>
          </CardContent>
        </Card>

        <Card variant="outlined" sx={{ borderRadius: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>API Gateway</Typography>
            <Stack spacing={1.5}>
              <TextField label="URL del Gateway" value={process.env.NEXT_PUBLIC_API_GATEWAY || 'http://localhost:8080'} fullWidth disabled />
              <Typography variant="caption" color="text.secondary">
                Configurado via variable de entorno NEXT_PUBLIC_API_GATEWAY
              </Typography>
            </Stack>
          </CardContent>
        </Card>
      </Stack>
    </Box>
  )
}
