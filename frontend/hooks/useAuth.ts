'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService, User } from '@/services/api/auth.service';

export const useAuth = () => {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    // Cargar token del localStorage al iniciar
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
      // Intentar obtener el usuario
      authService.getCurrentUser(storedToken)
        .then(userData => setUser(userData))
        .catch(() => {
          localStorage.removeItem('token');
          setToken(null);
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = async (credentials: { email: string; password: string; rememberMe?: boolean }) => {
    const response = await authService.login(credentials);
    localStorage.setItem('token', response.access_token);
    setToken(response.access_token);
    setUser(response.user);
    router.push('/dashboard');
    return response;
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch {
      // Ignorar errores
    }
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    router.push('/login');
  };

  return {
    user,
    token,
    isLoading,
    isAuthenticated: !!token && !!user,
    login,
    logout,
  };
};