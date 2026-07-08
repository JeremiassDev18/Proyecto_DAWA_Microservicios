'use client'

import { CrudPageTemplate, type FormField } from '@/components/ui/CrudPageTemplate'
import { useFacultades } from '@/hooks/useFacultades'
import type { Facultad } from '@/types/admin.types'

const formFields: FormField[] = [
  { name: 'nombre', label: 'Nombre', required: true },
  { name: 'codigo', label: 'Código', required: true },
  { name: 'activo', label: 'Estado', type: 'boolean' },
]

export default function FacultadesPage() {
  const hook = useFacultades()

  return (
    <CrudPageTemplate<Facultad>
      title="Facultades"
      subtitle="Registro de unidades académicas"
      items={hook.facultades}
      isLoading={hook.isLoading}
      isError={hook.isError}
      isCreating={hook.isCreating}
      isUpdating={hook.isUpdating}
      isDeleting={hook.isDeleting}
      refetch={hook.refetch}
      onCreate={hook.createFacultad}
      onUpdate={hook.updateFacultad}
      onDelete={hook.deleteFacultad}
      columns={[
        { id: 'nombre', label: 'Nombre' },
        { id: 'codigo', label: 'Código' },
      ]}
      formFields={formFields}
      searchFields={['nombre', 'codigo']}
      searchPlaceholder="Buscar facultad"
      entityName="facultad"
      createLabel="Nueva facultad"
      statusField="activo"
      getInitialForm={() => ({ nombre: '', codigo: '', activo: true })}
    />
  )
}
