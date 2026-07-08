'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { trainingService } from '@/services/api/training.service'
import { useToast } from './useToast'

export function useTraining() {
  const { showToast } = useToast()

  const modelsQuery = useQuery({
    queryKey: ['models'],
    queryFn: () => trainingService.getModels(),
  })

  const metricsQuery = useQuery({
    queryKey: ['modelMetrics'],
    queryFn: () => trainingService.getModelMetrics(),
  })

  const trainMutation = useMutation({
    mutationFn: () => trainingService.train(),
    onSuccess: () => {
      showToast('Entrenamiento iniciado', 'success')
    },
    onError: () => showToast('No se pudo iniciar el entrenamiento', 'error'),
  })

  return {
    models: modelsQuery.data ?? [],
    isLoadingModels: modelsQuery.isLoading,
    metrics: metricsQuery.data,
    isLoadingMetrics: metricsQuery.isLoading,
    startTraining: trainMutation.mutate,
    isTraining: trainMutation.isPending,
    taskId: trainMutation.data?.task_id,
  }
}

export function usePending() {
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const query = useQuery({
    queryKey: ['pending'],
    queryFn: () => trainingService.getPending(),
  })

  const convertMutation = useMutation({
    mutationFn: (id: number) => trainingService.convertPending(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending'] })
      showToast('Convertido a dataset', 'success')
    },
    onError: () => showToast('Error al convertir', 'error'),
  })

  const resolveMutation = useMutation({
    mutationFn: (id: number) => trainingService.resolvePending(id),
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
    convertToDataset: convertMutation.mutate,
    isConverting: convertMutation.isPending,
    resolve: resolveMutation.mutate,
    isResolving: resolveMutation.isPending,
  }
}

export function useDocuments() {
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const query = useQuery({
    queryKey: ['documents'],
    queryFn: () => trainingService.getDocuments(),
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => trainingService.createDocument(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      showToast('Documento creado', 'success')
    },
    onError: () => showToast('Error al crear documento', 'error'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => trainingService.updateDocument(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      showToast('Documento actualizado', 'success')
    },
    onError: () => showToast('Error al actualizar documento', 'error'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => trainingService.deleteDocument(id),
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
    queryFn: () => trainingService.getUsageMetrics(),
    staleTime: 30 * 1000,
  })
}
