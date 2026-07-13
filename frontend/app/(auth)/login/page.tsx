'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Checkbox,
  FormControlLabel,
  Link,
  Alert,
  InputAdornment,
  IconButton,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { useAuth } from '@/hooks/useAuth';

const loginSchema = z.object({
  email: z.string().email('Email inválido'),
  password: z.string().min(6, 'La contraseña debe tener al menos 6 caracteres'),
  rememberMe: z.boolean().optional(),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const { login, isLoggingIn } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
      rememberMe: false,
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    setError(null);
    try {
      await login(data);
    } catch (err: any) {
      setError(err.error || 'Error al iniciar sesión');
    }
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            width: '100%',
            borderRadius: 2,
          }}
        >
          <Typography variant="h4" component="h1" gutterBottom align="center" sx={{ fontWeight: 'bold' }}>
            DAWA
          </Typography>
          <Typography variant="subtitle1" align="center" color="textSecondary" gutterBottom>
            Sistema de Tutorías con IA
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mt: 2, mb: 2 }}>
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit(onSubmit)}>
            <TextField
              {...register('email')}
              label="Correo Electrónico"
              type="email"
              fullWidth
              margin="normal"
              error={!!errors.email}
              helperText={errors.email?.message}
              disabled={isLoggingIn}
            />

            <TextField
              {...register('password')}
              label="Contraseña"
              type={showPassword ? 'text' : 'password'}
              fullWidth
              margin="normal"
              error={!!errors.password}
              helperText={errors.password?.message}
              disabled={isLoggingIn}
              slotProps={{
  input: {
    endAdornment: (
      <InputAdornment position="end">
        <IconButton onClick={() => setShowPassword(!showPassword)} edge="end">
          {showPassword ? <VisibilityOff /> : <Visibility />}
        </IconButton>
      </InputAdornment>
    ),
  }
}}
            />

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
              <FormControlLabel
                control={
                  <Checkbox {...register('rememberMe')} color="primary" />
                }
                label="Recordarme"
              />
              <Link href="/recuperar-password" variant="body2">
                ¿Olvidaste tu contraseña?
              </Link>
            </Box>

            <Button
              type="submit"
              variant="contained"
              fullWidth
              size="large"
              sx={{ mt: 3, mb: 2 }}
              disabled={isLoggingIn}
            >
              {isLoggingIn ? 'Iniciando sesión...' : 'Iniciar Sesión'}
            </Button>
          </form>

          <Box
            sx={{
              mt: 3,
              p: 2,
              borderRadius: 2,
              bgcolor: 'grey.50',
              border: '1px solid',
              borderColor: 'grey.200',
            }}
          >
            <Typography variant="caption" sx={{ fontWeight: 600, color: 'text.secondary', display: 'block', mb: 1 }}>
              Credenciales de prueba
            </Typography>
            {[
              { role: '🎓  Estudiante', email: 'jeremias@test.com', password: 'estudiante123' },
              { role: '👨‍🏫  Docente', email: 'carlos@test.com', password: 'docente123' },
              { role: '🔧  Administrador', email: 'admin@sistema.com', password: 'admin123' },
            ].map((cred) => (
              <Box
                key={cred.email}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  py: 0.6,
                  '&:not(:last-child)': { borderBottom: '1px solid', borderColor: 'grey.200' },
                }}
              >
                <Typography variant="body2" sx={{ fontWeight: 500, minWidth: 130, fontSize: '0.8rem' }}>
                  {cred.role}
                </Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary', fontSize: '0.78rem', fontFamily: 'monospace' }}>
                  {cred.email}
                </Typography>
                <Typography
                  variant="body2"
                  component="span"
                  sx={{
                    ml: 'auto',
                    color: 'text.disabled',
                    fontSize: '0.75rem',
                    fontFamily: 'monospace',
                    cursor: 'pointer',
                    '&:hover': { color: 'primary.main' },
                  }}
                  onClick={() => navigator.clipboard.writeText(cred.password)}
                  title="Copiar contraseña"
                >
                  {cred.password}
                </Typography>
              </Box>
            ))}
          </Box>
        </Paper>
      </Box>
    </Container>
  );
}