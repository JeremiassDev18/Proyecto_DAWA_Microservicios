'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { Toaster } from 'react-hot-toast'
import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { useState, useEffect } from 'react'
import { theme } from '@/theme'
import { setLogoutHandler } from '@/services/api'
import { QUERY_STALE_TIME, QUERY_RETRY, TOAST_DURATION } from '@/config/constants'

function AuthBridge({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    import('@/hooks/useAuth').then(({ getGlobalLogout }) => {
      const logout = getGlobalLogout()
      if (logout) setLogoutHandler(logout)
    })
  }, [])
  return <>{children}</>
}

function ClientOnly({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])
  return mounted ? <>{children}</> : null
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: QUERY_STALE_TIME,
        retry: QUERY_RETRY,
        refetchOnWindowFocus: false,
      },
    },
  }))

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AuthBridge>
          <ClientOnly>
            {children}
          </ClientOnly>
        </AuthBridge>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: TOAST_DURATION,
            style: {
              borderRadius: 12,
              padding: '12px 16px',
              fontSize: '0.875rem',
            },
          }}
        />
        {process.env.NODE_ENV === 'development' && (
          <ReactQueryDevtools initialIsOpen={false} />
        )}
      </ThemeProvider>
    </QueryClientProvider>
  )
}
