'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useToast } from './useToast'

interface CrudService<T, C = Partial<T>, U = Partial<T>> {
  list?: () => Promise<T[]>
  get?: (id: number) => Promise<T>
  create?: (data: C) => Promise<T>
  update?: (id: number, data: U) => Promise<T>
  delete?: (id: number) => Promise<void>
}

export function useCrud<T, C = Partial<T>, U = Partial<T>>(
  service: CrudService<T, C, U>,
  queryKey: string,
  messages?: {
    created?: string
    updated?: string
    deleted?: string
    error?: string
  },
) {
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const msg = {
    created: 'Creado exitosamente',
    updated: 'Actualizado exitosamente',
    deleted: 'Eliminado exitosamente',
    error: 'Error en la operación',
    ...messages,
  }

  const listQuery = useQuery({
    queryKey: [queryKey],
    queryFn: () => service.list!(),
    enabled: !!service.list,
  })

  const createMutation = useMutation({
    mutationFn: (data: C) => service.create!(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [queryKey] })
      showToast(msg.created, 'success')
    },
    onError: () => showToast(msg.error, 'error'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: U }) => service.update!(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [queryKey] })
      showToast(msg.updated, 'success')
    },
    onError: () => showToast(msg.error, 'error'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => service.delete!(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [queryKey] })
      showToast(msg.deleted, 'success')
    },
    onError: () => showToast(msg.error, 'error'),
  })

  return {
    items: listQuery.data ?? [],
    isLoading: listQuery.isLoading,
    isError: listQuery.isError,
    error: listQuery.error,
    refetch: listQuery.refetch,
    create: createMutation.mutate,
    update: updateMutation.mutate,
    remove: deleteMutation.mutate,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  }
}
