'use client'

import { useState, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { chatService } from '@/services/api/chat.service'
import { useAuth } from './useAuth'
import { useToast } from './useToast'
import type { Conversation, Message, ChatResponse } from '@/types/chat.types'

export const useChat = () => {
  const { user, estudianteId } = useAuth()
  const { showToast } = useToast()
  const queryClient = useQueryClient()
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null)
  const [isSending, setIsSending] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])

  const userId = user?.id

  const {
    data: conversations = [],
    isLoading: isLoadingConversations,
    refetch: refetchConversations,
  } = useQuery({
    queryKey: ['conversations', userId],
    queryFn: () => chatService.getConversations(userId!),
    enabled: !!userId,
  })

  const sendMessage = useCallback(async (text: string) => {
    if (!userId) return

    setIsSending(true)

    const tempId = -Date.now()
    const userMessage: Message = {
      id: tempId,
      conversacion_id: currentConversationId || 0,
      rol: 'usuario',
      contenido: text,
      creado_en: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])

    try {
      const response: ChatResponse = await chatService.sendMessage({
        usuario_id: userId,
        mensaje: text,
        id_conversacion: currentConversationId || undefined,
        nombre: user?.nombre || 'Usuario',
        estudiante_id: estudianteId || undefined,
      })

      const newConvId = response.id_conversacion
      if (!currentConversationId) {
        setCurrentConversationId(newConvId)
      }

      const botMessage: Message = {
        id: response.id_mensaje,
        conversacion_id: newConvId,
        rol: 'bot',
        contenido: response.respuesta,
        tipo_resolucion: response.tipo_resolucion,
        confianza: response.confianza,
        creado_en: new Date().toISOString(),
      }

      setMessages((prev) => {
        const filtered = prev.filter((m) => m.id !== tempId)
        return [...filtered, userMessage, botMessage]
      })

      queryClient.invalidateQueries({ queryKey: ['conversations', userId] })
    } catch (error: unknown) {
      setMessages((prev) => prev.filter((m) => m.id !== tempId))
      const msg = error instanceof Error ? error.message : 'Error al enviar mensaje'
      showToast(msg, 'error')
    } finally {
      setIsSending(false)
    }
  }, [userId, currentConversationId, user?.nombre, queryClient, showToast])

  const selectConversation = useCallback((id: number) => {
    setCurrentConversationId(id)
    setMessages([])
  }, [])

  const sendFeedback = useCallback(async (messageId: number, util: boolean) => {
    try {
      await chatService.sendFeedback({ id_mensaje: messageId, util })
      showToast('Feedback enviado', 'success')
    } catch {
      showToast('Error al enviar feedback', 'error')
    }
  }, [showToast])

  const newConversation = useCallback(() => {
    setCurrentConversationId(null)
    setMessages([])
  }, [])

  return {
    conversations,
    messages,
    currentConversationId,
    isLoading: isLoadingConversations,
    isSending,
    selectConversation,
    sendMessage,
    sendFeedback,
    newConversation,
    refetchConversations,
  }
}
