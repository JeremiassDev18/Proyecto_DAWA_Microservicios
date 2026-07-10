'use client'

import { useEffect, useMemo, useRef } from 'react'
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Tooltip,
} from '@mui/material'
import { DeleteSweep as CleanIcon } from '@mui/icons-material'
import { MessageBubble } from '@/components/chat/MessageBubble'
import { ChatInput } from '@/components/chat/ChatInput'
import { useChat } from '@/hooks/useChat'
import { useToast } from '@/hooks/useToast'

export default function ChatPage() {
  const {
    messages,
    isLoading,
    isSending,
    sendMessage,
    sendFeedback,
    clearChat,
  } = useChat()

  const { showToast } = useToast()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const intentInfo = useMemo(() => {
    const lastBotMessage = [...messages].reverse().find(m => m.rol === 'bot')
    if (lastBotMessage && lastBotMessage.confianza) {
      return { nombre: lastBotMessage.tipo_resolucion || 'Desconocida', confianza: lastBotMessage.confianza }
    }
    return null
  }, [messages])

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text)
    showToast('Mensaje copiado', 'success')
  }

  const handleFeedback = (messageId: number, type: 'positive' | 'negative') => {
    sendFeedback(messageId, type === 'positive')
  }

  const handleClear = () => {
    clearChat()
    showToast('Chat limpiado', 'success')
  }

  return (
    <Box sx={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
          Chat IA
        </Typography>
        <Tooltip title="Limpiar chat">
          <IconButton onClick={handleClear} color="default" size="small">
            <CleanIcon />
          </IconButton>
        </Tooltip>
      </Box>

      <Paper sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <Box sx={{ flex: 1, overflowY: 'auto', p: 2 }}>
          {messages.length === 0 ? (
            <Box sx={{ p: 4, textAlign: 'center', color: 'text.secondary' }}>
              <Typography variant="body1">
                Escribe un mensaje para empezar
              </Typography>
            </Box>
          ) : (
            <>
              {messages.map((msg) => (
                <MessageBubble
                  key={msg.id}
                  message={msg}
                  isUser={msg.rol === 'usuario'}
                  onCopy={handleCopy}
                  onFeedback={msg.rol === 'bot' ? handleFeedback : undefined}
                />
              ))}
              {isSending && (
                <MessageBubble
                  message={{
                    id: -1,
                    conversacion_id: 0,
                    rol: 'bot',
                    contenido: '',
                    creado_en: new Date().toISOString(),
                  }}
                  isUser={false}
                  isLoading={true}
                />
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </Box>

        {intentInfo && (
          <Box sx={{ px: 2, py: 0.5, bgcolor: 'grey.50', borderTop: 1, borderColor: 'divider' }}>
            <Typography variant="caption" color="text.secondary">
              Intención: <strong>{intentInfo.nombre}</strong> |
              Confianza: <strong>{Math.round(intentInfo.confianza * 100)}%</strong>
            </Typography>
          </Box>
        )}

        <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
          <ChatInput
            onSendMessage={sendMessage}
            isLoading={isSending}
            placeholder="Escribe aquí..."
          />
        </Box>
      </Paper>
    </Box>
  )
}
