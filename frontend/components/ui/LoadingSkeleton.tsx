'use client'

import { Box, Skeleton, Card } from '@mui/material'

interface LoadingSkeletonProps {
  type?: 'card' | 'table' | 'list'
  count?: number
}

export function LoadingSkeleton({ type = 'card', count = 6 }: LoadingSkeletonProps) {
  if (type === 'card') {
    return (
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 3 }}>
        {Array.from({ length: count }).map((_, i) => (
          <Card key={i} sx={{ p: 3 }}>
            <Skeleton width={80} height={16} />
            <Skeleton width={120} height={36} sx={{ mt: 1 }} />
            <Skeleton width="60%" height={48} sx={{ mt: 2, borderRadius: 3 }} />
          </Card>
        ))}
      </Box>
    )
  }

  if (type === 'table') {
    return (
      <Box>
        <Skeleton variant="rectangular" height={48} sx={{ mb: 1, borderRadius: 2 }} />
        {Array.from({ length: count }).map((_, i) => (
          <Skeleton key={i} variant="rectangular" height={52} sx={{ mb: 0.5, borderRadius: 2 }} />
        ))}
      </Box>
    )
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} variant="rectangular" height={72} sx={{ borderRadius: 3 }} />
      ))}
    </Box>
  )
}
