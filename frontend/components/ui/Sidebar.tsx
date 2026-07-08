'use client';

import { usePathname } from 'next/navigation';
import {
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Typography,
} from '@mui/material';
import {
  Dashboard,
  Chat,
  Dataset,
  Psychology,
  Assessment,
  Pending,
  People,
  School,
  CalendarToday,
  Description,
  Settings,
} from '@mui/icons-material';

const menuItems = [
  { icon: Dashboard, label: 'Dashboard', path: '/dashboard' },
  { icon: Chat, label: 'Chat', path: '/chat' },
  { icon: Dataset, label: 'Dataset', path: '/dataset' },
  { icon: Psychology, label: 'Entrenamiento', path: '/entrenamiento' },
  { icon: Assessment, label: 'Métricas', path: '/metricas' },
  { icon: Pending, label: 'Pendientes', path: '/pendientes' },
  { icon: People, label: 'Administración', path: '/administracion/usuarios' },
  { icon: School, label: 'Académico', path: '/academico/carreras' },
  { icon: CalendarToday, label: 'Tutorías', path: '/tutorias' },
  { icon: Description, label: 'Documentos', path: '/documentos' },
  { icon: Settings, label: 'Configuración', path: '/configuracion' },
];

export const Sidebar = () => {
  const pathname = usePathname();

  return (
    <Box sx={{ width: 260, height: '100%', bgcolor: 'background.paper' }}>
      <Box sx={{ p: 2, display: 'flex', justifyContent: 'center' }}>
        <Typography variant="h6" color="primary" sx={{ fontWeight: 'bold' }}>
          DAWA
        </Typography>
      </Box>
      <Divider />
      <List>
        {menuItems.map((item) => {
          const isActive = pathname === item.path || pathname.startsWith(item.path + '/');
          return (
            <ListItem
              key={item.path}
              component="a"
              href={item.path}
              sx={{
                '&:hover': { bgcolor: 'action.hover' },
                borderRadius: 1,
                mx: 1,
                bgcolor: isActive ? 'action.selected' : 'transparent',
              }}
            >
              <ListItemIcon>
                <item.icon />
              </ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItem>
          );
        })}
      </List>
    </Box>
  );
};