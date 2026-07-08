import { api } from '@/services/api'
import type { User, AuthResponse } from '@/types/auth.types'

export const authService = {
  login: async (credentials: { email: string; password: string; rememberMe?: boolean }): Promise<AuthResponse> => {
    return api.security.post<AuthResponse>('/login', credentials)
  },

  logout: async (token?: string): Promise<void> => {
    try {
      const headers: Record<string, string> = {}
      if (token) headers.Authorization = `Bearer ${token}`
      await api.security.post('/logout', {}, { headers } as any)
    } catch { /* ignore */ }
  },

  getCurrentUser: async (token: string): Promise<User> => {
    return api.security.get<User>('/usuarios/me', {
      headers: { Authorization: `Bearer ${token}` },
    } as any)
  },

  recoverPassword: async (email: string): Promise<void> => {
    await api.security.post('/usuarios/recuperar-contrasena', { email })
  },

  changePassword: async (userId: number, data: { current_password: string; new_password: string; new_password_confirm: string }): Promise<void> => {
    await api.security.post(`/usuarios/${userId}/cambiar-contrasena`, data)
  },
}
