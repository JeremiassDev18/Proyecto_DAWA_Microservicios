'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { chatService } from '@/services/api/chat.service';
import { useAuth } from './useAuth';
import { useToast } from './useToast';
import { Conversation, Message } from '@/types/chat.types';

export const useChat = () => {
  const { user } = useAuth();
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null);
  const [isSending, setIsSending] = useState(false);

  const userId = user?.id || 1;

  // Obtener conversaciones
  const {
    data: conversations = [],
    isLoading: isLoadingConversations,
    refetch: refetchConversations,
  } = useQuery({
    queryKey: ['conversations', userId],
    queryFn: () => chatService.getConversations(userId),
    enabled: !!userId,
  });

  // Obtener mensajes de la conversación actual
  const {
    data: messages = [],
    isLoading: isLoadingMessages,
    refetch: refetchMessages,
  } = useQuery({
    queryKey: ['messages', currentConversationId],
    queryFn: () => chatService.getMessages(currentConversationId!),
    enabled: !!currentConversationId,
  });

  // Crear conversación
  const createConversationMutation = useMutation({
    mutationFn: (nombre?: string) => chatService.createConversation(userId, nombre),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['conversations', userId] });
      setCurrentConversationId(data.id);
      showToast('Conversación creada', 'success');
    },
    onError: () => {
      showToast('Error al crear conversación', 'error');
    },
  });

  // Eliminar conversación
  const deleteConversationMutation = useMutation({
    mutationFn: (id: number) => chatService.deleteConversation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations', userId] });
      if (currentConversationId) {
        setCurrentConversationId(null);
      }
      showToast('Conversación eliminada', 'success');
    },
    onError: () => {
      showToast('Error al eliminar conversación', 'error');
    },
  });

  // Enviar mensaje
  const sendMessageMutation = useMutation({
    mutationFn: (text: string) => {
      setIsSending(true);
      return chatService.sendMessage({
        usuario_id: userId,
        mensaje: text,
        id_conversacion: currentConversationId || undefined,
        nombre: user?.nombre || 'Usuario',
      });
    },
    onSuccess: (data: any) => {
      if (!currentConversationId) {
        setCurrentConversationId(data.id_conversacion);
      }
      queryClient.invalidateQueries({ queryKey: ['messages', data.id_conversacion] });
      queryClient.invalidateQueries({ queryKey: ['conversations', userId] });
      setIsSending(false);
    },
    onError: (error: any) => {
      setIsSending(false);
      showToast(error.response?.data?.error || 'Error al enviar mensaje', 'error');
    },
  });

  // Feedback
  const feedbackMutation = useMutation({
    mutationFn: ({ messageId, util }: { messageId: number; util: boolean }) =>
      chatService.sendFeedback({ id_mensaje: messageId, util }),
    onSuccess: () => {
      showToast('Feedback enviado', 'success');
    },
    onError: () => {
      showToast('Error al enviar feedback', 'error');
    },
  });

  // Regenerar mensaje
  const regenerateMutation = useMutation({
    mutationFn: (messageId: number) => {
      setIsSending(true);
      return chatService.regenerateMessage(messageId);
    },
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['messages', data.id_conversacion] });
      setIsSending(false);
    },
    onError: (error: any) => {
      setIsSending(false);
      showToast(error.response?.data?.error || 'Error al regenerar', 'error');
    },
  });

  // Seleccionar conversación
  const selectConversation = (id: number) => {
    setCurrentConversationId(id);
  };

  // Crear nueva conversación
  const createConversation = () => {
    createConversationMutation.mutate(undefined);
  };

  // Eliminar conversación
  const deleteConversation = (id: number) => {
    deleteConversationMutation.mutate(id);
  };

  // Enviar mensaje
  const sendMessage = (text: string) => {
    sendMessageMutation.mutate(text);
  };

  // Enviar feedback
  const sendFeedback = (messageId: number, util: boolean) => {
    feedbackMutation.mutate({ messageId, util });
  };

  // Regenerar mensaje
  const regenerateMessage = (messageId: number) => {
    regenerateMutation.mutate(messageId);
  };

  return {
    conversations,
    messages,
    currentConversationId,
    isLoading: isLoadingConversations || isLoadingMessages,
    isSending,
    selectConversation,
    createConversation,
    deleteConversation,
    sendMessage,
    sendFeedback,
    regenerateMessage,
    refetchConversations,
    refetchMessages,
  };
};