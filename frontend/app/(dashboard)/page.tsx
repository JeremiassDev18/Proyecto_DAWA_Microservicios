'use client';

import { useAuth } from '@/hooks/useAuth';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
} from '@mui/material';
import {
  People,
  School,
  Chat,
  SmartToy,
  Pending,
  Dataset,
} from '@mui/icons-material';

const stats = [
  { title: 'Usuarios', value: 1245, icon: People, color: '#1976d2' },
  { title: 'Docentes', value: 48, icon: School, color: '#2e7d32' },
  { title: 'Tutorías Activas', value: 26, icon: Chat, color: '#9c27b0' },
  { title: 'Modelo IA', value: 'v18 (95%)', icon: SmartToy, color: '#ed6c02' },
  { title: 'Pendientes IA', value: 14, icon: Pending, color: '#d32f2f' },
  { title: 'Dataset', value: '620 ejemplos', icon: Dataset, color: '#00897b' },
];

const DashboardCard = ({ title, value, icon: Icon, color }: any) => (
  <Card sx={{ height: '100%', transition: 'transform 0.2s', '&:hover': { transform: 'scale(1.02)' } }}>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography color="textSecondary" gutterBottom variant="caption">
            {title}
          </Typography>
          <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
            {value}
          </Typography>
        </Box>
        <Icon sx={{ fontSize: 40, color }} />
      </Box>
    </CardContent>
  </Card>
);

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
            Dashboard
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            Bienvenido, {user?.nombre || 'Usuario'}
          </Typography>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {stats.map((stat, index) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={index}>
            <DashboardCard {...stat} />
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}