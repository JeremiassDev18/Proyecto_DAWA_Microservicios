'use client'

import { Box, Typography } from '@mui/material'
import { InboxOutlined } from '@mui/icons-material'

interface EmptyStateProps {
  title?: string
  message?: string
  icon?: React.ReactNode
  action?: React.ReactNode
}

export function EmptyState({
  title = 'Sin datos',
  message = 'No hay información para mostrar',
  icon,
  action,
}: EmptyStateProps) {
  return (
    <Box sx={{ py: 8, textAlign: 'center' }}>
      <Box sx={{ color: 'text.disabled', mb: 2 }}>
        {icon || <InboxOutlined sx={{ fontSize: 56 }} />}
      </Box>
      <Typography variant="h6" color="text.secondary" gutterBottom>
        {title}
      </Typography>
      <Typography variant="body2" color="text.disabled" sx={{ mb: 2, maxWidth: 400, mx: 'auto' }}>
        {message}
      </Typography>
      {action}
    </Box>
  )
}
