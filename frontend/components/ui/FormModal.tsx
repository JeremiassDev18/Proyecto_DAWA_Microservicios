'use client'

import { Dialog, DialogActions, DialogContent, DialogTitle, Button, CircularProgress } from '@mui/material'
import type { ReactNode } from 'react'

interface FormModalProps {
  open: boolean
  title: string
  children: ReactNode
  loading?: boolean
  submitLabel?: string
  cancelLabel?: string
  onSubmit?: () => void
  onCancel: () => void
}

export function FormModal({
  open,
  title,
  children,
  loading = false,
  submitLabel = 'Guardar',
  cancelLabel = 'Cancelar',
  onSubmit,
  onCancel,
}: FormModalProps) {
  return (
    <Dialog open={open} onClose={loading ? undefined : onCancel} maxWidth="md" fullWidth>
      <DialogTitle sx={{ fontWeight: 700 }}>{title}</DialogTitle>
      <DialogContent dividers>{children}</DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onCancel} disabled={loading} variant="outlined">
          {cancelLabel}
        </Button>
        {onSubmit ? (
          <Button onClick={onSubmit} disabled={loading} variant="contained">
            {loading ? <CircularProgress size={20} /> : submitLabel}
          </Button>
        ) : null}
      </DialogActions>
    </Dialog>
  )
}
