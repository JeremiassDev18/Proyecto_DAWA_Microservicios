'use client'

import { useCrud } from './useCrud'
import { adminService } from '@/services/api/admin.service'
import type { Carrera } from '@/types/admin.types'

export function useCarreras() {
  const crud = useCrud<Carrera>(
    {
      list: adminService.getCarreras,
      get: adminService.getCarrera,
      create: (data) => adminService.createCarrera(data),
      update: (id, data) => adminService.updateCarrera(id, data),
      delete: adminService.deleteCarrera,
    },
    'carreras',
    {
      created: 'Carrera creada correctamente',
      updated: 'Carrera actualizada correctamente',
      deleted: 'Carrera eliminada correctamente',
      error: 'No se pudo completar la operación',
    },
  )

  return {
    ...crud,
    carreras: crud.items,
    createCarrera: crud.create,
    updateCarrera: ({ id, payload }: { id: number; payload: Partial<Carrera> }) => crud.update({ id, data: payload }),
    deleteCarrera: crud.remove,
  }
}
