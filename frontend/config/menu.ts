import {
  Dashboard, Chat, Assessment,
  Pending, People, School, CalendarToday, Book, Assignment, Description, Settings,
} from '@mui/icons-material'
import { ROUTES } from './routes'
import { ROLES } from './permissions'

export interface MenuItem {
  icon: typeof Dashboard
  label: string
  path: string
  roles?: string[]
}

export const menuItems: MenuItem[] = [
  { icon: Dashboard, label: 'Dashboard', path: ROUTES.HOME },
  { icon: Chat, label: 'Chat', path: ROUTES.CHAT },
  { icon: Assessment, label: 'Métricas', path: ROUTES.METRICAS, roles: [ROLES.ADMIN, ROLES.MANAGER] },
  { icon: Pending, label: 'Pendientes IA', path: ROUTES.PENDIENTES, roles: [ROLES.ADMIN] },
  { icon: People, label: 'Administración', path: ROUTES.ADMIN_USUARIOS, roles: [ROLES.ADMIN] },
  { icon: School, label: 'Académico', path: ROUTES.ACADEMICO_CARRERAS, roles: [ROLES.ADMIN, ROLES.MANAGER] },
  { icon: CalendarToday, label: 'Tutorías', path: ROUTES.TUTORIAS },
  { icon: Book, label: 'Mis Materias', path: ROUTES.ACADEMICO_MATERIAS, roles: [ROLES.ESTUDIANTE] },
  { icon: Assignment, label: 'Mi Bitácora', path: ROUTES.ACADEMICO_BITACORA, roles: [ROLES.ESTUDIANTE] },
  { icon: Description, label: 'Documentos', path: ROUTES.DOCUMENTOS, roles: [ROLES.ADMIN] },
  { icon: Settings, label: 'Configuración', path: ROUTES.CONFIGURACION },
]
