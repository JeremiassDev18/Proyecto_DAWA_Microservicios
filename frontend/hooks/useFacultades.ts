'use client'

import { useCrud } from './useCrud'
import { adminService } from '@/services/api/admin.service'
import type { Facultad } from '@/types/admin.types'

export function useFacultades() {
  const crud = useCrud<Facultad>(
    {
      list: adminService.getFacultades,
      get: adminService.getFacultad,
      create: adminService.createFacultad,
      update: (id, data) => adminService.updateFacultad(id, data),
      delete: adminService.deleteFacultad,
    },
    'facultades',
    {
      created: 'Facultad creada correctamente',
      updated: 'Facultad actualizada correctamente',
      deleted: 'Facultad eliminada correctamente',
      error: 'No se pudo completar la operación',
    },
  )

  return {
    ...crud,
    facultades: crud.items,
    createFacultad: crud.create,
    updateFacultad: ({ id, payload }: { id: number; payload: Partial<Facultad> }) => crud.update({ id, data: payload }),
    deleteFacultad: crud.remove,
  }
}
