'use client'

import { Card, CardContent, Typography, Box } from '@mui/material'

interface ChartCardProps {
  title: string
  subtitle?: string
  children: React.ReactNode
  height?: number
}

export function ChartCard({ title, subtitle, children, height = 300 }: ChartCardProps) {
  return (
    <Card>
      <CardContent>
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="caption" color="text.secondary">
              {subtitle}
            </Typography>
          )}
        </Box>
        <Box sx={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {children}
        </Box>
      </CardContent>
    </Card>
  )
}
