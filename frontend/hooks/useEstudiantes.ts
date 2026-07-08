'use client'

import { useCrud } from './useCrud'
import { adminService } from '@/services/api/admin.service'
import type { Estudiante } from '@/types/admin.types'

export function useEstudiantes() {
  const crud = useCrud<Estudiante>(
    {
      list: adminService.getEstudiantes,
      get: adminService.getEstudiante,
      create: (data) => adminService.createEstudiante(data),
      update: (id, data) => adminService.updateEstudiante(id, data),
      delete: adminService.deleteEstudiante,
    },
    'estudiantes',
    {
      created: 'Estudiante creado correctamente',
      updated: 'Estudiante actualizado correctamente',
      deleted: 'Estudiante eliminado correctamente',
      error: 'No se pudo completar la operación',
    },
  )

  return {
    ...crud,
    estudiantes: crud.items,
    createEstudiante: crud.create,
    updateEstudiante: ({ id, payload }: { id: number; payload: Partial<Estudiante> }) => crud.update({ id, data: payload }),
    deleteEstudiante: crud.remove,
  }
}
