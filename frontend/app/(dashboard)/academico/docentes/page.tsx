'use client'

import { CrudPageTemplate, type FormField } from '@/components/ui/CrudPageTemplate'
import { useDocentes } from '@/hooks/useDocentes'
import type { Docente } from '@/types/admin.types'

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
