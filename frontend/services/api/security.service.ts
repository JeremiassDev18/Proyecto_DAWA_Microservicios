import { api } from '@/services/api'
import type { User } from '@/types/auth.types'
import type { Role } from '@/types/admin.types'

export const securityService = {
  getUsers: async (): Promise<User[]> => {
    const data = await api.security.get<any>('/usuarios')
    return data.usuarios || data
  },
  getUser: async (id: number): Promise<User> => {
    return api.security.get<User>(`/usuarios/${id}`)
  },
  createUser: async (data: { nombre: string; email: string; password: string; estado?: boolean }): Promise<User> => {
    const response = await api.security.post<any>('/usuarios', data)
    return response.usuario || response
  },
  updateUser: async (id: number, data: Partial<User> & { password?: string; estado?: boolean }): Promise<User> => {
    const response = await api.security.put<any>(`/usuarios/${id}`, data)
    return response.usuario || response
  },
  deleteUser: async (id: number): Promise<void> => {
    await api.security.delete(`/usuarios/${id}`)
  },

  getRoles: async (): Promise<Role[]> => {
    const data = await api.security.get<any>('/roles')
    return data.roles || data
  },
  getRole: async (id: number): Promise<Role> => {
    return api.security.get<Role>(`/roles/${id}`)
  },
  createRole: async (data: { nombre_rol: string; descripcion?: string }): Promise<Role> => {
    const response = await api.security.post<any>('/roles', data)
    return response.rol || response
  },
  updateRole: async (id: number, data: { nombre_rol: string; descripcion?: string }): Promise<Role> => {
    const response = await api.security.put<any>(`/roles/${id}`, data)
    return response.rol || response
  },
  deleteRole: async (id: number): Promise<void> => {
    await api.security.delete(`/roles/${id}`)
  },

  getPermissions: async () => {
    const data = await api.security.get<any>('/permisos')
    return data.permisos || data
  },
}
