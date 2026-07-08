'use client'

import { useCrud } from './useCrud'
import { datasetService } from '@/services/api/dataset.service'
import type { DatasetEntry } from '@/types/dataset.types'

export function useDataset() {
  const crud = useCrud<DatasetEntry>(
    {
      list: () => datasetService.list(),
      create: (data) => datasetService.create(data),
      update: (id, data) => datasetService.update(id, data),
      delete: (id) => datasetService.delete(id),
    },
    'dataset',
    {
      created: 'Ejemplo creado correctamente',
      updated: 'Ejemplo actualizado correctamente',
      deleted: 'Ejemplo eliminado correctamente',
      error: 'No se pudo completar la operación',
    },
  )

  return {
    ...crud,
    dataset: crud.items,
  }
}
