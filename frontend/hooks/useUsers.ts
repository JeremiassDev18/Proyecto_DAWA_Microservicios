'use client'

import { useCrud } from './useCrud'
import { securityService } from '@/services/api/security.service'
import type { User } from '@/types/auth.types'

export function useUsers() {
  const crud = useCrud<User, { nombre: string; email: string; password: string; estado?: boolean }>(
    {
      list: securityService.getUsers,
      get: securityService.getUser,
      create: securityService.createUser,
      update: (id, data) => securityService.updateUser(id, data),
      delete: securityService.deleteUser,
    },
    'users',
    {
      created: 'Usuario creado correctamente',
      updated: 'Usuario actualizado correctamente',
      deleted: 'Usuario eliminado correctamente',
      error: 'No se pudo completar la operación',
    },
  )

  return {
    ...crud,
    users: crud.items,
    createUser: crud.create,
    updateUser: ({ id, payload }: { id: number; payload: Partial<User> & { password?: string; estado?: boolean } }) =>
      crud.update({ id, data: payload }),
    deleteUser: crud.remove,
  }
}
