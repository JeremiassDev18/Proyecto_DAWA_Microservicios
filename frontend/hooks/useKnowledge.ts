'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { knowledgeService } from '@/services/api/knowledge.service'
import { useToast } from './useToast'

export function usePending() {
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const query = useQuery({
    queryKey: ['pending'],
    queryFn: () => knowledgeService.getPending(),
  })

  const resolveMutation = useMutation({
    mutationFn: (id: number) => knowledgeService.resolvePending(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending'] })
      showToast('Marcado como resuelto', 'success')
    },
    onError: () => showToast('Error al resolver', 'error'),
  })

  return {
    pending: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    resolve: resolveMutation.mutate,
    isResolving: resolveMutation.isPending,
  }
}

export function useDocuments() {
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const query = useQuery({
    queryKey: ['documents'],
    queryFn: () => knowledgeService.getDocuments(),
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => knowledgeService.createDocument(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      showToast('Documento creado', 'success')
    },
    onError: () => showToast('Error al crear documento', 'error'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => knowledgeService.updateDocument(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      showToast('Documento actualizado', 'success')
    },
    onError: () => showToast('Error al actualizar documento', 'error'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => knowledgeService.deleteDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      showToast('Documento eliminado', 'success')
    },
    onError: () => showToast('Error al eliminar documento', 'error'),
  })

  return {
    documents: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    createDocument: createMutation.mutate,
    updateDocument: updateMutation.mutate,
    deleteDocument: deleteMutation.mutate,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  }
}

export function useUsageMetrics() {
  return useQuery({
    queryKey: ['usageMetrics'],
    queryFn: () => knowledgeService.getUsageMetrics(),
    staleTime: 30 * 1000,
  })
}
