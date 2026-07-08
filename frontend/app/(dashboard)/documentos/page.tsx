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
import { useDocuments } from '@/hooks/useTraining'

export default function DocumentosPage() {
  const { documents, isLoading, isError, isCreating, isUpdating, isDeleting, refetch, createDocument, updateDocument, deleteDocument } = useDocuments()
  const [search, setSearch] = useState('')
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<any>(null)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [form, setForm] = useState({ nombre: '', categoria: '', contenido: '', activo: true })

  const filtered = useMemo(() => {
    const term = search.toLowerCase()
    if (!term) return documents
    return documents.filter((item: any) => `${item.nombre} ${item.categoria}`.toLowerCase().includes(term))
  }, [search, documents])

  const resetForm = () => { setForm({ nombre: '', categoria: '', contenido: '', activo: true }); setEditing(null) }

  const handleSubmit = () => {
    if (editing) updateDocument({ id: editing.id, data: form })
    else createDocument(form)
    setOpen(false)
    resetForm()
  }

  return (
    <Box>
      <PageContainer title="Documentos" subtitle="Base de conocimiento RAG del chatbot" loading={isLoading} action={{ label: 'Nuevo documento', onClick: () => { resetForm(); setOpen(true) }, icon: <Add /> }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 3, alignItems: 'center' }}>
          <SearchInput value={search} onChange={setSearch} placeholder="Buscar documento..." />
          <Box sx={{ flexGrow: 1 }} />
          <Chip label={`${filtered.length} documentos`} size="small" />
        </Stack>

        {isError ? <ErrorState title="Error al cargar documentos" onRetry={() => refetch()} /> : (
          <DataTable
            rows={filtered}
            columns={[
              { id: 'nombre', label: 'Nombre' },
              { id: 'categoria', label: 'Categoría' },
              { id: 'activo', label: 'Estado', render: (row: any) => <StatusBadge status={row.activo ? 'activo' : 'inactivo'} /> },
            ]}
            actions={(row: any) => (
              <Stack direction="row" spacing={1} sx={{ justifyContent: 'flex-end' }}>
                <Button size="small" variant="outlined" startIcon={<Edit />} onClick={() => { setEditing(row); setForm({ nombre: row.nombre, categoria: row.categoria, contenido: row.contenido || '', activo: row.activo }); setOpen(true) }}>Editar</Button>
                <Button size="small" color="error" variant="outlined" startIcon={<Delete />} onClick={() => { setSelectedId(row.id); setConfirmOpen(true) }}>Eliminar</Button>
              </Stack>
            )}
            emptyTitle="Sin documentos"
            emptyMessage="Agrega documentos a la base de conocimiento."
          />
        )}
      </PageContainer>

      <FormModal open={open} title={editing ? 'Editar documento' : 'Nuevo documento'} onCancel={() => { setOpen(false); resetForm() }} onSubmit={handleSubmit} loading={isCreating || isUpdating}>
        <Stack spacing={2} sx={{ py: 1 }}>
          <TextField label="Nombre" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} fullWidth />
          <TextField label="Categoría" value={form.categoria} onChange={(e) => setForm({ ...form, categoria: e.target.value })} fullWidth />
          <TextField label="Contenido" value={form.contenido} onChange={(e) => setForm({ ...form, contenido: e.target.value })} fullWidth multiline minRows={4} />
          <Button variant="outlined" color={form.activo ? 'success' : 'inherit'} onClick={() => setForm({ ...form, activo: !form.activo })}>{form.activo ? 'Activo' : 'Inactivo'}</Button>
        </Stack>
      </FormModal>

      <ConfirmDialog open={confirmOpen} title="Eliminar documento" message="¿Eliminar este documento?" confirmLabel="Eliminar" onConfirm={() => { if (selectedId) deleteDocument(selectedId); setConfirmOpen(false); setSelectedId(null) }} onCancel={() => { setConfirmOpen(false); setSelectedId(null) }} severity="error" loading={isDeleting} />
    </Box>
  )
}
