'use client';

import { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Tooltip,
  Chip,
} from '@mui/material';
import {
  ContentCopy,
  ThumbUp,
  ThumbDown,
  Refresh,
} from '@mui/icons-material';
import { Message } from '@/types/chat.types';

interface MessageBubbleProps {
  message: Message;
  isUser: boolean;
  onCopy?: (text: string) => void;
  onRegenerate?: (messageId: number) => void;
  onFeedback?: (messageId: number, type: 'positive' | 'negative') => void;
  showActions?: boolean;
  isLoading?: boolean;
}

export const MessageBubble = ({
  message,
  isUser,
  onCopy,
  onRegenerate,
  onFeedback,
  showActions = true,
  isLoading = false,
}: MessageBubbleProps) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (onCopy) {
      onCopy(message.contenido);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: isUser ? 'flex-end' : 'flex-start',
        mb: 2,
        maxWidth: '85%',
        mx: isUser ? 'auto 0 0 auto' : '0 auto auto 0',
      }}
    >
      <Paper
        elevation={0}
        sx={{
          p: 2,
          bgcolor: isUser ? 'primary.main' : 'grey.100',
          color: isUser ? 'white' : 'text.primary',
          borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
          maxWidth: '100%',
          wordBreak: 'break-word',
          position: 'relative',
        }}
      >
        {isLoading ? (
          <Box sx={{ display: 'flex', gap: 0.5, p: 1 }}>
            <Box sx={{ width: 8, height: 8, bgcolor: 'grey.400', borderRadius: '50%', animation: 'pulse 1.5s infinite' }} />
            <Box sx={{ width: 8, height: 8, bgcolor: 'grey.400', borderRadius: '50%', animation: 'pulse 1.5s infinite 0.3s' }} />
            <Box sx={{ width: 8, height: 8, bgcolor: 'grey.400', borderRadius: '50%', animation: 'pulse 1.5s infinite 0.6s' }} />
          </Box>
        ) : (
          <>
            <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
              {message.contenido}
            </Typography>
            {message.confianza && (
              <Chip
                label={`Confianza: ${Math.round(message.confianza * 100)}%`}
                size="small"
                color={message.confianza > 0.7 ? 'success' : 'warning'}
                sx={{ mt: 1, height: 20, fontSize: '0.65rem' }}
              />
            )}
            {message.tipo_resolucion && (
              <Chip
                label={`Tipo: ${message.tipo_resolucion}`}
                size="small"
                variant="outlined"
                sx={{ mt: 1, ml: 1, height: 20, fontSize: '0.65rem' }}
              />
            )}
          </>
        )}
      </Paper>

      {/* Acciones */}
      {!isUser && !isLoading && showActions && (
        <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
          <Tooltip title={copied ? '¡Copiado!' : 'Copiar'}>
            <IconButton size="small" onClick={handleCopy}>
              <ContentCopy fontSize="small" />
            </IconButton>
          </Tooltip>
          {onRegenerate && (
            <Tooltip title="Regenerar">
              <IconButton size="small" onClick={() => onRegenerate(message.id)}>
                <Refresh fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {onFeedback && (
            <>
              <Tooltip title="Útil">
                <IconButton size="small" onClick={() => onFeedback(message.id, 'positive')}>
                  <ThumbUp fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title="No útil">
                <IconButton size="small" onClick={() => onFeedback(message.id, 'negative')}>
                  <ThumbDown fontSize="small" />
                </IconButton>
              </Tooltip>
            </>
          )}
          <Typography variant="caption" color="text.secondary" sx={{ ml: 1, alignSelf: 'center' }}>
            {formatTime(message.creado_en)}
          </Typography>
        </Box>
      )}
    </Box>
  );
};