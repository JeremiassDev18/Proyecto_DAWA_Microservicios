'use client'

import { useState } from 'react'
import {
  Box,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  Typography,
  TextField,
  InputAdornment,
  Divider,
  CircularProgress,
  Chip,
} from '@mui/material'
import {
  Add as AddIcon,
  Search as SearchIcon,
} from '@mui/icons-material'
import { Conversation } from '@/types/chat.types'

interface ConversationListProps {
  conversations: Conversation[]
  currentConversationId?: number
  onSelectConversation: (id: number) => void
  onNewConversation: () => void
  isLoading?: boolean
}

export const ConversationList = ({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  isLoading = false,
}: ConversationListProps) => {
  const [searchTerm, setSearchTerm] = useState('')

  const filteredConversations = conversations.filter(conv =>
    conv.nombre_cliente?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    conv.id.toString().includes(searchTerm)
  )

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (days === 0) return 'Hoy'
    if (days === 1) return 'Ayer'
    if (days < 7) return `Hace ${days} días`
    return date.toLocaleDateString('es-ES')
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 'bold' }} gutterBottom>
          Conversaciones
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
          <TextField
            placeholder="Buscar..."
            size="small"
            fullWidth
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            slotProps={{
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon fontSize="small" />
                  </InputAdornment>
                ),
              },
            }}
          />
          <Box
            onClick={onNewConversation}
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 40,
              height: 40,
              borderRadius: 2,
              cursor: 'pointer',
              bgcolor: 'primary.main',
              color: 'white',
              flexShrink: 0,
              '&:hover': { opacity: 0.85 },
            }}
          >
            <AddIcon />
          </Box>
        </Box>
        <Divider />
      </Box>

      <Box sx={{ flex: 1, overflowY: 'auto', px: 1 }}>
        {isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress size={30} />
          </Box>
        ) : filteredConversations.length === 0 ? (
          <Box sx={{ textAlign: 'center', p: 4, color: 'text.secondary' }}>
            <Typography variant="body2">
              {searchTerm ? 'No se encontraron conversaciones' : 'No hay conversaciones aún'}
            </Typography>
          </Box>
        ) : (
          <List disablePadding>
            {filteredConversations.map((conv) => {
              const isActive = conv.id === currentConversationId
              return (
                <ListItem key={conv.id} disablePadding>
                  <ListItemButton
                    selected={isActive}
                    onClick={() => onSelectConversation(conv.id)}
                    sx={{
                      borderRadius: 1,
                      '&.Mui-selected': {
                        bgcolor: 'primary.light',
                        '&:hover': { bgcolor: 'primary.light' },
                      },
                    }}
                  >
                    <ListItemText
                      primary={conv.nombre_cliente || `Conversación ${conv.id}`}
                      secondary={
                        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                          <span>{formatDate(conv.iniciado_en)}</span>
                          {conv.total_mensajes !== undefined && (
                            <Chip
                              label={`${conv.total_mensajes} mensajes`}
                              size="small"
                              variant="outlined"
                              sx={{ height: 18, fontSize: '0.6rem' }}
                            />
                          )}
                        </Box>
                      }
                      slotProps={{
                        primary: {
                          variant: 'body2',
                          sx: { fontWeight: isActive ? 'bold' : 'normal' },
                        },
                        secondary: { variant: 'caption' },
                      }}
                    />
                  </ListItemButton>
                </ListItem>
              )
            })}
          </List>
        )}
      </Box>
    </Box>
  )
}
