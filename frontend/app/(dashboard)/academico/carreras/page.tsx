'use client'

import { CrudPageTemplate, type FormField } from '@/components/ui/CrudPageTemplate'
import { useCarreras } from '@/hooks/useCarreras'
import type { Carrera } from '@/types/admin.types'

const formFields: FormField[] = [
  { name: 'nombre', label: 'Nombre', required: true },
  { name: 'codigo', label: 'Código', required: true },
  {
    name: 'modalidad', label: 'Modalidad', type: 'select', required: true,
    options: [
      { value: 'Presencial', label: 'Presencial' },
      { value: 'Semipresencial', label: 'Semipresencial' },
      { value: 'En Línea', label: 'En Línea' },
    ],
  },
  { name: 'facultad_id', label: 'Facultad ID', type: 'number', required: true },
  { name: 'activo', label: 'Estado', type: 'boolean' },
]

export default function CarrerasPage() {
  const hook = useCarreras()

  return (
    <CrudPageTemplate<Carrera>
      title="Carreras"
      subtitle="Definición de programas académicos"
      items={hook.carreras}
      isLoading={hook.isLoading}
      isError={hook.isError}
      isCreating={hook.isCreating}
      isUpdating={hook.isUpdating}
      isDeleting={hook.isDeleting}
      refetch={hook.refetch}
      onCreate={hook.createCarrera}
      onUpdate={hook.updateCarrera}
      onDelete={hook.deleteCarrera}
      columns={[
        { id: 'nombre', label: 'Nombre' },
        { id: 'codigo', label: 'Código' },
        { id: 'modalidad', label: 'Modalidad' },
        { id: 'facultad_id', label: 'Facultad' },
      ]}
      formFields={formFields}
      searchFields={['nombre', 'codigo']}
      searchPlaceholder="Buscar carrera"
      entityName="carrera"
      createLabel="Nueva carrera"
      statusField="activo"
      getInitialForm={() => ({ nombre: '', codigo: '', modalidad: 'Presencial', facultad_id: '', activo: true })}
    />
  )
}
