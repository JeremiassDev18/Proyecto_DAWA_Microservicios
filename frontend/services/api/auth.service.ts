import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_GATEWAY || 'http://localhost:8080';

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface User {
  id: number;
  email: string;
  nombre: string;
  roles: string[];
  permissions: string[];
}

export interface AuthResponse {
  access_token: string;
  refresh_token?: string;
  user: User;
}

export const authService = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    try {
      const response = await axios.post(`${API_URL}/security/login`, credentials);
      return response.data;
    } catch (error: any) {
      throw error.response?.data || { error: 'Error al iniciar sesión' };
    }
  },

  logout: async (): Promise<void> => {
    try {
      await axios.post(`${API_URL}/security/logout`);
    } catch {
      // Ignorar errores en logout
    }
  },

  getCurrentUser: async (token: string): Promise<User> => {
    const response = await axios.get(`${API_URL}/security/usuarios/me`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },

  recoverPassword: async (email: string): Promise<void> => {
    await axios.post(`${API_URL}/security/usuarios/recuperar-contrasena`, { email });
  },

  changePassword: async (userId: number, data: any): Promise<void> => {
    await axios.post(`${API_URL}/security/usuarios/${userId}/cambiar-contrasena`, data);
  }
};