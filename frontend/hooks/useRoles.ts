'use client'

import { useCrud } from './useCrud'
import { securityService } from '@/services/api/security.service'
import type { Role } from '@/types/admin.types'

export function useRoles() {
  const crud = useCrud<Role, { nombre_rol: string; descripcion?: string }, { nombre_rol: string; descripcion?: string }>(
    {
      list: securityService.getRoles,
      get: securityService.getRole,
      create: securityService.createRole,
      update: (id, data) => securityService.updateRole(id, data),
      delete: securityService.deleteRole,
    },
    'roles',
    {
      created: 'Rol creado correctamente',
      updated: 'Rol actualizado correctamente',
      deleted: 'Rol eliminado correctamente',
      error: 'No se pudo completar la operación',
    },
  )

  return {
    ...crud,
    roles: crud.items,
    createRole: crud.create,
    updateRole: ({ id, payload }: { id: number; payload: { nombre_rol: string; descripcion?: string } }) =>
      crud.update({ id, data: payload }),
    deleteRole: crud.remove,
  }
}
