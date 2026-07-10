'use client'

import { CrudPageTemplate, type FormField } from '@/components/ui/CrudPageTemplate'
import { useDocentes } from '@/hooks/useDocentes'
import type { Docente } from '@/types/admin.types'
import { Chip, Stack, Typography } from '@mui/material'

const formFields: FormField[] = [
  { name: 'nombres', label: 'Nombres', required: true },
  { name: 'apellidos', label: 'Apellidos', required: true },
  { name: 'email', label: 'Correo', type: 'email', required: true },
  { name: 'activo', label: 'Estado', type: 'boolean' },
]

export default function DocentesPage() {
  const hook = useDocentes()

  return (
    <CrudPageTemplate<Docente>
      title="Docentes"
      subtitle="Registro y gestión del personal académico"
      items={hook.docentes}
      isLoading={hook.isLoading}
      isError={hook.isError}
      isCreating={hook.isCreating}
      isUpdating={hook.isUpdating}
      isDeleting={hook.isDeleting}
      refetch={hook.refetch}
      onCreate={hook.createDocente}
      onUpdate={hook.updateDocente}
      onDelete={hook.deleteDocente}
      columns={[
        { id: 'nombres', label: 'Nombres' },
        { id: 'apellidos', label: 'Apellidos' },
        { id: 'email', label: 'Correo' },
        {
          id: 'facultad_nombre',
          label: 'Facultad',
          render: (row) => row.facultad_nombre || '—',
        },
        {
          id: 'asignaturas',
          label: 'Asignaturas',
          render: (row) => {
            const asigs = row.asignaturas || []
            if (asigs.length === 0) return <Typography variant="body2" color="text.secondary">Sin asignaturas</Typography>
            return (
              <Stack spacing={0.5}>
                {asigs.map((a) => (
                  <Typography key={a.id} variant="body2">
                    {a.nombre}{a.nivel ? ` (${a.nivel})` : ''}
                  </Typography>
                ))}
              </Stack>
            )
          },
        },
        {
          id: 'total_estudiantes',
          label: 'Estudiantes',
          align: 'center',
          render: (row) => {
            const total = row.total_estudiantes || 0
            return (
              <Chip
                label={total}
                size="small"
                color={total > 0 ? 'primary' : 'default'}
                variant="outlined"
              />
            )
          },
        },
      ]}
      formFields={formFields}
      searchFields={['nombres', 'apellidos', 'email']}
      searchPlaceholder="Buscar docente"
      entityName="docente"
      createLabel="Nuevo docente"
      statusField="activo"
      getInitialForm={() => ({ nombres: '', apellidos: '', email: '', activo: true })}
    />
  )
}
