'use client'

import { CrudPageTemplate, type FormField } from '@/components/ui/CrudPageTemplate'
import { useUsers } from '@/hooks/useUsers'
import { PERMISSIONS } from '@/config/permissions'
import type { User } from '@/types/auth.types'

const formFields: FormField[] = [
  { name: 'nombre', label: 'Nombre', required: true },
  { name: 'email', label: 'Correo', type: 'email', required: true },
  { name: 'password', label: 'Contraseña', type: 'password', helperText: 'Deja vacío para conservar la actual' },
  { name: 'estado', label: 'Estado', type: 'boolean' },
]

export default function UsuariosPage() {
  const hook = useUsers()

  return (
    <CrudPageTemplate<User>
      title="Usuarios"
      subtitle="Gestión de cuentas y estados del sistema"
      items={hook.users}
      isLoading={hook.isLoading}
      isError={hook.isError}
      isCreating={hook.isCreating}
      isUpdating={hook.isUpdating}
      isDeleting={hook.isDeleting}
      refetch={hook.refetch}
      onCreate={hook.createUser}
      onUpdate={hook.updateUser}
      onDelete={hook.deleteUser}
      columns={[
        { id: 'nombre', label: 'Nombre' },
        { id: 'email', label: 'Correo' },
      ]}
      formFields={formFields}
      searchFields={['nombre', 'email']}
      searchPlaceholder="Buscar por nombre o correo"
      entityName="usuario"
      createLabel="Nuevo usuario"
      permission={PERMISSIONS.WRITE_USERS}
      statusField="estado"
      getInitialForm={() => ({ nombre: '', email: '', password: '', estado: true })}
      transformPayload={(form) => {
        const payload: Record<string, any> = { nombre: form.nombre, email: form.email, estado: form.estado }
        if (form.password) payload.password = form.password
        return payload
      }}
    />
  )
}
