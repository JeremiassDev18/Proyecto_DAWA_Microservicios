'use client'

import { Card, CardContent, Typography, Box, Skeleton, useTheme } from '@mui/material'
import type { SvgIconComponent } from '@mui/icons-material'

interface StatCardProps {
  title: string
  value: string | number
  icon: SvgIconComponent
  color?: string
  loading?: boolean
  onClick?: () => void
}

export function StatCard({ title, value, icon: Icon, color, loading, onClick }: StatCardProps) {
  const theme = useTheme()
  const resolvedColor = color || theme.palette.primary.main

  return (
    <Card
      onClick={onClick}
      sx={{
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 200ms ease',
        '&:hover': onClick ? { transform: 'translateY(-2px)', boxShadow: 4 } : {},
      }}
    >
      <CardContent sx={{ p: 3, '&:last-child': { pb: 3 } }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
              {title}
            </Typography>
            {loading ? (
              <Skeleton width={80} height={36} sx={{ mt: 0.5 }} />
            ) : (
              <Typography variant="h3" sx={{ mt: 0.5, fontWeight: 700 }}>
                {value}
              </Typography>
            )}
          </Box>
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: 3,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: `${resolvedColor}14`,
              color: resolvedColor,
            }}
          >
            <Icon sx={{ fontSize: 24 }} />
          </Box>
        </Box>
      </CardContent>
    </Card>
  )
}
