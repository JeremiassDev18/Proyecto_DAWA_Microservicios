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
  Alert,
  Link,
} from '@mui/material';
import { authService } from '@/services/api/auth.service';
import { useToast } from '@/hooks/useToast';

const recoverSchema = z.object({
  email: z.string().email('Email inválido'),
});

type RecoverFormData = z.infer<typeof recoverSchema>;

export default function RecoverPasswordPage() {
  const { showToast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RecoverFormData>({
    resolver: zodResolver(recoverSchema),
    defaultValues: {
      email: '',
    },
  });

  const onSubmit = async (data: RecoverFormData) => {
    setIsLoading(true);
    try {
      await authService.recoverPassword(data.email);
      setSuccess(true);
      showToast('Correo de recuperación enviado', 'success');
    } catch (err: any) {
      showToast(err.response?.data?.error || 'Error al enviar correo', 'error');
    } finally {
      setIsLoading(false);
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
            Recuperar Contraseña
          </Typography>

          {success ? (
            <Alert severity="success" sx={{ mt: 2 }}>
              Se ha enviado un correo con las instrucciones para recuperar tu contraseña.
            </Alert>
          ) : (
            <>
              <Typography variant="body2" color="textSecondary" sx={{ mt: 2, mb: 2 }}>
                Ingresa tu correo electrónico y te enviaremos un enlace para restablecer tu contraseña.
              </Typography>

              <form onSubmit={handleSubmit(onSubmit)}>
                <TextField
                  {...register('email')}
                  label="Correo Electrónico"
                  type="email"
                  fullWidth
                  margin="normal"
                  error={!!errors.email}
                  helperText={errors.email?.message}
                  disabled={isLoading}
                />

                <Button
                  type="submit"
                  variant="contained"
                  fullWidth
                  size="large"
                  sx={{ mt: 3, mb: 2 }}
                  disabled={isLoading}
                >
                  {isLoading ? 'Enviando...' : 'Enviar Instrucciones'}
                </Button>
              </form>
            </>
          )}

          <Box sx={{ textAlign: 'center', mt: 2 }}>
            <Link href="/login" variant="body2">
              Volver al inicio de sesión
            </Link>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
}