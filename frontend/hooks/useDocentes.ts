'use client'

import { useCrud } from './useCrud'
import { adminService } from '@/services/api/admin.service'
import type { Docente } from '@/types/admin.types'

export function useDocentes() {
  const crud = useCrud<Docente>(
    {
      list: adminService.getDocentes,
      get: adminService.getDocente,
      create: (data) => adminService.createDocente(data),
      update: (id, data) => adminService.updateDocente(id, data),
      delete: adminService.deleteDocente,
    },
    'docentes',
    {
      created: 'Docente creado correctamente',
      updated: 'Docente actualizado correctamente',
      deleted: 'Docente eliminado correctamente',
      error: 'No se pudo completar la operación',
    },
  )

  return {
    ...crud,
    docentes: crud.items,
    createDocente: crud.create,
    updateDocente: ({ id, payload }: { id: number; payload: Partial<Docente> }) => crud.update({ id, data: payload }),
    deleteDocente: crud.remove,
  }
}
