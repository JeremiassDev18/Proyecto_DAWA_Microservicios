'use client'

import { Box, Typography, Button } from '@mui/material'
import { ErrorOutlined } from '@mui/icons-material'

interface ErrorStateProps {
  title?: string
  message?: string
  onRetry?: () => void
}

export function ErrorState({
  title = 'Error',
  message = 'Ocurrió un error al cargar los datos',
  onRetry,
}: ErrorStateProps) {
  return (
    <Box sx={{ py: 8, textAlign: 'center' }}>
      <ErrorOutlined sx={{ fontSize: 56, color: 'error.main', mb: 2 }} />
      <Typography variant="h6" color="text.secondary" gutterBottom>
        {title}
      </Typography>
      <Typography variant="body2" color="text.disabled" sx={{ mb: 3, maxWidth: 400, mx: 'auto' }}>
        {message}
      </Typography>
      {onRetry && (
        <Button variant="outlined" onClick={onRetry}>
          Reintentar
        </Button>
      )}
    </Box>
  )
}
