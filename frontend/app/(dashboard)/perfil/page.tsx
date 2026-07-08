'use client'

import { useState } from 'react'
import { Box, Card, CardContent, Typography, Stack, TextField, Button, Avatar, Divider, Chip } from '@mui/material'
import { Save, Lock } from '@mui/icons-material'
import { useAuth } from '@/hooks/useAuth'
import { authService } from '@/services/api/auth.service'
import { useToast } from '@/hooks/useToast'

export default function PerfilPage() {
  const { user } = useAuth()
  const { showToast } = useToast()
  const [passwordForm, setPasswordForm] = useState({ current_password: '', new_password: '', new_password_confirm: '' })
  const [isChanging, setIsChanging] = useState(false)

  const handleChangePassword = async () => {
    if (!passwordForm.new_password || passwordForm.new_password !== passwordForm.new_password_confirm) {
      showToast('Las contraseñas no coinciden', 'error')
      return
    }
    setIsChanging(true)
    try {
      await authService.changePassword(user!.id, passwordForm)
      showToast('Contraseña actualizada', 'success')
      setPasswordForm({ current_password: '', new_password: '', new_password_confirm: '' })
    } catch {
      showToast('Error al cambiar contraseña', 'error')
    } finally {
      setIsChanging(false)
    }
  }

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>Mi Perfil</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Información personal y seguridad
      </Typography>

      <Stack spacing={3}>
        <Card variant="outlined" sx={{ borderRadius: 3 }}>
          <CardContent>
            <Stack direction="row" spacing={3} sx={{ alignItems: 'center', mb: 3 }}>
              <Avatar sx={{ width: 64, height: 64, bgcolor: 'primary.main', fontSize: '1.5rem', fontWeight: 700 }}>
                {user?.nombre?.[0]?.toUpperCase() || 'U'}
              </Avatar>
              <Box>
                <Typography variant="h5" sx={{ fontWeight: 700 }}>{user?.nombre}</Typography>
                <Typography variant="body2" color="text.secondary">{user?.email}</Typography>
                <Stack direction="row" spacing={0.5} sx={{ mt: 1 }}>
                  {user?.roles?.map((role) => (
                    <Chip key={role} label={role} size="small" color="primary" variant="outlined" />
                  ))}
                </Stack>
              </Box>
            </Stack>
            <Divider />
            <Stack spacing={1.5} sx={{ mt: 2 }}>
              <Stack direction="row" sx={{ justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">ID</Typography>
                <Typography variant="body2">{user?.id}</Typography>
              </Stack>
              <Stack direction="row" sx={{ justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">Estado</Typography>
                <Chip label={user?.estado !== false ? 'Activo' : 'Inactivo'} color={user?.estado !== false ? 'success' : 'default'} size="small" />
              </Stack>
              <Stack direction="row" sx={{ justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">Permisos</Typography>
                <Typography variant="body2">{user?.permissions?.length || 0} permisos</Typography>
              </Stack>
            </Stack>
          </CardContent>
        </Card>

        <Card variant="outlined" sx={{ borderRadius: 3 }}>
          <CardContent>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 2 }}>
              <Lock fontSize="small" />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>Cambiar contraseña</Typography>
            </Stack>
            <Stack spacing={2}>
              <TextField label="Contraseña actual" type="password" value={passwordForm.current_password} onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })} fullWidth />
              <TextField label="Nueva contraseña" type="password" value={passwordForm.new_password} onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })} fullWidth />
              <TextField label="Confirmar nueva contraseña" type="password" value={passwordForm.new_password_confirm} onChange={(e) => setPasswordForm({ ...passwordForm, new_password_confirm: e.target.value })} fullWidth />
              <Button variant="contained" startIcon={<Save />} onClick={handleChangePassword} disabled={isChanging}>
                {isChanging ? 'Guardando...' : 'Cambiar contraseña'}
              </Button>
            </Stack>
          </CardContent>
        </Card>
      </Stack>
    </Box>
  )
}
