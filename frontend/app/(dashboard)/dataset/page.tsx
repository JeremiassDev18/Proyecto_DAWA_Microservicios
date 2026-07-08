'use client'

import { useMemo, useState } from 'react'
import { Box, Button, Stack, TextField, Chip } from '@mui/material'
import { Add, Delete, Edit } from '@mui/icons-material'
import { PageContainer } from '@/components/ui/PageContainer'
import { DataTable } from '@/components/ui/DataTable'
import { FormModal } from '@/components/ui/FormModal'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { ErrorState } from '@/components/ui/ErrorState'
import { SearchInput } from '@/components/ui/SearchInput'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { useDataset } from '@/hooks/useDataset'

export default function DatasetPage() {
  const { dataset, isLoading, isError, isCreating, isUpdating, isDeleting, refetch, create, update, remove } = useDataset()
  const [search, setSearch] = useState('')
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<any>(null)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [form, setForm] = useState({ texto_pregunta: '', intencion: '', respuesta: '', activo: true })

  const filtered = useMemo(() => {
    const term = search.toLowerCase()
    if (!term) return dataset
    return dataset.filter((item) => `${item.texto_pregunta} ${item.intencion} ${item.respuesta}`.toLowerCase().includes(term))
  }, [search, dataset])

  const resetForm = () => { setForm({ texto_pregunta: '', intencion: '', respuesta: '', activo: true }); setEditing(null) }

  const handleSubmit = () => {
    if (editing) update({ id: editing.id, data: form })
    else create(form)
    setOpen(false)
    resetForm()
  }

  return (
    <Box>
      <PageContainer title="Dataset" subtitle="Gestión de ejemplos de entrenamiento del chatbot" loading={isLoading} action={{ label: 'Nuevo ejemplo', onClick: () => { resetForm(); setOpen(true) }, icon: <Add /> }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 3, alignItems: 'center' }}>
          <SearchInput value={search} onChange={setSearch} placeholder="Buscar en dataset..." />
          <Box sx={{ flexGrow: 1 }} />
          <Chip label={`${filtered.length} ejemplos`} size="small" />
        </Stack>

        {isError ? <ErrorState title="Error al cargar dataset" onRetry={() => refetch()} /> : (
          <DataTable
            rows={filtered}
            columns={[
              { id: 'texto_pregunta', label: 'Pregunta' },
              { id: 'intencion', label: 'Intención' },
              { id: 'respuesta', label: 'Respuesta' },
              { id: 'validado', label: 'Validado', render: (row: any) => <StatusBadge status={row.validado ? 'activo' : 'inactivo'} /> },
            ]}
            actions={(row: any) => (
              <Stack direction="row" spacing={1} sx={{ justifyContent: 'flex-end' }}>
                <Button size="small" variant="outlined" startIcon={<Edit />} onClick={() => { setEditing(row); setForm({ texto_pregunta: row.texto_pregunta, intencion: row.intencion, respuesta: row.respuesta, activo: row.activo }); setOpen(true) }}>Editar</Button>
                <Button size="small" color="error" variant="outlined" startIcon={<Delete />} onClick={() => { setSelectedId(row.id); setConfirmOpen(true) }}>Eliminar</Button>
              </Stack>
            )}
            emptyTitle="Dataset vacío"
            emptyMessage="Agrega ejemplos de entrenamiento para mejorar el chatbot."
          />
        )}
      </PageContainer>

      <FormModal open={open} title={editing ? 'Editar ejemplo' : 'Nuevo ejemplo'} onCancel={() => { setOpen(false); resetForm() }} onSubmit={handleSubmit} loading={isCreating || isUpdating}>
        <Stack spacing={2} sx={{ py: 1 }}>
          <TextField label="Pregunta" value={form.texto_pregunta} onChange={(e) => setForm({ ...form, texto_pregunta: e.target.value })} fullWidth multiline minRows={2} />
          <TextField label="Intención" value={form.intencion} onChange={(e) => setForm({ ...form, intencion: e.target.value })} fullWidth />
          <TextField label="Respuesta" value={form.respuesta} onChange={(e) => setForm({ ...form, respuesta: e.target.value })} fullWidth multiline minRows={3} />
          <Button variant="outlined" color={form.activo ? 'success' : 'inherit'} onClick={() => setForm({ ...form, activo: !form.activo })}>{form.activo ? 'Activo' : 'Inactivo'}</Button>
        </Stack>
      </FormModal>

      <ConfirmDialog open={confirmOpen} title="Eliminar ejemplo" message="¿Eliminar este ejemplo del dataset?" confirmLabel="Eliminar" onConfirm={() => { if (selectedId) remove(selectedId); setConfirmOpen(false); setSelectedId(null) }} onCancel={() => { setConfirmOpen(false); setSelectedId(null) }} severity="error" loading={isDeleting} />
    </Box>
  )
}
