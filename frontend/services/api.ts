import axios, { AxiosInstance, type InternalAxiosRequestConfig, type AxiosRequestConfig, type AxiosError } from 'axios'
import { API_CONFIG } from '@/lib/api.config'

let logoutHandler: (() => void) | null = null

export function setLogoutHandler(handler: () => void) {
  logoutHandler = handler
}

function getToken(): string | null {
  if (typeof document === 'undefined') return null
  const match = document.cookie.match(/(?:^|; )token=([^;]*)/)
  return match ? decodeURIComponent(match[1]) : null
}

export class ApiError {
  constructor(
    public status: number,
    public message: string,
    public data?: unknown,
  ) {}
}

function extractErrorMessage(error: AxiosError): string {
  const data = error.response?.data as Record<string, unknown> | undefined
  if (!data) return error.message || 'Error de red'
  return (data.error || data.detail || data.message || error.message || 'Error desconocido') as string
}

function createClient(baseURL: string): AxiosInstance {
  const client = axios.create({
    baseURL,
    timeout: 30000,
    headers: { 'Content-Type': 'application/json' },
  })

  client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })

  client.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
      const status = error.response?.status

      if (status === 401 && logoutHandler) {
        document.cookie = 'token=; path=/; max-age=0; SameSite=Lax'
        logoutHandler()
      }

      const apiError = new ApiError(
        status ?? 0,
        extractErrorMessage(error),
        error.response?.data,
      )

      return Promise.reject(apiError)
    },
  )

  return client
}

const serviceClients = new Map<string, AxiosInstance>()

function getServiceClient(service: string): AxiosInstance {
  if (serviceClients.has(service)) return serviceClients.get(service)!
  const baseURL = `${API_CONFIG.gateway}${(API_CONFIG.services as Record<string, string>)[service] || ''}`
  const client = createClient(baseURL)
  serviceClients.set(service, client)
  return client
}

export const api = {
  security: {
    get: <T>(url: string, config?: AxiosRequestConfig) =>
      getServiceClient('security').get<T>(url, config).then((r) => r.data),
    post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
      getServiceClient('security').post<T>(url, data, config).then((r) => r.data),
    put: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
      getServiceClient('security').put<T>(url, data, config).then((r) => r.data),
    delete: <T>(url: string, config?: AxiosRequestConfig) =>
      getServiceClient('security').delete<T>(url, config).then((r) => r.data),
  },
  admin: {
    get: <T>(url: string, config?: AxiosRequestConfig) =>
      getServiceClient('admin').get<T>(url, config).then((r) => r.data),
    post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
      getServiceClient('admin').post<T>(url, data, config).then((r) => r.data),
    put: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
      getServiceClient('admin').put<T>(url, data, config).then((r) => r.data),
    delete: <T>(url: string, config?: AxiosRequestConfig) =>
      getServiceClient('admin').delete<T>(url, config).then((r) => r.data),
  },
  tutorias: {
    get: <T>(url: string, config?: AxiosRequestConfig) =>
      getServiceClient('tutorias').get<T>(url, config).then((r) => r.data),
    post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
      getServiceClient('tutorias').post<T>(url, data, config).then((r) => r.data),
    put: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
      getServiceClient('tutorias').put<T>(url, data, config).then((r) => r.data),
    delete: <T>(url: string, config?: AxiosRequestConfig) =>
      getServiceClient('tutorias').delete<T>(url, config).then((r) => r.data),
  },
  chatbot: {
    get: <T>(url: string, config?: AxiosRequestConfig) =>
      getServiceClient('chatbot').get<T>(url, config).then((r) => r.data),
    post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
      getServiceClient('chatbot').post<T>(url, data, config).then((r) => r.data),
    put: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
      getServiceClient('chatbot').put<T>(url, data, config).then((r) => r.data),
    delete: <T>(url: string, config?: AxiosRequestConfig) =>
      getServiceClient('chatbot').delete<T>(url, config).then((r) => r.data),
  },
}
