'use client'

import { useQuery } from '@tanstack/react-query'
import { adminService } from '@/services/api/admin.service'
import type { DashboardStats } from '@/types/admin.types'

export function useDashboard() {
  return useQuery<DashboardStats>({
    queryKey: ['dashboard'],
    queryFn: () => adminService.getDashboardStats(),
    staleTime: 30 * 1000,
  })
}
