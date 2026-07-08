'use client'

import { Box, Typography, Button, Skeleton } from '@mui/material'
import { Add } from '@mui/icons-material'

interface PageContainerProps {
  title: string
  subtitle?: string
  loading?: boolean
  action?: {
    label: string
    onClick: () => void
    icon?: React.ReactNode
  }
  children: React.ReactNode
}

export function PageContainer({ title, subtitle, loading, action, children }: PageContainerProps) {
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
        <Box>
          {loading ? (
            <>
              <Skeleton width={200} height={32} />
              <Skeleton width={300} height={20} sx={{ mt: 0.5 }} />
            </>
          ) : (
            <>
              <Typography variant="h4" sx={{ fontWeight: 700, letterSpacing: '-0.02em' }}>
                {title}
              </Typography>
              {subtitle && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                  {subtitle}
                </Typography>
              )}
            </>
          )}
        </Box>
        {action && (
          <Button variant="contained" startIcon={action.icon || <Add />} onClick={action.onClick}>
            {action.label}
          </Button>
        )}
      </Box>
      {children}
    </Box>
  )
}
