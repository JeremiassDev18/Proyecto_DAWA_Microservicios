'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { authService } from '@/services/api/auth.service'
import { adminService } from '@/services/api/admin.service'
import { resetLogoutFlag } from '@/services/api'
import type { User } from '@/types/auth.types'
import type { Estudiante } from '@/types/admin.types'
import { ROUTES } from '@/config/routes'

const TOKEN_COOKIE = 'token'
const COOKIE_MAX_AGE = 86400

function setTokenCookie(token: string) {
  document.cookie = `${TOKEN_COOKIE}=${token}; path=/; max-age=${COOKIE_MAX_AGE}; SameSite=Lax`
}

function removeTokenCookie() {
  document.cookie = `${TOKEN_COOKIE}=; path=/; max-age=0; SameSite=Lax`
}

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}

function hasRole(roles: any[] | undefined, roleName: string): boolean {
  if (!roles) return false
  return roles.some(r =>
    (typeof r === 'string' && r.toLowerCase() === roleName.toLowerCase()) ||
    (typeof r === 'object' && r !== null && ((r.nombre || r.rol || '')).toLowerCase() === roleName.toLowerCase())
  )
}

let globalLogout: (() => void) | null = null

export function useAuth() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [estudianteId, setEstudianteId] = useState<number | null>(null)
  const [docenteId, setDocenteId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isLoggingIn, setIsLoggingIn] = useState(false)
  const [token, setToken] = useState<string | null>(null)

  const logout = useCallback(async () => {
    try {
      const currentToken = getCookie('token')
      await authService.logout(currentToken || undefined)
    } catch { /* ignore */ }
    removeTokenCookie()
    setToken(null)
    setUser(null)
    setEstudianteId(null)
    setDocenteId(null)
    router.push(ROUTES.LOGIN)
  }, [router])

  useEffect(() => {
    globalLogout = logout
  }, [logout])

  useEffect(() => {
    const storedToken = getCookie('token')
    if (storedToken) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setToken(storedToken)
      authService.getCurrentUser(storedToken)
        .then(async (userData) => {
          setUser(userData)
          // Buscar estudiante por email si el rol es estudiante
          if (hasRole(userData.roles, 'estudiante') && userData.email) {
            try {
              const estudiante = await adminService.getEstudianteByEmail(userData.email)
              if (estudiante) {
                setEstudianteId(estudiante.id)
              }
            } catch { /* si falla, no hay estudianteId */ }
          }
          // Buscar docente por email si el rol es profesor
          if (hasRole(userData.roles, 'profesor') && userData.email) {
            try {
              const docente = await adminService.getDocenteByEmail(userData.email)
              if (docente) {
                setDocenteId(docente.id)
              }
            } catch { /* si falla, no hay docenteId */ }
          }
        })
        .catch(() => {
          removeTokenCookie()
          setToken(null)
        })
        .finally(() => setIsLoading(false))
    } else {
      setIsLoading(false)
    }
  }, [])

  const login = async (credentials: { email: string; password: string; rememberMe?: boolean }) => {
    setIsLoggingIn(true)
    try {
      const response = await authService.login(credentials)
      setTokenCookie(response.access_token)
      setToken(response.access_token)
      setUser(response.user)
      resetLogoutFlag()
      router.push(ROUTES.HOME)
      return response
    } finally {
      setIsLoggingIn(false)
    }
  }

  return {
    user,
    estudianteId,
    docenteId,
    token,
    isLoading,
    isLoggingIn,
    isAuthenticated: !!token && !!user,
    login,
    logout,
  }
}

export function getGlobalLogout() {
  return globalLogout
}
