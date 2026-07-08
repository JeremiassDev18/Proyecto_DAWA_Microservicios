'use client'

import { CrudPageTemplate, type FormField } from '@/components/ui/CrudPageTemplate'
import { useRoles } from '@/hooks/useRoles'
import { PERMISSIONS } from '@/config/permissions'
import type { Role } from '@/types/admin.types'

const formFields: FormField[] = [
  { name: 'nombre_rol', label: 'Nombre del rol', required: true },
  { name: 'descripcion', label: 'Descripción', multiline: true, minRows: 3 },
]

export default function RolesPage() {
  const hook = useRoles()

  return (
    <CrudPageTemplate<Role>
      title="Roles"
      subtitle="Definición de permisos y accesos"
      items={hook.roles}
      isLoading={hook.isLoading}
      isError={hook.isError}
      isCreating={hook.isCreating}
      isUpdating={hook.isUpdating}
      isDeleting={hook.isDeleting}
      refetch={hook.refetch}
      onCreate={hook.createRole}
      onUpdate={hook.updateRole}
      onDelete={hook.deleteRole}
      columns={[
        { id: 'nombre_rol', label: 'Nombre' },
        { id: 'descripcion', label: 'Descripción' },
      ]}
      formFields={formFields}
      searchFields={['nombre_rol', 'descripcion']}
      searchPlaceholder="Buscar rol"
      entityName="rol"
      createLabel="Nuevo rol"
      permission={PERMISSIONS.WRITE_ROLES}
      getInitialForm={() => ({ nombre_rol: '', descripcion: '' })}
    />
  )
}
