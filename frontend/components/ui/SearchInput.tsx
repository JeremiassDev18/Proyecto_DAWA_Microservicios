'use client'

import { TextField, InputAdornment } from '@mui/material'
import { Search } from '@mui/icons-material'

interface SearchInputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

export function SearchInput({ value, onChange, placeholder = 'Buscar...' }: SearchInputProps) {
  return (
    <TextField
      size="small"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      slotProps={{
        input: {
          startAdornment: (
            <InputAdornment position="start">
              <Search sx={{ color: 'text.disabled', fontSize: 20 }} />
            </InputAdornment>
          ),
        },
      }}
      sx={{ minWidth: 280 }}
    />
  )
}
