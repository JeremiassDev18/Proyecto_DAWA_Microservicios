export const PERMISSIONS = {
  READ_USERS: 'read_users',
  WRITE_USERS: 'write_users',
  READ_REPORTS: 'read_reports',
  READ_TUTORIAS: 'read_tutorias',
  WRITE_TUTORIAS: 'write_tutorias',
  READ_ROLES: 'read_roles',
  WRITE_ROLES: 'write_roles',
  READ_PERMISOS: 'read_permisos',
  WRITE_PERMISOS: 'write_permisos',
} as const

export type Permission = (typeof PERMISSIONS)[keyof typeof PERMISSIONS]

export const ROLES = {
  ADMIN: 'admin',
  ESTUDIANTE: 'estudiante',
  PROFESOR: 'profesor',
  MANAGER: 'manager',
  VIEWER: 'viewer',
} as const

export type Rol = (typeof ROLES)[keyof typeof ROLES]
