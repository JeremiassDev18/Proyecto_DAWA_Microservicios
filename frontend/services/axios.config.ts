import axios from 'axios';
import { API_CONFIG } from '@/lib/api.config';

class ApiClient {
  private static instance: ApiClient;
  private clients: Map<string, any> = new Map();

  static getInstance(): ApiClient {
    if (!ApiClient.instance) {
      ApiClient.instance = new ApiClient();
    }
    return ApiClient.instance;
  }

  getClient(service: string) {
    if (this.clients.has(service)) {
      return this.clients.get(service)!;
    }

    const baseURL = `${API_CONFIG.gateway}${this.getServicePath(service)}`;
    const client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    client.interceptors.request.use(
      (config: any) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error: any) => Promise.reject(error)
    );

    client.interceptors.response.use(
      (response: any) => response,
      (error: any) => {
        if (error.response?.status === 401) {
          this.handleLogout();
        }
        return Promise.reject(error);
      }
    );

    this.clients.set(service, client);
    return client;
  }

  private getServicePath(service: string): string {
    const paths: Record<string, string> = {
      security: API_CONFIG.services.security,
      admin: API_CONFIG.services.admin,
      tutorias: API_CONFIG.services.tutorias,
      chatbot: API_CONFIG.services.chatbot,
    };
    return paths[service] || '';
  }

  private getToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('token');
    }
    return null;
  }

  private handleLogout(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
  }
}

export const apiClient = ApiClient.getInstance();