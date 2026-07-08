'use client'

import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import type { ReactNode } from 'react'

export interface DataTableColumn<T> {
  id: keyof T | string
  label: string
  render?: (row: T) => ReactNode
  align?: 'left' | 'center' | 'right'
  width?: number | string
}

interface DataTableProps<T> {
  columns: DataTableColumn<T>[]
  rows: T[]
  loading?: boolean
  emptyTitle?: string
  emptyMessage?: string
  actions?: (row: T) => ReactNode
}

export function DataTable<T extends Record<string, any>>({
  columns,
  rows,
  loading,
  emptyTitle = 'Sin datos',
  emptyMessage = 'No hay información para mostrar.',
  actions,
}: DataTableProps<T>) {
  if (!loading && rows.length === 0) {
    return (
      <Paper variant="outlined" sx={{ borderRadius: 3, p: 4, textAlign: 'center' }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          {emptyTitle}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          {emptyMessage}
        </Typography>
      </Paper>
    )
  }

  return (
    <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 3, overflow: 'hidden' }}>
      <Table size="small">
        <TableHead>
          <TableRow>
            {columns.map((column) => (
              <TableCell key={String(column.id)} align={column.align || 'left'} sx={{ width: column.width }}>
                {column.label}
              </TableCell>
            ))}
            {actions ? <TableCell align="right">Acciones</TableCell> : null}
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((row, index) => (
            <TableRow key={row.id ?? index} hover>
              {columns.map((column) => (
                <TableCell key={String(column.id)} align={column.align || 'left'}>
                  {column.render ? column.render(row) : row[String(column.id)]}
                </TableCell>
              ))}
              {actions ? <TableCell align="right">{actions(row)}</TableCell> : null}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}
