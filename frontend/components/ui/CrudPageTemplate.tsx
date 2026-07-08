'use client'

import { useMemo, useState } from 'react'
import { Box, Button, Stack, TextField, Typography, MenuItem, Select, FormControl, InputLabel } from '@mui/material'
import { Add, Delete, Edit } from '@mui/icons-material'
import { PageContainer } from './PageContainer'
import { DataTable, type DataTableColumn } from './DataTable'
import { FormModal } from './FormModal'
import { ConfirmDialog } from './ConfirmDialog'
import { ErrorState } from './ErrorState'
import { SearchInput } from './SearchInput'
import { StatusBadge } from './StatusBadge'
import { PermissionGuard } from './PermissionGuard'

export interface FormField {
  name: string
  label: string
  type?: 'text' | 'number' | 'password' | 'email' | 'select' | 'boolean'
  fullWidth?: boolean
  multiline?: boolean
  minRows?: number
  options?: { value: string | number; label: string }[]
  helperText?: string
  required?: boolean
}

interface CrudPageTemplateProps<T extends Record<string, any>> {
  title: string
  subtitle?: string
  items: T[]
  isLoading: boolean
  isError: boolean
  isCreating?: boolean
  isUpdating?: boolean
  isDeleting?: boolean
  refetch: () => void
  onCreate: (data: any) => void
  onUpdate: (params: { id: number; payload: any }) => void
  onDelete: (id: number) => void
  columns: DataTableColumn<T>[]
  formFields: FormField[]
  searchFields?: string[]
  searchPlaceholder?: string
  createLabel?: string
  entityName: string
  permission?: string
  statusField?: string
  getInitialForm: () => Record<string, any>
  transformPayload?: (form: Record<string, any>, editing: T | null) => any
  extraFormContent?: React.ReactNode
}

