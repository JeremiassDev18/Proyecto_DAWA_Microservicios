import { apiClient } from '../axios.config';

const client = apiClient.getClient('admin');

export interface DashboardStats {
  usuarios: number;
  docentes_activos: number;
  tutorias_activas: number;
  modelo_version: string;
  pendientes_ia: number;
  dataset_size: number;
}

export const adminService = {
  getDashboardStats: async (): Promise<DashboardStats> => {
    const response = await client.get('/dashboard/');
    return response.data;
  },
};