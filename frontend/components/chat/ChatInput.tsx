'use client';

import { useState, useRef, useEffect } from 'react';
import {
  Box,
  TextField,
  IconButton,
  Paper,
  InputAdornment,
} from '@mui/material';
import { Send as SendIcon } from '@mui/icons-material';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
  placeholder?: string;
}

export const ChatInput = ({
  onSendMessage,
  isLoading = false,
  placeholder = 'Escribe aquí...',
}: ChatInputProps) => {
  const [message, setMessage] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSend = () => {
    if (message.trim() && !isLoading) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Enfocar el input al cargar
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  return (
    <Paper
      elevation={2}
      sx={{
        p: 1,
        bgcolor: 'background.paper',
        borderRadius: 3,
        display: 'flex',
        alignItems: 'flex-end',
      }}
    >
      <TextField
        inputRef={inputRef}
        multiline
        maxRows={4}
        fullWidth
        placeholder={placeholder}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={isLoading}
        variant="standard"
        sx={{
          '& .MuiInput-root': {
            '&:before': { borderBottom: 'none' },
            '&:after': { borderBottom: 'none' },
            '&:hover:not(.Mui-disabled):before': { borderBottom: 'none' },
          },
        }}
      />
      <IconButton
        color="primary"
        onClick={handleSend}
        disabled={!message.trim() || isLoading}
        sx={{ ml: 1, alignSelf: 'flex-end' }}
      >
        <SendIcon />
      </IconButton>
    </Paper>
  );
};