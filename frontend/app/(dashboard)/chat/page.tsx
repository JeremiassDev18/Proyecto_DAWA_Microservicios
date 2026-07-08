'use client';

import { useEffect, useRef, useState } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  LinearProgress,
} from '@mui/material';
import { ConversationList } from '@/components/chat/ConversationList';
import { MessageBubble } from '@/components/chat/MessageBubble';
import { ChatInput } from '@/components/chat/ChatInput';
import { useChat } from '@/hooks/useChat';
import { useToast } from '@/hooks/useToast';
import { Message } from '@/types/chat.types';

export default function ChatPage() {
  const {
    conversations,
    messages,
    currentConversationId,
    isLoading,
    isSending,
    selectConversation,
    createConversation,
    deleteConversation,
    sendMessage,
    sendFeedback,
    regenerateMessage,
  } = useChat();

  const { showToast } = useToast();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [intentInfo, setIntentInfo] = useState<{ nombre: string; confianza: number } | null>(null);

  // Scroll al final cuando cambian los mensajes
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Manejar copiar mensaje
  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    showToast('Mensaje copiado', 'success');
  };

  // Manejar feedback
  const handleFeedback = (messageId: number, type: 'positive' | 'negative') => {
    sendFeedback(messageId, type === 'positive');
  };

  // Manejar regeneración
  const handleRegenerate = (messageId: number) => {
    regenerateMessage(messageId);
  };

  // Obtener el último mensaje del bot para mostrar la intención
  useEffect(() => {
    const lastBotMessage = [...messages].reverse().find(m => m.rol === 'bot');
    if (lastBotMessage && lastBotMessage.confianza) {
      setIntentInfo({
        nombre: lastBotMessage.tipo_resolucion || 'Desconocida',
        confianza: lastBotMessage.confianza,
      });
    } else {
      setIntentInfo(null);
    }
  }, [messages]);

  const currentConversation = conversations.find(c => c.id === currentConversationId);

  return (
    <Box sx={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold' }}>
        Chat IA
      </Typography>

      <Grid container sx={{ flex: 1, overflow: 'hidden' }}>
        {/* Sidebar de conversaciones */}
        <Grid size={{ xs: 12, md: 3 }} sx={{ height: '100%', pr: { md: 2 } }}>
          <Paper sx={{ height: '100%', overflow: 'hidden' }}>
            <ConversationList
              conversations={conversations}
              currentConversationId={currentConversationId || undefined}
              onSelectConversation={selectConversation}
              onCreateConversation={createConversation}
              onDeleteConversation={deleteConversation}
              isLoading={isLoading}
            />
          </Paper>
        </Grid>

        {/* Área del chat */}
        <Grid size={{ xs: 12, md: 9 }} sx={{ height: '100%' }}>
          <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            {/* Header del chat */}
            <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
              <Typography variant="h6">
                {currentConversation?.nombre_cliente || 'Nueva conversación'}
              </Typography>
              {currentConversation && (
                <Typography variant="caption" color="text.secondary">
                  {currentConversation.total_mensajes || 0} mensajes
                </Typography>
              )}
            </Box>

            {/* Mensajes */}
            <Box sx={{ flex: 1, overflowY: 'auto', p: 2 }}>
              {isLoading && !messages.length ? (
                <Box sx={{ p: 4, textAlign: 'center' }}>
                  <LinearProgress />
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                    Cargando mensajes...
                  </Typography>
                </Box>
              ) : messages.length === 0 ? (
                <Box sx={{ p: 4, textAlign: 'center', color: 'text.secondary' }}>
                  <Typography variant="body1">
                    {currentConversationId
                      ? 'No hay mensajes en esta conversación'
                      : 'Selecciona o crea una conversación para empezar'}
                  </Typography>
                </Box>
              ) : (
                <>
                  {messages.map((msg: Message) => (
                    <MessageBubble
                      key={msg.id}
                      message={msg}
                      isUser={msg.rol === 'usuario'}
                      onCopy={handleCopy}
                      onRegenerate={msg.rol === 'bot' ? handleRegenerate : undefined}
                      onFeedback={msg.rol === 'bot' ? handleFeedback : undefined}
                    />
                  ))}
                  {isSending && (
                    <MessageBubble
                      message={{
                        id: -1,
                        conversacion_id: currentConversationId || -1,
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

            {/* Info de intención */}
            {intentInfo && (
              <Box sx={{ px: 2, py: 0.5, bgcolor: 'grey.50', borderTop: 1, borderColor: 'divider' }}>
                <Typography variant="caption" color="text.secondary">
                  Intención: <strong>{intentInfo.nombre}</strong> | 
                  Confianza: <strong>{Math.round(intentInfo.confianza * 100)}%</strong>
                </Typography>
              </Box>
            )}

            {/* Input */}
            <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
              <ChatInput
                onSendMessage={sendMessage}
                isLoading={isSending}
                placeholder={currentConversationId ? 'Escribe aquí...' : 'Inicia una conversación primero'}
              />
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}