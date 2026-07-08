import toast from 'react-hot-toast'

const TOAST_COLORS = {
  success: '#16a34a',
  error: '#dc2626',
  info: '#0284c7',
  warning: '#d97706',
}

export const useToast = () => {
  const showToast = (message: string, type: 'success' | 'error' | 'info' | 'warning' = 'info') => {
    const styles = {
      success: { icon: '✅', style: { background: TOAST_COLORS.success, color: 'white' } },
      error: { icon: '❌', style: { background: TOAST_COLORS.error, color: 'white' } },
      info: { icon: 'ℹ️', style: { background: TOAST_COLORS.info, color: 'white' } },
      warning: { icon: '⚠️', style: { background: TOAST_COLORS.warning, color: 'white' } },
    }

    const config = styles[type]
    toast(message, {
      icon: config.icon,
      style: config.style,
    })
  }

  return { showToast }
}
