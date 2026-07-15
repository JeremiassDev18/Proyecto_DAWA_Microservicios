'use client'

import { useAuth } from '@/hooks/useAuth'

interface PermissionGuardProps {
  permission?: string
  role?: string
  children: React.ReactNode
  fallback?: React.ReactNode
}

export function PermissionGuard({ permission, role, children, fallback = null }: PermissionGuardProps) {
  const { user } = useAuth()

  if (!user) return fallback

  if (permission && !user.permissions?.includes(permission)) return fallback
  if (role && !user.roles?.includes(role)) return fallback

  return <>{children}</>
}
