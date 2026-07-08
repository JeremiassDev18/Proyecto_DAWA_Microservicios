'use client'

import { Chip } from '@mui/material'

const statusConfig: Record<string, { color: 'success' | 'warning' | 'error' | 'info' | 'default'; label: string }> = {
  pendiente: { color: 'warning', label: 'Pendiente' },
  confirmada: { color: 'info', label: 'Confirmada' },
  asignada: { color: 'info', label: 'Asignada' },
  atendida: { color: 'success', label: 'Atendida' },
  cancelada: { color: 'error', label: 'Cancelada' },
  activo: { color: 'success', label: 'Activo' },
  inactivo: { color: 'error', label: 'Inactivo' },
  true: { color: 'success', label: 'Sí' },
  false: { color: 'error', label: 'No' },
}

interface StatusBadgeProps {
  status: string
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status?.toLowerCase()] || { color: 'default' as const, label: status }
  return <Chip label={config.label} color={config.color} size="small" variant="filled" />
}
