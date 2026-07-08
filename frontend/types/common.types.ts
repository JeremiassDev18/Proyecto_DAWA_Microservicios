export interface ApiResponse<T> {
  data?: T
  error?: string
  detail?: string
  message?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface SelectOption {
  value: number
  label: string
}