export function CrudPageTemplate<T extends Record<string, any>>({
  title,
  subtitle,
  items,
  isLoading,
  isError,
  isCreating,
  isUpdating,
  isDeleting,
  refetch,
  onCreate,
  onUpdate,
  onDelete,
  columns,
  formFields,
  searchFields = ['nombre'],
  searchPlaceholder = 'Buscar...',
  createLabel,
  entityName,
  permission,
  statusField,
  getInitialForm,
  transformPayload,
  extraFormContent,
}: CrudPageTemplateProps<T>) {
  const [search, setSearch] = useState('')
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<T | null>(null)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [form, setForm] = useState<Record<string, any>>(getInitialForm)

  const filtered = useMemo(() => {
    const term = search.toLowerCase()
    if (!term) return items
    return items.filter((item) =>
      searchFields.some((field) => {
        const val = item[field]
        return val != null && String(val).toLowerCase().includes(term)
      })
    )
  }, [search, items, searchFields])

  const resetForm = () => {
    setForm(getInitialForm())
    setEditing(null)
  }

  const openCreate = () => {
    resetForm()
    setOpen(true)
  }

  const openEdit = (item: T) => {
    setEditing(item)
    const newForm: Record<string, any> = {}
    formFields.forEach((field) => {
      const val = item[field.name]
      newForm[field.name] = val != null ? val : getInitialForm()[field.name]
    })
    setForm(newForm)
    setOpen(true)
  }

  const handleSubmit = () => {
    const payload = transformPayload ? transformPayload(form, editing) : form
    if (editing) {
      onUpdate({ id: editing.id, payload })
    } else {
      onCreate(payload)
    }
    setOpen(false)
    resetForm()
  }

  const handleDelete = () => {
    if (selectedId) {
      onDelete(selectedId)
      setConfirmOpen(false)
      setSelectedId(null)
    }
  }

  const updateField = (name: string, value: any) => {
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const finalColumns: DataTableColumn<T>[] = statusField
    ? [
        ...columns,
        {
          id: statusField,
          label: 'Estado',
          render: (row: T) => <StatusBadge status={String(row[statusField] ?? 'activo')} />,
        },
      ]
    : columns

  const actionButtons = (row: T) => {
    const buttons = (
      <Stack direction="row" spacing={1} sx={{ justifyContent: 'flex-end' }}>
        <Button size="small" variant="outlined" startIcon={<Edit />} onClick={() => openEdit(row)}>
          Editar
        </Button>
        <Button
          size="small"
          color="error"
          variant="outlined"
          startIcon={<Delete />}
          onClick={() => {
            setSelectedId(row.id)
            setConfirmOpen(true)
          }}
        >
          Eliminar
        </Button>
      </Stack>
    )

    if (permission) {
      return <PermissionGuard permission={permission}>{buttons}</PermissionGuard>
    }
    return buttons
  }

  const renderFormField = (field: FormField) => {
    if (field.type === 'boolean') {
      return (
        <Button
          key={field.name}
          variant="outlined"
          color={form[field.name] ? 'success' : 'inherit'}
          onClick={() => updateField(field.name, !form[field.name])}
        >
          {form[field.name] ? 'Activo' : 'Inactivo'}
        </Button>
      )
    }

    if (field.type === 'select' && field.options) {
      return (
        <FormControl key={field.name} fullWidth>
          <InputLabel>{field.label}</InputLabel>
          <Select
            value={form[field.name] ?? ''}
            label={field.label}
            onChange={(e) => updateField(field.name, e.target.value)}
          >
            {field.options.map((opt) => (
              <MenuItem key={opt.value} value={opt.value}>
                {opt.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      )
    }

    return (
      <TextField
        key={field.name}
        label={field.label}
        type={field.type || 'text'}
        value={form[field.name] ?? ''}
        onChange={(e) => updateField(field.name, field.type === 'number' ? Number(e.target.value) : e.target.value)}
        fullWidth={field.fullWidth !== false}
        multiline={field.multiline}
        minRows={field.minRows}
        helperText={field.helperText}
        required={field.required}
      />
    )
  }

  return (
    <Box>
      <PageContainer
        title={title}
        subtitle={subtitle}
        loading={isLoading}
        action={{ label: createLabel || `Nuevo ${entityName}`, onClick: openCreate, icon: <Add /> }}
      >
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 3, alignItems: 'center' }}>
          <SearchInput value={search} onChange={setSearch} placeholder={searchPlaceholder} />
          <Box sx={{ flexGrow: 1 }} />
          <Typography variant="body2" color="text.secondary">
            {filtered.length} registros
          </Typography>
        </Stack>

        {isError ? (
          <ErrorState
            title={`Error al cargar ${entityName}s`}
            message={`No se pudieron cargar los ${entityName}s.`}
            onRetry={() => refetch()}
          />
        ) : (
          <DataTable
            rows={filtered}
            columns={finalColumns}
            actions={actionButtons}
            emptyTitle={`No hay ${entityName}s`}
            emptyMessage={`Aún no se han registrado ${entityName}s.`}
          />
        )}
      </PageContainer>

      <FormModal
        open={open}
        title={editing ? `Editar ${entityName}` : `Crear ${entityName}`}
        onCancel={() => {
          setOpen(false)
          resetForm()
        }}
        onSubmit={handleSubmit}
        loading={isCreating || isUpdating}
      >
        <Stack spacing={2} sx={{ py: 1 }}>
          {formFields.map(renderFormField)}
          {extraFormContent}
        </Stack>
      </FormModal>

      <ConfirmDialog
        open={confirmOpen}
        title={`Eliminar ${entityName}`}
        message={`¿Deseas eliminar este ${entityName} del sistema?`}
        confirmLabel="Eliminar"
        onConfirm={handleDelete}
        onCancel={() => {
          setConfirmOpen(false)
          setSelectedId(null)
        }}
        severity="error"
        loading={isDeleting}
      />
    </Box>
  )
}
